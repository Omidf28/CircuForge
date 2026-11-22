"""Run one prespecified comparison of four methods at one actual SPICE call each."""
import argparse
from pathlib import Path

from circuforge.evaluation.physics_comparison import run_comparison
from circuforge.simulation.ngspice import Ngspice

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "examples/physics-onecall-v1.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ngspice")
    args = parser.parse_args()
    result = run_comparison(args.manifest, args.output, Ngspice(args.ngspice))
    print(f"Recorded {result['completed_trials']} trials and {result['actual_calls']} actual calls; not accepted until audited.")


if __name__ == "__main__":
    main()
