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
