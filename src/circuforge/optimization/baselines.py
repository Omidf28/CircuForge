"""Seeded continuous RC baselines under shared SPICE/proposal budgets."""
import json
import math
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from pydantic import Field

from circuforge.domain.specs import CircuitCandidate, DesignSpec, Model
from circuforge.evaluation.records import environment
from circuforge.optimization.base import BudgetExhausted, Evaluation, Evaluator, ProposalLimit
from circuforge.simulation.ngspice import Ngspice

Method = Literal["random", "grid", "scipy", "analytic_rc"]


class Options(Model):
    method: Method
    seed: Annotated[int, Field(strict=True, ge=0, le=2**32 - 1)] = 0


class BaselineResult(Model):
    spec: DesignSpec
    options: Options
    simulator_calls: int
    proposals: int
    cache_hits: int
    failures: int
    invalid_candidates: int
    converged: bool
    stop_reason: str
    best: Evaluation | None
    history: tuple[Evaluation, ...]
    environment: dict
    ngspice_version: str
    optimizer_settings: dict


class LogSpace:
    def __init__(self, spec: DesignSpec):
        self.spec = spec
        self.component_bounds = [spec.resistance_ohm, spec.capacitance_f]
        self.unit_bounds = [(0., 0. if b.minimum == b.maximum else 1.) for b in self.component_bounds]

    def candidate(self, unit) -> CircuitCandidate:
        if len(unit) != 2 or any(not math.isfinite(float(x)) or not 0 <= x <= 1 for x in unit):
            raise ValueError("RC coordinates must be two finite values in [0,1]")
        values = []
        for coordinate, bounds in zip(unit, self.component_bounds):
            if coordinate == 0:
                value = bounds.minimum
            elif coordinate == 1:
                value = bounds.maximum
            else:
                value = 10 ** (math.log10(bounds.minimum) + coordinate * math.log10(bounds.maximum / bounds.minimum))
            values.append(min(bounds.maximum, max(bounds.minimum, value)))
        return CircuitCandidate(topology=self.spec.filter_type, resistance_ohm=values[0], capacitance_f=values[1])

    @property
    def fixed(self):
        return all(a == b for a, b in self.unit_bounds)

    def grid(self, budget: int):
        active = sum(a != b for a, b in self.unit_bounds)
        n = math.ceil(math.sqrt(budget)) if active == 2 else budget
        axes = [np.linspace(0., 1., n) if n > 1 and a != b else
                np.array([.5 if a != b else 0.]) for a, b in self.unit_bounds]
        points = [(r, c) for r in axes[0] for c in axes[1]]
        # A budget-sized, evenly indexed subset of the rectangular log grid.
        for i in np.linspace(0, len(points) - 1, min(budget, len(points)), dtype=int):
            yield points[int(i)]


def run_baseline(spec: DesignSpec, simulator: Ngspice, method: Method, *, seed: int = 0,
                 output: Path | None = None) -> BaselineResult:
    options = Options(method=method, seed=seed)  # reject unsupported options before any SPICE call
    if output is not None:
        output.mkdir(parents=True, exist_ok=False)
    evaluator = Evaluator(spec, simulator, output / "evaluations" if output is not None else None)
    space = LogSpace(spec)
    rng = np.random.default_rng(seed)
    stop = "budget_exhausted"
    settings = {"parameter_space": "log10 R/C mapped to [0,1]", "early_target_stop": False,
                "proposal_limit": evaluator.proposal_limit, "grid_seed_used": False if method == "grid" else None}
    try:
        if method == "analytic_rc":
            from circuforge.optimization.analytic import analytic_candidate

            settings.update(analytic_seed_used=False,
                            candidate_policy="closest feasible RC product; geometric R midpoint",
                            model="ideal unloaded continuous first-order RC", maximum_actual_calls=1)
            evaluator.evaluate(analytic_candidate(spec))
            stop = "analytic_candidate_evaluated"
        elif space.fixed:
            evaluator.evaluate(space.candidate([0., 0.]))
            stop = "domain_exhausted"
        elif method == "grid":
            for point in space.grid(spec.max_evaluations):
                evaluator.evaluate(space.candidate(point))
            stop = "budget_exhausted" if evaluator.calls == spec.max_evaluations else "grid_exhausted"
        elif method == "random":
            while evaluator.calls < spec.max_evaluations:
                evaluator.evaluate(space.candidate(rng.random(2)))
        else:
            from scipy.optimize import differential_evolution

            settings.update(strategy="best1bin", popsize=5, polish=False, workers=1,
                            updating="immediate", tol=0., atol=0., restarts=0)
            # Restart exact-energy convergence rather than quietly comparing a
            # smaller DE budget. The objective enforces the hard cap mid-generation.
            while evaluator.calls < spec.max_evaluations:
                settings["restarts"] += 1
                differential_evolution(lambda x: evaluator.evaluate(space.candidate(x)).objective,
                                       space.unit_bounds, rng=rng, popsize=5,
                                       maxiter=spec.max_evaluations, tol=0., atol=0.,
                                       polish=False, workers=1, updating="immediate")
    except BudgetExhausted:
        stop = "budget_exhausted"
    except ProposalLimit:
        stop = "proposal_limit"
    best = evaluator.best
    result = BaselineResult(spec=spec, options=options, simulator_calls=evaluator.calls,
                            proposals=evaluator.proposals, cache_hits=evaluator.cache_hits,
                            failures=sum(e.status not in {"evaluated", "invalid_candidate"} for e in evaluator.history),
                            invalid_candidates=sum(e.status == "invalid_candidate" for e in evaluator.history),
                            converged=best is not None and best.target_passed, stop_reason=stop,
                            best=best, history=tuple(evaluator.history), environment=environment(),
                            ngspice_version=simulator.info.version, optimizer_settings=settings)
    if output is not None:
        (output / "report.json").write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return result


def comparison_summary(results: list[BaselineResult]) -> dict:
    """Summarize the three methods in a single comparison export."""
    return {"seed": results[0].options.seed, "budget_per_method": results[0].spec.max_evaluations,
            "matched_actual_calls": len({r.simulator_calls for r in results}) == 1,
            "results": [{"method": r.options.method, "simulator_calls": r.simulator_calls,
                         "converged": r.converged, "failures": r.failures,
                         "target_relative_error": r.best.relative_error if r.best else None,
                         "stop_reason": r.stop_reason} for r in results]}


def compare(spec: DesignSpec, simulator: Ngspice, *, seed: int = 0, output: Path | None = None):
    """Independent caches and identical caps; record actual calls for fair review."""
    if output is not None:
        output.mkdir(parents=True, exist_ok=False)
    results = [run_baseline(spec, simulator, method, seed=seed, output=output / method if output else None)
               for method in ("random", "grid", "scipy")]
    if output is not None:
        summary = comparison_summary(results)
        (output / "comparison.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return results
