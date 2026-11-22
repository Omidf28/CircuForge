"""Reject unmeasurable sweeps before allocating files or launching ngspice."""
import json

import pytest
from pydantic import ValidationError

from circuforge.cli import main
from circuforge.domain.specs import Sweep


@pytest.mark.parametrize("start,stop", [(100., 100.000001), (1e-9, 1.000001e-9),
                                        (1e12, 1.000001e12)])
def test_single_sample_sweep_is_rejected_at_validation(start, stop):
    with pytest.raises(ValidationError, match="at least two frequency samples"):
        Sweep(start_hz=start, stop_hz=stop, points_per_decade=100)


@pytest.mark.parametrize("density", [10, 100, 1000])
def test_exact_one_interval_remains_valid(density):
    sweep = Sweep(start_hz=100., stop_hz=100 * 10 ** (1 / density), points_per_decade=density)
    assert sweep.expected_points == 2


@pytest.mark.parametrize("search", [False, True])
def test_cli_rejects_single_sample_before_preflight_or_output(tmp_path, monkeypatch, capsys, search):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"cutoff_hz": 100.0000005,
                               "sweep": {"start_hz": 100., "stop_hz": 100.000001,
                                         "points_per_decade": 100}}))
    output = tmp_path / "output"

    def forbidden(*args):
        raise AssertionError("invalid sweep must not instantiate the simulator")

    monkeypatch.setattr("circuforge.cli.Ngspice", forbidden)
    args = ["simulate", "--spec", str(spec), "--output", str(output)]
    if search:
        args.append("--search")
    assert main(args) == 2
    assert not output.exists()
    error = json.loads(capsys.readouterr().err)
    assert "at least two frequency samples" in error["error"]
