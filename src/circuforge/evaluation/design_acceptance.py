"""Independent raw-data and archive audit of the shared CLI/API design exports."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

from circuforge.application import MAX_BUNDLE_BYTES, SELECTED_FILES
from circuforge.contracts import DesignRequest, DesignResult, Waveform
from circuforge.evaluation.acceptance import audit_evaluation, evidence_file, read_json, require
from circuforge.evaluation.records import environment
from circuforge.optimization.baselines import BaselineResult
from circuforge.simulation.ngspice import parse_ac

POLICY = "phase5-local-interface-v1"


def expected_files(result: DesignResult) -> set[str]:
    require(result.best is not None and all(e.verified for e in result.history), "reference design execution failed")
    names = {"request.json", "report.json", "engine/report.json", "response.png", *SELECTED_FILES}
    for index, evaluation in enumerate(result.history, 1):
        require(evaluation.simulator_call == index and evaluation.artifact == f"call-{index:04d}", "unsafe/discontinuous call identity")
        for name in (*SELECTED_FILES, "evaluation.json"):
            names.add(f"engine/evaluations/call-{index:04d}/{name}")
    return names


def verify_manifest(manifest: dict, names: set[str], read_file) -> None:
    require(manifest["format"] == "circuforge-design-v1", "unknown artifact format")
    entries = manifest["files"]
    require(len(entries) == len(names) and {e["path"] for e in entries} == names, "missing/duplicate/unexpected manifest files")
    for entry in entries:
        content = read_file(entry["path"])
        require(len(content) == entry["bytes"] and hashlib.sha256(content).hexdigest() == entry["sha256"],
                "artifact checksum/size mismatch")


def extract_bundle(archive: Path, destination: Path) -> None:
    require(archive.stat().st_size <= MAX_BUNDLE_BYTES, "oversized ZIP")
    with zipfile.ZipFile(archive) as stream:
        infos = stream.infolist()
        names = [i.filename for i in infos]
        require(len(infos) <= 257 and len(names) == len(set(names)) and
                sum(i.file_size for i in infos) <= 64 * 1024 * 1024, "duplicate/oversized archive entries")
        for entry in infos:
            path = PurePosixPath(entry.filename)
            require(not path.is_absolute() and ".." not in path.parts and ":" not in entry.filename and
                    "\\" not in entry.filename and not entry.is_dir() and
                    not stat.S_ISLNK(entry.external_attr >> 16), "unsafe archive member")
        result = DesignResult.model_validate_json(stream.read("report.json"))
        expected = expected_files(result)
        require(set(names) == expected | {"manifest.json"}, "archive contents differ from typed trace")
        verify_manifest(json.loads(stream.read("manifest.json")), expected, stream.read)
        destination.mkdir(parents=True, exist_ok=False)
        for name in names:
            target = destination / name
            require(target.resolve().is_relative_to(destination.resolve()), "unsafe extraction path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(stream.read(name))


def audit_design(root: Path, request: DesignRequest) -> DesignResult:
    from PIL import Image

    result = DesignResult.model_validate(read_json(root, "report.json"))
    require(result.request == request and DesignRequest.model_validate(read_json(root, "request.json")) == request,
            "exported request differs from input")
    require(result.environment == environment(), "stale/different code or numerical environment")
    require(result.history and result.simulator_calls == len(result.history) and result.failures == 0 and
            result.cache_hits == 0, "failed/incomplete reference trace")
    fixed = request.spec.resistance_ohm.minimum == request.spec.resistance_ohm.maximum and request.spec.capacitance_f.minimum == request.spec.capacitance_f.maximum
    expected_calls = 1 if request.method == "simulate" or fixed else request.spec.max_evaluations
    require(result.simulator_calls == expected_calls <= request.spec.max_evaluations, "incorrect actual call budget")
    names = expected_files(result)
    if request.method == "simulate":
        require(result.history[0].candidate == request.candidate and result.proposals == 1, "incorrect simulation candidate")
        engine = read_json(root, "engine/report.json")
        require(engine == {"method": "simulate", "history": [e.model_dump() for e in result.history]}, "engine trace mismatch")
    else:
        baseline = BaselineResult.model_validate(read_json(root, "engine/report.json"))
        require(baseline.spec == request.spec and baseline.options.method == request.method and baseline.options.seed == request.seed and
                baseline.history == result.history and baseline.best == result.best and baseline.simulator_calls == result.simulator_calls and
                baseline.proposals == result.proposals and baseline.failures == baseline.invalid_candidates == baseline.cache_hits == 0,
                "optimizer trace differs from export")
    for evaluation in result.history:
        audit_evaluation(root, "engine/evaluations/" + evaluation.artifact, request.spec, evaluation, result.ngspice_version)
    best = min(result.history, key=lambda e: (not e.target_passed, e.objective))
    require(result.best == best and result.status == ("passed" if best.target_passed else "target_missed"), "incorrect best/status")
    selected = "engine/evaluations/" + best.artifact
    for name in SELECTED_FILES:
        require(evidence_file(root, name).read_bytes() == evidence_file(root, selected + "/" + name).read_bytes(),
                "selected response/log is not the chosen real call")
    raw = parse_ac(evidence_file(root, "stdout.log").read_text(encoding="utf-8"), request.spec.source_amplitude_v, request.spec.sweep.expected_points)
    expected_waveform = Waveform(frequency_hz=tuple(raw.frequency_hz), transfer_real=tuple(raw.transfer.real),
                                transfer_imag=tuple(raw.transfer.imag), gain_db=tuple(raw.gain_db), phase_deg=tuple(raw.phase_deg))
    require(result.waveform == expected_waveform, "JSON waveform differs from raw AC output")
    with Image.open(evidence_file(root, "response.png")) as chart:
        require(chart.format == "PNG" and chart.width >= 600 and chart.height >= 400, "missing/invalid response chart")
        chart.verify()
    verify_manifest(read_json(root, "manifest.json"), names, lambda name: evidence_file(root, name).read_bytes())
    if (root / "bundle.zip").exists():
        require((root / "bundle.zip").stat().st_size <= MAX_BUNDLE_BYTES, "oversized bundled ZIP")
        with zipfile.ZipFile(root / "bundle.zip") as archive:
            infos = archive.infolist()
            require(len(infos) == len(names) + 1 and set(archive.namelist()) == names | {"manifest.json"} and
                    sum(i.file_size for i in infos) <= 64 * 1024 * 1024 and
                    all(not stat.S_ISLNK(i.external_attr >> 16) for i in infos), "unexpected bundled ZIP contents")
            require(archive.read("manifest.json") == evidence_file(root, "manifest.json").read_bytes(), "ZIP manifest differs from exported manifest")
            verify_manifest(read_json(root, "manifest.json"), names, archive.read)
    require({p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} == names | {"manifest.json"} |
            ({"bundle.zip"} if (root / "bundle.zip").exists() else set()), "untracked/missing export artifact")
    return result


def numerical_result(result: DesignResult) -> dict:
    data = result.model_dump(mode="json")
    for evaluation in [*data["history"], *([data["best"]] if data["best"] else [])]:
        evaluation.pop("elapsed_s", None)
    return data


def compare_interfaces(cli: DesignResult, api: DesignResult, archive: DesignResult) -> None:
    require(numerical_result(cli) == numerical_result(api) == numerical_result(archive), "CLI/API numerical contract mismatch")


def audit_walkthrough(source: Path, root: Path, installed_prefix: Path) -> dict:
    from circuforge.application import load_request

    summary = read_json(root, "walkthrough.json")
    module = Path(summary["installed_module"]).resolve()
    require(Path(summary["prefix"]).resolve() == installed_prefix.resolve() and module.is_file() and
            module.is_relative_to(installed_prefix.resolve()) and "site-packages" in module.parts,
            "walkthrough used source checkout instead of installed package")
    require(summary["status"] == "passed" and summary["environment"] == environment(), "installed package/source/environment mismatch")
    require(summary["server_stopped"] and summary["temporary_storage_empty"] and
            not list((root / "server-temp").iterdir()), "server or temporary files leaked")
    require(summary["health"]["service"] == "circuforge" and summary["health"]["simulator"] == "not_checked" and
            summary["health"]["max_calls"] == 8 and summary["health"]["active_design_limit"] == 1,
            "incorrect server limits/health claims")
    require(summary["rejected"] == {"unsupported_netlist": 422, "browser_origin": 403, "oversized_body": 413}, "request guard checks incomplete")
    cases = ("design-lowpass", "design-optimization", "design-target-miss")
    require(len(summary["cases"]) == len(summary["commands"]) == 3, "incomplete walkthrough")
    actual = raw = 0
    for index, name in enumerate(cases):
        request = load_request(source / (name + ".json"))
        folder = root / name
        cli = audit_design(folder / "cli", request)
        api = DesignResult.model_validate_json(evidence_file(folder, "api.json").read_bytes())
        archived = audit_design(folder / "api", request)
        compare_interfaces(cli, api, archived)
        # Audit the downloaded ZIP itself again, independently of the extracted copy.
        with zipfile.ZipFile(evidence_file(folder, "api.zip")) as archive:
            require(set(archive.namelist()) == expected_files(archived) | {"manifest.json"} and
                    len(archive.namelist()) == len(expected_files(archived)) + 1, "downloaded ZIP differs from extracted evidence")
            verify_manifest(read_json(folder / "api", "manifest.json"), expected_files(archived), archive.read)
        command = summary["commands"][index]
        require(Path(command[0]).resolve().is_relative_to(installed_prefix.resolve()) and command[1:4] == ["-I", "-m", "circuforge"],
                "CLI was not invoked in isolated installed mode")
        row = summary["cases"][index]
        expected_status = "target_missed" if name == "design-target-miss" else "passed"
        require(row == {"case": name, "status": expected_status, "calls_per_interface": cli.simulator_calls,
                        "cli_exit": 1 if expected_status == "target_missed" else 0, "json_http": 200, "zip_http": 200,
                        "zip_status": expected_status, "temporary_storage_empty": True} and cli.status == expected_status,
                "incorrect CLI/HTTP status or hidden target miss")
        actual += cli.simulator_calls * 3
        raw += cli.simulator_calls * 2
    require(summary["actual_simulator_calls"] == actual == 27 and summary["raw_calls_audited"] == raw == 18,
            "incorrect walkthrough call accounting")
    return {"status": "passed", "policy": POLICY, "acceptance_mode": "automated", "manual_review_required": False,
            "actual_simulator_calls": actual, "raw_calls_audited": raw,
            "json_interface_calls_matched": actual - raw, "installed_module": str(module),
            "environment": environment(), "outcomes": summary["cases"],
            "claim": "installed CLI and real loopback HTTP reproduced; raw CLI/ZIP evidence audited and JSON numerical traces matched; no human review asserted"}
