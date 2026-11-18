"""Render saved genuine AC data; plotting is optional developer tooling."""
from pathlib import Path
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True, layout="constrained")
for family, label in [("lowpass", "RC low-pass"), ("highpass", "RC high-pass")]:
    path = root / "evidence" / f"{family}-2026-11-18" / "response.csv"
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    f = [float(row["frequency_hz"]) for row in rows]
    axes[0].semilogx(f, [float(row["gain_db"]) for row in rows], label=label)
    axes[1].semilogx(f, [float(row["phase_deg"]) for row in rows], label=label)
axes[0].axhline(-3.0102999566, color="gray", linestyle=":", label="Half power")
axes[0].set(ylabel="Gain (dB)", title="CircuForge: genuine ngspice-47 AC response\n1 kohm / 100 nF; ideal source, infinite load")
axes[1].set(xlabel="Frequency (Hz)", ylabel="Phase (degrees)")
for ax in axes:
    ax.grid(True, which="both", alpha=.25)
    ax.axvline(1591.549430919, color="gray", linestyle="--", alpha=.6)
axes[0].legend()
fig.savefig(root / "evidence/rc-responses.png", dpi=160)
