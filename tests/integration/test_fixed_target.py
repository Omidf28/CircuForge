import json

import pytest

from circuforge.cli import main
from circuforge.domain.specs import Bounds, DesignSpec
from circuforge.simulation.ngspice import SimulationError, executable_path


@pytest.mark.integration
@pytest.mark.parametrize("topology", ["rc_lowpass", "rc_highpass"])
@pytest.mark.parametrize("search", [False, True])
def test_rounded_target_with_fixed_elements_runs_real_cli(tmp_path, topology, search):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    spec = DesignSpec(filter_type=topology, cutoff_hz=1591.5494,
                      resistance_ohm=Bounds(minimum=1000., maximum=1000.),
                      capacitance_f=Bounds(minimum=1e-7, maximum=1e-7))
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(spec.model_dump_json(), encoding="utf-8")
    output = tmp_path / "result"
    args = ["simulate", "--spec", str(spec_path), "--output", str(output)]
    if search:
        args.append("--search")
    assert main(args) == 0
    report = json.loads((output / "report.json").read_text())
    assert report["target_passed"] and report["analytic_check_passed"]
    assert report["target_relative_error"] <= .001
    assert report["simulator_calls"] == 1
    assert report["candidate"]["resistance_ohm"] == 1000.
    assert report["candidate"]["capacitance_f"] == 1e-7
