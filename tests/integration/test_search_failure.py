"""One genuine AC run followed by an intentionally unavailable executable."""
from dataclasses import replace
import json

import pytest

from circuforge.cli import main
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


@pytest.mark.integration
def test_real_partial_search_survives_subsequent_launch_failure(tmp_path, monkeypatch):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    adapter = Ngspice()

    class BecomesUnavailable:
        @property
        def info(self):
            return adapter.info

        def simulate(self, spec, candidate):
            result = adapter.simulate(spec, candidate)
            # Do not modify any installed executable. Only change this test
            # adapter's path so its next real Popen fails at process launch.
            adapter.info = replace(adapter.info, executable=str(tmp_path / "absent.exe"))
            return result

    monkeypatch.setattr("circuforge.cli.Ngspice", lambda _: BecomesUnavailable())
    spec = tmp_path / "spec.json"
    spec.write_text('{"cutoff_hz":2300.0,"max_evaluations":3}')
    output = tmp_path / "partial"
    assert main(["simulate", "--search", "--spec", str(spec), "--output", str(output)]) == 2
    record = json.loads((output / "failure.json").read_text())
    assert record["status"] == "launch_error"
    assert record["simulator_calls"] == 2
    assert len(record["search_history"]) == 2
    first, failed = record["search_history"]
    assert first["status"] == "success" and first["returncode"] == 0
    assert first["measured_cutoff_hz"] == pytest.approx(1000., rel=.001)
    assert failed["status"] == "launch_error"
    assert "measured_cutoff_hz" not in failed
    assert "ngspice" in record["ngspice_version"].lower()
    assert record["command"][0].endswith("absent.exe")
