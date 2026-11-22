import json
from pathlib import Path

import pytest

from circuforge.evaluation.physics_comparison import (Experiment, aggregate, derived_case,
                                                     load_experiment)
from circuforge.evaluation import physics_comparison as comparison

ROOT = Path(__file__).resolve().parents[2]


def config():
    return json.loads((ROOT / "examples/physics-onecall-v1.json").read_text())


def test_frozen_onecall_policy_keeps_original_domains_and_tolerances():
    policy, source = load_experiment(ROOT / "examples/physics-onecall-v1.json")
    assert sum(case.expected_feasible for case in source.cases) * 3 * 4 * 2 == 384 <= policy.max_total_spice_calls
    for original in source.cases:
        case = derived_case(original, policy)
        expected = original.inputs.model_dump()
        expected.update(max_evaluations=1, timeout_s=5.0)
        assert case.inputs.model_dump() == expected
        assert case.expected_feasible == original.expected_feasible
    assert all(case.inputs.max_evaluations == 12 for case in source.cases)


@pytest.mark.parametrize("changes", [{"calls_per_method": 2}, {"calls_per_method": True},
                                    {"max_total_spice_calls": 501}, {"repetitions": 3},
                                    {"methods": ["random", "grid", "analytic_rc"]},
                                    {"source_benchmark": "../private.json"}])
def test_changed_caps_methods_or_source_paths_are_rejected(changes):
    with pytest.raises(ValueError):
        Experiment.model_validate({**config(), **changes})


def test_changed_source_manifest_blocks_before_any_simulator(tmp_path):
    (tmp_path / "physics.json").write_text(json.dumps(config()))
    (tmp_path / "benchmark-v2.json").write_text("{}")
    with pytest.raises(ValueError, match="source benchmark changed"):
        load_experiment(tmp_path / "physics.json")


def test_aggregates_keep_rejections_and_fixed_controls_out_of_free_domain_success():
    def row(feasible, passed, fixed):
        return dict(method="analytic_rc", expected_feasible=feasible, target_passed=passed,
                    simulator_calls=int(feasible), inputs={
                        name: dict(minimum=1.0, maximum=1.0 if fixed else 2.0)
                        for name in ("resistance_ohm", "capacitance_f")})
    result = aggregate([row(True, True, True), row(True, True, False), row(True, False, False), row(False, False, False)])
    method = result["analytic_rc"]
    assert method["design_passes"] == 2 and method["design_misses"] == 1
    assert method["free_domain_passes"] == method["fixed_control_passes"] == method["infeasible_rejections"] == 1
    assert method["free_domain_trials"] == 2 and method["simulator_calls"] == 3


@pytest.mark.parametrize("corruption", [None, "rows", "candidate"])
def test_replay_accepts_timing_differences_but_not_changed_candidates(tmp_path, monkeypatch, corruption):
    # Synthetic trace-equality test only; no raw-physics acceptance is simulated.
    first, replay = tmp_path / "first", tmp_path / "replay"
    for index, path in enumerate((first, replay)):
        path.mkdir()
        (path / "summary.json").write_text(json.dumps({"rows": [{"candidate": "fixture"}]}))
        (path / "report.json").write_text(json.dumps({"history": [{"candidate": "fixture", "elapsed_s": index}], "best": None}))
    monkeypatch.setattr(comparison, "audit_comparison", lambda *args: {"audited_calls": 1})
    if corruption == "rows":
        (replay / "summary.json").write_text(json.dumps({"rows": [{"candidate": "changed"}]}))
    elif corruption == "candidate":
        (replay / "report.json").write_text(json.dumps({"history": [{"candidate": "changed", "elapsed_s": 1}], "best": None}))
    if corruption:
        with pytest.raises(ValueError, match="replay|trace"):
            comparison.audit_replay(tmp_path / "not-loaded.json", first, replay)
    else:
        assert comparison.audit_replay(tmp_path / "not-loaded.json", first, replay)["audited_calls_including_replay"] == 2
