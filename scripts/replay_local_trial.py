"""Prepare/run a separately approved two-request local replay; old ledgers stay closed."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.acceptance import audit_evaluation, require
from circuforge.evaluation.local_trial import _record, _session, _wait_slot
from circuforge.evaluation.records import environment
from circuforge.local_provider import (LocalTrialLimit, MAX_OUTPUT, RESERVED_INPUT,
                                      OllamaProvider, TrialBudget, write_json)
from circuforge.optimization.base import Evaluator
from circuforge.proposals import TokenReservation
from circuforge.simulation.ngspice import Ngspice

ROOT = Path(__file__).resolve().parents[1]
POLICY = "p6-local-replay-supplement-v1"
LIMITS = dict(max_model_requests=2, max_total_reserved_tokens=4608, max_seconds=120,
              max_spice_attempts=2, max_provider_cost_microusd=0, cpu_threads=2,
              gpu_layers=0, automatic_retries=0)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_hashes(source: Path) -> dict:
    return {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in ("result.json", "budget.json", "approved-policy.json")}


def load_policy(path: Path) -> dict:
    policy = read(path)
    require(policy.get("policy") == POLICY and policy.get("limits") == LIMITS, "unsupported replay policy/caps")
    require(policy.get("status") == "approved_local_only" and policy.get("inference_approved") is True and
            isinstance(policy.get("owner_response"), str) and bool(policy["owner_response"].strip()),
            "fresh bounded replay resource approval missing")
    require(policy.get("execution_closed") is False, "supplemental allowance closed")
    return policy


def audit_primary(source: Path) -> dict:
    spec = importlib.util.spec_from_file_location("supplement_primary_auditor", ROOT / "scripts/audit_local_trial.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.audit(source)
    require(result["integrity_status"] == "passed" and result["comparison_data_status"] == "complete" and
            result["completed_equal_budget_trials"] == 4, "primary comparisons are not eligible")
    return result


class ReplayBudget(TrialBudget):
    """Smaller, separate envelope; original TrialBudget counters are never reopened."""

    def remaining(self) -> float:
        super().remaining()
        remaining = 120.0 - (self._clock() - self.started)
        if not 0 < remaining <= 120:
            raise LocalTrialLimit("supplemental 120-second deadline reached")
        return remaining

    def reserve_model(self) -> int:
        if self.requests >= 2:
            raise LocalTrialLimit("supplemental two-request ceiling reached")
        return super().reserve_model()

    def reserve_spice(self):
        if self.spice_calls >= 2:
            raise LocalTrialLimit("supplemental two-SPICE ceiling reached")
        return super().reserve_spice()


class ReplaySimulator:
    """Charge each attempt and shorten its timeout to the remaining total window."""

    def __init__(self, simulator, budget):
        self.simulator, self.budget, self.info = simulator, budget, simulator.info

    def simulate(self, spec, candidate):
        self.budget.reserve_spice()
        bounded = spec.model_copy(update={"timeout_s": min(spec.timeout_s, self.budget.remaining())})
        return self.simulator.simulate(bounded, candidate)


def run(policy: dict, source: Path, simulator, output: Path, *, transport=None) -> dict:
    """Input/output paths are trusted operator arguments, never model suggestions."""
    # Programmatic callers must pass the same explicit permission check as CLI callers.
    require(policy.get("policy") == POLICY and policy.get("limits") == LIMITS and
            policy.get("status") == "approved_local_only" and policy.get("inference_approved") is True and
            isinstance(policy.get("owner_response"), str) and bool(policy["owner_response"].strip()) and
            policy.get("execution_closed") is False, "fresh bounded replay resource approval missing")
    require(source_hashes(source) == policy["source_sha256"], "primary source changed")
    primary = audit_primary(source)
    original = read(source / "result.json")
    config = read(source / "approved-policy.json")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "approved-policy.json", policy)
    budget = ReplayBudget(output)
    provider = OllamaProvider(budget, transport=transport)
    counted = ReplaySimulator(simulator, budget)
    result = dict(policy=POLICY, status="blocked", primary_audit=primary,
                  source_sha256=policy["source_sha256"], environment=environment(),
                  ngspice_version=simulator.info.version, replay=[], audited_spice_calls=0,
                  primary_allowance_reopened=False, comparisons_rescored=False,
                  phase6_accepted=False)
    try:
        provider.preflight()
        for index, case in enumerate(config["experiment"]["cases"]):
            spec = DesignSpec.model_validate(case["spec"])
            session = _session(spec, provider, 7, 1)
            raw = output / "replay" / case["id"]
            evaluator = Evaluator(spec, counted, raw)
            _wait_slot(budget)
            proposal = session.propose(TokenReservation(input_tokens=RESERVED_INPUT, output_tokens=MAX_OUTPUT))
            record = dict(case=case["id"], **_record(session, evaluator),
                          exact_candidate_replay=False)
            result["replay"].append(record)
            try:
                sent = read(output / f"model-{index + 1:03d}-request.json")
                require(sent == read(source / f"model-{index + 1:03d}-request.json"), "replay prompt/options differ")
                require(proposal.status in {"accepted", "invalid_candidate"}, "replay transport/usage failure")
                if proposal.status == "accepted":
                    evaluation = evaluator.evaluate(proposal.candidate)
                    require(evaluation.verified, "replay physical verification failed")
                    audit_evaluation(raw, evaluation.artifact, spec, evaluation, simulator.info.version)
                    result["audited_spice_calls"] += 1
                record["exact_candidate_replay"] = (proposal.candidate is not None and
                    proposal.candidate.model_dump() == original["pilot"][index]["proposal_ledger"][0]["candidate"])
            finally:
                record.update(_record(session, evaluator))
                write_json(output / "progress.json", result)
        require(source_hashes(source) == policy["source_sha256"], "primary changed during replay")
        result["status"] = "completed_observations"
        # A separate read-only composite audit is still required; runner self-report cannot accept Phase 6.
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        result["error"] = str(exc)
    finally:
        budget.save()
        result["budget"] = read(output / "budget.json")
        result["finished_environment"] = environment()
        if result["finished_environment"] != result["environment"]:
            result["status"] = "blocked"
            result["error"] = "source/environment changed during replay"
        write_json(output / "result.json", result)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=ROOT / "examples/local-replay-supplement-v1.json")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ngspice")
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)  # Before constructing a simulator or contacting a model.
        require(source_hashes(args.source) == policy["source_sha256"], "primary source changed")
        result = run(policy, args.source, Ngspice(args.ngspice), args.output)
        print(f"{result['status']}: {result['budget']['model_requests']} new model requests, "
              f"{result['budget']['spice_attempts']} new SPICE attempts; original window unchanged.")
        return 0 if result["status"] == "completed_observations" else 1
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        print(f"Replay blocked: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
