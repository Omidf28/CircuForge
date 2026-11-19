"""Raw physics, seeded perturbation, objective, fairness and holdout replay audit."""
import hashlib
import math
from pathlib import Path

import numpy as np

from circuforge.domain.tolerance import SamplingPlan, perturb, sample_factors
from circuforge.evaluation.acceptance import audit_evaluation, evidence_file, read_json, require
from circuforge.evaluation.records import environment
from circuforge.optimization.base import Evaluation
from circuforge.optimization.robustness import METHODS, Experiment, load_experiment, proposals

POLICY = "phase4-tolerance-v1"


def _statistics(history: list[Evaluation]) -> dict:
    """Recompute each marginal quantile independently from verified call records."""
    quantiles = {}
    for name, field in (("cutoff_hz", "measured_cutoff_hz"), ("relative_error", "relative_error")):
        values = [getattr(e, field) for e in history]
        quantiles[name] = {key: float(np.quantile(values, q, method="linear"))
                           for key, q in (("q05", .05), ("q50", .5), ("q95", .95))}
    return {"samples": len(history), "quantile_method": "linear", **quantiles,
            "log_error_q95": float(np.quantile([e.objective for e in history], .95, method="linear")),
            "target_passes": sum(e.target_passed for e in history),
            "pass_rate": sum(e.target_passed for e in history) / len(history)}


def _same_numbers(left, right) -> bool:
    if isinstance(right, dict):
        return isinstance(left, dict) and left.keys() == right.keys() and all(_same_numbers(left[k], v) for k, v in right.items())
    if isinstance(right, float):
        return isinstance(left, (float, int)) and math.isfinite(left) and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-14)
    return left == right


