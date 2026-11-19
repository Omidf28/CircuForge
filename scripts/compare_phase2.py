"""Bounded five-case evidence for P2-H1 review, not a Phase 3 benchmark."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

from pydantic import TypeAdapter

from circuforge.domain.cases import Case
from circuforge.optimization.baselines import Options, compare
from circuforge.simulation.ngspice import Ngspice, SimulationError

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "examples/phase2-review-cases.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ngspice")
    args = parser.parse_args(argv)
    try:
        Options(method="random", seed=args.seed)
        content = args.cases.read_bytes()
        cases = TypeAdapter(list[Case]).validate_json(content)
        if not 1 <= len(cases) <= 8 or len({c.id for c in cases}) != len(cases):
            raise ValueError("provide 1–8 uniquely identified review cases")
        cap = sum(c.spec.max_evaluations * 3 for c in cases)
        if cap > 1000:
            raise ValueError("review batch exceeds the 1000 total attempted-call cap")
        if args.output.exists():
            raise FileExistsError("output must be a new directory")
        simulator = Ngspice(args.ngspice)
        args.output.mkdir(parents=True)
        rows = []
        all_measured = True
        for case in cases:
            runs = compare(case.spec, simulator, seed=args.seed, output=args.output / case.id)
            matched = len({r.simulator_calls for r in runs}) == 1
            for run in runs:
                row = {"case": case.id, "target_hz": case.spec.cutoff_hz, "method": run.options.method,
                       "budget": case.spec.max_evaluations, "simulator_calls": run.simulator_calls,
                       "matched_actual_calls": matched, "converged": run.converged,
                       "target_relative_error": run.best.relative_error if run.best else None,
                       "objective": run.best.objective if run.best else None,
                       "failures": run.failures, "stop_reason": run.stop_reason}
                rows.append(row)
                all_measured = all_measured and run.best is not None
                print(f"{case.id}/{run.options.method}: calls={run.simulator_calls}, "
                      f"target_pass={run.converged}, error={row['target_relative_error']}", flush=True)
            summary = {"purpose": "Phase 2 baseline evidence for owner review; not a statistical benchmark",
                       "seed": args.seed, "configured_total_call_cap": cap,
                       "actual_calls": sum(r["simulator_calls"] for r in rows),
                       "cases_sha256": hashlib.sha256(content).hexdigest(),
                       "completed_cases": len(rows) // 3, "planned_cases": len(cases),
                       "acceptance_status": "requires_automated_gate", "manual_review_required": False,
                       "results": rows}
            (args.output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            with (args.output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        return 0 if all_measured else 1
    except (OSError, ValueError, SimulationError) as exc:
        print(f"Phase 2 comparison error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
