from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError

from circuforge.domain.specs import Bounds, DesignSpec
from circuforge.optimization.baselines import LogSpace, run_baseline
from circuforge.simulation.metrics import analytic_response
from circuforge.simulation.ngspice import Preflight, SimulationError


class AnalyticFixture:
    """Offline optimizer fixture, never real simulation evidence."""
    info = Preflight("unit-fixture", "analytic fixture only")

    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def simulate(self, spec, candidate):
        self.calls += 1
        if self.fail:
            raise SimulationError("timeout", "controlled test failure")
        return SimpleNamespace(response=analytic_response(candidate, np.geomspace(1, 1e6, 601)), elapsed_s=.001)


@pytest.mark.parametrize("method", ["random", "grid", "scipy"])
@pytest.mark.parametrize("budget", [1, 7, 16])
def test_budget_and_fixed_seed_replay(method, budget):
    spec = DesignSpec(max_evaluations=budget)
    simulator = AnalyticFixture()
    first = run_baseline(spec, simulator, method, seed=73)
    assert first.simulator_calls == budget == simulator.calls
    second = run_baseline(spec, AnalyticFixture(), method, seed=73)
    assert first.history == second.history
    assert first.best == second.best
    assert first.proposals <= 20 * budget + 20
    for entry in first.history:
        spec.validate_candidate(entry.candidate)


@pytest.mark.parametrize("method", ["random", "grid", "scipy"])
def test_fixed_domain_uses_one_call(method):
    spec = DesignSpec(resistance_ohm=Bounds(minimum=1000., maximum=1000.),
                      capacitance_f=Bounds(minimum=1e-7, maximum=1e-7))
    result = run_baseline(spec, AnalyticFixture(), method)
    assert result.simulator_calls == 1 and result.converged
    assert result.stop_reason == "domain_exhausted"


@pytest.mark.parametrize("method", ["random", "grid", "scipy"])
def test_all_failures_consume_equal_budget_and_report_no_best(method):
    result = run_baseline(DesignSpec(max_evaluations=13), AnalyticFixture(fail=True), method)
    assert result.simulator_calls == result.failures == 13
    assert result.best is None and not result.converged


def test_seed_changes_random_proposals_and_options_are_validated():
    a = run_baseline(DesignSpec(max_evaluations=2), AnalyticFixture(), "random", seed=1)
    b = run_baseline(DesignSpec(max_evaluations=2), AnalyticFixture(), "random", seed=2)
    assert [e.candidate for e in a.history] != [e.candidate for e in b.history]
    with pytest.raises(ValidationError):
        run_baseline(DesignSpec(), AnalyticFixture(), "unknown")
    with pytest.raises(ValidationError):
        run_baseline(DesignSpec(), AnalyticFixture(), "random", seed=-1)


def test_unit_coordinates_reject_nonfinite_or_outside_values():
    for point in ([float("nan"), 0.], [1.1, 0.], [-.1, 0.]):
        with pytest.raises(ValueError):
            LogSpace(DesignSpec()).candidate(point)
