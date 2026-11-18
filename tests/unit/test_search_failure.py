"""Controlled failures and analytic fixtures test accounting, not SPICE accuracy."""
import json
from types import SimpleNamespace

import numpy as np
import pytest

from circuforge.cli import main
from circuforge.domain.specs import DesignSpec
from circuforge.optimization.search import SearchFailure, search
from circuforge.simulation.metrics import analytic_response
from circuforge.simulation.ngspice import SimulationError


class ControlledSimulator:
    def __init__(self, *, fail_at=2, failure_status="timeout", invalid_metrics=False):
        self.calls = 0
        self.fail_at = fail_at
        self.failure_status = failure_status
        self.invalid_metrics = invalid_metrics

    def simulate(self, spec, candidate):
        self.calls += 1
        if self.calls == self.fail_at and not self.invalid_metrics:
            raise SimulationError(self.failure_status, "controlled test failure",
                                  stdout="controlled stdout", stderr="controlled stderr", returncode=7)
        frequencies = [1., 2.] if self.calls == self.fail_at else np.geomspace(1, 1e6, 601)
        return SimpleNamespace(response=analytic_response(candidate, frequencies),
                               stdout="analytic unit-test fixture only", stderr="", returncode=0, elapsed_s=.01)


@pytest.mark.parametrize("status", ["timeout", "nonzero_exit", "parse_error", "launch_error"])
@pytest.mark.parametrize("fail_at", [1, 2])
def test_failure_preserves_attempted_calls_history_and_budget(status, fail_at):
    simulator = ControlledSimulator(fail_at=fail_at, failure_status=status)
    spec = DesignSpec(cutoff_hz=2300., max_evaluations=3)
    with pytest.raises(SearchFailure) as caught:
        search(spec, simulator)
    error = caught.value
    assert error.status == status
    assert error.simulator_calls == simulator.calls == fail_at <= spec.max_evaluations
    assert len(error.history) == fail_at
    assert error.history[-1]["status"] == status
    assert "measured_cutoff_hz" not in error.history[-1]
    assert error.stdout == "controlled stdout"
    assert error.stderr == "controlled stderr"
    assert error.returncode == 7
    if fail_at == 2:
        assert error.history[0]["status"] == "success"
        assert error.history[0]["measured_cutoff_hz"] > 0
    assert error.context()["candidate"] == error.candidate.model_dump()


def test_search_metric_failure_retains_successful_simulator_return_code():
    simulator = ControlledSimulator(invalid_metrics=True)
    with pytest.raises(SearchFailure) as caught:
        search(DesignSpec(cutoff_hz=2300.), simulator)
    assert caught.value.status == "metric_error"
    assert caught.value.returncode == 0
    assert caught.value.simulator_calls == 2
    assert "bracket" in str(caught.value)


def test_cli_persists_partial_search_evidence(tmp_path, monkeypatch):
    simulator = ControlledSimulator()
    monkeypatch.setattr("circuforge.cli.Ngspice", lambda _: simulator)
    spec = tmp_path / "spec.json"
    spec.write_text('{"cutoff_hz":2300.0,"max_evaluations":3}')
    output = tmp_path / "failure"
    assert main(["simulate", "--search", "--spec", str(spec), "--output", str(output)]) == 2
    record = json.loads((output / "failure.json").read_text())
    assert record["status"] == "timeout"
    assert record["simulator_calls"] == 2
    assert len(record["search_history"]) == 2
    assert record["search_history"][0]["status"] == "success"
    assert record["search_history"][1]["status"] == "timeout"
    assert record["spec"]["max_evaluations"] == 3
    assert "R1 in out" in (output / "circuit.cir").read_text()
    assert (output / "stdout.log").read_text() == "controlled stdout"
    assert (output / "stderr.log").read_text() == "controlled stderr"
    assert not (output / "report.json").exists()


def test_budget_prevents_later_failure_attempt():
    simulator = ControlledSimulator(fail_at=2)
    result = search(DesignSpec(cutoff_hz=2300., max_evaluations=1), simulator)
    assert result.simulator_calls == simulator.calls == 1
    assert not result.converged
