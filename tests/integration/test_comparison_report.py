"""Actual ngspice exports and CLI checks for the offline baseline report."""

from hashlib import sha256
import json
from pathlib import Path
from shutil import copytree

import pytest

from circuforge.cli import main
from circuforge.domain.specs import DesignSpec
from circuforge.optimization.baselines import BaselineResult, compare, comparison_summary
from circuforge.simulation.ngspice import Ngspice, SimulationError


@pytest.fixture(scope="module")
def simulator():
    try:
        return Ngspice()
    except SimulationError as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="module")
def fixed_comparison(simulator, tmp_path_factory):
    source = Path(__file__).resolve().parents[2]
    spec = DesignSpec.model_validate_json((source / "examples/fixed-target.json").read_bytes())
    output = tmp_path_factory.mktemp("fixed comparison") / "run"
    compare(spec, simulator, seed=42, output=output)
    return output


def _render(comparison, output, capsys):
    # A deliberately missing executable proves this CLI route is offline.
    code = main(["--ngspice", str(output.parent / "missing.exe"), "comparison-report",
                 "--comparison", str(comparison), "--output", str(output)])
    return code, capsys.readouterr()


@pytest.mark.integration
def test_comparison_report_displays_three_raw_audited_candidates(fixed_comparison, tmp_path, capsys):
    before = {path: sha256(path.read_bytes()).hexdigest()
              for path in fixed_comparison.rglob("*") if path.is_file()}
    output = tmp_path / "baseline report.html"
    code, captured = _render(fixed_comparison, output, capsys)
    assert code == 0 and json.loads(captured.out)["status"] == "report_written"
    page = output.read_text(encoding="utf-8")
    assert page.count("Verified · target met") == 6
    assert page.count("<meter ") == 3
    assert "Actual simulator calls match across methods." in page
    assert all(f"{name} candidates (1)" in page for name in ("Random", "Grid", "SciPy"))
    assert "<script" not in page
    assert before == {path: sha256(path.read_bytes()).hexdigest()
                      for path in fixed_comparison.rglob("*") if path.is_file()}

    code, captured = _render(fixed_comparison, output, capsys)
    assert code == 2 and "output already exists" in captured.err
    assert output.read_text(encoding="utf-8") == page


@pytest.mark.integration
@pytest.mark.parametrize("tamper,reason", [
    ("summary", "differs from the method reports"),
    ("raw", "CSV/raw output mismatch"),
    ("missing", "missing/unsafe evidence file"),
])
def test_comparison_report_rejects_incomplete_or_contradictory_evidence(
        fixed_comparison, tmp_path, capsys, tamper, reason):
    copied = tmp_path / "copied evidence"
    copytree(fixed_comparison, copied)
    if tamper == "summary":
        summary = copied / "comparison.json"
        payload = json.loads(summary.read_bytes())
        payload["matched_actual_calls"] = False
        summary.write_text(json.dumps(payload), encoding="utf-8")
    else:
        csv = copied / "grid/evaluations/call-0001/response.csv"
        if tamper == "missing":
            csv.unlink()
        else:
            lines = csv.read_text(encoding="utf-8").splitlines()
            values = lines[1].split(",")
            values[1] = "0"
            lines[1] = ",".join(values)
            csv.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output = tmp_path / "must not exist.html"
    code, captured = _render(copied, output, capsys)
    assert code == 2 and reason in captured.err
    assert not output.exists()


@pytest.mark.integration
def test_comparison_report_explains_unmeasured_candidates_and_escapes_recorded_text(
        simulator, tmp_path, capsys):
    spec = DesignSpec(cutoff_hz=1500.0, max_evaluations=1,
                      resistance_ohm={"minimum": 1000.0, "maximum": 20000.0},
                      capacitance_f={"minimum": 1e-7, "maximum": 1e-7},
                      sweep={"start_hz": 1000.0, "stop_hz": 10000.0, "points_per_decade": 50})
    root = tmp_path / "narrow-sweep"
    runs = compare(spec, simulator, seed=42, output=root)
    grid = runs[1]
    assert grid.best is None and grid.history[0].failure_type == "cutoff_unmeasurable"

    # Treat a reason read from the local export as untrusted display text.
    note = '<img src="https://example.invalid" onerror="alert(1)">'
    grid = grid.model_copy(update={"history": (grid.history[0].model_copy(update={
        "reason": f"{grid.history[0].reason} {note}"}),)})
    runs[1] = grid
    (root / "grid/report.json").write_text(grid.model_dump_json(), encoding="utf-8")
    (root / "comparison.json").write_text(json.dumps(comparison_summary(runs)), encoding="utf-8")

    output = tmp_path / "diagnostics.html"
    code, _ = _render(root, output, capsys)
    assert code == 0
    page = output.read_text(encoding="utf-8")
    assert "No verified candidate" in page and "Unverified" in page
    assert "&lt;img" in page and note not in page
    assert page.count("<meter ") == sum(run.best is not None for run in runs)


@pytest.mark.integration
def test_comparison_report_warns_when_actual_call_counts_differ(
        fixed_comparison, tmp_path, capsys):
    root = tmp_path / "unequal calls"
    copytree(fixed_comparison, root)
    runs = [BaselineResult.model_validate_json((root / method / "report.json").read_bytes())
            for method in ("random", "grid", "scipy")]
    # Model a method that stopped before submitting any simulator work.
    grid = runs[1].model_copy(update={"history": (), "simulator_calls": 0, "proposals": 0,
                                      "best": None, "converged": False, "stop_reason": "interrupted"})
    runs[1] = grid
    (root / "grid/report.json").write_text(grid.model_dump_json(), encoding="utf-8")
    (root / "comparison.json").write_text(json.dumps(comparison_summary(runs)), encoding="utf-8")

    output = tmp_path / "unequal.html"
    code, _ = _render(root, output, capsys)
    assert code == 0
    page = output.read_text(encoding="utf-8")
    assert "Actual simulator calls differ." in page and "No verified candidate" in page
    assert page.count("<meter ") == 2
