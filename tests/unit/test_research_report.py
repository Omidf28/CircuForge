"""Synthetic reporting fixtures, never scientific acceptance evidence."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest


def command():
    path = Path(__file__).resolve().parents[2] / "scripts/report_research.py"
    spec = importlib.util.spec_from_file_location("research_report_command", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def dataset(tmp_path):
    module = command()
    manifest = tmp_path / "manifest.json"
    save(manifest, {"fixture": "synthetic"})
    root = tmp_path / "run"
    row = dict(case="fixture", seed=7, method="random", simulator_calls=2,
               failures=0, relative_error=0.1, wall_s=1.0)
    batch = dict(manifest_sha256=module.sha256(manifest), completed_trials=1, planned_trials=1,
                 actual_calls=2, trials=[row], environment={"fixture": "test-only"})
    acceptance = dict(status="passed", policy="fixture-policy", acceptance_mode="automated", tests_passed=1,
                      trials=1, audited_calls=2, audited_calls_including_replay=4)
    save(root / "acceptance.json", acceptance)
    save(root / "first/summary.json", batch)
    replay = copy.deepcopy(batch)
    replay["trials"][0]["wall_s"] = 2.0
    save(root / "replay/summary.json", replay)
    (root / "tests.xml").write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0">'
                                   '<testcase name="synthetic-report-fixture"/></testsuite></testsuites>')
    return module, root, manifest


def test_historical_replay_excludes_runtime_and_preserves_target_miss(dataset):
    module, root, manifest = dataset
    acceptance, batch, paths = module.accepted_dataset(root, manifest, "fixture-policy")
    assert batch["trials"][0]["relative_error"] == 0.1
    assert acceptance["audited_calls"] == 2  # Replay is not pooled into a new scoring sample.
    assert len(paths) == 5


@pytest.mark.parametrize("change", ["policy", "manifest", "test_count", "skipped", "calls", "duplicate", "replay"])
def test_inconsistent_historical_evidence_blocks_reporting(dataset, change):
    module, root, manifest = dataset
    acceptance = module.read(root / "acceptance.json")
    batch = module.read(root / "first/summary.json")
    if change == "policy":
        acceptance["status"] = "blocked"
    elif change == "manifest":
        manifest.write_text("{}")
    elif change == "test_count":
        acceptance["tests_passed"] = 2
    elif change == "skipped":
        (root / "tests.xml").write_text('<testsuites><testsuite tests="1" skipped="1"/></testsuites>')
    elif change == "calls":
        batch["actual_calls"] = 3
    elif change == "duplicate":
        batch["trials"] *= 2
        batch["completed_trials"] = batch["planned_trials"] = acceptance["trials"] = 2
        batch["actual_calls"] = acceptance["audited_calls"] = 4
        acceptance["audited_calls_including_replay"] = 8
    else:
        batch["trials"][0]["relative_error"] = 0.001
    save(root / "acceptance.json", acceptance)
    save(root / "first/summary.json", batch)
    with pytest.raises(ValueError):
        module.accepted_dataset(root, manifest, "fixture-policy")


def test_export_refuses_to_overwrite_existing_report(dataset, monkeypatch):
    module, root, _ = dataset
    output = root / "already-present"
    output.mkdir()
    keep = output / "report.md"
    keep.write_text("keep this report")
    monkeypatch.setattr(module, "collect", lambda *args: {})
    assert module.main(["--benchmark", str(root), "--robustness", str(root),
                        "--local", str(root), "--output", str(output)]) == 1
    assert keep.read_text() == "keep this report"
