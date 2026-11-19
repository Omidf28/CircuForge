"""Matched-call nominal/robust random-search ablation with fresh holdout samples."""
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Annotated, Literal

import numpy as np
from pydantic import Field, model_validator

from circuforge.domain.cases import Case
from circuforge.domain.specs import CircuitCandidate, DesignSpec, Model
from circuforge.domain.tolerance import SamplingPlan, Seed, ToleranceModel, perturb, sample_factors
from circuforge.evaluation.records import environment
from circuforge.evaluation.statistics import empirical_statistics
from circuforge.optimization.base import Evaluation, Evaluator
from circuforge.optimization.baselines import LogSpace
from circuforge.simulation.ngspice import Ngspice

METHODS = ("nominal", "robust")


class Experiment(Model):
    version: Literal["1.0"]
    provenance: str = Field(min_length=30)
    tolerance: ToleranceModel
    seeds: tuple[Seed, ...]
    cases: tuple[Case, ...]
    training_calls: Annotated[int, Field(strict=True, ge=8, le=128)] = 64
    training_samples: Annotated[int, Field(strict=True, ge=3, le=15)] = 7
    holdout_samples: Annotated[int, Field(strict=True, ge=8, le=128)] = 32
    penalty_weight: Annotated[float, Field(strict=True, gt=0, le=10, allow_inf_nan=False)] = 1.
    max_spice_calls: Annotated[int, Field(strict=True, ge=1, le=2000)] = 2000

    @model_validator(mode="after")
    def bounded_experiment(self):
        if not 2 <= len(self.seeds) <= 3 or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("require two or three unique seeds")
        if not 2 <= len(self.cases) <= 4 or len({c.id for c in self.cases}) != len(self.cases):
            raise ValueError("require two to four uniquely identified cases")
        if {c.spec.filter_type for c in self.cases} != {"rc_lowpass", "rc_highpass"}:
            raise ValueError("both low-pass and high-pass must be represented")
        if len({c.spec.model_dump_json() for c in self.cases}) != len(self.cases):
            raise ValueError("duplicate electrical cases under different identifiers")
        if self.training_calls % (1 + self.training_samples):
            raise ValueError("training call budget must be divisible by nominal-plus-sample block size")
        if self.tolerance.resistance_fraction == self.tolerance.capacitance_fraction == 0:
            raise ValueError("comparison requires nonzero component variability")
        if self.configured_calls > self.max_spice_calls:
            raise ValueError("experiment exceeds the declared total SPICE-call cap")
        for case in self.cases:
            if LogSpace(case.spec).fixed:
                raise ValueError("comparison requires a variable nominal search domain")
            if case.spec.max_evaluations != self.training_calls:
                raise ValueError("case max_evaluations must equal the declared training call budget")
            self.simulation_spec(case.spec)
        return self

    @property
    def calls_per_trial(self):
        return self.training_calls + self.holdout_samples

    @property
    def configured_calls(self):
        return self.calls_per_trial * len(self.cases) * len(self.seeds) * len(METHODS)

    def simulation_spec(self, nominal: DesignSpec) -> DesignSpec:
        data = nominal.model_dump()
        for field, tolerance in (("resistance_ohm", self.tolerance.resistance_fraction),
                                 ("capacitance_f", self.tolerance.capacitance_fraction)):
            bounds = data[field]
            data[field] = {"minimum": bounds["minimum"] * (1 - tolerance),
                           "maximum": bounds["maximum"] * (1 + tolerance)}
        data["max_evaluations"] = self.calls_per_trial
        spec = DesignSpec.model_validate(data)
        low = 1 / (2 * math.pi * spec.resistance_ohm.maximum * spec.capacitance_f.maximum)
        high = 1 / (2 * math.pi * spec.resistance_ohm.minimum * spec.capacitance_f.minimum)
        if not spec.sweep.start_hz < low <= high < spec.sweep.stop_hz:
            raise ValueError("sweep must bracket the entire perturbed cutoff envelope")
        return spec


def load_experiment(path: Path) -> Experiment:
    return Experiment.model_validate_json(path.read_bytes())


def proposals(spec: DesignSpec, seed: int, count: int) -> list[CircuitCandidate]:
    space = LogSpace(spec)
    rng = np.random.default_rng(np.random.SeedSequence([seed, 0]))
    return [space.candidate(rng.random(2)) for _ in range(count)]


