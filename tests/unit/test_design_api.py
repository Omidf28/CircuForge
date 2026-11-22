"""Reject malformed/oversized/remote work before simulator or artifact allocation."""
import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import httpx
import pytest
from pydantic import ValidationError

from circuforge.api import create_app
from circuforge.application import load_request, run_design
from circuforge.cli import main
from circuforge.contracts import DesignRequest, DesignResult
from circuforge.simulation.ngspice import SimulationError

REPO = Path(__file__).resolve().parents[2]
PAYLOAD = json.loads((REPO / "examples/design-lowpass.json").read_text(encoding="utf-8"))


def send(app, *, payload=None, content=None, headers=None, client_host="127.0.0.1", base_url="http://127.0.0.1"):
    async def execute():
        transport = httpx.ASGITransport(app=app, client=(client_host, 50000))
        async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
            return await client.post("/v1/designs", json=payload, content=content, headers=headers)
    return asyncio.run(execute())


@pytest.mark.parametrize("field,value", [("netlist", ".control\nshell echo forbidden"), ("output", "../../outside"), ("ngspice", "other.exe")])
def test_arbitrary_execution_and_paths_are_not_request_fields(field, value):
    data = copy.deepcopy(PAYLOAD)
    data[field] = value
    with pytest.raises(ValidationError):
        DesignRequest.model_validate(data)


def test_input_size_and_invalid_cli_never_start_simulator(tmp_path, monkeypatch):
    source = tmp_path / "request.json"
    source.write_bytes(b" " * 16385)
    with pytest.raises(ValueError, match="16 KiB"):
        load_request(source)

    def forbidden(*args):
        raise AssertionError("must reject before simulator preflight")

    monkeypatch.setattr("circuforge.cli.Ngspice", forbidden)
    assert main(["design", "--request", str(source), "--output", str(tmp_path / "out")]) == 2
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("damage", ["missing_candidate", "optimizer_candidate", "wrong_topology", "calls", "timeout", "total_time", "sweep"])
def test_unsupported_or_unbounded_design_request_is_rejected(damage):
    data = copy.deepcopy(PAYLOAD)
    if damage == "missing_candidate":
        data.pop("candidate")
    elif damage == "optimizer_candidate":
        data["method"] = "random"
    elif damage == "wrong_topology":
        data["candidate"]["topology"] = "rc_highpass"
    elif damage == "calls":
        data["spec"]["max_evaluations"] = 33
    elif damage == "timeout":
        data["spec"]["timeout_s"] = 6.
    elif damage == "total_time":
        data["spec"].update(max_evaluations=32, timeout_s=2.)
    else:
        data["spec"]["sweep"] = {"start_hz": 1., "stop_hz": 1e6, "points_per_decade": 500}
    with pytest.raises(ValidationError):
        DesignRequest.model_validate(data)


@pytest.mark.parametrize("damage,code", [("invalid", 422), ("api_calls", 422), ("api_timeout", 422), ("api_sweep", 422),
                                        ("body", 413), ("origin", 403), ("host", 400), ("remote", 403),
                                        ("content_type", 415), ("json", 422), ("busy", 429), ("chunked", 413)])
def test_request_guards_prevent_any_compute(tmp_path, monkeypatch, damage, code):
    def forbidden(*args):
        raise AssertionError("guard must run before simulator construction")

    monkeypatch.setattr("circuforge.api.Ngspice", forbidden)
    app = create_app(temporary_root=tmp_path)
    payload = copy.deepcopy(PAYLOAD)
    kwargs = {"payload": payload}
    if damage == "invalid":
        payload["spec"]["load"] = "finite"
    elif damage == "api_calls":
        payload["spec"]["max_evaluations"] = 9
    elif damage == "api_timeout":
        payload["spec"]["timeout_s"] = 3.
    elif damage == "api_sweep":
        payload["spec"]["sweep"] = {"start_hz": 1., "stop_hz": 1e6, "points_per_decade": 200}
    elif damage == "body":
        kwargs = {"content": b"x" * 16385, "headers": {"Content-Type": "application/json"}}
    elif damage == "origin":
        kwargs["headers"] = {"Origin": "https://untrusted.example"}
    elif damage == "host":
        kwargs["base_url"] = "http://untrusted.example"
    elif damage == "remote":
        kwargs["client_host"] = "192.0.2.10"
    elif damage == "content_type":
        kwargs = {"content": b"{}", "headers": {"Content-Type": "text/plain"}}
    elif damage == "json":
        kwargs = {"content": b"{", "headers": {"Content-Type": "application/json"}}
    elif damage == "busy":
        app.state.design_gate.acquire()
    elif damage == "chunked":
        async def chunks():
            yield b"x" * 10000
            yield b"x" * 10000
        kwargs = {"content": chunks(), "headers": {"Content-Type": "application/json"}}
    try:
        result = send(app, **kwargs)
        assert result.status_code == code, result.text
        assert list(tmp_path.iterdir()) == []
    finally:
        if damage == "busy":
            app.state.design_gate.release()


