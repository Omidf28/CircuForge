import math

import numpy as np
import pytest
from pydantic import ValidationError

from circuforge.domain.specs import Bounds, CircuitCandidate, DesignSpec, Sweep
from circuforge.simulation.metrics import Response, analytic_cutoff, analytic_response, cutoff_hz
from circuforge.simulation.ngspice import parse_ac
from circuforge.synthesis.rc import netlist


@pytest.mark.parametrize("field,value", [
    ("cutoff_hz", 0), ("cutoff_hz", -1), ("cutoff_hz", float("nan")),
    ("cutoff_hz", float("inf")), ("cutoff_hz", "1k"), ("cutoff_hz", True),
    ("filter_type", "rlc"), ("filter_type", "x\n.include secret"),
    ("source_impedance_ohm", 50), ("load", "1000"), ("value_policy", "E24"),
    ("max_evaluations", 1001), ("timeout_s", 100), ("source_amplitude_v", 0),
    ("netlist", ".control\nshell cmd"),
])
def test_invalid_spec(field, value):
    with pytest.raises(ValidationError):
        DesignSpec(**{field: value})


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan"), "1k\n.end", True])
def test_invalid_element(value):
    with pytest.raises(ValidationError):
        CircuitCandidate(resistance_ohm=value)


def test_bounds_feasibility_and_limits():
    with pytest.raises(ValidationError):
        Bounds(minimum=10.0, maximum=1.0)
    with pytest.raises(ValidationError, match="infeasible"):
        DesignSpec(cutoff_hz=100.0, resistance_ohm=Bounds(minimum=1000.0, maximum=1000.0),
                   capacitance_f=Bounds(minimum=1e-7, maximum=1e-7))
    with pytest.raises(ValidationError):
        Sweep(start_hz=10.0, stop_hz=1.0)
    with pytest.raises(ValidationError, match="budget"):
        Sweep(start_hz=1e-9, stop_hz=1e15, points_per_decade=1000)
    with pytest.raises(ValueError, match="bounds"):
        DesignSpec().validate_candidate(CircuitCandidate(resistance_ohm=1.0))


def test_trusted_netlist():
    text = netlist(DesignSpec(), CircuitCandidate())
    assert "R1 in out 1000\n" in text
    assert "V1 in 0 AC 1\n" in text
    assert ".ac dec 100 1 1000000\n" in text
    assert ".print ac vr(out) vi(out)\n" in text
    assert text.endswith(".end\n")
    assert ".control" not in text and ".include" not in text
    with pytest.raises(TypeError):
        netlist(DesignSpec(), "untrusted netlist")


@pytest.mark.parametrize("r,c", [(1000., 1e-7), (10000., 1e-8), (4700., 2.2e-8), (100., 1e-6)])
def test_analytic_reference_and_cutoff(r, c):
    candidate = CircuitCandidate(resistance_ohm=r, capacitance_f=c)
    fc = analytic_cutoff(candidate)
    assert fc == pytest.approx(1 / (2 * math.pi * r * c))
    at_fc = analytic_response(candidate, [fc, 10 * fc])
    assert abs(at_fc.transfer[0]) == pytest.approx(1 / math.sqrt(2))
    assert at_fc.phase_deg[0] == pytest.approx(-45)
    response = analytic_response(candidate, np.logspace(0, 6, 601))
    assert abs(cutoff_hz(response) / fc - 1) < 0.001


def test_cutoff_resolution_across_grid_offsets():
    for fc in np.geomspace(101, 98765, 100):
        candidate = CircuitCandidate(resistance_ohm=1000., capacitance_f=1 / (2 * math.pi * 1000 * fc))
        response = analytic_response(candidate, np.logspace(0, 6, 601))
        assert abs(cutoff_hz(response) / fc - 1) < 0.001


def test_cutoff_requires_bracket():
    response = analytic_response(CircuitCandidate(), [1, 10, 100])
    with pytest.raises(ValueError, match="bracket"):
        cutoff_hz(response)


@pytest.mark.parametrize("freq,h", [([1, 1], [1, 1]), ([2, 1], [1, 1]),
                                     ([0, 1], [1, 1]), ([1, 2], [1, float("nan")]),
                                     ([1, 2], [1, 0]), ([1], [1])])
def test_malformed_response(freq, h):
    with pytest.raises(ValueError):
        Response(freq, h)


# Deliberately synthetic parser fixture; never presented as simulator evidence.
TABLE = "Index frequency vr(out) vi(out)\n0 1.0 2.0 -0.02\n1 2.0 1.9 -0.04\n"


def test_parser_normalizes_amplitude():
    result = parse_ac(TABLE, 2.0, 2)
    np.testing.assert_allclose(result.transfer, [1 - .01j, .95 - .02j])


@pytest.mark.parametrize("text", ["", TABLE.replace("1 2.0", "3 2.0"),
                                  TABLE.replace("1.9", "nan"), TABLE.replace("1.9", "bad"),
                                  TABLE.replace("vr(out)", "vm(out)"), TABLE + "2 3 1 0\n"])
def test_parser_rejects_incomplete_corrupt_data(text):
    with pytest.raises(ValueError):
        parse_ac(text, 1.0, 2)
