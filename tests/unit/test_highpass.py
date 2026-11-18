import math

import numpy as np
import pytest

from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.simulation.metrics import analytic_cutoff, analytic_response, cutoff_hz
from circuforge.synthesis.rc import netlist


@pytest.mark.parametrize("r,c", [(1000., 1e-7), (10000., 1e-8), (4700., 2.2e-8), (100., 1e-6)])
def test_highpass_reference(r, c):
    candidate = CircuitCandidate(topology="rc_highpass", resistance_ohm=r, capacitance_f=c)
    fc = analytic_cutoff(candidate)
    response = analytic_response(candidate, [fc, fc * 10])
    assert abs(response.transfer[0]) == pytest.approx(1 / math.sqrt(2))
    assert response.phase_deg[0] == pytest.approx(45.)
    response = analytic_response(candidate, np.logspace(0, 6, 601))
    assert abs(cutoff_hz(response, candidate.topology) / fc - 1) < .001
    text = netlist(DesignSpec(filter_type="rc_highpass"), candidate)
    assert "C1 in out " in text
    assert "R1 out 0 " in text


def test_topology_mismatch():
    with pytest.raises(ValueError, match="topology"):
        DesignSpec().validate_candidate(CircuitCandidate(topology="rc_highpass"))
