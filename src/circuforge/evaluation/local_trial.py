"""One explicitly approved, capped local-model comparison; no cloud fallback."""
import json
from pathlib import Path
import time

from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.acceptance import audit_evaluation, require
from circuforge.evaluation.records import environment
from circuforge.local_provider import (BASE_URL, DIGEST, MAX_OUTPUT, MODEL, RESERVED_INPUT,
                                      LocalTrialLimit, OllamaProvider, TrialBudget, write_json)
from circuforge.optimization.base import Evaluator
from circuforge.optimization.baselines import run_baseline
from circuforge.proposals import ProposalLimits, ProposalSession, TokenReservation

POLICY = "p6-local-ollama-trial-v1"
LIMITS = dict(max_provider_cost_microusd=0, max_model_requests=32,
              reserved_input_tokens_per_request=2048, max_output_tokens_per_request=256,
              max_total_reserved_tokens=73728, request_deadline_s=60,
              experiment_deadline_s=600, minimum_request_interval_s=1,
              max_parallel_requests=1, cpu_threads=2, gpu_layers=0, context_tokens=2048,
              max_total_spice_attempts=80, spice_timeout_s=5)


def load_trial(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("policy") == POLICY and data.get("authorization_task") == "P6-H1",
            "unknown trial or authorization policy")
    require(data.get("status") == "approved_local_only" and data.get("inference_approved") is True and
            data.get("owner_response") == "تأیید آزمایش فقط محلی با همین سقف‌ها", "explicit local trial approval missing")
    require(data.get("execution_closed") is not True, "this trial allowance is closed; no automatic fresh run")
    require(data.get("limits") == LIMITS, "trial exceeds or changes approved resource settings")
    provider = data["provider"]
    require(provider["kind"] == "local_ollama" and provider["base_url"] == BASE_URL and
            provider["model"] == MODEL and provider["digest"] == DIGEST, "unapproved model/endpoint")
    require(all(provider.get(name) is False for name in (
        "allow_downloads", "allow_remote_endpoints", "allow_cloud_models", "allow_redirects", "allow_environment_proxy")),
        "unapproved transport permissions")
    experiment = data["experiment"]
    require(experiment["seeds"] == [7, 42] and experiment["methods"] == ["random", "grid", "scipy", "local_ollama"] and
            experiment["spice_budget_per_method_per_trial"] == 4 and
            experiment["max_model_proposals_per_trial"] == 7 and
            experiment["pilot_requests"] == experiment["replay_requests"] == 2 and
            experiment["early_target_stop"] is False, "unapproved experiment configuration")
    require(len(experiment["cases"]) == 2, "trial must have exactly two declared cases")
    expected_ids = ["local-lowpass", "local-highpass"]
    for index, case in enumerate(experiment["cases"]):
        require(case["id"] == expected_ids[index], "unsafe/unexpected case ID")
        spec = DesignSpec.model_validate(case["spec"])
        expected = DesignSpec(filter_type=("rc_lowpass", "rc_highpass")[index], cutoff_hz=2300.0,
                              resistance_ohm={"minimum": 100.0, "maximum": 10000.0},
                              capacitance_f={"minimum": 1e-8, "maximum": 1e-6},
                              max_evaluations=4, timeout_s=5.0)
        require(spec == expected, "case differs from approved numeric specification")
    require(data.get("results") is None, "input must not contain invented experiment results")
    return data


class CountedSimulator:
    def __init__(self, simulator, budget: TrialBudget):
        self.simulator, self.budget, self.info = simulator, budget, simulator.info

    def simulate(self, spec, candidate):
        self.budget.reserve_spice()
        return self.simulator.simulate(spec, candidate)


def _wait_slot(budget: TrialBudget):
    remaining = budget.remaining()
    if budget.last_request is not None:
        delay = max(0.0, 1.0 - (budget._clock() - budget.last_request))
        if delay >= remaining:
            raise LocalTrialLimit("request interval would exceed experiment deadline")
        if delay:
            time.sleep(delay)


def _session(spec, provider, seed, attempts):
    return ProposalSession(spec, provider, seed=seed,
                           limits=ProposalLimits(max_requests=attempts, max_total_tokens=attempts * 2304))


def _audit(evaluator, root, spec, version, result):
    for evaluation in evaluator.history:
        audit_evaluation(root, evaluation.artifact, spec, evaluation, version)
        result["audited_spice_calls"] += 1


def _record(session, evaluator):
    return dict(proposal_ledger=[p.model_dump() for p in session.history],
                usage=session.usage.model_dump(), history=[e.model_dump() for e in evaluator.history],
                simulator_calls=evaluator.calls, cache_hits=evaluator.cache_hits,
                best=evaluator.best.model_dump() if evaluator.best else None)


