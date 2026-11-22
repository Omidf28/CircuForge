"""Read-only composite gate for original comparison data and a separately capped replay."""
import argparse
import importlib.util
from pathlib import Path

from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.acceptance import audit_evaluation, require
from circuforge.evaluation.records import environment
from circuforge.local_provider import DIGEST, MODEL, write_json
from circuforge.optimization.base import Evaluation
from circuforge.proposals import ProviderReply, TokenReservation, TokenUsage


def runner():
    spec = importlib.util.spec_from_file_location("supplement_replay_runner", Path(__file__).with_name("replay_local_trial.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(source: Path, output: Path) -> dict:
    replay = runner()
    policy = replay.load_policy(output / "approved-policy.json")
    require(replay.source_hashes(source) == policy["source_sha256"], "primary source changed")
    primary = replay.audit_primary(source)
    result = replay.read(output / "result.json")
    budget = replay.read(output / "budget.json")
    require(result["policy"] == replay.POLICY and result["primary_audit"] == primary and
            result["source_sha256"] == policy["source_sha256"], "incorrect primary linkage")
    require(result["primary_allowance_reopened"] is False and result["comparisons_rescored"] is False and
            result["phase6_accepted"] is False, "runner claimed unsupported scientific acceptance")
    require(result["environment"] == result["finished_environment"] == environment(), "replay environment differs")
    require(result["budget"] == budget and 0 <= budget["model_requests"] <= 2 and
            budget["reserved_tokens"] == 2304 * budget["model_requests"] <= 4608 and
            0 <= budget["spice_attempts"] <= 2 and budget["cost_microusd"] == 0 and
            0 <= budget["elapsed_s"] <= 121, "supplemental resource accounting differs")
    records = budget["records"]
    require(len(records) == budget["model_requests"] == len(result["replay"]), "missing attempt records")
    if records:
        model = replay.read(output / "local-model.json")
        require(model["model"] == MODEL and model["digest"] == DIGEST, "wrong replay model")
    config = replay.read(source / "approved-policy.json")
    original = replay.read(source / "result.json")
    known = unknown = calls = observed = exact = 0
    for index, (attempt, record) in enumerate(zip(records, result["replay"]), start=1):
        case = config["experiment"]["cases"][index - 1]
        spec = DesignSpec.model_validate(case["spec"])
        require(record["case"] == case["id"] and attempt["request"] == index and
                attempt["reserved_tokens"] == 2304 and
                0 <= attempt["client_elapsed_s"] <= 60.5, "unexpected replay request")
        sent = replay.read(output / f"model-{index:03d}-request.json")
        require(sent == replay.read(source / f"model-{index:03d}-request.json"), "replay prompt/options differ")
        saved = None
        if "reported_usage" in attempt:
            response = replay.read(output / f"model-{index:03d}-response.json")
            usage = TokenUsage.model_validate(attempt["reported_usage"])
            require(attempt["status"] == "reported" and response["done"] is True and response["model"] == MODEL and
                    isinstance(response["response"], str) and
                    response["prompt_eval_count"] == usage.input_tokens and response["eval_count"] == usage.output_tokens and
                    usage.input_tokens <= 2048 and usage.output_tokens <= 256, "replay usage differs")
            saved = ProviderReply(response["response"], usage)
            known += usage.input_tokens + usage.output_tokens
        else:
            unknown += 1

        class SavedReply:
            def propose(self, request):
                if saved is None:
                    raise RuntimeError("saved unknown-usage failure")
                return saved

        session = replay._session(spec, SavedReply(), 7, 1)
        proposal = session.propose(TokenReservation(input_tokens=2048, output_tokens=256))
        require(record["proposal_ledger"] == [proposal.model_dump()] and record["usage"] == session.usage.model_dump(),
                "replay proposal/usage ledger differs from saved response")
        returned = proposal.status in {"accepted", "invalid_candidate"}
        observed += returned
        candidate_equal = proposal.candidate is not None and proposal.candidate.model_dump() == original["pilot"][index - 1]["proposal_ledger"][0]["candidate"]
        require(record["exact_candidate_replay"] == candidate_equal, "false exact-candidate replay claim")
        exact += candidate_equal
        history = [Evaluation.model_validate(row) for row in record["history"]]
        require(record["cache_hits"] == 0 and record["simulator_calls"] == len(history) <= 1 and
                len(history) == int(proposal.status == "accepted"), "replay simulation partition differs")
        for evaluation in history:
            require(evaluation.candidate == proposal.candidate and evaluation.verified and evaluation.simulator_call == 1,
                    "unverified replay candidate")
            audit_evaluation(output / "replay" / case["id"], evaluation.artifact, spec, evaluation, result["ngspice_version"])
            calls += 1
        require(record["best"] == (history[0].model_dump() if history else None), "incorrect replay best result")
    require(calls == budget["spice_attempts"] == result["audited_spice_calls"], "unaccounted supplemental SPICE attempts")
    complete = (result["status"] == "completed_observations" and observed == 2 and unknown == 0 and not budget["blocked"])
    return dict(status="passed" if complete else "blocked_incomplete", policy="phase6-local-supplemental-replay-v1",
                acceptance_mode="automated", primary_comparison_trials=primary["completed_equal_budget_trials"],
                primary_model_requests=primary["model_requests"], primary_spice_attempts=primary["audited_real_spice_calls"],
                supplemental_model_requests=budget["model_requests"], supplemental_spice_attempts=calls,
                supplemental_reserved_tokens=budget["reserved_tokens"], supplemental_known_reported_tokens=known,
                supplemental_unknown_usage=unknown, completed_replay_observations=observed,
                exact_candidate_replays=exact, original_deadline_failure_preserved=True,
                comparisons_rescored=False, model_efficacy_established=False,
                note="Separate authorized observation window; original ledgers remain unchanged. Candidate differences are reported, never waived or relabeled as exact replay.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.source, args.input)
        write_json(args.input / "acceptance.json", result)
        print(result)
        return 0 if result["status"] == "passed" else 1
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        print(f"Supplemental audit blocked: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
