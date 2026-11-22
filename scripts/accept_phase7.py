"""Automatic local research-MVP gate: fresh tests, installed-demo evidence and prior scientific gates."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree

from circuforge.evaluation.acceptance import require, validate_junit
from circuforge.evaluation.records import environment

ROOT = Path(__file__).resolve().parents[1]
POLICY = "phase7-local-research-mvp-v1"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_hashes():
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for directory in ("src", "scripts", "tests") for path in sorted((ROOT / directory).rglob("*.py"))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "demo", "interface-evidence", "primary-trial", "replay-supplement"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--ngspice", required=True)
    args = parser.parse_args(argv)
    created = False
    result = dict(status="blocked", policy=POLICY, acceptance_mode="automated", manual_technical_review_required=False,
                  release_scope="local validated research MVP; no remote publication/deployment", remote_published=False,
                  owner_cv_approved=False, new_model_requests=0, new_demo_spice_calls=0)
    try:
        initial_sources = source_hashes()
        plan = read(ROOT / "planning/phase-tasks.json")
        tasks = {t["id"]: t for p in plan["phases"] for t in p["tasks"]}
        require(all(tasks[t]["status"] == "done" and tasks[t].get("evidence") for t in
                    ("P3-C3", "P4-C3", "P5-C4", "P6-C2", "P7-C1", "P7-C2")), "unaccepted task dependency")
        interface = read(args.interface_evidence / "acceptance.json")
        require(interface["status"] == "passed" and interface["policy"] == "phase5-local-interface-v1" and
                interface["environment"] == environment() and
                validate_junit(args.interface_evidence / "tests.xml") == interface["tests_passed"],
                "installed-interface acceptance stale or failed")
        composite = module("audit_local_replay").audit(args.primary_trial, args.replay_supplement)
        require(composite["status"] == "passed" and composite == read(args.replay_supplement / "acceptance.json"),
                "scientific composite gate missing or inconsistent")
        report = read(ROOT / "docs/research/summary.json")
        require(report["phase6_status"] == "passed" and report["replay_supplement"] == composite,
                "research report omits accepted replay evidence")
        require(all(hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() == row["sha256"] for row in report["sources"]),
                "research input hashes changed")
        args.output.mkdir(parents=True, exist_ok=False)
        created = True
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
               "CIRCUFORGE_NGSPICE": args.ngspice, "MPLCONFIGDIR": str(args.output / "matplotlib-cache")}
        env.pop("PYTEST_ADDOPTS", None)
        junit = args.output / "tests.xml"
        command = [sys.executable, "-m", "pytest", "-q", "-ra", "-p", "no:cacheprovider", "--junitxml", str(junit)]
        result["commands"] = [command]
        print("Running full current suite; no scientific model requests...", flush=True)
        with (args.output / "tests.log").open("wb") as log:
            completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL, shell=False, timeout=300)
        require(completed.returncode == 0, "fresh suite failed; inspect tests.log")
        tests = validate_junit(junit)
        print(f"All {tests} tests passed without skips. Auditing captured installed demo...", flush=True)
        demo = module("audit_demo").audit(ROOT / "examples", args.demo)
        require(demo == read(args.demo / "acceptance.json"), "demo acceptance differs from raw audit")
        identity = read(args.demo / "demo.json")["installed_identity"]
        require(Path(identity["module"]).resolve() == Path(interface["installed_module"]).resolve(),
                "demo did not use the accepted fresh installation")
        require(source_hashes() == initial_sources and interface["environment"] == environment(),
                "source/tests/environment changed during acceptance")
        result.update(status="passed", tests_passed=tests, environment=environment(), demo=demo,
                      demo_root=str(args.demo.resolve()), scientific_gate=composite,
                      interface_acceptance_sha256=hashlib.sha256((args.interface_evidence / "acceptance.json").read_bytes()).hexdigest(),
                      research_summary_sha256=hashlib.sha256((ROOT / "docs/research/summary.json").read_bytes()).hexdigest(),
                      checked_sources=initial_sources)
        print(f"PASS: local research MVP gate; {tests} tests, 75-second annotated installed-CLI replay, nine raw-audited demo calls.", flush=True)
        code = 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError, ElementTree.ParseError) as exc:
        result["error"] = str(exc)
        print(f"Local MVP gate blocked: {exc}", flush=True)
        code = 1
    if created:
        result["executed_at_utc"] = datetime.now(timezone.utc).isoformat()
        (args.output / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
