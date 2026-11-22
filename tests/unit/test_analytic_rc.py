"""Analytic-response fixtures are offline checks, never ngspice evidence."""
import math
from types import SimpleNamespace

import numpy as np
from pydantic import ValidationError
import pytest

from circuforge.contracts import DesignRequest
from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.optimization.analytic import analytic_candidate
from circuforge.optimization.baselines import run_baseline
from circuforge.simulation.metrics import analytic_cutoff, analytic_response
from circuforge.simulation.ngspice import Preflight, SimulationError


@pytest.mark.parametrize("topology", ["rc_lowpass", "rc_highpass"])
@pytest.mark.parametrize("target", [10.0, 1000.0, 2300.0, 1e6])
def test_continuous_proposal_hits_closed_form_product_within_bounds(topology, target):
    spec = DesignSpec(filter_type=topology, cutoff_hz=target,
                      resistance_ohm={"minimum": 100.0, "maximum": 10000.0},
                      capacitance_f={"minimum": 1e-12, "maximum": 1e-3},
                      sweep={"start_hz": target / 100, "stop_hz": target * 100, "points_per_decade": 100})
    candidate = analytic_candidate(spec)
    spec.validate_candidate(candidate)
    assert math.isclose(analytic_cutoff(candidate), target, rel_tol=2e-15)


@pytest.mark.parametrize("r,c,target", [
    ((560.0, 560.0), (1e-8, 1e-6), 2300.0),
    ((100.0, 10000.0), (1e-7, 1e-7), 2300.0),
    ((1000.0, 1000.0), (1e-7, 1e-7), 1 / (2 * math.pi * 1e-4)),
    ((1000.0, 1000.0), (1e-7, 1e-7), 1591.0),
])
def test_fixed_components_and_tolerance_only_feasibility(r, c, target):
    spec = DesignSpec(cutoff_hz=target, resistance_ohm=dict(minimum=r[0], maximum=r[1]),
                      capacitance_f=dict(minimum=c[0], maximum=c[1]))
    candidate = analytic_candidate(spec)
    spec.validate_candidate(candidate)
    assert abs(analytic_cutoff(candidate) / target - 1) <= spec.relative_error_tolerance


@pytest.mark.parametrize("product", [1e-10, 1e-3])
def test_achievable_endpoints_are_not_rounded_out_of_component_bounds(product):
    target = 1 / (2 * math.pi * product)
    spec = DesignSpec(cutoff_hz=target, resistance_ohm=dict(minimum=100.0, maximum=10000.0),
                      capacitance_f=dict(minimum=1e-12, maximum=1e-7),
                      sweep=dict(start_hz=target / 10, stop_hz=target * 10, points_per_decade=100))
    candidate = analytic_candidate(spec)
    spec.validate_candidate(candidate)
    assert math.isclose(analytic_cutoff(candidate), target, rel_tol=2e-15)


def test_untyped_and_bypassed_nonideal_spec_cannot_enter_proposer():
    with pytest.raises(TypeError):
        analytic_candidate({"cutoff_hz": 1000.0})
    with pytest.raises(ValidationError):
        analytic_candidate(DesignSpec().model_copy(update={"load": "finite"}))


class Fixture:
    info = Preflight("offline-fixture", "analytic response fixture only")

    def __init__(self, fail=False):
        self.calls, self.fail = 0, fail

    def simulate(self, spec, candidate):
        self.calls += 1
        if self.fail:
            raise SimulationError("timeout", "synthetic timeout")
        return SimpleNamespace(response=analytic_response(candidate, np.geomspace(1, 1e6, 601)), elapsed_s=.001)


def test_one_real_evaluation_slot_is_used_without_filling_unused_budget():
    first = run_baseline(DesignSpec(max_evaluations=32), Fixture(), "analytic_rc", seed=7)
    second = run_baseline(DesignSpec(max_evaluations=32), Fixture(), "analytic_rc", seed=42)
    assert first.simulator_calls == first.proposals == 1
    assert first.cache_hits == first.failures == first.invalid_candidates == 0
    assert first.history == second.history and first.converged
    assert first.optimizer_settings["analytic_seed_used"] is False
    assert first.stop_reason == "analytic_candidate_evaluated"


def test_failed_measurement_is_charged_and_never_replaced_by_analytic_success():
    simulator = Fixture(fail=True)
    result = run_baseline(DesignSpec(), simulator, "analytic_rc")
    assert simulator.calls == result.simulator_calls == result.failures == 1
    assert result.best is None and not result.converged
    assert result.history[0].status == "simulation_error"


def test_tight_target_miss_is_not_waived_by_exact_analytic_product():
    result = run_baseline(DesignSpec(relative_error_tolerance=1e-12), Fixture(), "analytic_rc")
    assert result.best.verified and not result.best.target_passed and not result.converged
    assert result.best.relative_error > result.spec.relative_error_tolerance


def test_shared_request_accepts_method_and_rejects_user_candidate():
    request = DesignRequest(spec=DesignSpec(max_evaluations=1, timeout_s=2.0), method="analytic_rc")
    assert request.candidate is None
    with pytest.raises(ValidationError, match="must not supply"):
        DesignRequest(spec=request.spec, method="analytic_rc", candidate=CircuitCandidate())
