"""Fail-closed proposal task acceptance boundaries; no simulator substitution."""
import importlib.util
from pathlib import Path

import pytest

from circuforge.simulation.ngspice import SimulationError


def load_command():
    path = Path(__file__).resolve().parents[2] / "scripts/accept_proposals.py"
    spec = importlib.util.spec_from_file_location("proposal_acceptance_command", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_simulator_is_blocked_without_creating_evidence(monkeypatch, tmp_path):
    module = load_command()

    def missing(_):
        raise SimulationError("unavailable", "controlled absent executable")

    monkeypatch.setattr(module, "preflight", missing)
    output = tmp_path / "missing"
    assert module.main(["--output", str(output)]) == 2
    assert not output.exists()


def test_existing_evidence_is_never_overwritten(monkeypatch, tmp_path):
    module = load_command()
    monkeypatch.setattr(module, "preflight", lambda _: None)
    sentinel = tmp_path / "acceptance.json"
    sentinel.write_text("previous evidence")
    assert module.main(["--output", str(tmp_path)]) == 2
    assert sentinel.read_text() == "previous evidence"


def test_skips_do_not_count_as_task_acceptance(tmp_path):
    module = load_command()
    junit = tmp_path / "tests.xml"
    junit.write_text('<testsuites><testsuite tests="1" skipped="1"><testcase><skipped/></testcase></testsuite></testsuites>')
    with pytest.raises(ValueError, match="skipped"):
        module.validate_junit(junit)
