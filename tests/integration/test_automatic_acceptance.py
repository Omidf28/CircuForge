"""Actual small-budget SPICE evidence; synthetic XML is only an audit fixture."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.acceptance import AcceptanceError, audit_phase2
from circuforge.optimization.baselines import compare
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


@pytest.fixture(scope="module")
def real_evidence(tmp_path_factory):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    root = tmp_path_factory.mktemp("automatic-gate-real")
    adapter = Ngspice()
    cases = [{"id": f"case-{i}", "spec": {"cutoff_hz": target, "max_evaluations": 2,
              "resistance_ohm": {"minimum": 100., "maximum": 10000.},
              "capacitance_f": {"minimum": 1e-8, "maximum": 1e-6}}}
             for i, target in enumerate([500., 1000., 1500., 2000., 3000.])]
    case_file = root / "cases.json"
    case_file.write_text(json.dumps(cases))
    comparison = root / "comparison"
    comparison.mkdir()
    rows = []
    for case in cases:
        spec = DesignSpec.model_validate(case["spec"])
        for report in compare(spec, adapter, seed=42, output=comparison / case["id"]):
            rows.append({"case": case["id"], "method": report.options.method, "target_hz": spec.cutoff_hz,
                         "budget": 2, "simulator_calls": report.simulator_calls, "matched_actual_calls": True,
                         "converged": report.converged, "target_relative_error": report.best.relative_error,
                         "objective": report.best.objective, "failures": 0, "stop_reason": report.stop_reason})
    (comparison / "summary.json").write_text(json.dumps({"cases_sha256": hashlib.sha256(case_file.read_bytes()).hexdigest(),
        "completed_cases": 5, "planned_cases": 5, "configured_total_call_cap": 30, "actual_calls": 30,
        "seed": 42, "results": rows}))
    junit = root / "xml-fixture.xml"
    junit.write_text('<testsuite tests="1"><testcase name="synthetic-xml-fixture"/></testsuite>')
    return root


@pytest.mark.integration
def test_real_evidence_passes_without_relabeling_target_misses(real_evidence):
    result = audit_phase2(real_evidence / "comparison", real_evidence / "cases.json", real_evidence / "xml-fixture.xml")
    assert result["status"] == "passed" and not result["manual_review_required"]
    assert result["raw_calls_checked"] == 30
    assert result["design_misses"] > 0


@pytest.mark.integration
@pytest.mark.parametrize("damage", ["missing_csv", "changed_csv", "changed_metric", "false_convergence", "wrong_budget", "wrong_fingerprint"])
def test_corrupted_evidence_blocks_gate(real_evidence, tmp_path, damage):
    root = tmp_path / "copy"
    shutil.copytree(real_evidence, root)
    comparison = root / "comparison"
    artifact = comparison / "case-0/random/evaluations/call-0001"
    if damage == "missing_csv":
        (artifact / "response.csv").unlink()
    elif damage == "changed_csv":
        csv = artifact / "response.csv"
        rows = csv.read_text().splitlines()
        fields = rows[1].split(",")
        fields[1] = "0.1"
        rows[1] = ",".join(fields)
        csv.write_text("\n".join(rows) + "\n")
    elif damage in {"changed_metric", "false_convergence"}:
        path = comparison / "case-0/random/report.json"
        report = json.loads(path.read_text())
        if damage == "changed_metric":
            report["history"][0]["objective"] = 0.
        else:
            report["converged"] = not report["converged"]
        path.write_text(json.dumps(report))
    else:
        path = comparison / "summary.json"
        summary = json.loads(path.read_text())
        if damage == "wrong_budget":
            summary["actual_calls"] += 1
        else:
            summary["cases_sha256"] = "wrong"
        path.write_text(json.dumps(summary))
    with pytest.raises(AcceptanceError):
        audit_phase2(comparison, root / "cases.json", root / "xml-fixture.xml")
