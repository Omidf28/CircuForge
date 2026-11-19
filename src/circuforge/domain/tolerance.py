"""Declared component variability; no manufacturing or correlation inference."""
from typing import Annotated, Literal

import numpy as np
from pydantic import Field

from circuforge.domain.specs import CircuitCandidate, Model

Seed = Annotated[int, Field(strict=True, ge=0, le=2**32 - 1)]
Fraction = Annotated[float, Field(strict=True, ge=0, le=.2, allow_inf_nan=False)]


class ToleranceModel(Model):
    distribution: Literal["independent_uniform"] = "independent_uniform"
    resistance_fraction: Fraction = .01
    capacitance_fraction: Fraction = .05


class SamplingPlan(Model):
    seed: Seed
    samples: Annotated[int, Field(strict=True, ge=2, le=256)]
    stream: Literal["training", "holdout"]


def sample_factors(model: ToleranceModel, plan: SamplingPlan) -> np.ndarray:
    stream = 1 if plan.stream == "training" else 2
    rng = np.random.default_rng(np.random.SeedSequence([plan.seed, stream]))
    half_widths = np.array([model.resistance_fraction, model.capacitance_fraction])
    return 1 + rng.uniform(-1., 1., (plan.samples, 2)) * half_widths


def perturb(candidate: CircuitCandidate, factors) -> CircuitCandidate:
    values = np.asarray(factors, dtype=float)
    if values.shape != (2,) or not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("provide two finite positive multiplicative component factors")
    return CircuitCandidate(topology=candidate.topology,
                            resistance_ohm=candidate.resistance_ohm * float(values[0]),
                            capacitance_f=candidate.capacitance_f * float(values[1]))
