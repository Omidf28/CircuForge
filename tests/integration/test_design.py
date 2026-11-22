"""Measured export/ASGI checks; the acceptance walkthrough also uses real HTTP."""
import asyncio
import json
from pathlib import Path
import shutil
import zipfile

import httpx
import pytest

from circuforge.api import create_app
from circuforge.application import load_request
from circuforge.application import run_design
from circuforge.cli import main
from circuforge.contracts import DesignResult
from circuforge.contracts import DesignRequest
from circuforge.evaluation.acceptance import AcceptanceError
from circuforge.evaluation.design_acceptance import audit_design, compare_interfaces, extract_bundle
from circuforge.simulation.ngspice import SimulationError, executable_path
from circuforge.simulation.ngspice import Ngspice

REPO = Path(__file__).resolve().parents[2]
CASES = ("design-lowpass", "design-optimization", "design-target-miss")


@pytest.fixture(scope="module")
def real_designs(tmp_path_factory):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    root = tmp_path_factory.mktemp("design-real")
    scratch = root / "scratch"
    scratch.mkdir()
    app = create_app(temporary_root=scratch)
    for name in CASES:
        source = REPO / "examples" / (name + ".json")
        output = root / name
        code = main(["design", "--request", str(source), "--output", str(output / "cli")])
        assert code == (1 if name == "design-target-miss" else 0)

        async def requests():
            transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 50000))
            async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1") as client:
                payload = json.loads(source.read_text(encoding="utf-8"))
                return await client.post("/v1/designs", json=payload), await client.post("/v1/designs/export", json=payload)

        data, archive = asyncio.run(requests())
        assert data.status_code == archive.status_code == 200
        (output / "api.json").write_text(data.text, encoding="utf-8")
        (output / "api.zip").write_bytes(archive.content)
        extract_bundle(output / "api.zip", output / "api")
        assert not list(scratch.iterdir())
    return root


@pytest.mark.integration
def test_cli_api_and_downloaded_raw_exports_match(real_designs):
    for name in CASES:
        request = load_request(REPO / "examples" / (name + ".json"))
        root = real_designs / name
        cli = audit_design(root / "cli", request)
        archive = audit_design(root / "api", request)
        api = DesignResult.model_validate_json((root / "api.json").read_bytes())
        compare_interfaces(cli, api, archive)
        assert cli.simulator_calls == (1 if name == "design-lowpass" else 4)
        assert cli.status == ("target_missed" if name == "design-target-miss" else "passed")


@pytest.mark.integration
@pytest.mark.parametrize("damage", ["status", "waveform", "checksum", "selected_csv", "missing_chart", "zip"])
def test_corrupt_design_evidence_blocks_acceptance(real_designs, tmp_path, damage):
    source = real_designs / "design-target-miss/cli"
    root = tmp_path / "copy"
    shutil.copytree(source, root)
    path = root / "report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if damage == "status":
        report["status"] = "passed"
    elif damage == "waveform":
        report["waveform"]["transfer_real"][0] += .1
    elif damage == "checksum":
        p = root / "manifest.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["files"][0]["sha256"] = "wrong"
        p.write_text(json.dumps(data), encoding="utf-8")
    elif damage == "selected_csv":
        (root / "response.csv").write_text("unrelated data", encoding="utf-8")
    elif damage == "zip":
        with zipfile.ZipFile(root / "bundle.zip", "w") as stream:
            stream.writestr("unrelated.txt", "wrong export")
    else:
        (root / "response.png").unlink()
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(AcceptanceError):
        audit_design(root, load_request(REPO / "examples/design-target-miss.json"))


def test_archive_traversal_is_rejected_without_writing_outside(tmp_path):
    source = tmp_path / "malicious.zip"
    with zipfile.ZipFile(source, "w") as stream:
        stream.writestr("../outside.txt", "must never be extracted")
    with pytest.raises(AcceptanceError, match="unsafe"):
        extract_bundle(source, tmp_path / "destination")
    assert not (tmp_path / "outside.txt").exists() and not (tmp_path / "destination").exists()


@pytest.mark.integration
@pytest.mark.parametrize("method", ["random", "scipy"])
def test_other_declared_optimizer_methods_export_verified_real_history(tmp_path, method):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    payload = json.loads((REPO / "examples/design-lowpass.json").read_text(encoding="utf-8"))
    payload.pop("candidate")
    payload["method"] = method
    payload["spec"]["max_evaluations"] = 2
    request = DesignRequest.model_validate(payload)
    output = tmp_path / "run"
    result = run_design(request, Ngspice(), output)
    audited = audit_design(output, request)
    assert audited == result and result.simulator_calls == 2 and result.failures == 0
