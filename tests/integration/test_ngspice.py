import numpy as np
import pytest

from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.simulation.metrics import analytic_cutoff, analytic_response, cutoff_hz
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


@pytest.mark.integration
@pytest.mark.parametrize("topology", ["rc_lowpass", "rc_highpass"])
@pytest.mark.parametrize("r,c,amplitude", [(1000., 1e-7, 1.), (10000., 1e-8, 2.),
                                            (4700., 2.2e-8, .5), (100., 1e-6, 1.)])
def test_real_lowpass(r, c, amplitude, topology):
    try:
        executable_path()
    except SimulationError as exc:
        if exc.status == "unavailable":
            pytest.skip(str(exc))
        raise
    simulator = Ngspice()
    candidate = CircuitCandidate(topology=topology, resistance_ohm=r, capacitance_f=c)
    result = simulator.simulate(DesignSpec(filter_type=topology, source_amplitude_v=amplitude), candidate)
    assert result.returncode == 0
    reference = analytic_response(candidate, result.response.frequency_hz)
    np.testing.assert_allclose(result.response.transfer, reference.transfer, rtol=2e-5, atol=1e-8)
    np.testing.assert_allclose(result.response.phase_deg, reference.phase_deg, atol=.001)
    assert abs(cutoff_hz(result.response, topology) / analytic_cutoff(candidate) - 1) < .001
    assert len(result.response.frequency_hz) == 601
