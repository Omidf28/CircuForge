"""Empirical finite-sample summaries, distinct from confidence guarantees."""
import numpy as np

from circuforge.optimization.base import Evaluation


def empirical_statistics(evaluations: list[Evaluation]) -> dict:
    """Linear empirical quantiles; failed samples cannot silently disappear."""
    if len(evaluations) < 2 or any(not e.verified or e.status != "evaluated" for e in evaluations):
        raise ValueError("statistics require at least two independently verified measurements; failures block them")
    values = np.asarray([[e.measured_cutoff_hz, e.relative_error, e.objective] for e in evaluations], dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("statistics require finite measurements")
    quantiles = np.quantile(values, [.05, .5, .95], axis=0, method="linear")
    return {"samples": len(evaluations), "quantile_method": "linear",
            "cutoff_hz": dict(zip(("q05", "q50", "q95"), quantiles[:, 0].tolist())),
            "relative_error": dict(zip(("q05", "q50", "q95"), quantiles[:, 1].tolist())),
            "log_error_q95": float(quantiles[2, 2]),
            "target_passes": sum(e.target_passed for e in evaluations),
            "pass_rate": sum(e.target_passed for e in evaluations) / len(evaluations)}
