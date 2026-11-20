"""Mock HTTP only: these tests never invoke the installed Ollama model."""
import asyncio
import json
from pathlib import Path

import httpx
import pytest

from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.local_trial import load_trial
from circuforge.local_provider import DIGEST, MODEL, LocalModelError, LocalTrialLimit, OllamaProvider, TrialBudget
from circuforge.proposals import ProposalSession, TokenReservation


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


def envelope(**changes):
    return dict(model=MODEL, done=True, prompt_eval_count=50, eval_count=30,
                response=json.dumps(dict(topology="rc_lowpass", resistance_ohm=1000.0, capacitance_f=1e-7)), **changes)


def handler_for(generation, *, digest=DIGEST):
    def handler(request):
        assert request.url.host == "127.0.0.1" and request.url.port == 11434
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": MODEL, "digest": digest}]})
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["completion"]})
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "test-fixture"})
        assert request.url.path == "/api/generate"
        return generation(request)
    return handler


def prepared(tmp_path, generation):
    budget = TrialBudget(tmp_path)
    adapter = OllamaProvider(budget, transport=httpx.MockTransport(handler_for(generation)))
    adapter.preflight()
    return budget, adapter, ProposalSession(DesignSpec(), adapter)


def propose(session):
    return session.propose(TokenReservation(input_tokens=2048, output_tokens=256))


def test_local_request_has_exact_approved_options_and_real_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://invalid.example:1234")
    seen = []

    def generate(request):
        data = json.loads(request.content)
        seen.append(data)
        assert data["options"] == dict(seed=42, num_ctx=2048, num_predict=256, num_gpu=0, num_thread=2, temperature=0.7)
        assert data["model"] == MODEL and data["keep_alive"] == 0 and data["stream"] is False
        assert "C:" not in data["prompt"] and "D:" not in data["prompt"]
        assert json.loads((tmp_path / "budget.json").read_text())["model_requests"] == 1
        return httpx.Response(200, json=envelope())

    budget, _, session = prepared(tmp_path, generate)
    result = propose(session)
    assert result.status == "accepted" and result.input_tokens == 50 and result.output_tokens == 30
    assert result.cost_microusd == 0 and budget.requests == len(seen) == 1
    assert budget.records[0]["reported_usage"] == {"input_tokens": 50, "output_tokens": 30}
    assert (tmp_path / "model-001-response.json").is_file()


def test_digest_mismatch_blocks_before_generation(tmp_path):
    budget = TrialBudget(tmp_path)
    adapter = OllamaProvider(budget, transport=httpx.MockTransport(handler_for(lambda _: pytest.fail("inference"), digest="wrong")))
    with pytest.raises(LocalModelError, match="preflight"):
        adapter.preflight()
    assert budget.requests == 0


@pytest.mark.parametrize("generation", [
    lambda _: httpx.Response(302, headers={"Location": "https://unapproved.example"}),
    lambda _: httpx.Response(200, content=b"x" * 70000),
    lambda _: httpx.Response(200, json={"model": MODEL, "done": False}),
    lambda _: httpx.Response(200, json={**envelope(), "prompt_eval_count": -1}),
    lambda _: httpx.Response(200, json={**envelope(), "model": "unapproved"}),
])
def test_bad_response_or_redirect_keeps_reservation_and_never_falls_back(tmp_path, generation):
    budget, _, session = prepared(tmp_path, generation)
    result = propose(session)
    assert result.status == "provider_error" and result.candidate is None
    assert result.accounting == "reserved" and result.input_tokens + result.output_tokens == 2304
    assert budget.requests == 1 and budget.spice_calls == 0


def test_reported_overrun_is_not_clipped_and_blocks_shared_budget(tmp_path):
    budget, _, session = prepared(tmp_path, lambda _: httpx.Response(200, json={**envelope(), "eval_count": 257}))
    result = propose(session)
    assert result.status == "usage_overrun" and result.output_tokens == 257
    assert budget.blocked and budget.records[0]["reported_usage"]["output_tokens"] == 257
    with pytest.raises(LocalTrialLimit, match="blocked"):
        budget.reserve_spice()


def test_shared_request_token_spice_and_time_caps_are_exact(tmp_path):
    clock = Clock()
    budget = TrialBudget(tmp_path, clock=clock)
    for _ in range(32):
        budget.reserve_model()
        clock.now += 1
    with pytest.raises(LocalTrialLimit, match="32-request"):
        budget.reserve_model()
    assert json.loads((tmp_path / "budget.json").read_text())["reserved_tokens"] == 73728
    for _ in range(80):
        budget.reserve_spice()
    with pytest.raises(LocalTrialLimit, match="80-attempt"):
        budget.reserve_spice()
    clock.now = 600
    with pytest.raises(LocalTrialLimit, match="deadline"):
        budget.remaining()
    assert budget.requests == 32 and budget.spice_calls == 80
    with pytest.raises(LocalTrialLimit, match="reset"):
        TrialBudget(tmp_path)


def test_shared_request_rate_rejection_does_not_add_attempt(tmp_path):
    clock = Clock()
    budget = TrialBudget(tmp_path, clock=clock)
    budget.reserve_model()
    clock.now = 0.5
    with pytest.raises(LocalTrialLimit, match="interval"):
        budget.reserve_model()
    assert budget.requests == 1


