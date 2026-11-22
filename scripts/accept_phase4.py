"""Fail-closed Phase 4 gate: tests, two tolerance studies and independent raw audit."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from circuforge.evaluation.acceptance import validate_junit
from circuforge.evaluation.robust_acceptance import POLICY, audit_replay
from circuforge.optimization.robustness import load_experiment
from circuforge.simulation.ngspice import preflight

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new writable evidence directory")
    parser.add_argument("--manifest", type=Path, default=ROOT / "examples/robustness-v1.json")
    parser.add_argument("--ngspice", help="trusted executable override")
    args = parser.parse_args(argv)
    created = False
    decision = {"status": "blocked", "policy": POLICY, "acceptance_mode": "automated",
                "manual_review_required": False}
    commands = []
    try:
        args.output = args.output.resolve()
        args.manifest = args.manifest.resolve()
        load_experiment(args.manifest)
        import matplotlib  # optional report extra; fail before starting any expensive experiment
        info = preflight(args.ngspice)
        args.output.mkdir(parents=True, exist_ok=False)
        created = True
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src"),
               "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "CIRCUFORGE_NGSPICE": info.executable}
        env.pop("PYTEST_ADDOPTS", None)

        def execute(command, log_name, timeout):
            commands.append(command)
            with (args.output / log_name).open("wb") as log:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL, timeout=timeout, shell=False)
            if result.returncode != 0:
                raise ValueError(f"process exited {result.returncode}; see {log_name}")

        junit = args.output / "tests.xml"
        print("Running full test suite...", flush=True)
        execute([sys.executable, "-m", "pytest", "-q", "-ra", "--junitxml", str(junit),
                 "-o", f"cache_dir={args.output / 'pytest-cache'}"], "tests.log", 240)
        tests = validate_junit(junit)
        print(f"All {tests} tests passed without skips.", flush=True)
        for name in ("first", "replay"):
            print(f"Running fresh bounded tolerance study: {name}...", flush=True)
            execute([sys.executable, str(ROOT / "scripts/compare_robustness.py"), "--manifest", str(args.manifest),
                     "--ngspice", info.executable, "--output", str(args.output / name)], name + ".log", 600)
        print("Auditing raw physics, tolerance samples, objectives, holdout statistics and exact replay...", flush=True)
        decision = audit_replay(args.manifest, args.output / "first", args.output / "replay")
        decision.update(tests_passed=tests, commands=commands, ngspice_version=info.version,
                        manifest=str(args.manifest.resolve()), plotting_version=matplotlib.__version__)
        print(f"PASS: {decision['cases']} cases, {decision['seeds']} seeds, "
              f"{decision['audited_calls_including_replay']} raw calls including exact replay. "
              "Empirical nominal/holdout outcomes retained without requiring an optimizer win.", flush=True)
        code = 0
    except (OSError, ValueError, KeyError, TypeError, ImportError, ET.ParseError, subprocess.SubprocessError, RuntimeError) as exc:
        decision.update(status="blocked", error=str(exc), commands=commands,
                        next_action="repair and reproduce evidence; do not bypass the automatic gate")
        print(json.dumps(decision, indent=2), file=sys.stderr)
        code = 1 if created else 2
    if created:
        decision["executed_at_utc"] = datetime.now(timezone.utc).isoformat()
        (args.output / "acceptance.json").write_text(json.dumps(decision, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
