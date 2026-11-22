"""Failed/skipped stages must block before installation or HTTP walkthrough."""
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from circuforge.simulation.ngspice import Preflight, SimulationError

REPO = Path(__file__).resolve().parents[2]
module_spec = importlib.util.spec_from_file_location("accept_phase5_command", REPO / "scripts/accept_phase5.py")
command = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(command)


@pytest.mark.parametrize("mode", ["tests_fail", "tests_skip", "timeout", "build_fail", "install_fail", "audit_fail"])
def test_pipeline_failures_are_never_manual_waivers(tmp_path, monkeypatch, mode):
    output = tmp_path / "output"
    monkeypatch.setattr(command, "preflight", lambda _: Preflight("controlled-ngspice", "controlled-version"))
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        assert kwargs["shell"] is False and kwargs["timeout"] <= 300
        if mode == "timeout":
            raise subprocess.TimeoutExpired(args, 300)
        if len(calls) == 1:
            junit = Path(args[args.index("--junitxml") + 1])
            child = "<skipped/>" if mode == "tests_skip" else ""
            junit.write_text(f'<testsuite tests="1"><testcase name="controlled-xml">{child}</testcase></testsuite>', encoding="utf-8")
        else:
            assert "PYTHONPATH" not in kwargs["env"], "fresh installation must not import source checkout"
        if len(calls) == 2:
            wheels = output / "wheels"
            wheels.mkdir()
            (wheels / "circuforge-fixture.whl").write_bytes(b"controlled wheel fixture, never installed")
        failed = mode == "tests_fail" or (mode == "build_fail" and len(calls) == 2) or (mode == "install_fail" and len(calls) == 4)
        return SimpleNamespace(returncode=int(failed))

    def audit_failure(*args):
        raise ValueError("controlled incomplete walkthrough")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    monkeypatch.setattr(command, "audit_walkthrough", audit_failure)
    assert command.main(["--output", str(output)]) == 1
    record = json.loads((output / "acceptance.json").read_text(encoding="utf-8"))
    assert record["status"] == "blocked" and record["manual_review_required"] is False
    expected = {"tests_fail": 1, "tests_skip": 1, "timeout": 1, "build_fail": 2, "install_fail": 4, "audit_fail": 5}
    assert len(calls) == expected[mode]


def test_missing_ngspice_blocks_before_output_allocation(tmp_path, monkeypatch):
    def missing(_):
        raise SimulationError("unavailable", "controlled missing binary")
    monkeypatch.setattr(command, "preflight", missing)
    output = tmp_path / "output"
    assert command.main(["--output", str(output)]) == 2
    assert not output.exists()
