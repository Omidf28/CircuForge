"""Actual ngspice exports and CLI checks for the offline baseline report."""

from hashlib import sha256
import json
from pathlib import Path
from shutil import copytree
from types import SimpleNamespace

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


@pytest.fixture(scope="module")
def unmeasurable_comparison(simulator, tmp_path_factory):
    spec = DesignSpec(cutoff_hz=1500.0, max_evaluations=1,
                      resistance_ohm={"minimum": 1000.0, "maximum": 20000.0},
                      capacitance_f={"minimum": 1e-7, "maximum": 1e-7},
                      sweep={"start_hz": 1000.0, "stop_hz": 10000.0, "points_per_decade": 50})
    root = tmp_path_factory.mktemp("unmeasurable comparison") / "run"
    runs = compare(spec, simulator, seed=42, output=root)
    assert runs[1].best is None and runs[1].history[0].failure_type == "cutoff_unmeasurable"
    return root


@pytest.mark.integration
def test_comparison_report_explains_unmeasured_candidates_and_escapes_recorded_text(
        unmeasurable_comparison, tmp_path, capsys):
    root = tmp_path / "recorded failure"
    copytree(unmeasurable_comparison, root)

    # Deliberate display fixture. Binding the two records does not make their
    # free-form diagnostic text trustworthy HTML.
    note = '<img src="https://example.invalid" onerror="alert(1)">'
    method_report = root / "grid/report.json"
    per_call_report = root / "grid/evaluations/call-0001/evaluation.json"
    method = json.loads(method_report.read_bytes())
    per_call = json.loads(per_call_report.read_bytes())
    method["history"][0]["reason"] += " " + note
    per_call["reason"] = method["history"][0]["reason"]
    method_report.write_text(json.dumps(method), encoding="utf-8")
    per_call_report.write_text(json.dumps(per_call), encoding="utf-8")

    output = tmp_path / "diagnostics.html"
    code, _ = _render(root, output, capsys)
    assert code == 0
    page = output.read_text(encoding="utf-8")
    assert "No verified candidate" in page and "Unverified" in page
    assert "&lt;img" in page and note not in page
    assert page.count("<meter ") == sum(
        json.loads((root / name / "report.json").read_bytes())["best"] is not None
        for name in ("random", "grid", "scipy")
    )


@pytest.mark.integration
@pytest.mark.parametrize("damage,message", [
    ("reason", "failed-call record differs"),
    ("returncode", "failed-call return code"),
    ("netlist", "failed-call netlist"),
    ("missing_log", "missing/unsafe evidence file"),
])
def test_comparison_report_rejects_detached_failure_evidence(
        unmeasurable_comparison, tmp_path, capsys, damage, message):
    root = tmp_path / "copied failure"
    copytree(unmeasurable_comparison, root)
    call = root / "grid/evaluations/call-0001"
    if damage == "reason":
        report = root / "grid/report.json"
        data = json.loads(report.read_bytes())
        data["history"][0]["reason"] = "replacement not present in the per-call evidence"
        report.write_text(json.dumps(data), encoding="utf-8")
    elif damage == "returncode":
        report = call / "evaluation.json"
        data = json.loads(report.read_bytes())
        data["returncode"] = 23
        report.write_text(json.dumps(data), encoding="utf-8")
    elif damage == "netlist":
        (call / "circuit.cir").write_text("different saved netlist", encoding="ascii")
    else:
        (call / "stdout.log").unlink()
    output = tmp_path / "must not exist.html"
    code, captured = _render(root, output, capsys)
    assert code == 2 and message in captured.err
    assert not output.exists()


def test_comparison_report_retains_launch_failure_without_response_csv(tmp_path, capsys):
    class FailedLaunch:
        info = SimpleNamespace(version="ngspice controlled failure fixture", executable="fixture.exe")

        def simulate(self, spec, candidate):
            raise SimulationError("launch_error", "controlled launch failure")

    comparison = tmp_path / "failed launch"
    reports = compare(DesignSpec(max_evaluations=1), FailedLaunch(), seed=42, output=comparison)
    assert all(run.simulator_calls == run.failures == 1 for run in reports)
    assert not list(comparison.rglob("response.csv"))

    output = tmp_path / "launch failures.html"
    code, _ = _render(comparison, output, capsys)
    assert code == 0
    page = output.read_text(encoding="utf-8")
    assert page.count("controlled launch failure") == 3
    assert "<meter " not in page


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
