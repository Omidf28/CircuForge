"""Independently audit raw captured CLI evidence and its annotated replay artifact."""
import argparse
import hashlib
import importlib.util
from pathlib import Path

from PIL import Image, ImageSequence

from circuforge.application import load_request
from circuforge.contracts import DesignResult
from circuforge.evaluation.acceptance import require
from circuforge.evaluation.design_acceptance import audit_design
from circuforge.evaluation.records import environment


def exporter():
    spec = importlib.util.spec_from_file_location("captured_demo_exporter", Path(__file__).with_name("capture_demo.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(source: Path, root: Path) -> dict:
    demo = exporter()
    report = demo.read(root / "demo.json")
    require(report["policy"] == demo.POLICY and report["new_model_requests"] == 0 and
            report["exporter_sha256"] == demo.sha256(Path(demo.__file__)) and
            report["owner_cv_approved"] is False and report["remote_published"] is False and
            "not live screen recording" in report["capture_kind"], "unsupported demo/publication claim")
    identity = report["installed_identity"]
    probe = report["probe_command"]
    require(Path(identity["module"]).resolve().is_relative_to(Path(identity["prefix"]).resolve()) and
            "site-packages" in Path(identity["module"]).parts and identity["environment"] == environment(),
            "installed-package identity differs")
    require(len(probe) == 4 and probe[1:3] == ["-I", "-c"] and
            Path(probe[0]).resolve().is_relative_to(Path(identity["prefix"]).resolve()),
            "installed interpreter probe differs")
    require(len(report["cases"]) == len(demo.CASES), "incomplete demo cases")
    results, roots = [], []
    for record, (name, status, calls) in zip(report["cases"], demo.CASES):
        request = load_request(source / (name + ".json"))
        path = root / name
        result = audit_design(path / "cli", request)
        require(record["case"] == name and result.status == record["status"] == status and
                result.simulator_calls == record["calls"] == calls and
                record["exit"] == (0 if status == "passed" else 1), "demo status/call/exit mismatch")
        command = record["command"]
        require(len(command) == 11 and Path(command[0]).resolve() == Path(probe[0]).resolve() and
                command[1:5] == ["-I", "-m", "circuforge", "--ngspice"] and
                command[6:8] == ["design", "--request"] and command[9] == "--output" and
                Path(command[8]).resolve() == (source / (name + ".json")).resolve() and
                Path(command[10]).resolve() == (path / "cli").resolve(), "unexpected captured command")
        require(demo.sha256(source / (name + ".json")) == record["input_sha256"] and
                demo.sha256(path / "stdout.json") == record["stdout_sha256"] and
                result == DesignResult.model_validate_json((path / "stdout.json").read_bytes()), "transcript/input differs")
        results.append(result)
        roots.append(path / "cli")
    require(report["actual_spice_calls"] == sum(result.simulator_calls for result in results) == 9,
            "incorrect total demo calls")
    canonical = demo.frames(results, roots)
    for index, expected in enumerate(canonical):
        with Image.open(root / f"frame-{index:02d}.png") as actual:
            require(actual.convert("RGB").tobytes() == expected.tobytes(), "demo frame differs from verified data")
    expected_gif = demo.gif_bytes(canonical)
    require((root / "demo.gif").read_bytes() == expected_gif and
            report["gif_sha256"] == hashlib.sha256(expected_gif).hexdigest(), "animated replay differs from verified frames")
    with Image.open(root / "demo.gif") as animation:
        durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(animation)]
        require(animation.size == (1280, 800) and len(durations) == report["frames"] == 5 and
                sum(durations) == report["duration_ms"] == 75000 and report["loops"] is True,
                "incorrect animation duration/frame count")
    require((root / "claims.md").read_text(encoding="utf-8") == demo.CLAIMS and
            demo.sha256(root / "claims.md") == report["claims_sha256"], "unsupported portfolio wording")
    return dict(status="passed", policy=demo.POLICY, acceptance_mode="automated", actual_spice_calls=9,
                independently_raw_audited_calls=9, duration_s=75, frames=5, passes=2, target_misses=1,
                model_requests=0, owner_cv_approved=False, remote_published=False,
                capture_kind=report["capture_kind"], gif_sha256=report["gif_sha256"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        import json
        result = audit(args.source.resolve(), args.input.resolve())
        (args.input / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(result)
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"Demo audit blocked: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
