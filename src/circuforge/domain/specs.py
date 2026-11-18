"""SI units only; ideal voltage source and infinite load are explicit."""

import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Positive = Annotated[float, Field(gt=0, allow_inf_nan=False, strict=True)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class Bounds(Model):
    minimum: Positive
    maximum: Positive

    @model_validator(mode="after")
    def ordered(self):
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class Sweep(Model):
    start_hz: Positive = 1.0
    stop_hz: Positive = 1e6
    points_per_decade: Annotated[int, Field(strict=True, ge=10, le=1000)] = 100

    @model_validator(mode="after")
    def bounded(self):
        if not 1e-9 <= self.start_hz < self.stop_hz <= 1e15:
            raise ValueError("sweep must satisfy 1e-9 <= start < stop <= 1e15 Hz")
        if self.expected_points < 2:
            raise ValueError("sweep must contain at least two frequency samples")
        if self.expected_points > 20000:
            raise ValueError("sweep exceeds 20000 point budget")
        return self

    @property
    def expected_points(self) -> int:
        return math.floor(math.log10(self.stop_hz / self.start_hz) * self.points_per_decade + 1e-8) + 1


class CircuitCandidate(Model):
    topology: Literal["rc_lowpass", "rc_highpass"] = "rc_lowpass"
    resistance_ohm: Positive = 1000.0
    capacitance_f: Positive = 100e-9

    @model_validator(mode="after")
    def physical_range(self):
        if not 1e-3 <= self.resistance_ohm <= 1e12:
            raise ValueError("resistance must be in [1e-3, 1e12] ohm")
        if not 1e-15 <= self.capacitance_f <= 1.0:
            raise ValueError("capacitance must be in [1e-15, 1] F")
        return self


class DesignSpec(Model):
    filter_type: Literal["rc_lowpass", "rc_highpass"] = "rc_lowpass"
    cutoff_hz: Positive = 1591.5494309189535
    source_amplitude_v: Annotated[float, Field(strict=True, gt=0, le=1000, allow_inf_nan=False)] = 1.0
    source_impedance_ohm: Literal[0.0] = 0.0
    load: Literal["infinite"] = "infinite"
    value_policy: Literal["continuous"] = "continuous"
    resistance_ohm: Bounds = Bounds(minimum=10.0, maximum=1e6)
    capacitance_f: Bounds = Bounds(minimum=1e-12, maximum=1e-3)
    relative_error_tolerance: Annotated[float, Field(strict=True, gt=0, le=0.1, allow_inf_nan=False)] = 0.001
    max_evaluations: Annotated[int, Field(strict=True, ge=1, le=1000)] = 32
    timeout_s: Annotated[float, Field(strict=True, gt=0, le=30, allow_inf_nan=False)] = 10.0
    sweep: Sweep = Sweep()

    @model_validator(mode="after")
    def feasible(self):
        CircuitCandidate(resistance_ohm=self.resistance_ohm.minimum, capacitance_f=self.capacitance_f.minimum)
        CircuitCandidate(resistance_ohm=self.resistance_ohm.maximum, capacitance_f=self.capacitance_f.maximum)
        low = 1 / (2 * math.pi * self.resistance_ohm.maximum * self.capacitance_f.maximum)
        high = 1 / (2 * math.pi * self.resistance_ohm.minimum * self.capacitance_f.minimum)
        if not low <= self.cutoff_hz <= high:
            raise ValueError(f"target infeasible within R/C bounds: achievable cutoff [{low:g}, {high:g}] Hz")
        if not self.sweep.start_hz < self.cutoff_hz < self.sweep.stop_hz:
            raise ValueError("target cutoff must be inside the sweep")
        return self

    def validate_candidate(self, candidate: CircuitCandidate) -> None:
        if not isinstance(candidate, CircuitCandidate):
            raise TypeError("candidate must be a validated CircuitCandidate")
        if candidate.topology != self.filter_type:
            raise ValueError("candidate topology does not match spec")
        for value, bounds, unit in [(candidate.resistance_ohm, self.resistance_ohm, "ohm"),
                                     (candidate.capacitance_f, self.capacitance_f, "F")]:
            if not bounds.minimum <= value <= bounds.maximum:
                raise ValueError(f"candidate {value:g} {unit} is outside the permitted bounds")