def run_trial(config: dict, simulator, output: Path, *, transport=None, continue_rejected_pilot=False) -> dict:
    """Caller has validated approval and allocated a new trusted output directory."""
    # Revalidate even programmatic callers; no inference based on a bare flag.
    policy_copy = output / "approved-policy.json"
    if continue_rejected_pilot:
        require(json.loads(policy_copy.read_text(encoding="utf-8")) == config, "continuation policy changed")
    else:
        write_json(policy_copy, config)
    load_trial(policy_copy)
    initial = None
    if continue_rejected_pilot:
        initial = json.loads((output / "result.json").read_text(encoding="utf-8"))
        require(initial["status"] == "blocked" and len(initial["pilot"]) == 1 and
                initial["pilot"][0]["proposal_ledger"][0]["status"] == "invalid_candidate" and
                initial["trials"] == [] and initial["budget"]["model_requests"] == 1,
                "unexpected history; continuation refused")
        require(not (output / "initial-pilot-failure.json").exists(), "continuation already used")
        budget = TrialBudget.continue_rejected_pilot(output)
        write_json(output / "initial-pilot-failure.json", initial)
    else:
        budget = TrialBudget(output)
    provider = OllamaProvider(budget, transport=transport)
    counted = CountedSimulator(simulator, budget)
    result = dict(status="blocked", policy=POLICY, actual_provider="local_ollama", cost_microusd=0,
                  environment=environment(), ngspice_version=simulator.info.version,
                  pilot=[], trials=[], replay=[], audited_spice_calls=0, model_efficacy_established=False)
    if initial is not None:
        result["pilot"] = initial["pilot"]
        result["code_epochs"] = [initial["environment"], result["environment"]]
        result["continuation_note"] = "Rejected pilot retained; only orchestration changed, not prompts, specs, budgets or model. Original deadline retained conservatively."
    try:
        result["model"] = provider.preflight()
        # Invalid model proposals are observations, not substitutes or reasons to
        # erase the remaining prespecified comparison. Transport failures stop it.
        for index, case in enumerate(config["experiment"]["cases"]):
            if index < len(result["pilot"]):
                continue
            spec = DesignSpec.model_validate(case["spec"])
            session = _session(spec, provider, 7, 1)
            raw = output / "pilot" / case["id"]
            evaluator = Evaluator(spec, counted, raw)
            _wait_slot(budget)
            proposal = session.propose(TokenReservation(input_tokens=RESERVED_INPUT, output_tokens=MAX_OUTPUT))
            record = _record(session, evaluator)
            result["pilot"].append(record)
            try:
                require(proposal.status in {"accepted", "invalid_candidate"}, "pilot transport or usage failure")
                if proposal.status == "accepted":
                    evaluation = evaluator.evaluate(proposal.candidate)
                    require(evaluation.verified, "local pilot simulation/reference verification failed")
                    _audit(evaluator, raw, spec, simulator.info.version, result)
            finally:
                result["pilot"][-1] = _record(session, evaluator)
                write_json(output / "progress.json", result)

        for case in config["experiment"]["cases"]:
            spec = DesignSpec.model_validate(case["spec"])
            for seed in config["experiment"]["seeds"]:
                trial_root = output / "comparison" / case["id"] / f"seed-{seed}"
                trial_root.mkdir(parents=True)
                trial = dict(case=case["id"], spec=spec.model_dump(), seed=seed, results=[])
                result["trials"].append(trial)
                for method in ("random", "grid", "scipy"):
                    baseline = run_baseline(spec, counted, method, seed=seed, output=trial_root / method)
                    for evaluation in baseline.history:
                        audit_evaluation(trial_root / method / "evaluations", evaluation.artifact,
                                         spec, evaluation, simulator.info.version)
                        result["audited_spice_calls"] += 1
                    trial["results"].append(dict(method=method, simulator_calls=baseline.simulator_calls,
                                                  history=[e.model_dump() for e in baseline.history],
                                                  best=baseline.best.model_dump() if baseline.best else None))
                session = _session(spec, provider, seed, 7)
                raw = trial_root / "local_ollama" / "evaluations"
                evaluator = Evaluator(spec, counted, raw)
                try:
                    while evaluator.calls < spec.max_evaluations and len(session.history) < 7:
                        _wait_slot(budget)
                        proposal = session.propose(TokenReservation(input_tokens=RESERVED_INPUT, output_tokens=MAX_OUTPUT))
                        if proposal.status == "accepted":
                            evaluator.evaluate(proposal.candidate)
                        elif proposal.status in {"usage_overrun", "provider_error", "invalid_response"}:
                            raise LocalTrialLimit("provider failure/usage uncertainty stops the approved trial")
                finally:
                    local = dict(method="local_ollama", **_record(session, evaluator))
                    trial["results"].append(local)
                    write_json(trial_root / "local_ollama" / "report.json", local)
                    write_json(output / "progress.json", result)
                _audit(evaluator, raw, spec, simulator.info.version, result)
                trial["matched_actual_calls"] = all(r["simulator_calls"] == 4 for r in trial["results"])
                write_json(trial_root / "comparison.json", trial)

        # Replay two original requests, not two new optimized choices. Report differences.
        for index, case in enumerate(config["experiment"]["cases"]):
            spec = DesignSpec.model_validate(case["spec"])
            session = _session(spec, provider, 7, 1)
            raw = output / "replay" / case["id"]
            evaluator = Evaluator(spec, counted, raw)
            _wait_slot(budget)
            proposal = session.propose(TokenReservation(input_tokens=RESERVED_INPUT, output_tokens=MAX_OUTPUT))
            if proposal.status == "accepted":
                evaluator.evaluate(proposal.candidate)
                _audit(evaluator, raw, spec, simulator.info.version, result)
            record = _record(session, evaluator)
            original = result["pilot"][index]["proposal_ledger"][0]
            record["exact_candidate_replay"] = proposal.candidate is not None and proposal.candidate.model_dump() == original["candidate"]
            result["replay"].append(record)
        result["status"] = "completed" if all(t["matched_actual_calls"] for t in result["trials"]) else "incomplete_comparison"
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        result["error"] = str(exc)
    finally:
        budget.save()
        result["budget"] = json.loads((output / "budget.json").read_text(encoding="utf-8"))
        result["finished_environment"] = environment()
        require(result["environment"] == result["finished_environment"], "source/environment changed during experiment")
        write_json(output / "result.json", result)
    return result
