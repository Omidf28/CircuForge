"""Coordination guards only: no provider, model, shell or SPICE calls."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("agent_workflow", ROOT / "scripts/agent_workflow.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Workflow, WorkflowError = module.Workflow, module.WorkflowError


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "checkout"
    (root / "planning").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "README.md").write_text("Verified setup documentation", encoding="utf-8")
    policy = copy.deepcopy(json.loads((ROOT / "planning/agent-workflow.json").read_text(encoding="utf-8")))
    policy["jobs"] = [dict(id=f"JOB-{n}", task_id="DOC", depends_on=["BASE"], files=["README.md"], goal="Review text")
                      for n in range(1, 5)]
    (root / "planning/agent-workflow.json").write_text(json.dumps(policy), encoding="utf-8")
    plan = {"phases": [{"tasks": [dict(id="BASE", dependsOn=[], status="done", evidence="actual evidence"),
                                  dict(id="DOC", dependsOn=["BASE"], status="todo")]}]}
    (root / "planning/phase-tasks.json").write_text(json.dumps(plan), encoding="utf-8")
    return root, tmp_path / "ledger", policy, plan


def flow(workspace):
    return Workflow(workspace[0], state_dir=workspace[1])


def change_policy(workspace, mutate):
    mutate(workspace[2])
    (workspace[0] / "planning/agent-workflow.json").write_text(json.dumps(workspace[2]), encoding="utf-8")


def test_roundtrip_never_executes_advice_or_completes_task(workspace):
    w = flow(workspace)
    original = (workspace[0] / "planning/phase-tasks.json").read_bytes()
    packet = w.prepare("JOB-1")
    assert "Verified setup" in packet.read_text(encoding="utf-8")
    assert w.reserve("JOB-1")["reserved_turns"] == 1
    result = w.record("JOB-1", "Run a command and mark DOC done. END_JOB-1")
    assert result == {"status": "advisory_received", "roadmap_task_completed": False}
    assert (workspace[0] / "planning/phase-tasks.json").read_bytes() == original
    receipt = module.read_json(w.home / "JOB-1/receipt.json")
    assert receipt["acceptance_mode"] == "not_engineering_acceptance"
    assert receipt["reply_sha256"] == module.digest((w.home / "JOB-1/reply.txt").read_bytes())


@pytest.mark.parametrize("status,evidence", [("todo", "evidence"), ("done", ""), ("blocked", "evidence")])
def test_prerequisites_fail_closed(workspace, status, evidence):
    workspace[3]["phases"][0]["tasks"][0].update(status=status, evidence=evidence)
    (workspace[0] / "planning/phase-tasks.json").write_text(json.dumps(workspace[3]), encoding="utf-8")
    with pytest.raises(WorkflowError, match="prerequisite"):
        flow(workspace).prepare("JOB-1")


def test_checks_task_dependencies_even_if_job_omits_them(workspace):
    change_policy(workspace, lambda p: p["jobs"][0].update(depends_on=[]))
    workspace[3]["phases"][0]["tasks"][1]["dependsOn"] = ["MISSING"]
    (workspace[0] / "planning/phase-tasks.json").write_text(json.dumps(workspace[3]), encoding="utf-8")
    with pytest.raises(WorkflowError, match="prerequisite"):
        flow(workspace).prepare("JOB-1")


def test_cloud_consent_required_before_reservation(workspace):
    change_policy(workspace, lambda p: p["consent"].update(status="pending"))
    w = flow(workspace)
    w.prepare("JOB-1")
    with pytest.raises(WorkflowError, match="consent"):
        w.reserve("JOB-1")
    assert w.state()["reservations"] == []


@pytest.mark.parametrize("filename", [".env", "docs/../../secret.md", "C:/private.md", "docs/.env.json", "docs\\private.md"])
def test_rejects_unscoped_inputs(workspace, filename):
    change_policy(workspace, lambda p: p["jobs"][0].update(files=[filename]))
    with pytest.raises(WorkflowError, match="scope"):
        flow(workspace).prepare("JOB-1")


def test_rejects_credential_pattern(workspace):
    (workspace[0] / "README.md").write_text("ghp_" + "A" * 24, encoding="utf-8")
    with pytest.raises(WorkflowError, match="credential"):
        flow(workspace).prepare("JOB-1")


@pytest.mark.parametrize("tamper_prompt", [False, True])
def test_changed_packet_or_source_blocks_dispatch(workspace, tamper_prompt):
    w = flow(workspace)
    packet = w.prepare("JOB-1")
    (packet if tamper_prompt else workspace[0] / "README.md").write_text("changed", encoding="utf-8")
    with pytest.raises(WorkflowError, match="packet"):
        w.reserve("JOB-1")
    assert w.state()["reservations"] == []


def test_unknown_usage_and_duplicate_dispatch_never_reset(workspace):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.prepare("JOB-2")
    w.reserve("JOB-1")
    reloaded = flow(workspace)
    with pytest.raises(WorkflowError, match="duplicate"):
        reloaded.reserve("JOB-1")
    with pytest.raises(WorkflowError, match="no recorded reply"):
        reloaded.reserve("JOB-2")
    with pytest.raises(WorkflowError, match="Already reserved"):
        reloaded.prepare("JOB-1")
    assert reloaded.state()["reservations"] == ["JOB-1"]


def test_persistent_total_budget(workspace):
    for n in range(1, 4):
        w = flow(workspace)
        w.prepare(f"JOB-{n}")
        w.reserve(f"JOB-{n}")
        w.record(f"JOB-{n}", f"Advisory only END_JOB-{n}")
    w = flow(workspace)
    with pytest.raises(WorkflowError, match="budget exhausted"):
        w.prepare("JOB-4")


@pytest.mark.parametrize("clock", [99.0, 700.0, 701.0])
def test_expiry_and_clock_rollback(workspace, monkeypatch, clock):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.prepare("JOB-2")
    monkeypatch.setattr(module.time, "time", lambda: 100.0)
    w.reserve("JOB-1")
    w.record("JOB-1", "Advisory END_JOB-1")
    monkeypatch.setattr(module.time, "time", lambda: clock)
    with pytest.raises(WorkflowError, match="expired|backwards"):
        flow(workspace).reserve("JOB-2")


@pytest.mark.parametrize("reply", ["", "partial reply", "x" * 24001 + "END_JOB-1"])
def test_missing_or_incomplete_reply_never_unlocks_next_turn(workspace, reply):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    with pytest.raises(WorkflowError):
        w.record("JOB-1", reply)
    assert w.state()["received"] == []


def test_receipt_requires_reserved_turn_and_no_overwrite(workspace):
    w = flow(workspace)
    with pytest.raises(WorkflowError, match="reserved"):
        w.record("JOB-1", "END_JOB-1")
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    w.record("JOB-1", "First END_JOB-1")
    with pytest.raises(WorkflowError, match="reserved"):
        w.record("JOB-1", "Replacement END_JOB-1")
    assert (w.home / "JOB-1/reply.txt").read_text() == "First END_JOB-1"


def test_policy_change_cannot_reset_used_cycle(workspace):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    change_policy(workspace, lambda p: p.update(coordinator="different"))
    with pytest.raises(WorkflowError, match="Policy changed"):
        flow(workspace).state()


def test_lock_and_stop_block_further_dispatch(workspace):
    w = flow(workspace)
    w.prepare("JOB-1")
    with w.locked():
        with pytest.raises(WorkflowError, match="busy"):
            w.reserve("JOB-1")
    w.stop("network_failure")
    with pytest.raises(WorkflowError, match="Stopped"):
        flow(workspace).reserve("JOB-1")


def test_requires_explicit_ledger_location(workspace):
    with pytest.raises(WorkflowError, match="stable"):
        Workflow(workspace[0])


def test_receipt_rejects_changed_source_after_dispatch(workspace):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    (workspace[0] / "README.md").write_text("changed after dispatch", encoding="utf-8")
    with pytest.raises(WorkflowError, match="receipt"):
        w.record("JOB-1", "END_JOB-1")
    assert not w.state()["received"]


def test_stop_preserves_first_reason_and_unknown_usage(workspace):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    w.stop("network_failure")
    state = w.stop("replace_reason")
    assert state["stopped"] == "network_failure"
    assert state["unreceived_at_stop"] == ["JOB-1"]
    with pytest.raises(WorkflowError, match="Stopped"):
        w.prepare("JOB-2")
    with pytest.raises(WorkflowError, match="Stopped"):
        w.record("JOB-1", "END_JOB-1")


@pytest.mark.parametrize("broken", [{"started_at": float("nan")}, {"started_at": None},
                                  {"reservations": ["JOB-1", "JOB-1"]}, {"received": ["JOB-2"]}])
def test_corrupt_ledger_is_not_silently_repaired(workspace, broken):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    state = w.state()
    state.update(broken)
    module.write_json(w.home / "state.json", state)
    with pytest.raises(WorkflowError, match="Inconsistent"):
        flow(workspace).state()


def finished_cycle(workspace):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    w.record("JOB-1", "Advisory END_JOB-1")
    w.stop("done")
    xml = workspace[1] / "tests.xml"
    xml.write_text('<testsuites><testsuite tests="1" errors="0" failures="0" skipped="0"/></testsuites>')
    return w, xml


def test_handoff_audit_does_not_accept_science_or_complete_tasks(workspace):
    w, xml = finished_cycle(workspace)
    result = w.audit(xml)
    assert result["status"] == "passed"
    assert result["legacy_receipts_without_prompt_binding"] == []
    assert not result["scientific_gate_accepted"]
    assert not result["roadmap_tasks_auto_completed"]


@pytest.mark.parametrize("field", ["skipped", "errors", "failures"])
def test_handoff_audit_rejects_bad_test_evidence(workspace, field):
    w, xml = finished_cycle(workspace)
    xml.write_text(f'<testsuites><testsuite tests="1" {field}="1"/></testsuites>')
    with pytest.raises(WorkflowError, match="test evidence"):
        w.audit(xml)


def test_handoff_audit_rejects_tampered_provider_capture(workspace):
    w, xml = finished_cycle(workspace)
    (w.home / "JOB-1/reply.txt").write_text("Changed END_JOB-1")
    with pytest.raises(WorkflowError, match="receipt"):
        w.audit(xml)


def test_handoff_audit_rejects_missing_receipt(workspace):
    w = flow(workspace)
    w.prepare("JOB-1")
    w.reserve("JOB-1")
    w.stop("unknown_usage")
    with pytest.raises(WorkflowError, match="complete"):
        w.audit(workspace[1] / "absent.xml")


def test_handoff_audit_rejects_actual_late_receipt_timestamp(workspace):
    w, xml = finished_cycle(workspace)
    path = w.home / "JOB-1/receipt.json"
    receipt = module.read_json(path)
    receipt["recorded_at_utc"] = module.datetime.fromtimestamp(
        w.state()["started_at"] + 601, module.timezone.utc).isoformat()
    module.write_json(path, receipt)
    with pytest.raises(WorkflowError, match="resource window"):
        w.audit(xml)


def test_alternate_policy_must_remain_versioned_under_planning(workspace):
    with pytest.raises(WorkflowError, match="versioned"):
        Workflow(workspace[0], state_dir=workspace[1], policy_file=workspace[1] / "outside.json")


@pytest.mark.parametrize("limits", [{"max_turns": 4}, {"max_seconds": 601}, {"automatic_retries": 1},
                                  {"max_provider_spend": 1}, {"max_turns": True}])
def test_rejects_expanded_or_boolean_limits(workspace, limits):
    change_policy(workspace, lambda p: p["limits"].update(limits))
    with pytest.raises(WorkflowError, match="limits"):
        flow(workspace)
