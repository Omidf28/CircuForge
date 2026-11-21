"""Export descriptive matched-call data as CSV/PNG; no inference or simulation."""
import argparse
import csv
import json
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new report directory")
    args = parser.parse_args(argv)
    result = json.loads((args.input / "result.json").read_text(encoding="utf-8"))
    methods = ("random", "grid", "scipy", "local_ollama")
    rows, matrix, labels = [], [], []
    for trial in result["trials"]:
        records = {record["method"]: record for record in trial["results"]}
        if set(records) != set(methods) or any(records[method]["simulator_calls"] != 4 for method in methods):
            continue  # Never present a partial trial as a matched-call performance comparison.
        values = []
        for method in methods:
            record = records[method]
            if record["best"] is None:
                raise ValueError("matched trial contains no verified result")
            error = record["best"]["relative_error"]
            values.append(error * 100)
            rows.append(dict(case=trial["case"], seed=trial["seed"], method=method,
                             actual_spice_calls=record["simulator_calls"],
                             best_relative_error=error, target_passed=record["best"]["target_passed"]))
        matrix.append(values)
        labels.append(trial["case"].replace("local-", "") + f" / seed {trial['seed']}")
    if not rows:
        raise ValueError("no complete matched-call trials to plot")
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "matched-comparisons.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(figsize=(9, 5.8), layout="constrained")
    heatmap = axes.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=100, aspect="auto")
    axes.set_xticks(range(4), ["Random", "Grid", "SciPy", "Local Llama 3"])
    axes.set_yticks(range(len(labels)), labels)
    for y, values in enumerate(matrix):
        for x, value in enumerate(values):
            axes.text(x, y, f"{value:.2f}%", ha="center", va="center", color="white" if value > 60 else "black")
    figure.colorbar(heatmap, ax=axes, label="Best relative cutoff error (%) — lower is better")
    axes.set_title("RC pilot: four actual SPICE calls per method\nTarget tolerance 0.1%; descriptive results only", pad=15)
    figure.supxlabel("Two topologies / two seeds; model runtime is additional; final replay checks incomplete", fontsize=9)
    figure.savefig(args.output / "matched-comparisons.png", dpi=180)
    plt.close(figure)
    print(f"Exported {len(rows)} measured method records in {len(matrix)} matched-call trials.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
