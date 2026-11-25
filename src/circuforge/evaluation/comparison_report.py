"""Render a saved three-method comparison as a self-contained local report."""

from html import escape
import json
from pathlib import Path

from circuforge.evaluation.acceptance import METHODS, audit_evaluation, evidence_file, require
from circuforge.optimization.base import Evaluation
from circuforge.optimization.baselines import BaselineResult, comparison_summary
from circuforge.synthesis.rc import netlist

MAX_REPORT_BYTES = 16 * 1024**2
MAX_EVIDENCE_FILE_BYTES = 8 * 1024**2
MAX_AUDIT_BYTES = 192 * 1024**2
LABELS = {"random": "Random", "grid": "Grid", "scipy": "SciPy"}
CALL_FILES = ("evaluation.json", "circuit.cir", "stdout.log", "stderr.log")


def _read_report(root: Path, name: str) -> bytes:
    with evidence_file(root, name).open("rb") as stream:
        data = stream.read(MAX_REPORT_BYTES + 1)
    require(len(data) <= MAX_REPORT_BYTES, f"report exceeds size limit: {name}")
    return data


def _check_failed_call(root: Path, folder: str, run: BaselineResult, evaluation: Evaluation) -> None:
    """Bind the diagnostic to the saved call without certifying a measurement."""
    run.spec.validate_candidate(evaluation.candidate)
    metadata = json.loads(evidence_file(root, f"{folder}/evaluation.json").read_bytes())
    saved = Evaluation.model_validate({name: metadata[name] for name in Evaluation.model_fields})
    require(saved == evaluation, f"failed-call record differs from method history: {folder}")
    require(metadata["spec"] == run.spec.model_dump() and
            metadata["ngspice_version"] == run.ngspice_version and
            "ngspice" in run.ngspice_version.lower() and
            metadata["command"][1:] == ["-n", "-b", "circuit.cir"],
            f"failed-call provenance differs: {folder}")
    code = metadata["returncode"]
    require((code is None or type(code) is int) and (code == 0) == evaluation.simulator_exit_ok and
            (evaluation.status == "simulation_error" or code == 0),
            f"failed-call return code differs from recorded status: {folder}")
    require(evaluation.constraints_satisfied and bool(evaluation.reason and evaluation.failure_type),
            f"incomplete failed-call diagnostics: {folder}")
    circuit = evidence_file(root, f"{folder}/circuit.cir").read_text(encoding="ascii")
    require(circuit == netlist(run.spec, evaluation.candidate), f"failed-call netlist differs: {folder}")


def _audit_history(root: Path, method: str, run: BaselineResult, remaining: int) -> int:
    # Use fixed method names and sequential call IDs, never JSON-supplied paths.
    calls = failures = invalid = 0
    seen = set()
    spec = run.spec
    require(0 <= run.simulator_calls <= spec.max_evaluations and 0 <= run.cache_hits and
            len(run.history) + run.cache_hits <= run.proposals <= 20 * spec.max_evaluations + 20,
            f"invalid proposal or call counts: {method}")
    for evaluation in run.history:
        require(evaluation.verified == (evaluation.status == "evaluated") and
                (evaluation.verified or not evaluation.target_passed),
                f"inconsistent candidate status: {method}")
        if evaluation.status == "invalid_candidate":
            require(evaluation.simulator_call is None and evaluation.artifact is None,
                    f"rejected candidate has a simulator call: {method}")
            invalid += 1
            continue
        calls += 1
        call_id = f"call-{calls:04d}"
        require(calls <= run.simulator_calls and
                (evaluation.simulator_call, evaluation.artifact) == (calls, call_id),
                f"missing or out-of-order simulator call: {method}/{call_id}")
        candidate = evaluation.candidate
        key = (candidate.resistance_ohm, candidate.capacitance_f)
        require(key not in seen, f"duplicate candidate counted as a fresh call: {method}/{call_id}")
        seen.add(key)
        folder = f"{method}/evaluations/{call_id}"
        required_files = CALL_FILES if evaluation.status == "simulation_error" else (*CALL_FILES, "response.csv")
        for name in required_files:
            size = evidence_file(root, f"{folder}/{name}").stat().st_size
            remaining -= size
            require(size <= MAX_EVIDENCE_FILE_BYTES and remaining >= 0,
                    f"raw evidence exceeds audit size limit: {folder}/{name}")
        try:
            if evaluation.verified:
                audit_evaluation(root, folder, spec, evaluation, run.ngspice_version)
            else:
                _check_failed_call(root, folder, run, evaluation)
                failures += 1
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"malformed audit evidence: {folder}") from exc
    require((calls, failures, invalid) == (run.simulator_calls, run.failures, run.invalid_candidates),
            f"history does not match simulator counts: {method}")
    best = min((item for item in run.history if item.verified),
               key=lambda item: (not item.target_passed, item.objective), default=None)
    require(run.best == best and run.converged == bool(best and best.target_passed),
            f"inconsistent best candidate: {method}")
    return remaining


