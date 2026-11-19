"""Standalone scientific plot of audited empirical outcomes; optional dependency."""
from pathlib import Path

import numpy as np


def plot_comparison(summary: dict, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    rows = summary["trials"]
    pairs = list(dict.fromkeys((r["case"], r["seed"]) for r in rows))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    x = np.arange(len(pairs))
    for offset, method, color in ((-.18, "nominal", "#2563eb"), (.18, "robust", "#d97706")):
        group = [next(r for r in rows if (r["case"], r["seed"]) == key and r["method"] == method) for key in pairs]
        if any(r["holdout_statistics"] is None for r in group):
            raise ValueError("cannot plot incomplete/failed holdout statistics")
        axes[0].bar(x + offset, [100 * r["holdout_statistics"]["relative_error"]["q95"] for r in group],
                    width=.34, label=method, color=color)
        axes[1].bar(x + offset, [100 * r["holdout_statistics"]["pass_rate"] for r in group],
                    width=.34, label=method, color=color)
    for axis in axes:
        axis.set_xticks(x, [f"{case}\nseed {seed}" for case, seed in pairs])
        axis.grid(axis="y", alpha=.2)
        axis.set_axisbelow(True)
    axes[0].set_ylabel("Holdout 95th-percentile target error (%)")
    axes[1].set_ylabel("Holdout empirical target pass rate (%)")
    axes[1].set_ylim(0, 100)
    axes[0].legend()
    fig.suptitle("Declared independent R/C tolerances; matched total SPICE budgets")
    fig.savefig(output, dpi=160)
    plt.close(fig)
