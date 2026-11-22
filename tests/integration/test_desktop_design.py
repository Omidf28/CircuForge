"""Actual single-call desktop jobs; independent raw export audits, no UI automation."""
import time

import pytest

from circuforge.desktop.model import FormValues, RunController, build_request
from circuforge.evaluation.design_acceptance import audit_design
from circuforge.simulation.ngspice import SimulationError, executable_path


@pytest.mark.integration
@pytest.mark.parametrize("values,status", [(FormValues(), "passed"),
                                          (FormValues(topology="High-pass"), "passed"),
                                          (FormValues(mode="Simulate R/C"), "target_missed")])
def test_real_background_desktop_job_preserves_physics_status_and_evidence(tmp_path, values, status):
    try:
        executable = executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    controller = RunController()
    request = build_request(values)
    path = controller.start(request, tmp_path / "desktop runs", executable)
    deadline = time.monotonic() + 20
    event = None
    while event is None and time.monotonic() < deadline:
        event = controller.poll()
        time.sleep(.01)
    assert event is not None and event.error is None and not controller.busy
    assert event.result.status == status and event.result.simulator_calls == 1
    assert audit_design(path, request) == event.result
    assert (path / "bundle.zip").is_file() and (path / "response.png").is_file()


def test_missing_simulator_is_an_error_not_a_design_pass(tmp_path):
    controller = RunController()
    path = controller.start(build_request(FormValues()), tmp_path / "runs", str(tmp_path / "missing-ngspice.exe"))
    deadline = time.monotonic() + 5
    event = None
    while event is None and time.monotonic() < deadline:
        event = controller.poll()
        time.sleep(.01)
    assert event is not None and event.result is None and "unavailable" in event.error
    assert not path.exists()