def test_missing_simulator_reports_dependency_failure_and_releases_gate(tmp_path, monkeypatch):
    def unavailable(*args):
        raise SimulationError("unavailable", "controlled missing executable")

    monkeypatch.setattr("circuforge.api.Ngspice", unavailable)
    app = create_app(temporary_root=tmp_path)
    for _ in range(2):
        response = send(app, payload=PAYLOAD)
        assert response.status_code == 503 and response.json()["code"] == "unavailable"
    assert not list(tmp_path.iterdir())


def test_measured_failure_is_not_target_success_and_retains_cli_evidence(tmp_path, monkeypatch):
    class FailingSimulator:
        info = SimpleNamespace(version="controlled failure fixture", executable="test-unavailable")

        def simulate(self, spec, candidate):
            raise SimulationError("launch_error", "controlled failure")

    request = DesignRequest.model_validate(PAYLOAD)
    output = tmp_path / "cli"
    result = run_design(request, FailingSimulator(), output)
    assert result.status == "simulation_failed" and result.best is None and result.waveform is None
    assert result.simulator_calls == result.failures == 1
    assert (output / "bundle.zip").exists() and not (output / "response.png").exists()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr("circuforge.api.Ngspice", lambda _: FailingSimulator())
    response = send(create_app(temporary_root=scratch), payload=PAYLOAD)
    assert response.status_code == 502 and DesignResult.model_validate(response.json()).status == "simulation_failed"
    assert not list(scratch.iterdir())


def test_artifact_exception_cleans_temp_and_releases_gate(tmp_path, monkeypatch):
    monkeypatch.setattr("circuforge.api.Ngspice", lambda _: object())

    def unavailable_storage(*args):
        raise OSError("controlled unwritable artifact storage")

    monkeypatch.setattr("circuforge.api.run_design", unavailable_storage)
    app = create_app(temporary_root=tmp_path)
    for _ in range(2):
        response = send(app, payload=PAYLOAD)
        assert response.status_code == 500 and response.json()["code"] == "artifact_error"
    assert not list(tmp_path.iterdir())


def test_slow_body_is_bounded_before_any_compute(tmp_path, monkeypatch):
    def forbidden(*args):
        raise AssertionError("body timeout must not start simulator")
    monkeypatch.setattr("circuforge.api.Ngspice", forbidden)

    async def stalled_body():
        await asyncio.sleep(6)
        yield b"{}"

    response = send(create_app(temporary_root=tmp_path), content=stalled_body(), headers={"Content-Type": "application/json"})
    assert response.status_code == 408 and not list(tmp_path.iterdir())


def test_concurrent_design_is_rejected_without_queueing_or_temp_leak(tmp_path, monkeypatch):
    entered, release = Event(), Event()
    monkeypatch.setattr("circuforge.api.Ngspice", lambda _: object())

    def held_design(*args):
        entered.set()
        assert release.wait(5)
        raise OSError("controlled completion failure")

    monkeypatch.setattr("circuforge.api.run_design", held_design)
    app = create_app(temporary_root=tmp_path)
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(send, app, payload=PAYLOAD)
        try:
            assert entered.wait(5)
            assert send(app, payload=PAYLOAD).status_code == 429
        finally:
            release.set()
        assert first.result(timeout=10).status_code == 500
    assert not list(tmp_path.iterdir())
