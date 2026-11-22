"""Synthetic audit fixtures only; no real model or physical simulation claims."""
import importlib.util
import json
from pathlib import Path

import pytest

from circuforge.domain.specs import DesignSpec
from circuforge.local_provider import DIGEST, MODEL
from circuforge.proposals import ProposalSession, ProviderReply, TokenReservation, TokenUsage


def command():
    path = Path(__file__).resolve().parents[2] / "scripts/audit_local_trial.py"
    spec = importlib.util.spec_from_file_location("local_trial_audit_command", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence(root):
    policy_path = Path(__file__).resolve().parents[2] / "examples/local-proposal-trial-v1.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy.pop("execution_closed", None)

    class SavedFixture:
        def propose(self, request):
            return ProviderReply("{}", TokenUsage(input_tokens=2, output_tokens=3))

    session = ProposalSession(DesignSpec.model_validate(policy["experiment"]["cases"][0]["spec"]), SavedFixture(), seed=7)
    session.propose(TokenReservation(input_tokens=2048, output_tokens=256))
    record = dict(proposal_ledger=[p.model_dump() for p in session.history], usage=session.usage.model_dump(),
                  simulator_calls=0, history=[], best=None, cache_hits=0)
    files = {
        "approved-policy.json": policy,
        "local-model.json": dict(model=MODEL, digest=DIGEST),
        "result.json": dict(status="blocked", pilot=[record], replay=[], trials=[], audited_spice_calls=0),
        "budget.json": dict(model_requests=1, reserved_tokens=2304, spice_attempts=0, cost_microusd=0,
                            elapsed_s=0.02, records=[dict(request=1, reserved_tokens=2304, status="reported",
                                                        client_elapsed_s=0.01, reported_usage=dict(input_tokens=2, output_tokens=3))]),
        "model-001-request.json": dict(model=MODEL, stream=False, keep_alive=0, prompt="Synthetic fixture only",
                                       options=dict(num_gpu=0, num_thread=2, num_predict=256, num_ctx=2048)),
        "model-001-response.json": dict(model=MODEL, done=True, response="{}", prompt_eval_count=2, eval_count=3),
    }
    for name, data in files.items():
        (root / name).write_text(json.dumps(data), encoding="utf-8")
    return files


def test_rejected_saved_response_can_have_valid_integrity_without_phase_acceptance(tmp_path):
    evidence(tmp_path)
    result = command().audit(tmp_path)
    assert result["integrity_status"] == "passed"
    assert result["phase6_comparison_status"] == "blocked_incomplete"
    assert result["reported_tokens_known"] == 5 and result["audited_real_spice_calls"] == 0


@pytest.mark.parametrize("statuses,count", [
    (["accepted", "invalid_candidate"], 2),
    (["accepted", "provider_error"], 1),
    (["provider_error", "invalid_response"], 0),
])
def test_failed_replay_attempts_are_not_completed_observations(statuses, count):
    records = [{"proposal_ledger": [{"status": status}]} for status in statuses]
    assert command().completed_replays(records) == count


@pytest.mark.parametrize("mutation", ["usage", "candidate", "cpu", "quota", "deadline", "call_claim"])
def test_inconsistent_model_or_budget_evidence_is_rejected(tmp_path, mutation):
    files = evidence(tmp_path)
    name = "model-001-response.json"
    if mutation == "usage":
        files[name]["eval_count"] = 4
    elif mutation == "candidate":
        files[name]["response"] = json.dumps(dict(topology="rc_lowpass", resistance_ohm=1000.0, capacitance_f=1e-7))
    elif mutation == "cpu":
        name = "model-001-request.json"
        files[name]["options"]["num_gpu"] = -1
    elif mutation == "quota":
        name = "budget.json"
        files[name]["model_requests"] = 33
    elif mutation == "deadline":
        name = "budget.json"
        files[name]["elapsed_s"] = 800.0
    else:
        name = "result.json"
        files[name]["pilot"][0]["simulator_calls"] = 1
    (tmp_path / name).write_text(json.dumps(files[name]), encoding="utf-8")
    with pytest.raises(ValueError):
        command().audit(tmp_path)
