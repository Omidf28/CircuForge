"""One measured design/export use case shared by CLI and the loopback API."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from circuforge.contracts import MAX_REQUEST_BYTES, DesignRequest, DesignResult, Waveform
from circuforge.evaluation.records import environment
from circuforge.optimization.base import Evaluator
from circuforge.optimization.baselines import run_baseline
from circuforge.simulation.ngspice import Ngspice, parse_ac

MAX_BUNDLE_BYTES = 8 * 1024 * 1024
SELECTED_FILES = ("circuit.cir", "stdout.log", "stderr.log", "response.csv")


def load_request(path: Path) -> DesignRequest:
    with path.open("rb") as stream:
        data = stream.read(MAX_REQUEST_BYTES + 1)
    if len(data) > MAX_REQUEST_BYTES:
        raise ValueError("request exceeds 16 KiB limit")
    return DesignRequest.model_validate_json(data)


def plot_waveform(waveform: Waveform, measured_hz: float, target_hz: float, destination: Path) -> None:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(9, 6), layout="constrained")
    FigureCanvasAgg(fig)
    axes = fig.subplots(2, 1, sharex=True)
    axes[0].semilogx(waveform.frequency_hz, waveform.gain_db, label="measured ngspice")
    axes[1].semilogx(waveform.frequency_hz, waveform.phase_deg)
    for axis in axes:
        axis.axvline(measured_hz, color="#d97706", linestyle="--", label="measured cutoff")
        axis.axvline(target_hz, color="#16a34a", linestyle=":", label="target")
        axis.grid(True, which="both", alpha=.2)
    axes[0].set_ylabel("Gain (dB)")
    axes[1].set_ylabel("Phase (degrees)")
    axes[1].set_xlabel("Frequency (Hz)")
    axes[0].legend()
    fig.suptitle("Ideal RC response from recorded AC samples")
    fig.savefig(destination, dpi=140)


def export_bundle(output: Path) -> None:
    files = sorted(p for p in output.rglob("*") if p.is_file() and p.name not in {"manifest.json", "bundle.zip"})
    if len(files) > 256 or sum(p.stat().st_size for p in files) > 64 * 1024 * 1024:
        raise ValueError("artifact export exceeds file/size limits")
    entries = []
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(output.resolve()):
            raise ValueError("unsafe export artifact")
        entries.append({"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = {"format": "circuforge-design-v1", "files": entries}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(output / "bundle.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for entry in entries:
            archive.write(output / entry["path"], entry["path"])
        archive.write(output / "manifest.json", "manifest.json")
    if (output / "bundle.zip").stat().st_size > MAX_BUNDLE_BYTES:
        raise ValueError("compressed export exceeds 8 MiB limit")


def run_design(request: DesignRequest, simulator: Ngspice, output: Path) -> DesignResult:
    import matplotlib  # check optional export dependency before allocation/simulation

    output.mkdir(parents=True, exist_ok=False)
    (output / "request.json").write_text(request.model_dump_json(indent=2) + "\n", encoding="utf-8")
    engine = output / "engine"
    if request.method == "simulate":
        engine.mkdir()
        evaluator = Evaluator(request.spec, simulator, engine / "evaluations")
        evaluator.evaluate(request.candidate)
        history, best = tuple(evaluator.history), evaluator.best
        calls, proposals, hits = evaluator.calls, evaluator.proposals, evaluator.cache_hits
        (engine / "report.json").write_text(json.dumps({"method": "simulate", "history": [e.model_dump() for e in history]}, indent=2) + "\n", encoding="utf-8")
    else:
        baseline = run_baseline(request.spec, simulator, request.method, seed=request.seed, output=engine)
        history, best = baseline.history, baseline.best
        calls, proposals, hits = baseline.simulator_calls, baseline.proposals, baseline.cache_hits
    failures = sum(not e.verified for e in history)
    status = "simulation_failed" if failures or best is None else "passed" if best.target_passed else "target_missed"
    waveform = None
    if best is not None:
        selected = engine / "evaluations" / best.artifact
        for name in SELECTED_FILES:
            shutil.copy2(selected / name, output / name)
        response = parse_ac((output / "stdout.log").read_text(encoding="utf-8"),
                            request.spec.source_amplitude_v, request.spec.sweep.expected_points)
        waveform = Waveform(frequency_hz=tuple(response.frequency_hz), transfer_real=tuple(response.transfer.real),
                            transfer_imag=tuple(response.transfer.imag), gain_db=tuple(response.gain_db), phase_deg=tuple(response.phase_deg))
        plot_waveform(waveform, best.measured_cutoff_hz, request.spec.cutoff_hz, output / "response.png")
    result = DesignResult(status=status, request=request, best=best, history=history, simulator_calls=calls,
                          proposals=proposals, cache_hits=hits, failures=failures, environment=environment(),
                          ngspice_version=simulator.info.version, waveform=waveform)
    (output / "report.json").write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    export_bundle(output)
    return result