def _load_comparison(root: Path) -> list[BaselineResult]:
    runs = [BaselineResult.model_validate_json(_read_report(root, f"{method}/report.json"))
            for method in METHODS]
    first = runs[0]
    for method, run in zip(METHODS, runs, strict=True):
        require(run.options.method == method and run.options.seed == first.options.seed and
                run.spec == first.spec and run.environment == first.environment and
                run.ngspice_version == first.ngspice_version,
                f"comparison methods do not share inputs and provenance: {method}")
    require(json.loads(_read_report(root, "comparison.json")) == comparison_summary(runs),
            "comparison.json differs from the method reports")
    remaining = MAX_AUDIT_BYTES
    for method, run in zip(METHODS, runs, strict=True):
        remaining = _audit_history(root, method, run, remaining)
    return runs


def _candidate_status(item: Evaluation | None) -> str:
    if item is None:
        return "No verified candidate"
    if not item.verified:
        return "Unverified"
    return "Verified · target met" if item.target_passed else "Verified · target missed"


def _error_percent(item: Evaluation | None) -> float | None:
    return item.relative_error * 100 if item and item.verified else None


def _number(value: float | None) -> str:
    return "—" if value is None else f"{value:.6g}"


def _text(value: str) -> str:
    return escape(value if len(value) <= 500 else value[:499] + "…")


def _error_meter(error: float | None, maximum: float) -> str:
    if error is None:
        return "—"
    return f'<meter min="0" max="{maximum}" value="{error}">{_number(error)}%</meter> {_number(error)}%'


def _method_row(run: BaselineResult, scale: float) -> str:
    best = run.best
    return (
        f"<tr><th scope='row'>{LABELS[run.options.method]}</th>"
        f"<td>{run.simulator_calls} / {run.spec.max_evaluations}</td>"
        f"<td>{_candidate_status(best)}</td>"
        f"<td>{_number(best.measured_cutoff_hz if best else None)}</td>"
        f"<td>{_error_meter(_error_percent(best), scale)}</td>"
        f"<td>{run.failures}</td><td>{_text(run.stop_reason)}</td></tr>"
    )


def _candidate_row(item: Evaluation) -> str:
    candidate = item.candidate
    reason = "—" if item.verified else _text(item.reason or item.failure_type or item.status)
    error = _error_percent(item)
    return (
        f"<tr><td>{item.simulator_call or '—'}</td>"
        f"<td>{_number(candidate.resistance_ohm)}</td><td>{_number(candidate.capacitance_f)}</td>"
        f"<td>{_candidate_status(item)}</td>"
        f"<td>{_number(item.measured_cutoff_hz if item.verified else None)}</td>"
        f"<td>{_number(error)}</td><td>{reason}</td></tr>"
    )


