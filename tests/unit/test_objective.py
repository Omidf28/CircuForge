"""Synthetic analytic fixtures isolate budget/objective behavior; no SPICE claims."""
from types import SimpleNamespace
import math

import numpy as np
import pytest

from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.optimization.base import BudgetExhausted, Evaluation, Evaluator, FAILURE_PENALTY, ProposalLimit
from circuforge.simulation.metrics import analytic_response
from circuforge.simulation.ngspice import SimulationError


class AnalyticFixture:
    def __init__(self, failure=False, wrong=False, unbracketed=False):
        self.calls = 0
        self.failure, self.wrong, self.unbracketed = failure, wrong, unbracketed

    def simulate(self, spec, candidate):
        self.calls += 1
        if self.failure:
            raise SimulationError("timeout", "controlled failure", returncode=-1)
        fixture = candidate.model_copy(update={"capacitance_f": candidate.capacitance_f * 2}) if self.wrong else candidate
        frequencies = [1., 2.] if self.unbracketed else np.geomspace(1, 1e6, 601)
        return SimpleNamespace(response=analytic_response(fixture, frequencies), elapsed_s=.001)


def test_cache_and_hard_budget():
    sim = AnalyticFixture()
    evaluator = Evaluator(DesignSpec(max_evaluations=1), sim)
    first = evaluator.evaluate(CircuitCandidate())
    assert first.verified and first.target_passed
    assert evaluator.evaluate(CircuitCandidate()) is first
    assert evaluator.calls == sim.calls == 1 and evaluator.cache_hits == 1
    with pytest.raises(BudgetExhausted):
        evaluator.evaluate(CircuitCandidate(resistance_ohm=2000.))
    assert sim.calls == 1


@pytest.mark.parametrize("candidate", [CircuitCandidate(resistance_ohm=1.), CircuitCandidate(topology="rc_highpass")])
def test_invalid_candidate_never_simulated(candidate):
    sim = AnalyticFixture()
    evaluator = Evaluator(DesignSpec(), sim)
    result = evaluator.evaluate(candidate)
    assert result.status == "invalid_candidate" and not result.constraints_satisfied
    assert result.objective == FAILURE_PENALTY and sim.calls == 0


@pytest.mark.parametrize("kwargs,status", [({"failure": True}, "simulation_error"),
                                          ({"wrong": True}, "verification_error"),
                                          ({"unbracketed": True}, "metric_error")])
def test_failed_evaluations_are_charged_cached_and_cannot_win(kwargs, status):
    evaluator = Evaluator(DesignSpec(), AnalyticFixture(**kwargs))
    result = evaluator.evaluate(CircuitCandidate())
    assert result.status == status and result.objective == FAILURE_PENALTY
    assert not result.verified and not result.target_passed and evaluator.best is None
    assert evaluator.evaluate(CircuitCandidate()) is result
    assert evaluator.calls == 1


def test_objective_error_is_distinct_from_constraints():
    result = Evaluator(DesignSpec(cutoff_hz=500.), AnalyticFixture()).evaluate(CircuitCandidate())
    assert result.constraints_satisfied and result.verified and not result.target_passed
    assert result.relative_error > 1 and result.objective > 0


def test_duplicate_proposals_are_bounded_even_when_call_budget_remains():
    evaluator = Evaluator(DesignSpec(max_evaluations=2), AnalyticFixture())
    for _ in range(evaluator.proposal_limit):
        evaluator.evaluate(CircuitCandidate())
    with pytest.raises(ProposalLimit):
        evaluator.evaluate(CircuitCandidate())
    assert evaluator.calls == 1 and evaluator.proposals == evaluator.proposal_limit


def test_passing_candidate_is_not_lost_to_log_objective_asymmetry():
    evaluator = Evaluator(DesignSpec(cutoff_hz=1000.), AnalyticFixture())
    for ratio in (1.0010001, .9990001):
        evaluator.history.append(Evaluation(candidate=CircuitCandidate(), status="evaluated",
                                             constraints_satisfied=True, verified=True,
                                             target_passed=abs(ratio - 1) <= .001,
                                             objective=abs(math.log(ratio)), measured_cutoff_hz=1000 * ratio,
                                             relative_error=abs(ratio - 1)))
    assert evaluator.history[0].objective < evaluator.history[1].objective
    assert evaluator.best.target_passed
    assert evaluator.best is evaluator.history[1]
