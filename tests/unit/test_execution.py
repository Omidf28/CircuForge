from pathlib import Path
import subprocess
import sys

import pytest

from circuforge.cli import main
from circuforge.simulation.ngspice import SimulationError, _execute, executable_path


def test_missing_simulator(monkeypatch):
    monkeypatch.setenv("CIRCUFORGE_NGSPICE", "certainly-missing-ngspice-executable")
    with pytest.raises(SimulationError) as caught:
        executable_path()
    assert caught.value.status == "unavailable"
    assert main(["preflight"]) == 2


def test_timeout_kills_and_waits(tmp_path):
    with pytest.raises(SimulationError) as caught:
        _execute(sys.executable, ["-c", "import time; time.sleep(5)"], str(tmp_path), .05)
    assert caught.value.status == "timeout"


def test_nonzero_exit_and_logs(tmp_path):
    with pytest.raises(SimulationError) as caught:
        _execute(sys.executable, ["-c", "import sys; print('failed'); sys.exit(7)"], str(tmp_path), 5)
    assert caught.value.status == "nonzero_exit"
    assert caught.value.returncode == 7
    assert "failed" in caught.value.stdout


def test_output_guard(tmp_path, monkeypatch):
    monkeypatch.setattr("circuforge.simulation.ngspice.MAX_OUTPUT_BYTES", 1024)
    with pytest.raises(SimulationError) as caught:
        _execute(sys.executable, ["-c", "print('x'*10000)"], str(tmp_path), 5)
    assert caught.value.status == "output_limit"
    assert len(caught.value.stdout) <= 1024


def test_launch_failure(tmp_path):
    with pytest.raises(SimulationError) as caught:
        _execute(str(tmp_path / "missing.exe"), [], str(tmp_path), 1)
    assert caught.value.status == "launch_error"
