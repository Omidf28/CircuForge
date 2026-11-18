"""Synthetic adapter output fixtures; these are not real simulation evidence."""
import numpy as np
import pytest

from circuforge.domain.specs import CircuitCandidate, DesignSpec, Sweep
from circuforge.simulation.ngspice import Ngspice, Preflight, SimulationError


@pytest.mark.parametrize("change", ["interior", "tiny_start", "endpoint"])
def test_adapter_rejects_wrong_grid_even_with_correct_count(monkeypatch, change):
    start = 1e-9 if change == "tiny_start" else 1.0
    sweep = Sweep(start_hz=start, stop_hz=start * 100, points_per_decade=10)
    # This spec has a feasible target inside the chosen sweep.
    spec = DesignSpec(cutoff_hz=start * 10, sweep=sweep,
                      resistance_ohm={"minimum": 10., "maximum": 1e12},
                      capacitance_f={"minimum": 1e-12, "maximum": 1.})
    f = start * 10 ** (np.arange(sweep.expected_points) / 10)
    if change == "interior":
        f[5] *= 1.01
    elif change == "tiny_start":
        f[0] *= .8  # old endpoint check's default absolute tolerance hid this
    else:
        f[-1] *= .99
    table = "Index frequency vr(out) vi(out)\n" + "".join(
        f"{i} {value:.15e} .9 -.1\n" for i, value in enumerate(f)
    )
    monkeypatch.setattr("circuforge.simulation.ngspice.preflight",
                        lambda _: Preflight("synthetic-test-only", "test fixture"))
    monkeypatch.setattr("circuforge.simulation.ngspice._execute", lambda *args: (table, "", 0, .01))
    with pytest.raises(SimulationError, match="frequency grid") as caught:
        Ngspice().simulate(spec, CircuitCandidate())
    assert caught.value.status == "parse_error"
