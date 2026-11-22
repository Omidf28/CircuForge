import numpy as np
import pytest

from circuforge.domain.specs import CircuitCandidate, DesignSpec, Sweep
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


@pytest.mark.integration
@pytest.mark.parametrize("start,stop,density", [(2., 123456., 100), (1., 1591.55, 100), (3., 99999., 17)])
def test_real_noninteger_decade_sweep(start, stop, density):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    sweep = Sweep(start_hz=start, stop_hz=stop, points_per_decade=density)
    candidate = CircuitCandidate()
    result = Ngspice().simulate(DesignSpec(cutoff_hz=1000., sweep=sweep), candidate)
    nominal = start * 10 ** (np.arange(sweep.expected_points) / density)
    endpoints = np.geomspace(start, stop, sweep.expected_points)
    assert any(np.allclose(result.response.frequency_hz, grid, rtol=1e-6, atol=0.)
               for grid in (nominal, endpoints))
    np.testing.assert_allclose(result.response.transfer,
                               analytic_response(candidate, result.response.frequency_hz).transfer,
                               rtol=2e-5, atol=1e-8)


@pytest.mark.integration
@pytest.mark.parametrize("topology", ["rc_lowpass", "rc_highpass"])
def test_real_two_sample_sweep_is_still_usable(topology):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    target = 101.
    candidate = CircuitCandidate(topology=topology, resistance_ohm=1000.,
                                 capacitance_f=1 / (2 * np.pi * 1000 * target))
    sweep = Sweep(start_hz=100., stop_hz=100 * 10 ** .01, points_per_decade=100)
    spec = DesignSpec(filter_type=topology, cutoff_hz=target, sweep=sweep)
    result = Ngspice().simulate(spec, candidate)
    assert len(result.response.frequency_hz) == 2
    assert abs(cutoff_hz(result.response, topology) / target - 1) < .001
