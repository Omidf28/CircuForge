"""Read-only audit of bounded local trial evidence; never calls a model/simulator."""
import argparse
import json
from pathlib import Path

from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.acceptance import audit_evaluation, require
from circuforge.evaluation.local_trial import load_trial
from circuforge.local_provider import DIGEST, MODEL, write_json
from circuforge.optimization.base import Evaluation
from circuforge.proposals import ProposalLimits, ProposalSession, ProviderReply, TokenReservation, TokenUsage


def audit(root: Path) -> dict:
    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
    budget = json.loads((root / "budget.json").read_text(encoding="utf-8"))
    config = load_trial(root / "approved-policy.json")
    require(0 <= budget["model_requests"] <= 32 and budget["reserved_tokens"] == budget["model_requests"] * 2304 <= 73728,
            "request/token ceiling or reservation mismatch")
    require(0 <= budget["spice_attempts"] <= 80 and budget["cost_microusd"] == 0, "SPICE/cost ceiling mismatch")
    # The client stops generation at 600s; allow only cancellation/file-record
    # cleanup here, never permission for another generation request.
    require(0 <= budget["elapsed_s"] <= 601.0, "experiment deadline exceeded beyond record cleanup")
    require(len(budget["records"]) == budget["model_requests"], "missing model attempt records")
    model = json.loads((root / "local-model.json").read_text(encoding="utf-8"))
    require(model["model"] == MODEL and model["digest"] == DIGEST, "different model identity")
    known_tokens = unknown_usage = 0
    replies = []
    for number, record in enumerate(budget["records"], start=1):
        require(record["request"] == number and record["reserved_tokens"] == 2304, "nonsequential model ledger")
        request = json.loads((root / f"model-{number:03d}-request.json").read_text(encoding="utf-8"))
        options = request["options"]
        require(request["model"] == MODEL and request["stream"] is False and request["keep_alive"] == 0 and
                options["num_gpu"] == 0 and options["num_thread"] == 2 and options["num_predict"] == 256 and
                options["num_ctx"] == 2048, "unapproved generation settings")
        require(len(request["prompt"].encode("utf-8")) <= 4096 and "C:" not in request["prompt"] and
                "D:" not in request["prompt"], "unexpected prompt payload")
        require(record.get("client_elapsed_s", 0) <= 60.5, "request deadline overshoot beyond cleanup allowance")
        if "reported_usage" in record:
            response = json.loads((root / f"model-{number:03d}-response.json").read_text(encoding="utf-8"))
            usage = record["reported_usage"]
            require(response["done"] is True and response["model"] == MODEL and
                    response["prompt_eval_count"] == usage["input_tokens"] and
                    response["eval_count"] == usage["output_tokens"], "model response/usage mismatch")
            known_tokens += usage["input_tokens"] + usage["output_tokens"]
            replies.append(ProviderReply(response["response"], TokenUsage.model_validate(usage)))
        else:
            unknown_usage += 1
            replies.append(None)
    audited = 0
    for path in sorted(root.rglob("evaluation.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        evaluation = Evaluation.model_validate({key: data[key] for key in Evaluation.model_fields})
        audit_evaluation(path.parent.parent, path.parent.name, DesignSpec.model_validate(data["spec"]),
                         evaluation, data["ngspice_version"])
        audited += 1
    require(audited == budget["spice_attempts"] and 0 <= result["audited_spice_calls"] <= audited,
            "raw call audit/accounting mismatch")
    # Check each recorded method count/history against its actual artifact tree.
    covered = 0

    def check_history(record, raw):
        history = record["history"]
        require(record["simulator_calls"] == len(history) == len(list(raw.glob("*/evaluation.json"))),
                "method call count differs from raw evidence")
        for index, value in enumerate(history, 1):
            require(value["artifact"] == f"call-{index:04d}", "unsafe/nonsequential artifact")
            metadata = json.loads((raw / value["artifact"] / "evaluation.json").read_text(encoding="utf-8"))
            require(Evaluation.model_validate(value) == Evaluation.model_validate(
                {field: metadata[field] for field in Evaluation.model_fields}), "method history differs from raw metadata")
        verified = [Evaluation.model_validate(value) for value in history if value["verified"]]
        best = min(verified, key=lambda value: (not value.target_passed, value.objective)) if verified else None
        require(record.get("best") == (best.model_dump() if best else None), "incorrect best-candidate selection")
        return len(history)

    offset = 0

    def replay_ledger(record, spec, seed, max_requests):
        nonlocal offset
        ledger = record["proposal_ledger"]

        class SavedResponses:
            def propose(self, request):
                nonlocal offset
                require(offset < len(replies), "missing saved model response")
                saved = replies[offset]
                offset += 1
                if saved is None:
                    raise RuntimeError("observed unknown-usage failure")
                return saved

        session = ProposalSession(spec, SavedResponses(), seed=seed,
                                  limits=ProposalLimits(max_requests=max_requests, max_total_tokens=max_requests * 2304))
        accepted = []
        for value in ledger:
            replayed = session.propose(TokenReservation(input_tokens=2048, output_tokens=256))
            require(replayed.model_dump() == value, "candidate/usage ledger differs from saved model response")
            if replayed.status == "accepted":
                accepted.append(replayed.candidate)
        require(session.usage.model_dump() == record["usage"], "session usage summary differs from attempt ledger")
        unique = []
        for candidate in accepted:
            if candidate not in unique:
                unique.append(candidate)
        require([candidate.model_dump() for candidate in unique] == [value["candidate"] for value in record["history"]],
                "simulated candidate not backed by an accepted model proposal")
        require(record["cache_hits"] == len(accepted) - len(unique), "model duplicate/cache accounting mismatch")

    cases = config["experiment"]["cases"]
    require(len(result["pilot"]) <= 2 and len(result["replay"]) <= 2, "extra pilot/replay calls")
    for index, record in enumerate(result["pilot"]):
        replay_ledger(record, DesignSpec.model_validate(cases[index]["spec"]), 7, 1)
        covered += check_history(record, root / "pilot" / cases[index]["id"])
    eligible = 0
    seen = set()
    for trial in result["trials"]:
        require(trial["case"] in {case["id"] for case in cases} and trial["seed"] in [7, 42], "unexpected trial")
        key = (trial["case"], trial["seed"])
        require(key not in seen, "duplicate trial")
        seen.add(key)
        declared = next(case for case in cases if case["id"] == trial["case"])
        require(DesignSpec.model_validate(trial["spec"]) == DesignSpec.model_validate(declared["spec"]), "changed case specification")
        methods = set()
        for method in trial["results"]:
            require(method["method"] in {"random", "grid", "scipy", "local_ollama"} and method["method"] not in methods,
                    "unexpected/duplicate comparison method")
            methods.add(method["method"])
            raw = root / "comparison" / trial["case"] / f"seed-{trial['seed']}" / method["method"] / "evaluations"
            covered += check_history(method, raw)
            if method["method"] == "local_ollama":
                replay_ledger(method, DesignSpec.model_validate(trial["spec"]), trial["seed"], 7)
        actual = [method["simulator_calls"] for method in trial["results"]]
        matched = len(actual) == 4 and all(n == 4 for n in actual)
        if "matched_actual_calls" in trial:
            require(trial["matched_actual_calls"] == matched, "false equal-budget comparison")
        eligible += matched
    for index, record in enumerate(result["replay"]):
        replay_ledger(record, DesignSpec.model_validate(cases[index]["spec"]), 7, 1)
        covered += check_history(record, root / "replay" / cases[index]["id"])
    require(covered == audited and offset == len(replies), "unaccounted raw calls or model requests")
    complete = result["status"] == "completed" and len(result["trials"]) == eligible == 4 and len(result["replay"]) == 2
    return dict(integrity_status="passed", phase6_comparison_status="passed" if complete else "blocked_incomplete",
                model_requests=budget["model_requests"], reserved_tokens=budget["reserved_tokens"],
                reported_tokens_known=known_tokens, requests_with_unknown_usage=unknown_usage,
                audited_real_spice_calls=audited, completed_equal_budget_trials=eligible,
                runtime_audited_spice_calls=result["audited_spice_calls"],
                elapsed_s=budget["elapsed_s"], cost_microusd=0,
                model_efficacy_established=False, note="Integrity does not turn an incomplete comparison into acceptance.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.input.resolve())
        write_json(args.input.resolve() / "audit.json", result)
        print(json.dumps(result, indent=2))
        return 0 if result["phase6_comparison_status"] == "passed" else 1
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps(dict(integrity_status="blocked", reason=str(exc)), indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
