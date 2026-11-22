"""Run the explicitly owner-approved zero-spend local-model trial, once."""
import argparse
from pathlib import Path

from circuforge.evaluation.local_trial import load_trial, run_trial
from circuforge.simulation.ngspice import Ngspice

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=ROOT / "examples/local-proposal-trial-v1.json")
    parser.add_argument("--output", type=Path, required=True, help="new writable experiment directory")
    parser.add_argument("--ngspice", help="trusted executable override")
    parser.add_argument("--continue-rejected-pilot", action="store_true",
                        help="one conservative continuation of the recorded first rejected pilot; never reset caps")
    args = parser.parse_args(argv)
    try:
        config = load_trial(args.policy)
        simulator = Ngspice(args.ngspice)
        output = args.output.resolve()
        if not args.continue_rejected_pilot:
            output.mkdir(parents=True, exist_ok=False)
        result = run_trial(config, simulator, output, continue_rejected_pilot=args.continue_rejected_pilot)
        print(f"{result['status']}: {result['budget']['model_requests']} model requests; "
              f"{result['budget']['spice_attempts']} SPICE attempts; zero provider cost.")
        return 0 if result["status"] == "completed" else 1
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"Local trial blocked: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
