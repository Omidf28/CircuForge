"""No arbitrary netlists or shell; isolated fixed-template ngspice runs."""

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

import numpy as np

from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.simulation.metrics import Response
from circuforge.synthesis.rc import netlist

MAX_OUTPUT_BYTES = 8 * 1024 * 1024


class SimulationError(RuntimeError):
    def __init__(self, status: str, message: str, *, stdout="", stderr="", returncode=None):
        super().__init__(message)
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def executable_path(override: str | None = None) -> str:
    requested = override or os.environ.get("CIRCUFORGE_NGSPICE") or "ngspice"
    resolved = shutil.which(requested)
    if not resolved or Path(resolved).suffix.lower() in {".bat", ".cmd", ".ps1"}:
        raise SimulationError("unavailable", "ngspice executable unavailable; install ngspice and add its bin directory to PATH or set CIRCUFORGE_NGSPICE to the executable path")
    return str(Path(resolved).resolve())


def _clean(text: str, workdir: str) -> str:
    text = text.replace(workdir, "<temporary-workspace>")
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)


def _execute(executable: str, args: list[str], workdir: str, timeout: float):
    """Spool output to disk; poll size and wall-clock to bound runaway output.

    This is a local trusted executable guard, not an OS security sandbox.
    -n disables user/system .spiceinit startup commands.
    """
    started = time.monotonic()
    paths = [Path(workdir) / "stdout.log", Path(workdir) / "stderr.log"]
    with paths[0].open("wb") as out, paths[1].open("wb") as err:
        try:
            process = subprocess.Popen([executable, *args], cwd=workdir, stdin=subprocess.DEVNULL,
                                       stdout=out, stderr=err, shell=False,
                                       env={**os.environ, "LC_ALL": "C", "LANG": "C", "TERM": "dumb"})
        except OSError as exc:
            raise SimulationError("launch_error", str(exc)) from exc
        status = None
        try:
            while process.poll() is None:
                if time.monotonic() - started > timeout:
                    status = "timeout"
                    break
                if sum(p.stat().st_size for p in paths) > MAX_OUTPUT_BYTES:
                    status = "output_limit"
                    break
                time.sleep(0.01)
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
    if sum(p.stat().st_size for p in paths) > MAX_OUTPUT_BYTES:
        status = status or "output_limit"
    logs = []
    for path in paths:
        with path.open("rb") as stream:
            logs.append(_clean(stream.read(MAX_OUTPUT_BYTES).decode("utf-8", errors="replace"), workdir))
    stdout, stderr = logs
    if status or process.returncode != 0:
        raise SimulationError(status or "nonzero_exit", f"ngspice {status or 'nonzero exit'} ({process.returncode})",
                              stdout=stdout, stderr=stderr, returncode=process.returncode)
    return stdout, stderr, process.returncode, time.monotonic() - started


@dataclass(frozen=True)
class Preflight:
    executable: str
    version: str


def preflight(override: str | None = None) -> Preflight:
    executable = executable_path(override)
    with tempfile.TemporaryDirectory(prefix="circuforge-check-") as workdir:
        stdout, stderr, _, _ = _execute(executable, ["-n", "--version"], workdir, 5.0)
    version = stdout.strip() or stderr.strip()
    if "ngspice" not in version.lower():
        raise SimulationError("invalid_executable", "version output does not identify ngspice")
    return Preflight(executable, version)


def parse_ac(text: str, amplitude_v: float, expected_points: int) -> Response:
    """Read the single .print AC table (index, frequency, real, imaginary)."""
    if not np.isfinite(amplitude_v) or amplitude_v <= 0:
        raise ValueError("source amplitude must be positive and finite")
    rows = []
    table = False
    for line in text.splitlines():
        fields = line.split()
        if fields and fields[0].lower() == "index":
            if [x.lower() for x in fields[1:]] != ["frequency", "vr(out)", "vi(out)"]:
                raise ValueError("unexpected AC table columns")
            table = True
        elif table and fields and fields[0].isdigit():
            if len(fields) != 4 or int(fields[0]) != len(rows):
                raise ValueError("malformed or discontinuous AC row")
            try:
                rows.append([float(x.replace("D", "E").replace("d", "e")) for x in fields[1:]])
            except ValueError as exc:
                raise ValueError("invalid numeric AC data") from exc
    if len(rows) != expected_points:
        raise ValueError(f"expected {expected_points} AC points, received {len(rows)}")
    data = np.asarray(rows)
    return Response(data[:, 0], (data[:, 1] + 1j * data[:, 2]) / amplitude_v)


@dataclass(frozen=True)
class SimulationResult:
    response: Response
    netlist: str
    executable: str
    version: str
    command: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int
    elapsed_s: float
    status: str = "success"


class Ngspice:
    def __init__(self, executable: str | None = None):
        self.info = preflight(executable)

    def simulate(self, spec: DesignSpec, candidate: CircuitCandidate) -> SimulationResult:
        text = netlist(spec, candidate)
        args = ["-n", "-b", "circuit.cir"]
        with tempfile.TemporaryDirectory(prefix="circuforge-run-") as workdir:
            (Path(workdir) / "circuit.cir").write_text(text, encoding="ascii")
            stdout, stderr, code, elapsed = _execute(self.info.executable, args, workdir, spec.timeout_s)
        try:
            response = parse_ac(stdout, spec.source_amplitude_v, spec.sweep.expected_points)
            nominal_grid = spec.sweep.start_hz * np.power(
                10.0, np.arange(spec.sweep.expected_points) / spec.sweep.points_per_decade
            )
            # ngspice-47 distributes noninteger-decade sweeps across both
            # endpoints. Also accept the traditional fixed decade step grid.
            endpoint_grid = np.geomspace(spec.sweep.start_hz, spec.sweep.stop_hz,
                                        spec.sweep.expected_points)
            # Check the full requested grid; no absolute tolerance that could
            # hide large relative errors in very low frequency sweeps.
            if not any(np.allclose(response.frequency_hz, grid, rtol=1e-6, atol=0.0)
                       for grid in (nominal_grid, endpoint_grid)):
                raise ValueError("AC output does not match the requested frequency grid")
        except ValueError as exc:
            raise SimulationError("parse_error", str(exc), stdout=stdout, stderr=stderr, returncode=code) from exc
        return SimulationResult(response, text, self.info.executable, self.info.version,
                                (self.info.executable, *args), stdout, stderr, code, elapsed)