def _table(headings: tuple[str, ...], rows: str, caption: str) -> str:
    headers = "".join(f'<th scope="col">{heading}</th>' for heading in headings)
    return (f'<div class="table"><table><caption>{caption}</caption><thead><tr>{headers}</tr></thead>'
            f"<tbody>{rows}</tbody></table></div>")


def _render(runs: list[BaselineResult]) -> str:
    spec = runs[0].spec
    tolerance = spec.relative_error_tolerance * 100
    scale = max(tolerance, *(_error_percent(run.best) or 0 for run in runs))
    matched = comparison_summary(runs)["matched_actual_calls"]
    scope = ("Actual simulator calls match across methods." if matched else
             "Actual simulator calls differ. These results are not an equal-call comparison.")
    summary = _table(("Method", "Calls / cap", "Best candidate", "Cutoff (Hz)", "Error vs target",
                      "Failed calls", "Stop reason"), "".join(_method_row(run, scale) for run in runs),
                     "Best audited result per method")
    histories = []
    for run in runs:
        label = LABELS[run.options.method]
        rows = "".join(_candidate_row(item) for item in run.history)
        table = _table(("Call", "R (Ω)", "C (F)", "Status", "Cutoff (Hz)", "Error (%)", "Failure reason"),
                       rows, f"{label} candidate history")
        histories.append(f"<details><summary>{label} candidates ({len(run.history)})</summary>{table}</details>")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>CircuForge baseline comparison</title>
<style>
  :root {{ color-scheme: light; background: #edf3f5; color: #152b3c; font: 16px/1.5 system-ui, sans-serif; }}
  body {{ max-width: 74rem; margin: auto; padding: clamp(1rem, 3vw, 3rem); }}
  h1 {{ font-size: clamp(1.8rem, 4vw, 2.8rem); line-height: 1.1; margin: 0 0 .8rem; }}
  h2 {{ margin: 2rem 0 .6rem; }}
  .context {{ color: #435b69; margin: .35rem 0; }}
  .notice {{ padding: .6rem .8rem; margin: 1rem 0; background: #ffffff; border-inline-start: .25rem solid {"#207561" if matched else "#a66a1a"}; }}
  .table {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; background: #ffffff; font-variant-numeric: tabular-nums; }}
  caption {{ text-align: left; padding: .5rem 0; font-weight: 650; }}
  th, td {{ text-align: left; padding: .65rem .7rem; border-bottom: 1px solid #dbe4e8; vertical-align: top; }}
  thead th {{ background: #dbe8ec; }}
  tbody tr:nth-child(even) {{ background: #f7fafb; }}
  td:last-child {{ overflow-wrap: anywhere; }}
  meter {{ width: 4.5rem; vertical-align: middle; }}
  details {{ margin: .5rem 0; border: 1px solid #cbdadf; background: #ffffff; padding: .5rem .8rem; }}
  summary {{ cursor: pointer; font-weight: 650; padding: .2rem 0; }}
</style>
</head>
<body>
<main>
<h1>Baseline comparison</h1>
<p class="context">CircuForge · {"RC low-pass" if spec.filter_type == "rc_lowpass" else "RC high-pass"} · Target {spec.cutoff_hz:g} Hz · Tolerance {tolerance:g}% · Seed {runs[0].options.seed}</p>
<p class="notice">{scope}</p>
{summary}
<p class="context">Error bars share a 0–{_number(scale)}% scale. Call counts include failed attempts.</p>
<h2>Candidate history</h2>
<p class="context">Verified candidates passed the raw ngspice response audit. Unverified entries show the recorded failure reason and have no ranked error.</p>
{"".join(histories)}
</main>
</body>
</html>
"""


def write_comparison_report(root: Path, output: Path) -> None:
    """Check the saved comparison and write a new report without calling ngspice."""
    require(output.suffix.lower() == ".html", "output must be a new .html file")
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    page = _render(_load_comparison(root.resolve()))
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(page)
