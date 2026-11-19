"""Run one versioned, bounded multi-seed nominal RC benchmark."""
import argparse
from pathlib import Path
import sys

from circuforge.evaluation.benchmark import load_benchmark, run_benchmark
from circuforge.simulation.ngspice import Ngspice, SimulationError

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "examples/benchmark-v2.json")
    parser.add_argument("--output", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--ngspice", help="trusted executable override")
    args = parser.parse_args(argv)
    try:
        load_benchmark(args.manifest)  # reject invalid cases/caps before simulator construction
        if args.output.exists():
            raise FileExistsError("output must be a new directory")
        summary = run_benchmark(args.manifest, args.output, Ngspice(args.ngspice))
        print(f"Completed {summary['completed_trials']} trials; {summary['actual_calls']} actual SPICE calls.")
        # Numerical target misses are exported, not confused with execution errors.
        return 0 if all(r["status"] == "infeasible_rejected" or r["candidate"] is not None
                        for r in summary["trials"]) else 1
    except (OSError, ValueError, SimulationError) as exc:
        print(f"Benchmark blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
