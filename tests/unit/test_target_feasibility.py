"""Feasibility must use the same relative-error policy as evaluation."""
import math

import pytest
from pydantic import ValidationError

from circuforge.domain.specs import Bounds, DesignSpec


@pytest.mark.parametrize("fixed", [False, True])
@pytest.mark.parametrize("side", ["below", "above"])
@pytest.mark.parametrize("within_tolerance", [False, True])
def test_achievable_interval_intersection(fixed, side, within_tolerance):
    r = Bounds(minimum=1000., maximum=1000. if fixed else 2000.)
    c = Bounds(minimum=1e-7, maximum=1e-7)
    low = 1 / (2 * math.pi * r.maximum * c.maximum)
    high = 1 / (2 * math.pi * r.minimum * c.minimum)
    error = .0005 if within_tolerance else .002
    target = low / (1 + error) if side == "below" else high / (1 - error)
    kwargs = dict(cutoff_hz=target, resistance_ohm=r, capacitance_f=c,
                  relative_error_tolerance=.001)
    if within_tolerance:
        assert DesignSpec(**kwargs).cutoff_hz == target
    else:
        with pytest.raises(ValidationError, match="does not overlap accepted cutoff"):
            DesignSpec(**kwargs)


@pytest.mark.parametrize("side", ["below", "above"])
def test_acceptance_interval_touching_achievable_bound_is_feasible(side):
    r = Bounds(minimum=1000., maximum=1000.)
    c = Bounds(minimum=1e-7, maximum=1e-7)
    fc = 1 / (2 * math.pi * 1000 * 1e-7)
    tolerance = .0625
    target = fc / (1 + tolerance) if side == "below" else fc / (1 - tolerance)
    DesignSpec(cutoff_hz=target, resistance_ohm=r, capacitance_f=c,
               relative_error_tolerance=tolerance)


def test_rounded_fixed_component_target_obeys_selected_tolerance():
    kwargs = dict(cutoff_hz=1591.5494,
                  resistance_ohm=Bounds(minimum=1000., maximum=1000.),
                  capacitance_f=Bounds(minimum=1e-7, maximum=1e-7))
    DesignSpec(**kwargs, relative_error_tolerance=.001)
    with pytest.raises(ValidationError, match="infeasible"):
        DesignSpec(**kwargs, relative_error_tolerance=1e-10)
