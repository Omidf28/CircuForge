import json

import pytest

from circuforge.cli import main


@pytest.mark.parametrize("command", ["optimize", "compare"])
def test_invalid_optimization_spec_never_starts_simulator(tmp_path, monkeypatch, command):
    spec = tmp_path / "invalid.json"
    spec.write_text(json.dumps({"filter_type": "arbitrary-circuit"}))
    output = tmp_path / "output"

    def forbidden(*args):
        raise AssertionError("invalid spec must not instantiate simulator")

    monkeypatch.setattr("circuforge.cli.Ngspice", forbidden)
    assert main([command, "--spec", str(spec), "--output", str(output)]) == 2
    assert not output.exists()
