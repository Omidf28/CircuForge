"""Small-budget genuine AC runs exercise all 20 cases, rejection and replay."""
import json
from pathlib import Path
import shutil

import pytest

from circuforge.evaluation.acceptance import AcceptanceError
from circuforge.evaluation.benchmark import audit_benchmark, audit_replay, run_benchmark
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


@pytest.fixture(scope="module")
def benchmark_evidence(tmp_path_factory):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))
    root = tmp_path_factory.mktemp("benchmark-real")
    data = json.loads((Path(__file__).resolve().parents[2] / "examples/benchmark-v2.json").read_text())
    data["seeds"] = [7, 42]
    for case in data["cases"]:
        case["inputs"]["max_evaluations"] = 1
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps(data))
    simulator = Ngspice()
    for name in ("first", "replay"):
        run_benchmark(manifest, root / name, simulator)
    return root


@pytest.mark.integration
def test_real_replay_audits_calls_and_excludes_rejections_from_design_success(benchmark_evidence):
    root = benchmark_evidence
    result = audit_replay(root / "manifest.json", root / "first", root / "replay")
    assert result["status"] == "passed" and result["numerical_replay"].startswith("exact")
    assert result["trials"] == 120 and result["infeasible_rejections"] == 24
    assert result["audited_calls_including_replay"] == 192
    assert result["design_passes"] + result["design_misses"] == 96
    assert result["design_misses"] > 0


@pytest.mark.integration
@pytest.mark.parametrize("damage", ["aggregate", "row", "rejection", "raw", "source", "missing_trial"])
def test_corruption_blocks_automatic_benchmark_gate(benchmark_evidence, tmp_path, damage):
    root = tmp_path / "copy"
    shutil.copytree(benchmark_evidence / "first", root)
    path = root / "summary.json"
    summary = json.loads(path.read_text())
    if damage == "aggregate":
        summary["aggregates"]["random"]["design_passes"] += 1
    elif damage == "row":
        summary["trials"][0]["objective"] = 0.
    elif damage == "rejection":
        index = next(i for i, r in enumerate(summary["trials"]) if not r["expected_feasible"])
        summary["trials"][index]["candidate"] = {"fabricated": True}
    elif damage == "raw":
        (root / "seed-7/lp-10hz/random/evaluations/call-0001/response.csv").unlink()
    elif damage == "source":
        summary["manifest_sha256"] = "wrong"
    else:
        summary["trials"].pop()
    path.write_text(json.dumps(summary))
    with pytest.raises(AcceptanceError):
        audit_benchmark(benchmark_evidence / "manifest.json", root)
