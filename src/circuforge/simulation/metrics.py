from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import NDArray

from circuforge.domain.specs import CircuitCandidate


@dataclass(frozen=True)
class Response:
    frequency_hz: NDArray[np.float64]
    transfer: NDArray[np.complex128]

    def __post_init__(self):
        f = np.array(self.frequency_hz, dtype=float, copy=True)
        h = np.array(self.transfer, dtype=complex, copy=True)
        if f.ndim != 1 or f.size < 2 or f.shape != h.shape:
            raise ValueError("frequency and complex transfer must be equal 1D arrays with >=2 points")
        if not np.all(np.isfinite(f)) or not np.all(np.isfinite(h)):
            raise ValueError("nonfinite AC data")
        if np.any(f <= 0) or np.any(np.diff(f) <= 0) or np.any(np.abs(h) == 0):
            raise ValueError("frequencies must be positive/increasing and transfer nonzero")
        f.setflags(write=False)
        h.setflags(write=False)
        object.__setattr__(self, "frequency_hz", f)
        object.__setattr__(self, "transfer", h)

    @property
    def gain_db(self):
        return 20 * np.log10(np.abs(self.transfer))

    @property
    def phase_deg(self):
        return np.rad2deg(np.unwrap(np.angle(self.transfer)))


def analytic_cutoff(candidate: CircuitCandidate) -> float:
    return 1 / (2 * math.pi * candidate.resistance_ohm * candidate.capacitance_f)


def analytic_response(candidate: CircuitCandidate, frequency_hz) -> Response:
    f = np.asarray(frequency_hz, dtype=float)
    normalized = 1j * f / analytic_cutoff(candidate)
    return Response(f, (1 if candidate.topology == "rc_lowpass" else normalized) / (1 + normalized))


def cutoff_hz(response: Response, topology: str = "rc_lowpass") -> float:
    """Interpolate dB versus log-frequency at half power (-3.0102999566 dB).

    The ideal unloaded template has known unity DC gain. Using the first finite
    sample as the passband would bias a sweep that starts near cutoff.
    """
    db = response.gain_db
    level = -10 * math.log10(2)
    # Batch .print rounds to ~6 significant digits, allowing tiny apparent
    # passband rises. 1e-5 dB covers that quantization, not actual peaking.
    if topology not in {"rc_lowpass", "rc_highpass"}:
        raise ValueError("unsupported topology")
    direction = -1 if topology == "rc_lowpass" else 1
    if np.any(direction * np.diff(db) < -1e-5):
        raise ValueError("expected monotone RC gain")
    crossings = np.flatnonzero((direction * (db[:-1] - level) <= 0) &
                              (direction * (db[1:] - level) >= 0))
    if crossings.size != 1:
        raise ValueError("sweep does not uniquely bracket the half-power cutoff")
    i = int(crossings[0])
    weight = (level - db[i]) / (db[i + 1] - db[i])
    return float(np.exp(np.log(response.frequency_hz[i]) + weight * np.log(response.frequency_hz[i + 1] / response.frequency_hz[i])))
