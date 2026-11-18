"""Deterministic bisection along the log R/C bounds using measured cutoffs."""

from dataclasses import dataclass
import math

from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.simulation.metrics import cutoff_hz
from circuforge.simulation.ngspice import Ngspice, SimulationResult


@dataclass(frozen=True)
class SearchResult:
    candidate: CircuitCandidate
    simulation: SimulationResult
    measured_cutoff_hz: float
    relative_error: float
    simulator_calls: int
    converged: bool
    history: tuple[dict, ...]


def search(spec: DesignSpec, simulator: Ngspice) -> SearchResult:
    """Cap calls, keep every candidate inside bounds, never substitute analytic data.

    Along this path R*C is monotone and spans the entire continuous feasible
    product interval. The analytic model only brackets candidates inside the
    configured sweep; every objective value comes from ngspice.
    """
    log_r = math.log(spec.resistance_ohm.minimum)
    log_c = math.log(spec.capacitance_f.minimum)
    dr = math.log(spec.resistance_ohm.maximum) - log_r
    dc = math.log(spec.capacitance_f.maximum) - log_c
    span = dr + dc
    log_fc_max = -math.log(2 * math.pi) - log_r - log_c
    lo, hi = 0.0, 1.0
    if span > 0:
        lo = max(lo, (log_fc_max - math.log(spec.sweep.stop_hz)) / span)
        hi = min(hi, (log_fc_max - math.log(spec.sweep.start_hz)) / span)
    history = []
    best = None
    seen = set()
    for _ in range(spec.max_evaluations):
        t = (lo + hi) / 2
        candidate = CircuitCandidate(
            topology=spec.filter_type,
            resistance_ohm=min(spec.resistance_ohm.maximum, max(spec.resistance_ohm.minimum, math.exp(log_r + t * dr))),
            capacitance_f=min(spec.capacitance_f.maximum, max(spec.capacitance_f.minimum, math.exp(log_c + t * dc))),
        )
        key = (candidate.resistance_ohm, candidate.capacitance_f)
        if key in seen:
            break
        seen.add(key)
        result = simulator.simulate(spec, candidate)
        measured = cutoff_hz(result.response, candidate.topology)
        error = abs(measured / spec.cutoff_hz - 1)
        history.append({"candidate": candidate.model_dump(), "measured_cutoff_hz": measured,
                        "relative_error": error, "elapsed_s": result.elapsed_s,
                        "returncode": result.returncode})
        if best is None or error < best[3]:
            best = (candidate, result, measured, error)
        if error <= spec.relative_error_tolerance:
            break
        if measured > spec.cutoff_hz:
            lo = t
        else:
            hi = t
    assert best is not None  # at least one permitted evaluation
    return SearchResult(*best, len(history), best[3] <= spec.relative_error_tolerance, tuple(history))
