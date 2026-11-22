"""Accept P6-C1 only: full tests and offline fixtures through audited real SPICE."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.acceptance import audit_evaluation, require, validate_junit
from circuforge.evaluation.records import environment
from circuforge.optimization.base import Evaluator
from circuforge.proposals import ProposalSession, ProviderReply, TokenUsage
from circuforge.simulation.ngspice import Ngspice, preflight

ROOT = Path(__file__).resolve().parents[1]
POLICY = "p6-c1-offline-contract-v1"


class OfflineFixture:
    """Prespecified smoke controls. These are not model-generated suggestions."""
    def propose(self, request):
        candidate = dict(topology="unsupported" if request.request_number == 1 else request.spec.filter_type,
                         resistance_ohm=2000.0 if request.request_number == 4 else 1000.0,
                         capacitance_f=1e-7)
        return ProviderReply(json.dumps(candidate), TokenUsage(input_tokens=2, output_tokens=3))


def verify_fixture(root: Path, topology: str, simulator: Ngspice) -> dict:
    spec = DesignSpec(filter_type=topology, max_evaluations=2)
    session = ProposalSession(spec, OfflineFixture(), seed=42)
    raw = root / topology / "evaluations"
    evaluator = Evaluator(spec, simulator, raw)
    rejected = session.propose()
    require(rejected.status == "invalid_candidate" and rejected.candidate is None and evaluator.calls == 0,
            "invalid topology was not rejected before simulation")
    for _ in range(3):
        proposal = session.propose()
        require(proposal.status == "accepted", "valid offline fixture rejected")
        evaluator.evaluate(proposal.candidate)
    require(evaluator.calls == 2 and evaluator.cache_hits == 1, "SPICE budget/cache mismatch")
    require([e.target_passed for e in evaluator.history] == [True, False], "reference pass or deliberate miss lost")
    require(session.usage.requests == 4 and session.usage.cost_microusd == 0,
            "offline request/cost ledger mismatch")
    for evaluation in evaluator.history:
        audit_evaluation(raw, evaluation.artifact, spec, evaluation, simulator.info.version)
    result = dict(spec=spec.model_dump(), session_usage=session.usage.model_dump(),
                  proposal_ledger=[p.model_dump() for p in session.history],
                  history=[e.model_dump() for e in evaluator.history],
                  simulator_calls=evaluator.calls, cache_hits=evaluator.cache_hits,
                  environment=environment(), ngspice_version=simulator.info.version,
                  usage_source="synthetic offline fixture, not tokenizer/provider billing",
                  actual_llm_calls=0)
    (root / topology / "report.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new writable evidence directory")
    parser.add_argument("--ngspice", help="trusted executable override")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    created = False
    decision = dict(status="blocked", policy=POLICY, scope="P6-C1 only", acceptance_mode="automated",
                    phase6_gate_passed=False, actual_llm_calls=0, provider_experiment="unrun")
    try:
        info = preflight(args.ngspice)
        output.mkdir(parents=True, exist_ok=False)
        created = True
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
               "CIRCUFORGE_NGSPICE": info.executable, "MPLCONFIGDIR": str(output / "matplotlib-cache")}
        env.pop("PYTEST_ADDOPTS", None)
        command = [sys.executable, "-m", "pytest", "-q", "-ra", "-p", "no:cacheprovider",
                   "--junitxml", str(output / "tests.xml")]
        decision["test_command"] = command
        print("Running complete suite (no skips permitted)...", flush=True)
        with (output / "tests.log").open("wb") as log:
            completed = subprocess.run(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, shell=False, timeout=180)
        require(completed.returncode == 0, "test process failed; see tests.log")
        count = validate_junit(output / "tests.xml")
        print(f"{count} tests passed. Auditing offline low/high-pass fixture calls...", flush=True)
        simulator = Ngspice(info.executable)
        results = [verify_fixture(output, topology, simulator) for topology in ("rc_lowpass", "rc_highpass")]
        decision.update(status="passed", tests_passed=count, cases=len(results),
                        audited_real_spice_calls=sum(r["simulator_calls"] for r in results),
                        offline_fixture_requests=8, reference_passes=2, deliberate_target_misses=2,
                        rejected_topologies=2, cache_hits=2, environment=environment(), ngspice_version=info.version)
        code = 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        decision["error"] = str(exc)
        code = 1 if created else 2
    if created:
        decision["executed_at_utc"] = datetime.now(timezone.utc).isoformat()
        (output / "acceptance.json").write_text(json.dumps(decision, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
