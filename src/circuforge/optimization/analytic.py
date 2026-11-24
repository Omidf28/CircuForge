"""A closed-form proposal for ideal unloaded, continuous first-order RC filters."""
import math

from circuforge.domain.specs import CircuitCandidate, DesignSpec


def analytic_candidate(spec: DesignSpec) -> CircuitCandidate:
    """Choose the closest feasible RC product and a deterministic geometric R split.

    Feasibility may be tolerance-only: clamp to the achievable product interval.
    Final bound clamping absorbs floating-point endpoint drift. This is only a
    proposal; a measured evaluation must independently verify and accept it.
    """
    if not isinstance(spec, DesignSpec):
        raise TypeError("analytic RC proposal requires a validated DesignSpec")
    spec = DesignSpec.model_validate(spec.model_dump())
    r, c = spec.resistance_ohm, spec.capacitance_f
    requested = 1.0 / (2.0 * math.pi * spec.cutoff_hz)
    product = min(r.maximum * c.maximum, max(r.minimum * c.minimum, requested))
    if product == r.minimum * c.minimum:
        resistance, capacitance = r.minimum, c.minimum
    elif product == r.maximum * c.maximum:
        resistance, capacitance = r.maximum, c.maximum
    else:
        lower = max(r.minimum, product / c.maximum)
        upper = min(r.maximum, product / c.minimum)
        resistance = min(r.maximum, max(r.minimum, math.sqrt(lower * upper)))
        capacitance = min(c.maximum, max(c.minimum, product / resistance))
    candidate = CircuitCandidate(topology=spec.filter_type, resistance_ohm=resistance,
                                 capacitance_f=capacitance)
    spec.validate_candidate(candidate)
    return candidate
