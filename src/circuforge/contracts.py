"""Shared typed CLI/API contract; requests contain circuit values, never paths."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from circuforge.domain.specs import CircuitCandidate, DesignSpec, Model
from circuforge.optimization.base import Evaluation

MAX_REQUEST_BYTES = 16 * 1024


class DesignRequest(Model):
    spec: DesignSpec
    method: Literal["simulate", "random", "grid", "scipy", "analytic_rc"] = "simulate"
    seed: Annotated[int, Field(strict=True, ge=0, le=2**32 - 1)] = 42
    candidate: CircuitCandidate | None = None

    @model_validator(mode="after")
    def bounded_operation(self):
        if self.spec.max_evaluations > 32 or self.spec.timeout_s > 5 or self.spec.max_evaluations * self.spec.timeout_s > 60:
            raise ValueError("design export requires <=32 calls, <=5 seconds/call and <=60 seconds configured simulator time")
        if self.spec.sweep.expected_points > 2000:
            raise ValueError("design export requires <=2000 AC samples")
        if self.method == "simulate":
            if self.candidate is None:
                raise ValueError("simulate requires an explicit candidate")
            self.spec.validate_candidate(self.candidate)
        elif self.candidate is not None:
            raise ValueError("optimizer requests must not supply a candidate")
        return self


Finite = Annotated[float, Field(allow_inf_nan=False)]
Vector = Annotated[tuple[Finite, ...], Field(min_length=2, max_length=2000)]


class Waveform(Model):
    frequency_hz: Vector
    transfer_real: Vector
    transfer_imag: Vector
    gain_db: Vector
    phase_deg: Vector

    @model_validator(mode="after")
    def aligned(self):
        if len({len(getattr(self, f)) for f in type(self).model_fields}) != 1:
            raise ValueError("waveform columns must have equal lengths")
        if self.frequency_hz[0] <= 0 or any(a >= b for a, b in zip(self.frequency_hz, self.frequency_hz[1:])):
            raise ValueError("frequency samples must be positive and strictly increasing")
        return self


class DesignResult(Model):
    status: Literal["passed", "target_missed", "simulation_failed"]
    request: DesignRequest
    best: Evaluation | None
    history: tuple[Evaluation, ...]
    simulator_calls: int
    proposals: int
    cache_hits: int
    failures: int
    environment: dict
    ngspice_version: str
    waveform: Waveform | None
    assumptions: tuple[str, ...] = ("ideal zero-ohm source", "infinite load", "ideal continuous R/C")
    cutoff_method: str = "half-power (-10*log10(2) dB), linear dB interpolation in log frequency"


class ServiceError(Model):
    code: str
    message: str
