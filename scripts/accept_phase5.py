"""Full tests, a fresh isolated package install and a real loopback CLI/API audit."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

from circuforge.evaluation.acceptance import validate_junit
from circuforge.evaluation.design_acceptance import POLICY, audit_walkthrough
from circuforge.simulation.ngspice import preflight

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new writable directory for all installation/test evidence")
    parser.add_argument("--ngspice", help="trusted executable override")
    args = parser.parse_args(argv)
    created = False
    decision = {"status": "blocked", "policy": POLICY, "acceptance_mode": "automated", "manual_review_required": False}
    commands = []
    try:
        args.output = args.output.resolve()
        info = preflight(args.ngspice)
        versions = {name: metadata.version(name) for name in ("numpy", "pydantic", "scipy", "matplotlib", "fastapi", "uvicorn", "httpx", "pytest")}
        args.output.mkdir(parents=True, exist_ok=False)
        created = True
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
               "CIRCUFORGE_NGSPICE": info.executable, "MPLCONFIGDIR": str(args.output / "matplotlib-cache")}
        env.pop("PYTEST_ADDOPTS", None)

        def execute(command, log_name, timeout):
            commands.append(command)
            with (args.output / log_name).open("wb") as log:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL, shell=False, timeout=timeout)
            if result.returncode:
                raise ValueError(f"process exited {result.returncode}; see {log_name}")

        junit = args.output / "tests.xml"
        print("Running full suite, including real API/CLI integration...", flush=True)
        execute([sys.executable, "-m", "pytest", "-q", "-ra", "--junitxml", str(junit),
                 "-o", f"cache_dir={args.output / 'pytest-cache'}"], "tests.log", 300)
        count = validate_junit(junit)
        env.pop("PYTHONPATH", None)  # installation and -I walkthrough must not see source checkout imports
        print(f"All {count} tests passed without skips. Building source-byte-preserving wheel...", flush=True)
        snapshot = args.output / "source"
        snapshot.mkdir()
        shutil.copy2(ROOT / "pyproject.toml", snapshot / "pyproject.toml")
        shutil.copytree(ROOT / "src", snapshot / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        wheels = args.output / "wheels"
        execute([sys.executable, "-m", "pip", "wheel", "--no-deps", "--index-url", "https://pypi.org/simple",
                 "--wheel-dir", str(wheels), str(snapshot)], "build.log", 180)
        candidates = list(wheels.glob("circuforge-*.whl"))
        if len(candidates) != 1:
            raise ValueError("expected one built project wheel")
        wheel = candidates[0]
        installed = args.output / "installed"
        print("Creating fresh virtual environment and installing pinned tested dependencies...", flush=True)
        execute([sys.executable, "-m", "venv", str(installed)], "venv.log", 90)
        python = installed / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        constraints = args.output / "constraints.txt"
        constraints.write_text("".join(f"{name}=={version}\n" for name, version in versions.items()), encoding="utf-8")
        execute([str(python), "-m", "pip", "install", "--index-url", "https://pypi.org/simple", "--constraint", str(constraints),
                 str(wheel) + "[api,test]"], "install.log", 240)
        print("Running installed package with Python -I through CLI and real loopback HTTP...", flush=True)
        walkthrough = args.output / "walkthrough"
        execute([str(python), "-I", str(ROOT / "scripts/walkthrough_phase5.py"), "--source", str(ROOT / "examples"),
                 "--output", str(walkthrough), "--ngspice", info.executable], "walkthrough.log", 180)
        decision = audit_walkthrough(ROOT / "examples", walkthrough, installed)
        decision.update(tests_passed=count, wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
                        versions=versions, ngspice_version=info.version, commands=commands)
        print(f"PASS: {count} tests, fresh isolated install, 27 real calls, 18 raw calls audited; JSON traces matched.", flush=True)
        code = 0
    except (OSError, ValueError, KeyError, TypeError, ImportError, RuntimeError, subprocess.SubprocessError, ET.ParseError, zipfile.BadZipFile) as exc:
        decision.update(status="blocked", error=str(exc), commands=commands,
                        next_action="repair dependencies/code/evidence and rerun; no manual waiver")
        print(json.dumps(decision, indent=2), file=sys.stderr)
        code = 1 if created else 2
    if created:
        decision["executed_at_utc"] = datetime.now(timezone.utc).isoformat()
        (args.output / "acceptance.json").write_text(json.dumps(decision, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
