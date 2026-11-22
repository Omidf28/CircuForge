"""Fresh tests and two raw-audited, one-call ideal-RC comparisons; no model traffic."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from xml.etree import ElementTree

from circuforge.evaluation.acceptance import require, validate_junit
from circuforge.evaluation.physics_comparison import audit_replay, load_experiment
from circuforge.evaluation.records import environment
from circuforge.simulation.ngspice import preflight

ROOT = Path(__file__).resolve().parents[1]


def source_hashes():
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for folder in ("src", "scripts", "tests") for path in sorted((ROOT / folder).rglob("*.py"))}


def plot(result, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    methods = list(result["aggregates"])
    values = [result["aggregates"][method]["free_domain_passes"] for method in methods]
    totals = [result["aggregates"][method]["free_domain_trials"] for method in methods]
    figure, axes = plt.subplots(figsize=(8, 4.8), layout="constrained")
    axes.bar(methods, values, color=["#64748b"] * 3 + ["#16715a"])
    for index, (value, total) in enumerate(zip(values, totals)):
        axes.text(index, value + .6, f"{value}/{total}", ha="center")
    axes.set_ylim(0, max(totals) + 5)
    axes.set_ylabel("Free-domain design passes (0.1% cutoff tolerance)")
    axes.set_title("New ideal-RC pilot: one actual SPICE call per method/trial")
    figure.supxlabel("Curated cases; analytic/grid seed repeats are controls; known-physics advantage is explicit", fontsize=8)
    figure.savefig(destination / "free-domain-passes.png", dpi=160)
    plt.close(figure)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "examples/physics-onecall-v1.json")
    parser.add_argument("--ngspice")
    args = parser.parse_args(argv)
    created = False
    decision = dict(status="blocked", policy="physics-onecall-v1", acceptance_mode="automated",
                    manual_review_required=False, model_requests=0)
    try:
        load_experiment(args.manifest)
        import matplotlib
        info = preflight(args.ngspice)
        initial_environment, initial_sources = environment(), source_hashes()
        args.output.mkdir(parents=True, exist_ok=False)
        created = True
        snapshot = args.output / "source"
        snapshot.mkdir()
        shutil.copytree(ROOT / "src", snapshot / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in ("pyproject.toml", "scripts/accept_analytic_rc.py", "scripts/compare_analytic_rc.py",
                     "examples/physics-onecall-v1.json", "examples/benchmark-v2.json", "examples/design-analytic-rc.json"):
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
               "CIRCUFORGE_NGSPICE": info.executable, "MPLCONFIGDIR": str(args.output / "matplotlib-cache")}
        env.pop("PYTEST_ADDOPTS", None)
        commands = []

        def execute(command, name, timeout):
            commands.append(command)
            with (args.output / name).open("wb") as log:
                result = subprocess.run(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                        stdout=log, stderr=subprocess.STDOUT, shell=False, timeout=timeout)
            require(result.returncode == 0, f"process exited {result.returncode}; inspect {name}")

        print("Running full current tests...", flush=True)
        execute([sys.executable, "-m", "pytest", "-q", "-ra", "-p", "no:cacheprovider",
                 "--junitxml", str(args.output / "tests.xml")], "tests.log", 360)
        tests = validate_junit(args.output / "tests.xml")
        print(f"All {tests} tests passed without skips. Running first/replay comparison...", flush=True)
        for name in ("first", "replay"):
            execute([sys.executable, str(ROOT / "scripts/compare_analytic_rc.py"), "--manifest", str(args.manifest),
                     "--ngspice", info.executable, "--output", str(args.output / name)], name + ".log", 240)
        print("Auditing every raw response, budget, rejection and exact numerical replay...", flush=True)
        decision = audit_replay(args.manifest, args.output / "first", args.output / "replay")
        require(environment() == initial_environment and source_hashes() == initial_sources,
                "source/tests/environment changed during acceptance")
        decision.update(tests_passed=tests, environment=initial_environment, checked_sources=initial_sources,
                        commands=commands, manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                        ngspice_version=info.version, plotting_version=matplotlib.__version__, model_requests=0,
                        scope="ideal unloaded continuous first-order RC only; separate from historical experiments",
                        limitation="analytic method uses known physics; seeded repetitions of deterministic controls are not independent samples")
        plot(decision, args.output)
        print(f"PASS: {tests} tests, {decision['audited_calls_including_replay']} raw-audited calls including replay.", flush=True)
        print(json.dumps(decision["aggregates"], indent=2), flush=True)
        code = 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError, subprocess.SubprocessError, ElementTree.ParseError) as exc:
        decision.update(status="blocked", error=str(exc))
        print(f"Physics comparison blocked: {exc}", flush=True)
        code = 1
    if created:
        decision["executed_at_utc"] = datetime.now(timezone.utc).isoformat()
        (args.output / "acceptance.json").write_text(json.dumps(decision, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
