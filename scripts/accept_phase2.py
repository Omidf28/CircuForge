"""One fail-closed local command: full tests, fresh bounded SPICE, raw audit."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from pydantic import TypeAdapter

from circuforge.domain.cases import Case
from circuforge.evaluation.acceptance import POLICY, audit_phase2, validate_junit
from circuforge.simulation.ngspice import preflight

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new writable evidence directory")
    parser.add_argument("--ngspice", help="trusted executable override")
    args = parser.parse_args(argv)
    created = False
    decision = {"status": "blocked", "policy": POLICY, "acceptance_mode": "automated",
                "manual_review_required": False}
    try:
        args.output = args.output.resolve()
        # Preflight and all fixed case/resource limits before allocating output.
        cases_path = ROOT / "examples/phase2-review-cases.json"
        cases = TypeAdapter(list[Case]).validate_json(cases_path.read_bytes())
        if not 5 <= len(cases) <= 8 or sum(c.spec.max_evaluations * 3 for c in cases) > 1000:
            raise ValueError("automatic gate requires 5–8 cases and <=1000 comparison calls")
        info = preflight(args.ngspice)
        args.output.mkdir(parents=True, exist_ok=False)
        created = True
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src"),
               "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "CIRCUFORGE_NGSPICE": info.executable}
        env.pop("PYTEST_ADDOPTS", None)
        junit = args.output / "tests.xml"
        test_command = [sys.executable, "-m", "pytest", "-q", "-ra", "--junitxml", str(junit),
                        "-o", f"cache_dir={args.output / 'pytest-cache'}"]
        print("Running full test suite...", flush=True)
        with (args.output / "tests.log").open("wb") as log:
            result = subprocess.run(test_command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, timeout=180, shell=False)
        if result.returncode != 0:
            raise ValueError(f"test process exited {result.returncode}; see tests.log")
        count = validate_junit(junit)
        print(f"All {count} tests passed without skips. Running fresh bounded comparison...", flush=True)
        comparison = args.output / "comparison"
        compare_command = [sys.executable, str(ROOT / "scripts/compare_phase2.py"), "--seed", "42",
                           "--ngspice", info.executable, "--output", str(comparison)]
        with (args.output / "comparison.log").open("wb") as log:
            result = subprocess.run(compare_command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, timeout=180, shell=False)
        if result.returncode != 0:
            raise ValueError(f"comparison exited {result.returncode}; see comparison.log")
        print("Auditing every raw response, metric, status and call count...", flush=True)
        decision = audit_phase2(comparison, cases_path, junit)
        decision.update(executed_at_utc=datetime.now(timezone.utc).isoformat(),
                        test_command=test_command, comparison_command=compare_command,
                        ngspice_version=info.version)
        (args.output / "acceptance.json").write_text(json.dumps(decision, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"PASS: technical gate; {decision['raw_calls_checked']} audited calls, "
              f"{decision['design_passes']} target passes / {decision['design_misses']} misses. "
              "No manual review required.", flush=True)
        return 0
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, subprocess.SubprocessError, RuntimeError) as exc:
        decision.update(status="blocked", error=str(exc), next_action="repair/reproduce evidence and rerun; do not bypass checks")
        if created:
            try:
                (args.output / "acceptance.json").write_text(json.dumps(decision, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            except OSError:
                pass
        print(json.dumps(decision, indent=2), file=sys.stderr)
        return 1 if created else 2


if __name__ == "__main__":
    raise SystemExit(main())
