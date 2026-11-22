"""Bounded nominal/robust component-tolerance experiment with independent holdout."""
import argparse
import importlib.util
from pathlib import Path
import sys

from circuforge.evaluation.robust_plot import plot_comparison
from circuforge.optimization.robustness import load_experiment, run_experiment
from circuforge.simulation.ngspice import Ngspice, SimulationError

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "examples/robustness-v1.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ngspice")
    args = parser.parse_args(argv)
    try:
        load_experiment(args.manifest)
        if importlib.util.find_spec("matplotlib") is None:
            raise ValueError("plot dependency unavailable; install circuforge[report]")
        if args.output.exists():
            raise FileExistsError("output must be a new directory")
        summary = run_experiment(args.manifest, args.output, Ngspice(args.ngspice))
        if any(r["stage"] != "completed" for r in summary["trials"]):
            raise ValueError("experiment contains failed/partial trials; inspect reports and raw artifacts")
        plot_comparison(summary, args.output / "comparison.png")
        print(f"Completed {summary['completed_trials']} trials; {summary['actual_calls']} actual SPICE calls.", flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, SimulationError) as exc:
        print(f"Tolerance experiment blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
