"""Manifest errors must be rejected before launching any simulator."""
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from circuforge.evaluation.benchmark import Benchmark, load_benchmark

MANIFEST = Path(__file__).resolve().parents[2] / "examples/benchmark-v2.json"


def test_versioned_cases_have_declared_outcomes_and_bounded_budget():
    manifest = load_benchmark(MANIFEST)
    assert len(manifest.cases) == 20 and manifest.seeds == (7, 42, 2026)
    assert sum(c.validated_spec() is not None for c in manifest.cases) == 16
    assert manifest.configured_call_cap == 2160 <= manifest.max_spice_calls
    assert {c.inputs.filter_type for c in manifest.cases} == {"rc_lowpass", "rc_highpass"}


@pytest.mark.parametrize("damage", ["label", "negative_label", "unsupported", "outside_sweep", "duplicate",
                                  "disguised_duplicate", "scale_duplicate", "swap_duplicate", "seed", "seed_type", "cap", "version", "too_few"])
def test_malformed_or_mislabeled_manifest_is_not_an_infeasible_result(damage):
    data = json.loads(MANIFEST.read_text())
    if damage == "label":
        data["cases"][0]["expected_feasible"] = False
    elif damage == "negative_label":
        data["cases"][-1]["expected_feasible"] = True
    elif damage == "unsupported":
        data["cases"][-1]["inputs"]["load"] = "finite"
    elif damage == "outside_sweep":
        data["cases"][-1]["inputs"]["sweep"]["start_hz"] = 2000.
    elif damage in {"duplicate", "disguised_duplicate"}:
        data["cases"][1] = copy.deepcopy(data["cases"][0])
        if damage == "disguised_duplicate":
            data["cases"][1]["id"] = "disguised"
            data["cases"][1]["inputs"]["max_evaluations"] = 1
    elif damage == "scale_duplicate":
        data["cases"][2] = copy.deepcopy(data["cases"][0])
        data["cases"][2]["id"] = "scaled"
        data["cases"][2]["inputs"]["cutoff_hz"] *= 10
        data["cases"][2]["inputs"]["resistance_ohm"]["minimum"] /= 10
        data["cases"][2]["inputs"]["resistance_ohm"]["maximum"] /= 10
    elif damage == "swap_duplicate":
        data["cases"][2] = copy.deepcopy(data["cases"][11])
        data["cases"][2]["id"] = "swapped-widths"
        data["cases"][2]["inputs"]["resistance_ohm"]["maximum"] = 10000.
        data["cases"][2]["inputs"]["capacitance_f"]["maximum"] = 1e-9
    elif damage == "seed":
        data["seeds"] = [7, 7]
    elif damage == "seed_type":
        data["seeds"][0] = True
    elif damage == "cap":
        data["max_spice_calls"] = 10
    elif damage == "version":
        data["version"] = "0.0"
    else:
        data["cases"] = data["cases"][:19]
    with pytest.raises(ValidationError):
        Benchmark.model_validate(data)


def test_superseded_v1_is_rejected_for_scale_equivalent_cases():
    with pytest.raises(ValidationError, match="scale-equivalent"):
        load_benchmark(MANIFEST.with_name("benchmark-v1.json"))
