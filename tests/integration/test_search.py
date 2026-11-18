import pytest

from circuforge.domain.specs import DesignSpec
from circuforge.optimization.search import search
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


@pytest.mark.integration
@pytest.mark.parametrize("topology", ["rc_lowpass", "rc_highpass"])
def test_real_bounded_search(topology):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    spec = DesignSpec(filter_type=topology, cutoff_hz=2300.0, max_evaluations=24)
    simulator = Ngspice()
    first = search(spec, simulator)
    second = search(spec, simulator)
    assert first.converged
    assert first.relative_error <= .001
    assert first.simulator_calls <= spec.max_evaluations
    assert first.simulator_calls == len(first.history)
    assert first.candidate == second.candidate
    assert first.measured_cutoff_hz == second.measured_cutoff_hz
    for entry in first.history:
        from circuforge.domain.specs import CircuitCandidate
        spec.validate_candidate(CircuitCandidate(**entry["candidate"]))
    limited = search(DesignSpec(filter_type=topology, cutoff_hz=2300.0, max_evaluations=1), simulator)
    assert limited.simulator_calls == 1
    assert not limited.converged
