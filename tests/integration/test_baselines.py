import json

import pytest

from circuforge.cli import main
from circuforge.domain.specs import DesignSpec
from circuforge.optimization.baselines import run_baseline
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


def simulator():
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    return Ngspice()


@pytest.mark.integration
@pytest.mark.parametrize("method", ["random", "grid", "scipy"])
def test_real_baseline_cap_and_replay(method):
    adapter = simulator()
    spec = DesignSpec(cutoff_hz=2300., max_evaluations=7,
                      resistance_ohm={"minimum": 100., "maximum": 10000.},
                      capacitance_f={"minimum": 1e-8, "maximum": 1e-6})
    first = run_baseline(spec, adapter, method, seed=73)
    second = run_baseline(spec, adapter, method, seed=73)
    assert first.simulator_calls == second.simulator_calls == 7
    trace = lambda r: [(e.candidate, e.measured_cutoff_hz, e.status) for e in r.history]
    assert trace(first) == trace(second)
    assert all(e.verified for e in first.history)


@pytest.mark.integration
@pytest.mark.parametrize("render_html", [False, True])
def test_real_comparison_exports_all_call_evidence_and_preserves_existing_output(
        tmp_path, capsys, monkeypatch, render_html):
    adapter = simulator()
    real_simulate = Ngspice.simulate
    attempts = []

    def count_simulation(self, spec, candidate):
        attempts.append(candidate)
        return real_simulate(self, spec, candidate)

    monkeypatch.setattr(Ngspice, "simulate", count_simulation)
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"cutoff_hz": 1591.5494,
                               "resistance_ohm": {"minimum": 1000., "maximum": 1000.},
                               "capacitance_f": {"minimum": 1e-7, "maximum": 1e-7}}))
    output = tmp_path / "گزارش مقایسه"
    args = ["--ngspice", adapter.info.executable, "compare", "--spec", str(spec),
            "--seed", "7", "--output", str(output)]
    if render_html:
        args.append("--html")
    assert main(args) == 0
    summary = json.loads(capsys.readouterr().out)
    assert len(attempts) == 3
    page = output / "comparison.html"
    if render_html:
        assert summary["report_html"] == str(page)
        assert page.read_bytes().count(b"<meter ") == 3
    else:
        assert "report_html" not in summary and not page.exists()
    comparison = json.loads((output / "comparison.json").read_text())
    assert comparison["matched_actual_calls"]
    for method in ("random", "grid", "scipy"):
        report = json.loads((output / method / "report.json").read_text())
        assert report["simulator_calls"] == 1 and report["converged"]
        artifact = output / method / "evaluations" / "call-0001"
        assert (artifact / "evaluation.json").is_file()
        assert len((artifact / "response.csv").read_text().splitlines()) == 602
        assert (artifact / "stdout.log").stat().st_size > 0
    before = (output / "comparison.json").read_bytes()
    assert main(args) == 2
    assert len(attempts) == 3
    assert (output / "comparison.json").read_bytes() == before
