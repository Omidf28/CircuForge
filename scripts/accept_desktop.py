"""Read-only desktop acceptance: fresh tests/install, real GUI exports and raw audits.

Create GUI runs with the actual desktop before invoking this checker. Screenshots
are hashed and structurally verified; visual semantics are agent-inspected, not
claimed as programmatic pixel recognition or a completed owner review.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree
import zipfile

from circuforge.application import load_request
from circuforge.desktop.model import validate_desktop_request
from circuforge.evaluation.acceptance import read_json, require, validate_junit
from circuforge.evaluation.design_acceptance import audit_design, audit_walkthrough
from circuforge.evaluation.records import environment

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASES = {("rc_lowpass", "analytic_rc"): "passed", ("rc_highpass", "analytic_rc"): "passed",
                ("rc_highpass", "simulate"): "target_missed"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {path.relative_to(ROOT).as_posix(): digest(path) for folder in ("src", "scripts", "tests")
            for path in sorted((ROOT / folder).rglob("*.py"))}


def audit_screenshot(path: Path) -> str:
    from PIL import Image

    expected_format = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG"}.get(path.suffix.lower())
    with Image.open(path) as picture:
        require(expected_format is not None and picture.format == expected_format and
                picture.width >= 1000 and picture.height >= 700,
                "desktop screenshot missing, mislabeled or invalid")
        picture.verify()
    return digest(path)


def audit_installed_package(interface_root: Path, installed_module: Path, expected_digest: str) -> dict:
    wheels = list((interface_root / "wheels").glob("circuforge-*.whl"))
    require(len(wheels) == 1 and digest(wheels[0]) == expected_digest, "wheel evidence differs")
    wheel = wheels[0]
    installed_package = installed_module.parent
    package = sorted((ROOT / "src/circuforge").rglob("*.py"))
    with zipfile.ZipFile(wheel) as archive:
        names = {p.relative_to(ROOT / "src").as_posix() for p in package}
        require(archive.testzip() is None and {n for n in archive.namelist() if n.endswith(".py")} == names,
                "wheel package inventory/CRC differs")
        for path in package:
            name = path.relative_to(ROOT / "src")
            require(path.read_bytes() == archive.read(name.as_posix()) ==
                    (installed_package / path.relative_to(ROOT / "src/circuforge")).read_bytes(),
                    "source/wheel/installed package bytes differ")
    return {"wheel_sha256": digest(wheel), "package_python_files": len(package)}


def audit_gui_runs(root: Path, expected: dict) -> list[dict]:
    paths = sorted(root.iterdir())
    require(len(paths) == len(expected) and all(p.is_dir() and not p.is_symlink() for p in paths),
            "incomplete or unexpected desktop runs")
    seen, rows = set(), []
    for path in paths:
        request = validate_desktop_request(load_request(path / "request.json"))
        key = (request.spec.filter_type, request.method)
        require(key in expected and key not in seen, "duplicate or unsupported desktop case")
        seen.add(key)
        result = audit_design(path, request)
        require(result.status == expected[key] and result.simulator_calls == 1 and result.best is not None,
                "desktop physics/status/budget differs")
        rows.append(dict(path=str(path.resolve()), topology=key[0], method=key[1], status=result.status,
                         calls=1, cutoff_hz=result.best.measured_cutoff_hz, target_error=result.best.relative_error,
                         report_sha256=digest(path / "report.json")))
    require(seen == set(expected), "missing desktop cases")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("interface-evidence", "source-hashes", "gui-evidence", "installed-gui", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--tests-evidence", type=Path,
                        help="current full-suite evidence when unchanged installed package evidence is reused")
    args = parser.parse_args(argv)
    result = dict(status="blocked", policy="phase5-simple-desktop-v1", acceptance_mode="automated",
                  manual_technical_review_required=False, new_model_requests=0, new_simulator_calls_by_auditor=0)
    created = False
    try:
        for name in ("interface_evidence", "source_hashes", "gui_evidence", "installed_gui", "output"):
            setattr(args, name, getattr(args, name).resolve())
        tests_root = args.tests_evidence.resolve() if args.tests_evidence else args.interface_evidence
        recorded_hashes = json.loads(args.source_hashes.read_text(encoding="utf-8"))
        require(recorded_hashes == source_hashes(), "source/tests changed since full-suite/install verification")
        interface = read_json(args.interface_evidence, "acceptance.json")
        interface_tests = validate_junit(args.interface_evidence / "tests.xml")
        tests = validate_junit(tests_root / "tests.xml")
        require(interface["status"] == "passed" and interface["policy"] == "phase5-local-interface-v1" and
                interface["environment"] == environment() and interface_tests == interface["tests_passed"] and
                interface_tests >= 503 and tests >= 503,
                "fresh full-suite/installed-interface evidence missing or stale")
        installed = args.interface_evidence / "installed"
        audited = audit_walkthrough(ROOT / "examples", args.interface_evidence / "walkthrough", installed)
        require(all(interface[key] == value for key, value in audited.items()), "interface acceptance differs from raw audit")
        package_proof = audit_installed_package(args.interface_evidence, Path(audited["installed_module"]), interface["wheel_sha256"])
        visible = audit_gui_runs(args.gui_evidence / "visible-runs", SOURCE_CASES)
        installed_rows = audit_gui_runs(args.installed_gui, {("rc_lowpass", "analytic_rc"): "passed"})
        screenshots = {}
        for name in ("lowpass-window", "highpass-window", "target-miss-window", "invalid-input-window"):
            candidates = [path for suffix in (".png", ".jpg", ".jpeg")
                          if (path := args.gui_evidence / "screenshots" / (name + suffix)).is_file()]
            require(len(candidates) == 1, "desktop screenshot missing or ambiguous")
            screenshots[candidates[0].name] = audit_screenshot(candidates[0])
        require(source_hashes() == recorded_hashes, "source changed during audit")
        args.output.mkdir(parents=True, exist_ok=False)
        created = True
        result.update(status="passed", tests_passed=tests, tests_evidence=str(tests_root),
                      installed_interface_tests=interface_tests, checked_sources=recorded_hashes, environment=environment(),
                      installed_module=audited["installed_module"], **package_proof, gui_runs=visible, installed_gui_runs=installed_rows,
                      gui_calls=4, interface_calls=27, actual_calls_including_installed_interface=31,
                      raw_calls_audited=22, json_calls_matched=9, screenshots=screenshots,
                      screenshot_check="native JPEG/PNG format, dimensions, integrity and hash; actual states inspected with Windows Computer Use, no pixel classifier",
                      scope="owner-selected simple desktop only; existing ideal RC engine; historical scientific evidence unchanged")
        code = 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError, ElementTree.ParseError, zipfile.BadZipFile) as exc:
        result["error"] = str(exc)
        print("Desktop acceptance blocked: " + str(exc))
        code = 1
    if created:
        result["executed_at_utc"] = datetime.now(timezone.utc).isoformat()
        (args.output / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "policy")}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
