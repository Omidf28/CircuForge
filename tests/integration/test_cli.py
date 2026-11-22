import json

import pytest

from circuforge.cli import main
from circuforge.simulation.ngspice import SimulationError, executable_path


@pytest.mark.integration
def test_cli_exports_real_response_and_preserves_existing_directory(tmp_path):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    spec = tmp_path / "spec.json"
    spec.write_text('{"filter_type":"rc_lowpass"}')
    output = tmp_path / "run"
    args = ["simulate", "--spec", str(spec), "--output", str(output)]
    assert main(args) == 0
    report_text = (output / "report.json").read_text()
    report = json.loads(report_text)
    assert report["simulator_calls"] == 1 and report["analytic_check_passed"]
    assert len((output / "response.csv").read_text().splitlines()) == 602
    assert (output / "stdout.log").stat().st_size > 0
    assert main(args) == 2
    assert (output / "report.json").read_text() == report_text


@pytest.mark.integration
def test_cli_records_metric_failure_after_genuine_simulator_success(tmp_path):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    spec = tmp_path / "spec.json"
    spec.write_text('{}')
    output = tmp_path / "unbracketed"
    # fc is below the 1 Hz sweep start, although both components are allowed.
    code = main(["simulate", "--spec", str(spec), "--output", str(output),
                 "--resistance-ohm", "1000000", "--capacitance-f", "0.001"])
    assert code == 2
    failure = json.loads((output / "failure.json").read_text())
    assert failure["status"] == "metric_error"
    assert failure["returncode"] == 0
    assert "bracket" in failure["error"]
    assert (output / "stdout.log").stat().st_size > 0
    assert not (output / "report.json").exists()
