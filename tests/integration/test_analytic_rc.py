import asyncio

import httpx
import pytest

from circuforge.api import create_app
from circuforge.application import run_design
from circuforge.contracts import DesignRequest, DesignResult
from circuforge.domain.cases import Case
from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.acceptance import audit_run
from circuforge.evaluation.design_acceptance import audit_design, extract_bundle
from circuforge.optimization.baselines import run_baseline
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


def simulator():
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    return Ngspice()


@pytest.mark.integration
@pytest.mark.parametrize("topology", ["rc_lowpass", "rc_highpass"])
def test_real_one_call_design_and_raw_audit(topology, tmp_path):
    spec = DesignSpec(filter_type=topology, cutoff_hz=2300.0, max_evaluations=7,
                      resistance_ohm=dict(minimum=100.0, maximum=10000.0),
                      capacitance_f=dict(minimum=1e-8, maximum=1e-6))
    result = run_baseline(spec, simulator(), "analytic_rc", seed=7, output=tmp_path / "case/analytic_rc")
    assert result.converged and result.simulator_calls == 1
    assert audit_run(tmp_path, Case(id="case", spec=spec), "analytic_rc", 7) == result


@pytest.mark.integration
def test_shared_design_and_api_export_keep_actual_onecall_budget(tmp_path):
    adapter = simulator()
    request = DesignRequest(spec=DesignSpec(cutoff_hz=2300.0, max_evaluations=4, timeout_s=2.0), method="analytic_rc")
    output = tmp_path / "cli"
    first = run_design(request, adapter, output)
    assert first.status == "passed" and first.simulator_calls == 1
    assert audit_design(output, request) == first
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    app = create_app(ngspice=adapter.info.executable, temporary_root=scratch)

    async def calls():
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 50000))
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1") as client:
            return await client.post("/v1/designs", json=request.model_dump()), await client.post("/v1/designs/export", json=request.model_dump())

    response, zipped = asyncio.run(calls())
    assert response.status_code == zipped.status_code == 200
    second = DesignResult.model_validate(response.json())
    assert second.status == "passed" and second.simulator_calls == 1
    (tmp_path / "api.zip").write_bytes(zipped.content)
    extract_bundle(tmp_path / "api.zip", tmp_path / "api")
    assert audit_design(tmp_path / "api", request).best.candidate == first.best.candidate
    assert not list(scratch.iterdir())
