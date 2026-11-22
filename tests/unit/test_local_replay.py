"""Mock-only replay guard tests. No installed model or simulator is contacted."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from circuforge.local_provider import DIGEST, MODEL, LocalTrialLimit
from circuforge.domain.specs import CircuitCandidate, DesignSpec


def command(name="replay_local_trial"):
    path = Path(__file__).resolve().parents[2] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name + "_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy():
    return json.loads((Path(__file__).resolve().parents[2] / "examples/local-replay-supplement-v1.json").read_text(encoding="utf-8"))


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


def test_pending_policy_stops_before_simulator_or_model(tmp_path, monkeypatch):
    module = command()
    monkeypatch.setattr(module, "Ngspice", lambda *args: pytest.fail("pending approval must not construct simulator"))
    assert module.main(["--source", str(tmp_path), "--output", str(tmp_path / "new")]) == 2
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("change", [{"max_model_requests": 3}, {"max_seconds": 121},
                                  {"max_spice_attempts": 3}, {"max_provider_cost_microusd": 1},
                                  {"cpu_threads": 3}, {"automatic_retries": 1}])
def test_expanded_supplemental_caps_are_rejected(tmp_path, change):
    module = command()
    data = policy()
    data.update(status="approved_local_only", inference_approved=True, owner_response="synthetic test permission")
    data["limits"].update(change)
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="caps"):
        module.load_policy(path)


def test_two_request_cap_preserves_reservations_and_refuses_reopening(tmp_path):
    module = command()
    clock = Clock()
    budget = module.ReplayBudget(tmp_path, clock=clock)
    budget.reserve_model()
    clock.now += 1
    budget.reserve_model()
    with pytest.raises(LocalTrialLimit, match="two-request"):
        budget.reserve_model()
    assert json.loads((tmp_path / "budget.json").read_text())["reserved_tokens"] == 4608
    with pytest.raises(LocalTrialLimit, match="reset"):
        module.ReplayBudget(tmp_path, clock=clock)


def test_two_spice_cap_and_original_deadline_are_enforced(tmp_path):
    module = command()
    clock = Clock()
    budget = module.ReplayBudget(tmp_path, clock=clock)
    budget.reserve_spice()
    budget.reserve_spice()
    with pytest.raises(LocalTrialLimit, match="two-SPICE"):
        budget.reserve_spice()
    clock.now = 120
    with pytest.raises(LocalTrialLimit, match="120-second"):
        budget.remaining()


def test_changed_primary_cannot_allocate_output_or_call_provider(tmp_path):
    module = command()
    data = policy()
    data.update(status="approved_local_only", inference_approved=True, owner_response="synthetic test permission")
    for name in data["source_sha256"]:
        (tmp_path / name).write_text("{}")
    with pytest.raises(ValueError, match="source changed"):
        module.run(data, tmp_path, object(), tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_simulator_timeout_is_clipped_to_remaining_total_window(tmp_path):
    module = command()
    clock = Clock()
    budget = module.ReplayBudget(tmp_path, clock=clock)
    seen = []
    simulator = SimpleNamespace(info="fixture", simulate=lambda spec, candidate: seen.append(spec))
    counted = module.ReplaySimulator(simulator, budget)
    spec = DesignSpec(timeout_s=5.0)
    clock.now = 119.75
    counted.simulate(spec, CircuitCandidate())
    assert seen[0].timeout_s == 0.25
    assert spec.timeout_s == 5.0
    assert budget.spice_calls == 1


@pytest.mark.parametrize("tamper", ["usage", "request", "candidate", "source", "budget", "primary", "best", "transport"])
def test_mock_returned_invalid_observations_and_composite_corruption_guards(tmp_path, monkeypatch, tamper):
    module = command()
    source = tmp_path / "primary"
    source.mkdir()
    config = json.loads((module.ROOT / "examples/local-proposal-trial-renewal-2026-11-21.json").read_text(encoding="utf-8"))
    module.write_json(source / "approved-policy.json", config)
    module.write_json(source / "budget.json", {"fixture": "not real execution"})
    module.write_json(source / "result.json", {"pilot": [{"proposal_ledger": [{"candidate": None}]}] * 2})
    data = policy()
    data.update(status="approved_local_only", inference_approved=True,
                owner_response="synthetic test permission", source_sha256=module.source_hashes(source))
    monkeypatch.setattr(module, "audit_primary", lambda path: {"fixture": "synthetic integrity"})
    clock = Clock()
    original_budget = module.ReplayBudget
    monkeypatch.setattr(module, "ReplayBudget", lambda path: original_budget(path, clock=clock))
    monkeypatch.setattr(module, "_wait_slot", lambda budget: setattr(clock, "now", clock.now + 1))
    sent = []

    def handler(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": MODEL, "digest": DIGEST}]})
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["completion"]})
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "synthetic"})
        assert request.url.path == "/api/generate"
        sent.append(json.loads(request.content))
        module.write_json(source / f"model-{len(sent):03d}-request.json", sent[-1])
        if tamper == "transport":
            return httpx.Response(503, json={"fixture": "unknown usage"})
        return httpx.Response(200, json=dict(model=MODEL, done=True, response="{}", prompt_eval_count=3, eval_count=1))

    simulator = SimpleNamespace(info=SimpleNamespace(version="synthetic"),
                                simulate=lambda *args: pytest.fail("invalid model candidate must not simulate"))
    result = module.run(data, source, simulator, tmp_path / "supplement", transport=httpx.MockTransport(handler))
    if tamper == "transport":
        assert result["status"] == "blocked"
        assert len(sent) == result["budget"]["model_requests"] == 1
        assert result["budget"]["reserved_tokens"] == 2304
        assert result["replay"][0]["proposal_ledger"][0]["status"] == "provider_error"
        auditor = command("audit_local_replay")
        monkeypatch.setattr(auditor, "runner", lambda: module)
        monkeypatch.setattr(module, "audit_primary", lambda path: {"completed_equal_budget_trials": 4,
                                                                 "model_requests": 25, "audited_real_spice_calls": 65})
        result["primary_audit"] = module.audit_primary(source)
        module.write_json(tmp_path / "supplement/result.json", result)
        decision = auditor.audit(source, tmp_path / "supplement")
        assert decision["status"] == "blocked_incomplete"
        assert decision["completed_replay_observations"] == 0
        assert decision["supplemental_unknown_usage"] == 1
        return
    assert result["status"] == "completed_observations"
    assert len(sent) == result["budget"]["model_requests"] == 2
    assert result["budget"]["spice_attempts"] == 0
    assert result["phase6_accepted"] is False
    assert result["primary_allowance_reopened"] is False
    assert all(row["proposal_ledger"][0]["status"] == "invalid_candidate" for row in result["replay"])

    auditor = command("audit_local_replay")
    monkeypatch.setattr(auditor, "runner", lambda: module)
    # Composite acceptance still checks the original comparison eligibility in real use.
    monkeypatch.setattr(module, "audit_primary", lambda path: {"completed_equal_budget_trials": 4,
                                                             "model_requests": 25, "audited_real_spice_calls": 65})
    result["primary_audit"] = module.audit_primary(source)
    module.write_json(tmp_path / "supplement/result.json", result)
    decision = auditor.audit(source, tmp_path / "supplement")
    assert decision["status"] == "passed"
    assert decision["completed_replay_observations"] == 2
    assert decision["exact_candidate_replays"] == 0
    assert decision["supplemental_known_reported_tokens"] == 8
    assert decision["original_deadline_failure_preserved"]

    supplement = tmp_path / "supplement"
    if tamper == "usage":
        path = supplement / "model-001-response.json"
        body = module.read(path)
        body["eval_count"] += 1
    elif tamper == "request":
        path = supplement / "model-001-request.json"
        body = module.read(path)
        body["options"]["seed"] += 1
    elif tamper == "source":
        path = source / "result.json"
        body = {"tampered": True}
    elif tamper == "budget":
        path = supplement / "budget.json"
        body = module.read(path)
        body["model_requests"] = 3
    else:
        path = supplement / "result.json"
        body = module.read(path)
        if tamper == "candidate":
            body["replay"][0]["exact_candidate_replay"] = True
        elif tamper == "primary":
            body["phase6_accepted"] = True
        else:
            body["replay"][0]["best"] = {"invented": "design"}
    module.write_json(path, body)
    with pytest.raises(ValueError):
        auditor.audit(source, tmp_path / "supplement")