def test_total_http_deadline_cancels_delayed_response(tmp_path, monkeypatch):
    async def delayed(request):
        if request.url.path == "/api/generate":
            await asyncio.sleep(0.2)
            return httpx.Response(200, json=envelope())
        return handler_for(lambda _: None)(request)

    budget = TrialBudget(tmp_path)
    adapter = OllamaProvider(budget, transport=httpx.MockTransport(delayed))
    adapter.preflight()
    monkeypatch.setattr(budget, "remaining", lambda: 0.02)
    result = propose(ProposalSession(DesignSpec(), adapter))
    assert result.status == "provider_error" and result.accounting == "reserved"
    assert budget.records[0]["status"] == "TimeoutError" and budget.requests == 1


@pytest.mark.parametrize("change", ["approval", "cost", "endpoint", "download", "digest", "spec", "gpu", "extra_requests"])
def test_policy_cannot_widen_owner_permission(tmp_path, change):
    root = Path(__file__).resolve().parents[2]
    policy = json.loads((root / "examples/local-proposal-trial-v1.json").read_text(encoding="utf-8"))
    policy.pop("execution_closed", None)  # Pure fixture validation, not an inference permission.
    if change == "approval":
        policy["inference_approved"] = False
    elif change == "cost":
        policy["limits"]["max_provider_cost_microusd"] = 1
    elif change == "endpoint":
        policy["provider"]["base_url"] = "http://remote.invalid"
    elif change == "download":
        policy["provider"]["allow_downloads"] = True
    elif change == "digest":
        policy["provider"]["digest"] = "different"
    elif change == "spec":
        policy["experiment"]["cases"][0]["spec"]["cutoff_hz"] = 2000.0
    elif change == "gpu":
        policy["limits"]["gpu_layers"] = -1
    else:
        policy["limits"]["max_model_requests"] = 33
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ValueError):
        load_trial(path)


def test_consumed_allowance_is_closed_without_losing_owner_approval():
    root = Path(__file__).resolve().parents[2]
    path = root / "examples/local-proposal-trial-v1.json"
    policy = json.loads(path.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="closed"):
        load_trial(path)
    assert policy["owner_response"] == "تأیید آزمایش فقط محلی با همین سقف‌ها"
    assert 2 + 4 * 7 + 2 == policy["limits"]["max_model_requests"]
    assert 4 * 4 * 4 + 2 + 2 <= policy["limits"]["max_total_spice_attempts"]


def test_rejected_pilot_keeps_record_without_simulator_or_fallback(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from circuforge.evaluation import local_trial
    from circuforge.proposals import ProviderReply, TokenUsage

    class RejectedFixture:
        def __init__(self, budget, transport=None):
            self.budget = budget

        def preflight(self):
            return {"fixture": True}

        def propose(self, request):
            self.budget.reserve_model()
            return ProviderReply("{}", TokenUsage(input_tokens=2, output_tokens=3))

    monkeypatch.setattr(local_trial, "OllamaProvider", RejectedFixture)
    monkeypatch.setattr(local_trial, "run_baseline", lambda *a, **k: (_ for _ in ()).throw(LocalTrialLimit("fixture stop before baselines")))
    monkeypatch.setattr(local_trial, "_wait_slot", lambda budget: None)
    policy_path = Path(__file__).resolve().parents[2] / "examples/local-proposal-trial-v1.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy.pop("execution_closed", None)  # Mock-only controller fixture.
    result = local_trial.run_trial(policy, SimpleNamespace(info=SimpleNamespace(version="fixture")), tmp_path)
    assert result["status"] == "blocked" and result["audited_spice_calls"] == 0
    assert result["pilot"][0]["proposal_ledger"][0]["status"] == "invalid_candidate"
    assert result["budget"]["model_requests"] == 1 and result["budget"]["spice_attempts"] == 0
    assert (tmp_path / "result.json").is_file()


def test_rejected_pilot_continuation_retains_counters_and_shortens_deadline(tmp_path):
    budget = TrialBudget(tmp_path)
    budget.reserve_model()
    budget.settle(1, status="reported")
    resumed = TrialBudget.continue_rejected_pilot(tmp_path)
    assert resumed.requests == 1 and resumed.spice_calls == 0
    assert resumed.remaining() < budget.remaining() - 4.5
    resumed.last_request = None
    resumed.reserve_model()
    with pytest.raises(LocalTrialLimit, match="single recorded"):
        TrialBudget.continue_rejected_pilot(tmp_path)


def test_closed_trial_cli_refuses_before_simulator_or_output_creation(tmp_path, monkeypatch):
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "scripts/run_local_trial.py"
    spec = importlib.util.spec_from_file_location("closed_local_trial_command", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "Ngspice", lambda *a: pytest.fail("no simulator after closed allowance"))
    output = tmp_path / "must-not-exist"
    assert module.main(["--output", str(output)]) == 2
    assert not output.exists()


def test_fast_pilot_continuation_does_not_waive_global_request_rate(tmp_path):
    budget = TrialBudget(tmp_path)
    budget.reserve_model()
    budget.records[0]["client_elapsed_s"] = 0.01
    budget.settle(1, status="reported")
    resumed = TrialBudget.continue_rejected_pilot(tmp_path)
    with pytest.raises(LocalTrialLimit, match="interval"):
        resumed.reserve_model()
    assert resumed.requests == 1
