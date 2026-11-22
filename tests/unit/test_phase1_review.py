"""Invalid review inputs must fail before any simulator call or output writes."""
import importlib.util
import json
from pathlib import Path

import pytest

module_spec = importlib.util.spec_from_file_location(
    "phase1_review", Path(__file__).resolve().parents[2] / "scripts/verify_phase1.py"
)
review = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(review)

VALID = {"id": "reference", "topology": "rc_lowpass", "resistance_ohm": 1000.,
         "capacitance_f": 1e-7, "expected_cutoff_hz": 1591.5494309189537}


@pytest.mark.parametrize("change", ["duplicate", "wrong_reference", "unsafe_id", "unsupported", "over_budget"])
def test_invalid_fixture_file_never_runs_spice(tmp_path, monkeypatch, change):
    cases = [dict(VALID)]
    if change == "duplicate":
        cases.append(dict(VALID))
    elif change == "wrong_reference":
        cases[0]["expected_cutoff_hz"] = 100.
    elif change == "unsafe_id":
        cases[0]["id"] = "../outside"
    elif change == "unsupported":
        cases[0]["topology"] = "arbitrary-netlist"
    else:
        cases = [{**VALID, "id": f"case-{i}"} for i in range(17)]
    fixture = tmp_path / "fixtures.json"
    fixture.write_text(json.dumps(cases))
    output = tmp_path / "output"

    def forbidden(*args):
        raise AssertionError("invalid fixture must not invoke the simulation CLI")

    monkeypatch.setattr(review, "run_cli", forbidden)
    assert review.main(["--fixtures", str(fixture), "--output", str(output)]) == 2
    assert not output.exists()


def test_existing_output_is_preserved_before_any_simulation(tmp_path, monkeypatch):
    fixture = tmp_path / "fixtures.json"
    fixture.write_text(json.dumps([VALID]))
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("existing evidence")

    def forbidden(*args):
        raise AssertionError("existing output must not be overwritten")

    monkeypatch.setattr(review, "run_cli", forbidden)
    assert review.main(["--fixtures", str(fixture), "--output", str(output)]) == 2
    assert marker.read_text() == "existing evidence"
