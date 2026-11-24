"""Filesystem/cwd process fixtures; deliberately blocked audits, not scientific evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from circuforge.simulation.ngspice import Preflight

REPO = Path(__file__).resolve().parents[2]
JUNIT = '<testsuite tests="1"><testcase name="cwd-process-fixture"/></testsuite>'
REACHED = "path fixture reached audit; no real scientific acceptance"


def load(name):
    spec = importlib.util.spec_from_file_location(name + "_caller_paths", REPO / "scripts" / (name + ".py"))
    command = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(command)
    return command


def fixture_project(tmp_path):
    project, caller = tmp_path / "project", tmp_path / "caller with spaces"
    (project / "examples").mkdir(parents=True)
    (caller / "inputs").mkdir(parents=True)
    for name in ("phase2-review-cases.json", "benchmark-v2.json", "robustness-v1.json", "design-lowpass.json"):
        for folder in (project / "examples", caller / "inputs"):
            shutil.copyfile(REPO / "examples" / name, folder / name)
    (project / "src").mkdir()
    (project / "src/fixture.py").write_text("# never executed")
    (project / "pyproject.toml").write_text("# never built")
    return project, caller


def block_audit(*args):
    raise ValueError(REACHED)


@pytest.mark.parametrize("phase", [2, 3, 4, 5])
def test_gate_evidence_and_build_inputs_survive_child_cwd(tmp_path, monkeypatch, phase):
    command = load(f"accept_phase{phase}")
    project, caller = fixture_project(tmp_path)
    output = caller / "results with spaces"
    monkeypatch.setattr(command, "ROOT", project)
    monkeypatch.setattr(command, "preflight", lambda _: Preflight("fixture-only", "fixture-only"))
    monkeypatch.chdir(caller)
    calls = []

    def child_path(value):
        path = Path(value)
        return path if path.is_absolute() else project / path

    def argument(args, flag):
        return child_path(args[args.index(flag) + 1])

    def fake_run(args, **kwargs):
        calls.append(args)
        assert kwargs["cwd"] == project and kwargs["shell"] is False
        assert 0 < kwargs["timeout"] <= 600
        if "--junitxml" in args:
            path = argument(args, "--junitxml")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(JUNIT)
        elif "--wheel-dir" in args:
            assert child_path(args[-1]).joinpath("pyproject.toml").is_file()
            wheels = argument(args, "--wheel-dir")
            wheels.mkdir()
            (wheels / "circuforge-fixture.whl").write_bytes(b"not an installable wheel")
        elif "venv" in args:
            child_path(args[-1]).mkdir()
        elif "install" in args:
            assert argument(args, "--constraint").read_text()
            assert child_path(args[-1].removesuffix("[api,test]")).is_file()
            assert child_path(args[0]).parent.parent.is_dir()
        else:
            if "--manifest" in args:
                manifest = argument(args, "--manifest")
                assert manifest.read_bytes() == (caller / "inputs" / manifest.name).read_bytes()
            if "--source" in args:
                assert (argument(args, "--source") / "design-lowpass.json").is_file()
            argument(args, "--output").mkdir(parents=True)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    auditor = "audit_phase2" if phase == 2 else "audit_walkthrough" if phase == 5 else "audit_replay"
    monkeypatch.setattr(command, auditor, block_audit)
    args = ["--output", "results with spaces"]
    if phase in (3, 4):
        args += ["--manifest", "inputs/" + ("benchmark-v2.json" if phase == 3 else "robustness-v1.json")]
    assert command.main(args) == 1
    decision = json.loads((output / "acceptance.json").read_text())
    assert decision["status"] == "blocked" and decision["error"] == REACHED
    assert (output / "tests.xml").is_file()
    assert len(calls) == {2: 2, 3: 3, 4: 3, 5: 5}[phase]
    assert not (project / "results with spaces").exists()


def test_phase7_relative_evidence_and_junit_keep_caller_identity(tmp_path, monkeypatch):
    command = load("accept_phase7")
    project, caller = fixture_project(tmp_path)
    composite = {"status": "passed", "scope": "fixture only"}
    (project / "planning").mkdir()
    ids = ("P3-C3", "P4-C3", "P5-C4", "P6-C2", "P7-C1", "P7-C2")
    (project / "planning/phase-tasks.json").write_text(json.dumps({"phases": [{"tasks": [
        {"id": name, "status": "done", "evidence": "fixture only"} for name in ids]}]}))
    (project / "docs/research").mkdir(parents=True)
    (project / "docs/research/summary.json").write_text(json.dumps({
        "phase6_status": "passed", "replay_supplement": composite, "sources": []}))
    for name in ("demo", "interface", "primary", "supplement"):
        (caller / "inputs" / name).mkdir()
    interface = caller / "inputs/interface"
    (interface / "tests.xml").write_text(JUNIT)
    (interface / "acceptance.json").write_text(json.dumps({"status": "passed", "policy": "phase5-local-interface-v1",
                                                          "environment": {"fixture": True}, "tests_passed": 1}))
    (caller / "inputs/supplement/acceptance.json").write_text(json.dumps(composite))
    monkeypatch.setattr(command, "ROOT", project)
    monkeypatch.setattr(command, "environment", lambda: {"fixture": True})
    monkeypatch.chdir(caller)

    def module(name):
        def audit(*paths):
            assert all(path.is_dir() for path in paths)
            if name == "audit_demo":
                assert paths[1] == caller / "inputs/demo"
                block_audit()
            return composite
        return SimpleNamespace(audit=audit)

    def fake_run(args, **kwargs):
        assert kwargs["cwd"] == project and kwargs["shell"] is False
        path = Path(args[args.index("--junitxml") + 1])
        if not path.is_absolute():
            path = project / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(JUNIT)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(command, "module", module)
    monkeypatch.setattr(command.subprocess, "run", fake_run)
    args = ["--output", "results with spaces", "--demo", "inputs/demo", "--interface-evidence", "inputs/interface",
            "--primary-trial", "inputs/primary", "--replay-supplement", "inputs/supplement", "--ngspice", "fixture-only"]
    assert command.main(args) == 1
    decision = json.loads((caller / "results with spaces/acceptance.json").read_text())
    assert decision["status"] == "blocked" and decision["error"] == REACHED
    assert not (project / "results with spaces").exists()