def group_result(nominal: Evaluation, samples: list[Evaluation], weight: float) -> dict:
    valid = nominal.verified and all(e.verified for e in samples)
    risk = empirical_statistics(samples)["log_error_q95"] if valid and samples else None
    return {"nominal_call": nominal.simulator_call, "sample_calls": [e.simulator_call for e in samples],
            "valid": valid, "risk_log_error_q95": risk,
            "objective": nominal.objective + weight * risk if valid and samples else nominal.objective if valid else None}


def run_trial(config: Experiment, case: Case, seed: int, method: str, simulator: Ngspice, output: Path) -> dict:
    if method not in METHODS or seed not in config.seeds or case not in config.cases:
        raise ValueError("trial must belong to its validated experiment")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    simulation_spec = config.simulation_spec(case.spec)
    evaluator = Evaluator(simulation_spec, simulator, output / "evaluations")
    training_factors = sample_factors(config.tolerance, SamplingPlan(seed=seed, samples=config.training_samples, stream="training"))
    holdout_factors = sample_factors(config.tolerance, SamplingPlan(seed=seed, samples=config.holdout_samples, stream="holdout"))
    block = 1 if method == "nominal" else 1 + config.training_samples
    candidates = proposals(case.spec, seed, config.training_calls // block)
    groups = []
    selected = None
    holdout = []
    statistics = None

    def save(stage):
        report = {"stage": stage, "case": case.model_dump(), "seed": seed, "method": method,
                  "simulation_spec": simulation_spec.model_dump(), "tolerance": config.tolerance.model_dump(),
                  "training_groups": groups, "selected_group": selected,
                  "holdout_calls": [e.simulator_call for e in holdout], "holdout_statistics": statistics,
                  "history": [e.model_dump() for e in evaluator.history], "simulator_calls": evaluator.calls,
                  "cache_hits": evaluator.cache_hits, "proposals": evaluator.proposals,
                  "failures": sum(not e.verified for e in evaluator.history),
                  "environment": environment(), "ngspice_version": simulator.info.version,
                  "wall_s": time.monotonic() - started}
        (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return report

    for candidate in candidates:
        case.spec.validate_candidate(candidate)  # optimization bounds apply to nominal values
        nominal = evaluator.evaluate(candidate)
        samples = [evaluator.evaluate(perturb(candidate, f)) for f in training_factors] if method == "robust" else []
        groups.append(group_result(nominal, samples, config.penalty_weight))
        save("training")
    eligible = [i for i, group in enumerate(groups) if group["valid"]]
    if not eligible:
        return save("blocked")
    selected = min(eligible, key=lambda i: groups[i]["objective"])
    candidate = candidates[selected]
    for factors in holdout_factors:
        holdout.append(evaluator.evaluate(perturb(candidate, factors)))
    if all(e.verified for e in holdout):
        statistics = empirical_statistics(holdout)
    complete = statistics is not None and evaluator.calls == config.calls_per_trial and evaluator.cache_hits == 0 and all(e.verified for e in evaluator.history)
    return save("completed" if complete else "blocked")


def trial_row(report: dict) -> dict:
    index = report["selected_group"]
    nominal = report["history"][report["training_groups"][index]["nominal_call"] - 1] if index is not None else None
    return {"case": report["case"]["id"], "seed": report["seed"], "method": report["method"],
            "stage": report["stage"], "simulator_calls": report["simulator_calls"], "failures": report["failures"],
            "candidate": nominal["candidate"] if nominal else None,
            "nominal_relative_error": nominal["relative_error"] if nominal else None,
            "nominal_target_passed": nominal["target_passed"] if nominal else False,
            "holdout_statistics": report["holdout_statistics"]}


def run_experiment(manifest: Path, output: Path, simulator: Ngspice) -> dict:
    config = load_experiment(manifest)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    started = time.monotonic()
    for seed in config.seeds:
        for case in config.cases:
            for method in METHODS:
                report = run_trial(config, case, seed, method, simulator, output / f"seed-{seed}" / case.id / method)
                rows.append(trial_row(report))
                summary = {"version": config.version, "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                           "configured_calls": config.configured_calls, "actual_calls": sum(r["simulator_calls"] for r in rows),
                           "planned_trials": len(config.cases) * len(config.seeds) * 2, "completed_trials": len(rows),
                           "environment": environment(), "wall_s": time.monotonic() - started,
                           "manual_review_required": False, "acceptance_status": "requires_automated_gate", "trials": rows}
                (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                print(f"seed={seed} case={case.id} method={method} stage={report['stage']} calls={report['simulator_calls']}", flush=True)
    return summary