def audit_trial(config: Experiment, case, seed: int, method: str, root: Path, expected_env: dict) -> dict:
    report = read_json(root, "report.json")
    spec = config.simulation_spec(case.spec)
    require(report["case"] == case.model_dump() and report["seed"] == seed and report["method"] == method and
            report["simulation_spec"] == spec.model_dump() and report["tolerance"] == config.tolerance.model_dump(),
            "trial configuration mismatch")
    require(report["environment"] == expected_env, "trial source/environment changed")
    count = config.calls_per_trial
    history = [Evaluation.model_validate(e) for e in report["history"]]
    require(report["stage"] == "completed" and len(history) == report["simulator_calls"] == report["proposals"] == count and
            report["cache_hits"] == report["failures"] == 0, "partial, failed or unfair call accounting")
    require(math.isfinite(report["wall_s"]) and report["wall_s"] >= sum(e.elapsed_s for e in history) and
            all(math.isfinite(e.elapsed_s) and e.elapsed_s >= 0 for e in history), "invalid recorded runtime")
    for i, evaluation in enumerate(history, 1):
        require(evaluation.simulator_call == i and evaluation.artifact == f"call-{i:04d}", "discontinuous/unsafe call identity")
        audit_evaluation(root, f"evaluations/call-{i:04d}", spec, evaluation, report["ngspice_version"])
    require(len({e.candidate.model_dump_json() for e in history}) == count, "duplicate samples charged as new calls")
    train = sample_factors(config.tolerance, SamplingPlan(seed=seed, samples=config.training_samples, stream="training"))
    holdout = sample_factors(config.tolerance, SamplingPlan(seed=seed, samples=config.holdout_samples, stream="holdout"))
    block = 1 if method == "nominal" else 1 + config.training_samples
    candidates = proposals(case.spec, seed, config.training_calls // block)
    require(len(report["training_groups"]) == len(candidates), "incorrect candidate opportunity count")
    scores = []
    for i, candidate in enumerate(candidates):
        case.spec.validate_candidate(candidate)
        offset = i * block
        nominal = history[offset]
        require(nominal.candidate == candidate, "proposal stream differs from declared seed")
        samples = history[offset + 1:offset + block]
        if method == "robust":
            require([e.candidate for e in samples] == [perturb(candidate, f) for f in train], "incorrect training perturbations")
        risk = float(np.quantile([e.objective for e in samples], .95, method="linear")) if samples else None
        score = nominal.objective + config.penalty_weight * risk if risk is not None else nominal.objective
        expected = {"nominal_call": offset + 1, "sample_calls": list(range(offset + 2, offset + block + 1)),
                    "valid": True, "risk_log_error_q95": risk, "objective": score}
        require(_same_numbers(report["training_groups"][i], expected), "training objective/sample partition mismatch")
        scores.append(score)
    selected = min(range(len(scores)), key=scores.__getitem__)
    require(report["selected_group"] == selected, "selected design ignores the declared training objective")
    require(report["holdout_calls"] == list(range(config.training_calls + 1, count + 1)), "holdout overlaps training calls")
    held = history[config.training_calls:]
    require([e.candidate for e in held] == [perturb(candidates[selected], f) for f in holdout], "incorrect independent holdout samples")
    stats = _statistics(held)
    require(_same_numbers(report["holdout_statistics"], stats), "holdout quantiles/pass rate disagree with raw measurements")
    nominal = history[selected * block]
    expected_row = {"case": case.id, "seed": seed, "method": method, "stage": "completed",
                    "simulator_calls": count, "failures": 0, "candidate": nominal.candidate.model_dump(),
                    "nominal_relative_error": nominal.relative_error, "nominal_target_passed": nominal.target_passed,
                    "holdout_statistics": report["holdout_statistics"]}
    return expected_row


def audit_experiment(manifest: Path, root: Path) -> dict:
    config = load_experiment(manifest)
    summary = read_json(root, "summary.json")
    expected_env = environment()
    trials = len(config.cases) * len(config.seeds) * len(METHODS)
    require(summary["version"] == config.version and summary["manifest_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "manifest fingerprint/version mismatch")
    require(summary["environment"] == expected_env and summary["manual_review_required"] is False and
            summary["acceptance_status"] == "requires_automated_gate", "incorrect source/policy metadata")
    require(summary["configured_calls"] == summary["actual_calls"] == config.configured_calls and
            summary["planned_trials"] == summary["completed_trials"] == len(summary["trials"]) == trials,
            "incomplete or unbounded experiment")
    rows = {(r["case"], r["seed"], r["method"]): r for r in summary["trials"]}
    require(len(rows) == trials, "duplicate/missing trials")
    runtime = 0.
    for seed in config.seeds:
        for case in config.cases:
            for method in METHODS:
                folder = root / f"seed-{seed}" / case.id / method
                expected = audit_trial(config, case, seed, method, folder, expected_env)
                require(_same_numbers(rows[(case.id, seed, method)], expected), "summary differs from audited trial")
                runtime += read_json(folder, "report.json")["wall_s"]
    require(math.isfinite(summary["wall_s"]) and summary["wall_s"] >= runtime, "invalid total runtime")
    require(evidence_file(root, "comparison.png").stat().st_size > 1000, "comparison plot missing/empty")
    return {"cases": len(config.cases), "seeds": len(config.seeds), "trials": trials,
            "audited_calls": config.configured_calls, "environment": expected_env, "outcomes": summary["trials"]}


def audit_replay(manifest: Path, first: Path, second: Path) -> dict:
    left = audit_experiment(manifest, first)
    right = audit_experiment(manifest, second)
    require(left == right, "numerical outcome replay mismatch")
    config = load_experiment(manifest)
    for seed in config.seeds:
        for case in config.cases:
            for method in METHODS:
                relative = f"seed-{seed}/{case.id}/{method}/report.json"
                a, b = read_json(first, relative), read_json(second, relative)
                for key in ("training_groups", "selected_group", "holdout_calls", "holdout_statistics", "proposals", "cache_hits"):
                    require(a[key] == b[key], f"numerical replay mismatch: {key}")
                trace = lambda report: [{k: v for k, v in e.items() if k != "elapsed_s"} for e in report["history"]]
                require(trace(a) == trace(b), "candidate/measurement trace replay mismatch")
    return {"status": "passed", "policy": POLICY, "acceptance_mode": "automated", "manual_review_required": False,
            "numerical_replay": "exact; elapsed times excluded", "audited_calls_including_replay": left["audited_calls"] * 2,
            "claim": "nominal component-tolerance experiment reproduced; no hardware guarantee or required optimizer win", **left}
