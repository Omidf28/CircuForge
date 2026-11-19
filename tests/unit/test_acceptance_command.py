"""A test-process failure or skip must never fall through to acceptance."""
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from circuforge.simulation.ngspice import Preflight, SimulationError

REPO = Path(__file__).resolve().parents[2]
module_spec = importlib.util.spec_from_file_location("accept_command", REPO / "scripts/accept_phase2.py")
command = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(command)


def prepare(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "examples").mkdir(parents=True)
    (repo / "examples/phase2-review-cases.json").write_bytes((REPO / "examples/phase2-review-cases.json").read_bytes())
    monkeypatch.setattr(command, "ROOT", repo)
    return tmp_path / "output"


@pytest.mark.parametrize("mode", ["failure", "skip", "timeout"])
def test_failed_test_stage_blocks_before_comparison(tmp_path, monkeypatch, mode):
    output = prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(command, "preflight", lambda _: Preflight("test-only", "test-only"))
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        assert len(calls) == 1, "comparison must not run after failed/skipped tests"
        if mode == "timeout":
            raise subprocess.TimeoutExpired(args, 180)
        if mode == "skip":
            junit = Path(args[args.index("--junitxml") + 1])
            junit.write_text('<testsuite tests="1"><testcase name="xml-fixture"><skipped/></testcase></testsuite>')
        return SimpleNamespace(returncode=1 if mode == "failure" else 0)

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    assert command.main(["--output", str(output)]) == 1
    record = json.loads((output / "acceptance.json").read_text())
    assert record["status"] == "blocked" and not record["manual_review_required"]
    assert not (output / "comparison").exists()


def test_missing_simulator_blocks_before_creating_output(tmp_path, monkeypatch):
    output = prepare(tmp_path, monkeypatch)

    def missing(_):
        raise SimulationError("unavailable", "controlled unavailable executable")

    monkeypatch.setattr(command, "preflight", missing)
    assert command.main(["--output", str(output)]) == 2
    assert not output.exists()
