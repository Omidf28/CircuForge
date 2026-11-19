"""Actual small-budget RC tolerance sweeps, independent holdout and raw audits."""
import json
from pathlib import Path
import shutil

import pytest

from circuforge.evaluation.acceptance import AcceptanceError
from circuforge.evaluation.robust_acceptance import audit_experiment, audit_replay
from circuforge.evaluation.robust_plot import plot_comparison
from circuforge.optimization.robustness import run_experiment
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


@pytest.fixture(scope="module")
def real_tolerance_evidence(tmp_path_factory):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    root = tmp_path_factory.mktemp("robustness-real")
    data = json.loads((Path(__file__).resolve().parents[2] / "examples/robustness-v1.json").read_text())
    data.update(training_calls=8, training_samples=3, holdout_samples=8)
    for case in data["cases"]:
        case["spec"]["max_evaluations"] = 8
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps(data))
    adapter = Ngspice()
    for name in ("first", "replay"):
        summary = run_experiment(manifest, root / name, adapter)
        plot_comparison(summary, root / name / "comparison.png")
    return root


@pytest.mark.integration
def test_real_tolerances_reproduce_statistics_with_equal_total_budgets(real_tolerance_evidence):
    root = real_tolerance_evidence
    result = audit_replay(root / "manifest.json", root / "first", root / "replay")
    assert result["status"] == "passed" and not result["manual_review_required"]
    assert result["audited_calls_including_replay"] == 256
    assert all(r["simulator_calls"] == 16 and r["holdout_statistics"]["samples"] == 8 for r in result["outcomes"])
    for case in ("lp-narrow", "hp-asymmetric"):
        a = json.loads((root / f"first/seed-7/{case}/nominal/report.json").read_text())
        b = json.loads((root / f"first/seed-7/{case}/robust/report.json").read_text())
        assert a["history"][0]["candidate"] == b["history"][0]["candidate"]
        assert len(a["training_groups"]) == 8 and len(b["training_groups"]) == 2
        assert b["holdout_calls"] == list(range(9, 17))


@pytest.mark.integration
@pytest.mark.parametrize("damage", ["quantile", "pass_rate", "leakage", "budget", "seed", "missing_raw", "summary", "selection"])
def test_bad_tolerance_evidence_blocks_acceptance(real_tolerance_evidence, tmp_path, damage):
    root = tmp_path / "copy"
    shutil.copytree(real_tolerance_evidence / "first", root)
    path = root / "seed-7/lp-narrow/robust/report.json"
    report = json.loads(path.read_text())
    if damage == "quantile":
        report["holdout_statistics"]["relative_error"]["q95"] = 0.
    elif damage == "pass_rate":
        report["holdout_statistics"]["pass_rate"] = .1234567
    elif damage == "leakage":
        report["holdout_calls"][0] = 1
    elif damage == "budget":
        report["simulator_calls"] += 1
    elif damage == "seed":
        report["seed"] = 99
    elif damage == "missing_raw":
        (root / "seed-7/lp-narrow/robust/evaluations/call-0016/response.csv").unlink()
    elif damage == "selection":
        report["selected_group"] = 1 - report["selected_group"]
    else:
        s = root / "summary.json"
        summary = json.loads(s.read_text())
        summary["trials"][0]["nominal_relative_error"] = 0.
        s.write_text(json.dumps(summary))
    path.write_text(json.dumps(report))
    with pytest.raises(AcceptanceError):
        audit_experiment(real_tolerance_evidence / "manifest.json", root)
