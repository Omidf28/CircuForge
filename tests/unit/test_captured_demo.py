"""Synthetic artifact guards only; raw physics/installed CLI are checked in real acceptance."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pytest

from circuforge.evaluation.records import environment


def command():
    path = Path(__file__).resolve().parents[2] / "scripts/audit_demo.py"
    spec = importlib.util.spec_from_file_location("captured_demo_audit_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    audit = command()
    demo = audit.exporter()
    root, source = tmp_path / "demo", tmp_path / "source"
    root.mkdir()
    source.mkdir()
    python = tmp_path / "installed/Scripts/python.exe"
    results, roots, records = [], [], []
    for name, status, calls in demo.CASES:
        request = SimpleNamespace(method="simulate" if calls == 1 else "grid", spec=SimpleNamespace(cutoff_hz=1000.0))
        best = SimpleNamespace(measured_cutoff_hz=1000.0 if status == "passed" else 1200.0,
                               relative_error=0.0 if status == "passed" else 0.2,
                               candidate=SimpleNamespace(resistance_ohm=1000.0, capacitance_f=1e-7), verified=True)
        result = SimpleNamespace(status=status, simulator_calls=calls, request=request, best=best)
        path = root / name
        (path / "cli").mkdir(parents=True)
        Image.new("RGB", (640, 480), "white").save(path / "cli/response.png")
        (path / "stdout.json").write_text(json.dumps({"synthetic_fixture": name}))
        (source / (name + ".json")).write_text(json.dumps({"synthetic_fixture": name}))
        records.append(dict(case=name, status=status, calls=calls, exit=0 if status == "passed" else 1,
                            command=[str(python), "-I", "-m", "circuforge", "--ngspice", "fixture-spice", "design",
                                     "--request", str(source / (name + ".json")), "--output", str(path / "cli")],
                            input_sha256=demo.sha256(source / (name + ".json")), stdout_sha256=demo.sha256(path / "stdout.json")))
        results.append(result)
        roots.append(path / "cli")
    indexed = dict(zip((name for name, _, _ in demo.CASES), results))
    monkeypatch.setattr(audit, "audit_design", lambda path, request: indexed[path.parent.name])
    monkeypatch.setattr(audit, "load_request", lambda path: indexed[path.stem].request)
    monkeypatch.setattr(audit, "DesignResult", SimpleNamespace(model_validate_json=lambda data: indexed[json.loads(data)["synthetic_fixture"]]))
    images = demo.frames(results, roots)
    for index, image in enumerate(images):
        image.save(root / f"frame-{index:02d}.png")
    (root / "demo.gif").write_bytes(demo.gif_bytes(images))
    (root / "claims.md").write_text(demo.CLAIMS, encoding="utf-8")
    report = dict(policy=demo.POLICY, capture_kind="annotated replay; not live screen recording",
                  exporter_sha256=demo.sha256(Path(demo.__file__)), new_model_requests=0, owner_cv_approved=False,
                  probe_command=[str(python), "-I", "-c", "synthetic probe, never executed"],
                  remote_published=False, installed_identity={"prefix": str(tmp_path / "installed"),
                  "module": str(tmp_path / "installed/Lib/site-packages/circuforge/__init__.py"), "environment": environment()},
                  cases=records, actual_spice_calls=9, frames=5, duration_ms=75000, loops=True,
                  gif_sha256=demo.sha256(root / "demo.gif"), claims_sha256=demo.sha256(root / "claims.md"))
    (root / "demo.json").write_text(json.dumps(report))
    return audit, demo, root, source, report


def test_annotated_replay_does_not_claim_live_capture_or_owner_approval(artifact):
    audit, _, root, source, _ = artifact
    result = audit.audit(source, root)
    assert result["duration_s"] == 75 and result["frames"] == 5
    assert result["target_misses"] == 1
    assert result["owner_cv_approved"] is False
    assert result["remote_published"] is False


@pytest.mark.parametrize("change", ["stdout", "input", "frame", "gif", "claims", "exit", "calls", "live_claim", "duration"])
def test_changed_evidence_or_unsupported_demo_claim_blocks_acceptance(artifact, change):
    audit, _, root, source, report = artifact
    first = report["cases"][0]["case"]
    if change == "stdout":
        (root / first / "stdout.json").write_text("{}")
    elif change == "input":
        (source / (first + ".json")).write_text("{}")
    elif change == "frame":
        Image.new("RGB", (1280, 800), "black").save(root / "frame-00.png")
    elif change == "gif":
        (root / "demo.gif").write_bytes(b"not an authentic demo")
    elif change == "claims":
        (root / "claims.md").write_text("Owner approved: perfect PCB routing and guaranteed AI wins")
    else:
        if change == "exit":
            report["cases"][-1]["exit"] = 0
        elif change == "calls":
            report["actual_spice_calls"] = 1
        elif change == "live_claim":
            report["capture_kind"] = "live screen recording"
        else:
            report["duration_ms"] = 90000
        (root / "demo.json").write_text(json.dumps(report))
    with pytest.raises(ValueError):
        audit.audit(source, root)
