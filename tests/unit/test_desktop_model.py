"""Desktop request/concurrency fixtures; no GUI, model or simulated measurements."""
from dataclasses import replace
from pathlib import Path
from threading import Event
import time

import pytest

from circuforge.desktop.model import FormValues, RunController, build_request


def completed(controller, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        event = controller.poll()
        if event is not None:
            return event
        time.sleep(.01)
    raise AssertionError("worker did not publish a completion")


@pytest.mark.parametrize("topology,expected", [("Low-pass", "rc_lowpass"), ("High-pass", "rc_highpass")])
def test_labeled_form_converts_units_without_weakening_engine_limits(topology, expected):
    request = build_request(FormValues(topology=topology))
    assert request.method == "analytic_rc" and request.candidate is None
    assert request.spec.filter_type == expected
    assert request.spec.capacitance_f.minimum == pytest.approx(1e-8)
    assert request.spec.capacitance_f.maximum == pytest.approx(1e-6)
    assert request.spec.relative_error_tolerance == .001
    assert request.spec.max_evaluations == 1 and request.spec.timeout_s == 2.
    assert request.spec.sweep.expected_points <= 1001


def test_manual_candidate_is_measurable_even_when_it_will_miss_the_target():
    request = build_request(FormValues(mode="Simulate R/C"))
    assert request.method == "simulate" and request.candidate.resistance_ohm == 1000.
    assert request.candidate.capacitance_f == pytest.approx(1e-7)
    request.spec.validate_candidate(request.candidate)
    assert request.spec.sweep.start_hz < 1591.55 < request.spec.cutoff_hz < request.spec.sweep.stop_hz


@pytest.mark.parametrize("field,value", [("target_hz", "nan"), ("target_hz", "inf"), ("target_hz", "0"),
                                       ("target_hz", "-1"), ("target_hz", "words"), ("target_hz", "1e16"),
                                       ("tolerance_pct", "0"), ("tolerance_pct", "11"),
                                       ("r_min_ohm", "100000"), ("c_min_nf", "0"),
                                       ("topology", "rlc"), ("mode", "grid")])
def test_invalid_inputs_never_become_requests(field, value):
    with pytest.raises(ValueError):
        build_request(replace(FormValues(), **{field: value}))


def test_infeasible_bounds_are_explained_before_a_worker_can_start():
    with pytest.raises(ValueError, match="infeasible"):
        build_request(FormValues(r_min_ohm="100", r_max_ohm="100", c_min_nf="10", c_max_nf="10"))


def test_one_background_job_and_distinct_output_paths(tmp_path):
    entered, release = Event(), Event()
    captured = []

    def runner(request, output, executable):
        captured.append((request, output, executable))
        entered.set()
        assert release.wait(3)
        return None  # Explicit process fixture; no electrical success is claimed.

    controller = RunController(runner)
    request = build_request(FormValues())
    try:
        first = controller.start(request, tmp_path / "results with spaces", "fixture")
        assert entered.wait(1) and controller.busy and controller.poll() is None
        with pytest.raises(RuntimeError, match="already running"):
            controller.start(request, tmp_path)
    finally:
        release.set()
    event = completed(controller)
    assert not controller.busy and event.output == first and event.error is None
    second = controller.start(request, tmp_path / "results with spaces")
    completed(controller)
    assert first != second and captured[0] == (request, first, "fixture")
    assert not first.parent.exists(), "a fixture worker must not create real artifacts"


def test_worker_failure_is_delivered_without_touching_the_gui(tmp_path):
    def runner(*args):
        raise OSError("controlled unwritable destination")
    controller = RunController(runner)
    output = controller.start(build_request(FormValues()), tmp_path)
    event = completed(controller)
    assert event.output == output and event.result is None
    assert "controlled unwritable destination" in event.error and not controller.busy


def test_modified_request_cannot_bypass_desktop_caps(tmp_path):
    request = build_request(FormValues())
    request = request.model_copy(update={"spec": request.spec.model_copy(update={"max_evaluations": 2})})
    controller = RunController(lambda *args: pytest.fail("invalid request reached worker"))
    with pytest.raises(ValueError, match="one call"):
        controller.start(request, tmp_path / "must not exist")
    assert not controller.busy and not (tmp_path / "must not exist").exists()
