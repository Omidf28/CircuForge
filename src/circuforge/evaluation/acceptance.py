"""Fail-closed numerical/record acceptance; never implies human or hardware review."""
import csv
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from pydantic import TypeAdapter

from circuforge.domain.cases import Case
from circuforge.domain.specs import DesignSpec
from circuforge.evaluation.records import environment
from circuforge.optimization.base import Evaluation
from circuforge.optimization.baselines import BaselineResult
from circuforge.simulation.metrics import Response, cutoff_hz
from circuforge.simulation.ngspice import parse_ac
from circuforge.synthesis.rc import netlist

POLICY = "phase2-engineering-v1"
METHODS = ("random", "grid", "scipy")


class AcceptanceError(ValueError):
    """Insufficient or contradictory evidence blocks automatic acceptance."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceError(message)


def evidence_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), f"missing/unsafe evidence file: {relative}")
    return path


def read_json(root: Path, relative: str):
    return json.loads(evidence_file(root, relative).read_text(encoding="utf-8"))


def validate_junit(path: Path) -> int:
    tree = ET.parse(path)
    cases = list(tree.getroot().iter("testcase"))
    require(bool(cases), "test evidence contains no executed testcases")
    require(not any(list(tree.getroot().iter(tag)) for tag in ("failure", "error", "skipped")),
            "failed, errored or skipped tests block acceptance")
    suites = list(tree.getroot().iter("testsuite"))
    require(bool(suites), "test evidence contains no test suite")
    for suite in suites:
        require(all(int(suite.get(tag, "0")) == 0 for tag in ("failures", "errors", "skipped")),
                "test suite reports failure/error/skip")
    return len(cases)


def _close(a, b) -> bool:
    return a is not None and b is not None and math.isfinite(a) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)


def audit_evaluation(root: Path, folder: str, spec: DesignSpec, evaluation: Evaluation, ngspice_version: str) -> None:
    """Independently verify one recorded measured evaluation against raw physics."""
    spec.validate_candidate(evaluation.candidate)
    metadata = read_json(root, folder + "/evaluation.json")
    require(Evaluation.model_validate({k: metadata[k] for k in Evaluation.model_fields}) == evaluation,
            f"per-call record differs from history: {folder}")
    require(metadata["spec"] == spec.model_dump() and metadata["returncode"] == 0 and
            metadata["ngspice_version"] == ngspice_version and
            metadata["command"][1:] == ["-n", "-b", "circuit.cir"], f"execution metadata mismatch: {folder}")
    require("ngspice" in ngspice_version.lower(), "missing ngspice provenance")
    require(evidence_file(root, folder + "/circuit.cir").read_text(encoding="ascii") ==
            netlist(spec, evaluation.candidate), f"untrusted/different netlist: {folder}")
    evidence_file(root, folder + "/stderr.log")
    raw = parse_ac(evidence_file(root, folder + "/stdout.log").read_text(encoding="utf-8"),
                   spec.source_amplitude_v, spec.sweep.expected_points)
    with evidence_file(root, folder + "/response.csv").open(encoding="utf-8", newline="") as stream:
        data = list(csv.DictReader(stream))
    csv_response = Response([float(r["frequency_hz"]) for r in data],
                            [complex(float(r["transfer_real"]), float(r["transfer_imag"])) for r in data])
    require(np.array_equal(csv_response.frequency_hz, raw.frequency_hz) and
            np.array_equal(csv_response.transfer, raw.transfer), f"CSV/raw output mismatch: {folder}")
    require(np.allclose([float(r["gain_db"]) for r in data], raw.gain_db, rtol=0., atol=1e-10) and
            np.allclose([float(r["phase_deg"]) for r in data], raw.phase_deg, rtol=0., atol=1e-10),
            f"CSV gain/phase mismatch: {folder}")
    f = raw.frequency_hz
    sweep = spec.sweep
    grids = (sweep.start_hz * 10 ** (np.arange(sweep.expected_points) / sweep.points_per_decade),
             np.geomspace(sweep.start_hz, sweep.stop_hz, sweep.expected_points))
    require(any(np.allclose(f, g, rtol=1e-6, atol=0.) for g in grids), f"wrong sweep grid: {folder}")
    r, c = evaluation.candidate.resistance_ohm, evaluation.candidate.capacitance_f
    z = 2j * math.pi * f * r * c
    reference = (1 if spec.filter_type == "rc_lowpass" else z) / (1 + z)
    require(np.allclose(raw.transfer, reference, rtol=2e-5, atol=1e-8), f"RC complex response mismatch: {folder}")
    measured = cutoff_hz(raw, spec.filter_type)
    error = abs(measured / spec.cutoff_hz - 1)
    reference_error = abs(measured * (2 * math.pi * r * c) - 1)
    target_passed = error <= spec.relative_error_tolerance
    require(evaluation.status == "evaluated" and evaluation.constraints_satisfied and
            evaluation.simulator_exit_ok and evaluation.verified and reference_error <= .001 and
            evaluation.target_passed == target_passed, f"false acceptance/status: {folder}")
    require(_close(evaluation.measured_cutoff_hz, measured) and _close(evaluation.relative_error, error) and
            _close(evaluation.analytic_relative_error, reference_error) and
            _close(evaluation.objective, abs(math.log(measured / spec.cutoff_hz))),
            f"recorded metrics differ from raw response: {folder}")


def audit_run(root: Path, case: Case, method: str, seed: int, expected_environment=None) -> BaselineResult:
    """Reusable raw-evidence audit for one complete bounded optimizer run."""
    expected_environment = expected_environment or environment()
    fixed = (case.spec.resistance_ohm.minimum == case.spec.resistance_ohm.maximum and
             case.spec.capacitance_f.minimum == case.spec.capacitance_f.maximum)
    expected_calls = 1 if fixed else case.spec.max_evaluations
    prefix = f"{case.id}/{method}"
    report = BaselineResult.model_validate(read_json(root, prefix + "/report.json"))
    require(report.spec == case.spec and report.options.method == method and
            report.options.seed == seed, f"input/options mismatch: {prefix}")
    require(report.environment == expected_environment, f"stale/different code or environment: {prefix}")
    require(report.simulator_calls == expected_calls, f"unspent/exceeded call budget: {prefix}")
    require(report.proposals <= 20 * case.spec.max_evaluations + 20 and
            0 <= report.cache_hits <= report.proposals and
            report.proposals >= report.simulator_calls + report.cache_hits,
            f"invalid proposal/cache counts: {prefix}")
    require(report.failures == report.invalid_candidates == 0, f"invalid/failed reference evaluation: {prefix}")
    require(len(report.history) == expected_calls, f"incomplete call history: {prefix}")
    seen = set()
    for index, evaluation in enumerate(report.history, 1):
        require(evaluation.simulator_call == index and evaluation.artifact == f"call-{index:04d}",
                f"discontinuous/unsafe call identity: {prefix}")
        key = (evaluation.candidate.resistance_ohm, evaluation.candidate.capacitance_f)
        require(key not in seen, f"duplicate candidate charged as new call: {prefix}")
        seen.add(key)
        folder = prefix + "/evaluations/" + evaluation.artifact
        audit_evaluation(root, folder, case.spec, evaluation, report.ngspice_version)
    expected_best = min(report.history, key=lambda e: (not e.target_passed, e.objective))
    require(report.best == expected_best and report.converged == expected_best.target_passed,
            f"incorrect best/pass result: {prefix}")
    return report


def audit_phase2(root: Path, cases_path: Path, junit_path: Path) -> dict:
    """Audit raw responses and accounting against versioned case inputs.

    This policy accepts a correctly executed baseline comparison. Design success
    is a separate reported measurement; tolerance misses are never relabeled.
    """
    tests = validate_junit(junit_path)
    content = cases_path.read_bytes()
    cases = TypeAdapter(list[Case]).validate_json(content)
    require(5 <= len(cases) <= 8 and len({c.id for c in cases}) == len(cases), "need 5–8 unique cases")
    require(len({c.spec.model_dump_json() for c in cases}) >= 5, "need five distinct numerical cases")
    configured_cap = sum(c.spec.max_evaluations * 3 for c in cases)
    require(configured_cap <= 1000, "comparison exceeds policy call cap")
    summary = read_json(root, "summary.json")
    require(summary["cases_sha256"] == hashlib.sha256(content).hexdigest(), "case input fingerprint mismatch")
    require(summary["completed_cases"] == summary["planned_cases"] == len(cases), "incomplete comparison")
    require(summary["configured_total_call_cap"] == configured_cap, "configured cap mismatch")
    rows = summary["results"]
    require(len(rows) == len(cases) * 3, "missing comparison rows")
    row_by_id = {(r["case"], r["method"]): r for r in rows}
    require(len(row_by_id) == len(rows), "duplicate comparison rows")
    checked_calls = design_passes = design_misses = 0
    outcomes = []
    expected_environment = environment()
    for case in cases:
        reports = []
        fixed = (case.spec.resistance_ohm.minimum == case.spec.resistance_ohm.maximum and
                 case.spec.capacitance_f.minimum == case.spec.capacitance_f.maximum)
        expected_calls = 1 if fixed else case.spec.max_evaluations
        for method in METHODS:
            prefix = f"{case.id}/{method}"
            report = audit_run(root, case, method, summary["seed"], expected_environment)
            expected_best = report.best
            row = row_by_id[(case.id, method)]
            require(row["budget"] == case.spec.max_evaluations and row["simulator_calls"] == expected_calls and
                    row["matched_actual_calls"] and row["converged"] == report.converged and row["failures"] == 0 and
                    row["target_hz"] == case.spec.cutoff_hz and row["stop_reason"] == report.stop_reason and
                    _close(row["target_relative_error"], expected_best.relative_error) and
                    _close(row["objective"], expected_best.objective), f"summary disagrees with evidence: {prefix}")
            design_passes += int(report.converged)
            design_misses += int(not report.converged)
            checked_calls += report.simulator_calls
            reports.append(report)
            outcomes.append({"case": case.id, "method": method, "target_passed": report.converged,
                             "relative_error": expected_best.relative_error, "calls": report.simulator_calls})
        require(len({r.simulator_calls for r in reports}) == 1, f"unfair actual budgets: {case.id}")
    require(checked_calls == summary["actual_calls"] <= configured_cap, "total actual call mismatch")
    return {"status": "passed", "policy": POLICY, "acceptance_mode": "automated",
            "manual_review_required": False, "tests_passed": tests, "cases_checked": len(cases),
            "raw_calls_checked": checked_calls, "design_passes": design_passes, "design_misses": design_misses,
            "environment": expected_environment, "cases_sha256": hashlib.sha256(content).hexdigest(),
            "claim": "baseline execution/physics/accounting accepted; target outcomes remain as measured",
            "outcomes": outcomes}
