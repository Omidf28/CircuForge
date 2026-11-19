"""Automatic gate must stop on test, runner, replay or dependency failures."""
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from circuforge.simulation.ngspice import Preflight, SimulationError

REPO = Path(__file__).resolve().parents[2]
module_spec = importlib.util.spec_from_file_location("accept_phase3_command", REPO / "scripts/accept_phase3.py")
command = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(command)
MANIFEST = REPO / "examples/benchmark-v2.json"


@pytest.mark.parametrize("mode", ["tests_fail", "tests_skip", "timeout", "runner_fail", "replay_fail"])
def test_failures_block_instead_of_requesting_manual_override(tmp_path, monkeypatch, mode):
    output = tmp_path / "output"
    monkeypatch.setattr(command, "preflight", lambda _: Preflight("controlled-test", "controlled-test"))
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        assert kwargs["shell"] is False and kwargs["timeout"] <= 600
        assert "PYTEST_ADDOPTS" not in kwargs["env"]
        if mode == "timeout":
            raise subprocess.TimeoutExpired(args, 180)
        if len(calls) == 1:
            junit = Path(args[args.index("--junitxml") + 1])
            child = "<skipped/>" if mode == "tests_skip" else ""
            junit.write_text(f'<testsuite tests="1"><testcase name="controlled-xml">{child}</testcase></testsuite>')
        return SimpleNamespace(returncode=int(mode == "tests_fail" or (mode == "runner_fail" and len(calls) == 2)))

    def replay_failure(*args):
        raise ValueError("controlled replay mismatch")

    monkeypatch.setenv("PYTEST_ADDOPTS", "-k imaginary_subset")
    monkeypatch.setattr(command.subprocess, "run", fake_run)
    monkeypatch.setattr(command, "audit_replay", replay_failure)
    assert command.main(["--manifest", str(MANIFEST), "--output", str(output)]) == 1
    record = json.loads((output / "acceptance.json").read_text())
    assert record["status"] == "blocked" and record["manual_review_required"] is False
    assert len(calls) == (3 if mode == "replay_fail" else 2 if mode == "runner_fail" else 1)


def test_missing_simulator_leaves_output_uncreated(tmp_path, monkeypatch):
    def missing(_):
        raise SimulationError("unavailable", "controlled unavailable simulator")
    monkeypatch.setattr(command, "preflight", missing)
    output = tmp_path / "output"
    assert command.main(["--manifest", str(MANIFEST), "--output", str(output)]) == 2
    assert not output.exists()
