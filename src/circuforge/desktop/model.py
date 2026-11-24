"""Typed desktop input and a single background job, independent of Tk widgets."""
from dataclasses import dataclass
from datetime import datetime
import math
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Callable
from uuid import uuid4

from circuforge.application import run_design
from circuforge.contracts import DesignRequest, DesignResult
from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.simulation.metrics import analytic_cutoff
from circuforge.simulation.ngspice import Ngspice

TOPOLOGIES = {"Low-pass": "rc_lowpass", "High-pass": "rc_highpass"}
MODES = ("Analytic design", "Simulate R/C")


@dataclass(frozen=True)
class FormValues:
    topology: str = "Low-pass"
    mode: str = MODES[0]
    target_hz: str = "2300"
    tolerance_pct: str = "0.1"
    r_min_ohm: str = "100"
    r_max_ohm: str = "10000"
    c_min_nf: str = "10"
    c_max_nf: str = "1000"
    resistance_ohm: str = "1000"
    capacitance_nf: str = "100"


def number(value: str, label: str) -> float:
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{label}: enter a positive number (scientific notation is supported)") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{label}: enter a finite number greater than zero")
    return result


def build_request(values: FormValues) -> DesignRequest:
    """Convert explicitly labeled ohm/nF/percent fields to the existing SI contract."""
    if values.topology not in TOPOLOGIES or values.mode not in MODES:
        raise ValueError("Choose a supported RC filter and design mode")
    target = number(values.target_hz, "Target cutoff")
    topology = TOPOLOGIES[values.topology]
    candidate = None
    if values.mode == "Simulate R/C":
        candidate = CircuitCandidate(topology=topology,
                                     resistance_ohm=number(values.resistance_ohm, "Resistance"),
                                     capacitance_f=number(values.capacitance_nf, "Capacitance") * 1e-9)
        # The chosen candidate may miss the target; broad physical bounds permit
        # measuring that miss without relabeling it as an infeasible search.
        resistance = {"minimum": 1e-3, "maximum": 1e12}
        capacitance = {"minimum": 1e-15, "maximum": 1.0}
        reference = analytic_cutoff(candidate)
    else:
        resistance = {"minimum": number(values.r_min_ohm, "Minimum resistance"),
                      "maximum": number(values.r_max_ohm, "Maximum resistance")}
        capacitance = {"minimum": number(values.c_min_nf, "Minimum capacitance") * 1e-9,
                       "maximum": number(values.c_max_nf, "Maximum capacitance") * 1e-9}
        reference = target
    start = max(1e-9, min(target, reference) / 100)
    stop = min(1e15, max(target, reference) * 100)
    if not start < target < stop:
        raise ValueError("Target cutoff must lie strictly between 1e-9 and 1e15 Hz")
    density = max(10, min(100, math.floor(1000 / math.log10(stop / start))))
    spec = DesignSpec(filter_type=topology, cutoff_hz=target,
                      resistance_ohm=resistance, capacitance_f=capacitance,
                      relative_error_tolerance=number(values.tolerance_pct, "Allowed error (%)") / 100,
                      max_evaluations=1, timeout_s=2.0,
                      sweep={"start_hz": start, "stop_hz": stop, "points_per_decade": density})
    return DesignRequest(spec=spec, method="simulate" if candidate else "analytic_rc", candidate=candidate)


def validate_desktop_request(request: DesignRequest) -> DesignRequest:
    request = DesignRequest.model_validate(request.model_dump())
    if (request.method not in {"simulate", "analytic_rc"} or request.spec.max_evaluations != 1 or
            request.spec.timeout_s > 2 or request.spec.sweep.expected_points > 1001):
        raise ValueError("Desktop runs require simulate/analytic_rc, one call, <=2 seconds/call and <=1001 AC samples")
    return request


def execute_run(request: DesignRequest, output: Path, executable: str | None) -> DesignResult:
    request = validate_desktop_request(request)
    simulator = Ngspice(executable)
    output.parent.mkdir(parents=True, exist_ok=True)
    return run_design(request, simulator, output)


@dataclass(frozen=True)
class RunEvent:
    output: Path
    result: DesignResult | None = None
    error: str | None = None


class RunController:
    """One job at a time; the worker never reads or writes a Tk object.

    start/poll belong to the UI thread. Busy stays true until the UI consumes the
    completion, even if the worker has already stopped. Closing waits for this
    bounded simulation rather than interrupting evidence export.
    """
    def __init__(self, runner: Callable = execute_run):
        self._runner = runner
        self._events: Queue[RunEvent] = Queue(maxsize=1)
        self.busy = False

    def start(self, request: DesignRequest, root: Path, executable: str | None = None) -> Path:
        if self.busy:
            raise RuntimeError("A simulation is already running")
        request = validate_desktop_request(request)
        root = root.expanduser().resolve()
        output = root / f"run-{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:10]}"
        self.busy = True

        def work():
            try:
                event = RunEvent(output, result=self._runner(request, output, executable))
            except Exception as exc:
                event = RunEvent(output, error=f"{type(exc).__name__}: {exc}")
            self._events.put(event)

        try:
            Thread(target=work, name="circuforge-desktop-design", daemon=True).start()
        except RuntimeError:
            self.busy = False
            raise
        return output

    def poll(self) -> RunEvent | None:
        try:
            event = self._events.get_nowait()
        except Empty:
            return None
        self.busy = False
        return event
