"""Orchestration fixtures only: child cwd must not reinterpret caller paths."""
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from circuforge.simulation.ngspice import Preflight

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("relative_output,relative_manifest", [(True, False), (False, True), (True, True)])
def test_caller_paths_survive_children_running_in_project_directory(tmp_path, monkeypatch,
                                                                   relative_output, relative_manifest):
    module_spec = importlib.util.spec_from_file_location("analytic_acceptance_paths", REPO / "scripts/accept_analytic_rc.py")
    command = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(command)
    project, caller = tmp_path / "project", tmp_path / "caller with spaces"
    caller.mkdir()
    # Small snapshot fixture; no source copies are executed and no physics is claimed.
    for name in ("src/fixture.py", "pyproject.toml", "scripts/accept_analytic_rc.py",
                 "scripts/compare_analytic_rc.py", "examples/design-analytic-rc.json"):
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("orchestration fixture only", encoding="utf-8")
    for folder in (project / "examples", caller / "inputs"):
        folder.mkdir(exist_ok=True)
        for name in ("physics-onecall-v1.json", "benchmark-v2.json"):
            shutil.copyfile(REPO / "examples" / name, folder / name)
    monkeypatch.setattr(command, "ROOT", project)
    monkeypatch.setattr(command, "preflight", lambda _: Preflight("fixture-only", "fixture-only"))
    monkeypatch.setattr(command, "environment", lambda: {"scope": "orchestration fixture"})
    monkeypatch.setattr(command, "plot", lambda *args: None)
    monkeypatch.chdir(caller)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k unrelated_subset")
    calls = []

    def from_child(value, cwd):
        path = Path(value)
        return path if path.is_absolute() else cwd / path

    def fake_run(args, **kwargs):
        calls.append(args)
        assert kwargs["cwd"] == project and kwargs["shell"] is False
        assert "PYTEST_ADDOPTS" not in kwargs["env"]
        assert 0 < kwargs["timeout"] <= 360
        if "--junitxml" in args:
            path = from_child(args[args.index("--junitxml") + 1], kwargs["cwd"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('<testsuite tests="1"><testcase name="orchestration-fixture"/></testsuite>')
        else:
            manifest = from_child(args[args.index("--manifest") + 1], kwargs["cwd"])
            assert manifest.read_bytes() == (caller / "inputs/physics-onecall-v1.json").read_bytes()
            path = from_child(args[args.index("--output") + 1], kwargs["cwd"])
            path.mkdir(parents=True)
        return SimpleNamespace(returncode=0)

    def fixture_audit(manifest, first, replay):
        assert manifest == caller / "inputs/physics-onecall-v1.json"
        assert first.is_dir() and replay.is_dir()
        return {"status": "passed", "aggregates": {}, "audited_calls_including_replay": 0}

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    monkeypatch.setattr(command, "audit_replay", fixture_audit)
    output = caller / "results with spaces"
    manifest = caller / "inputs/physics-onecall-v1.json"
    args = ["--output", "results with spaces" if relative_output else str(output),
            "--manifest", "inputs/physics-onecall-v1.json" if relative_manifest else str(manifest)]
    assert command.main(args) == 0
    record = json.loads((output / "acceptance.json").read_text())
    assert record["status"] == "passed" and len(calls) == 3
    assert (output / "tests.xml").is_file() and not (project / "results with spaces").exists()
