"""Reconcile stored research evidence and export a report; no inference or SPICE."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from circuforge.evaluation.acceptance import require, validate_junit
from circuforge.evaluation.benchmark import aggregate

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numerical_rows(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if k != "wall_s"} for row in rows]


def accepted_dataset(root: Path, manifest: Path, policy: str) -> tuple[dict, dict, list[Path]]:
    """Check historical summary/test bindings; this is not a fresh raw physics audit."""
    acceptance = read(root / "acceptance.json")
    require(acceptance["status"] == "passed" and acceptance["policy"] == policy,
            "missing accepted historical policy")
    require(acceptance["acceptance_mode"] == "automated", "unexpected acceptance mode")
    require(validate_junit(root / "tests.xml") == acceptance["tests_passed"],
            "historical test count differs from evidence")
    batches = [read(root / name / "summary.json") for name in ("first", "replay")]
    for batch in batches:
        require(batch["manifest_sha256"] == sha256(manifest), "changed experiment manifest")
        require(batch["completed_trials"] == batch["planned_trials"] == len(batch["trials"]) == acceptance["trials"],
                "incomplete historical trial summary")
        require(batch["actual_calls"] == acceptance["audited_calls"] ==
                sum(row["simulator_calls"] for row in batch["trials"]), "historical call mismatch")
        require(all(row["failures"] == 0 for row in batch["trials"]), "historical simulation failure")
        identities = {(row["case"], row["seed"], row["method"]) for row in batch["trials"]}
        require(len(identities) == len(batch["trials"]), "duplicate historical trial")
    require(numerical_rows(batches[0]["trials"]) == numerical_rows(batches[1]["trials"]),
            "historical numerical summaries do not replay")
    require(batches[0]["environment"] == batches[1]["environment"], "replay environment differs")
    require(acceptance["audited_calls_including_replay"] == 2 * acceptance["audited_calls"],
            "incorrect replay-inclusive call count")
    paths = [manifest, root / "acceptance.json", root / "tests.xml",
             root / "first/summary.json", root / "replay/summary.json"]
    return acceptance, batches[0], paths


def collect(benchmark: Path, robustness: Path, local: Path, replay_supplement: Path | None = None) -> dict:
    nominal_manifest = ROOT / "examples/benchmark-v2.json"
    robust_manifest = ROOT / "examples/robustness-v1.json"
    nominal, batch, paths = accepted_dataset(benchmark, nominal_manifest, "phase3-reproducibility-v2")
    aggregates = aggregate(batch["trials"])
    require(aggregates == batch["aggregates"], "benchmark aggregates differ from trials")
    require(sum(row["design_passes"] for row in aggregates.values()) == nominal["design_passes"] and
            sum(row["design_misses"] for row in aggregates.values()) == nominal["design_misses"] and
            sum(row["infeasible_rejections"] for row in aggregates.values()) == nominal["infeasible_rejections"],
            "benchmark outcome counts differ from acceptance")
    cases = {case["id"]: case["inputs"] for case in read(nominal_manifest)["cases"]}
    fixed_passes = sum(row["converged"] and all(cases[row["case"]][part]["minimum"] ==
                       cases[row["case"]][part]["maximum"] for part in ("resistance_ohm", "capacitance_f"))
                       for row in batch["trials"])
    robust, tolerance, more_paths = accepted_dataset(robustness, robust_manifest, "phase4-tolerance-v1")
    paths.extend(more_paths)
    require(tolerance["trials"] == robust["outcomes"] and tolerance["environment"] == robust["environment"],
            "tolerance outcomes differ from historical acceptance")
    robust_settings = read(robust_manifest)
    for row in tolerance["trials"]:
        stats = row["holdout_statistics"]
        require(row["stage"] == "completed" and stats["samples"] == robust_settings["holdout_samples"],
                "incomplete holdout observation")
        require(0 <= stats["target_passes"] <= stats["samples"] and
                stats["pass_rate"] == stats["target_passes"] / stats["samples"], "holdout rate mismatch")
        require(row["simulator_calls"] == robust_settings["training_calls"] + stats["samples"],
                "unmatched tolerance call partition")
    paired = {}
    for row in tolerance["trials"]:
        paired.setdefault((row["case"], row["seed"]), {})[row["method"]] = row
    require(all(set(pair) == {"nominal", "robust"} for pair in paired.values()), "missing tolerance pair")
    improvements = sum(pair["robust"]["holdout_statistics"]["relative_error"]["q95"] <
                       pair["nominal"]["holdout_statistics"]["relative_error"]["q95"] for pair in paired.values())
    # This auditor only reads saved replies and raw traces. It never invokes a provider or simulator.
    spec = importlib.util.spec_from_file_location("research_local_auditor", ROOT / "scripts/audit_local_trial.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    local_audit = module.audit(local)
    require(local_audit == read(local / "audit.json"), "saved local audit differs from fresh read-only audit")
    require(local_audit["comparison_data_status"] == "complete", "local comparison data incomplete")
    result = read(local / "result.json")
    local_rows = []
    for trial in result["trials"]:
        for method in trial["results"]:
            best = method["best"]
            local_rows.append({"case": trial["case"], "seed": trial["seed"], "method": method["method"],
                               "simulator_calls": method["simulator_calls"],
                               "relative_error": best["relative_error"], "target_passed": best["target_passed"]})
    paths.extend(local / name for name in ("result.json", "audit.json", "budget.json", "approved-policy.json"))
    supplement = None
    supplement_rows = []
    if replay_supplement is not None:
        spec = importlib.util.spec_from_file_location("research_replay_auditor", ROOT / "scripts/audit_local_replay.py")
        auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor)
        supplement = auditor.audit(local, replay_supplement)
        require(supplement == read(replay_supplement / "acceptance.json"), "saved supplemental audit differs")
        saved = read(replay_supplement / "result.json")
        for record in saved["replay"]:
            best = record["best"]
            supplement_rows.append({"case": record["case"], "status": record["proposal_ledger"][0]["status"],
                                    "exact_candidate_replay": record["exact_candidate_replay"],
                                    "simulator_calls": record["simulator_calls"],
                                    "relative_error": best["relative_error"] if best else None,
                                    "target_passed": best["target_passed"] if best else None})
        paths.extend(replay_supplement / name for name in ("result.json", "acceptance.json", "budget.json", "approved-policy.json"))
    return {"report_policy": "research-report-v1", "scope": "stored-evidence-reporting",
            "new_model_requests": 0, "new_spice_calls": 0,
            "phase6_status": supplement["status"] if supplement else local_audit["phase6_comparison_status"],
            "phase7_release_accepted": False,
            "nominal": {k: nominal[k] for k in ("cases", "seeds", "trials", "design_passes", "design_misses",
                                               "infeasible_rejections", "audited_calls", "audited_calls_including_replay")},
            "fixed_control_passes": fixed_passes,
            "nominal_methods": aggregates, "tolerance_settings": robust_settings["tolerance"],
            "robust_q95_improvements": improvements, "tolerance_pairs": len(paired),
            "tolerance_rows": tolerance["trials"], "local_audit": local_audit, "local_rows": local_rows,
            "replay_supplement": supplement, "replay_supplement_rows": supplement_rows,
            "sources": [{"path": str(path.resolve()), "sha256": sha256(path)} for path in paths]}


def render(data: dict) -> str:
    n = data["nominal"]
    lines = ["# CircuForge research report", "",
             "This report reconciles stored experiments; it runs no new model or simulator.",
             "Historical Phase 3/4 acceptance and numerical summaries are checked against their",
             "manifests and test reports. Their raw physics audits remain historical; they are",
             "not repeated by this exporter. Local-trial raw traces and saved model replies are",
             "independently re-audited read-only. Input paths and SHA-256 hashes are in summary.json.", "",
             "## Methods and assumptions", "",
             "Ideal unloaded first-order RC low/high-pass filters use fc=1/(2*pi*R*C).",
             "Source impedance is zero; R/C are ideal continuous values. All studies retain",
             "their prespecified target tolerance; misses remain design failures even when engineering checks pass.",
             "Random/grid/SciPy use matched actual simulator calls within each comparison.",
             "These datasets have different domains/budgets and are not pooled or ranked across studies.", "",
             "## Nominal benchmark", "",
             f"{n['cases']} curated cases, {n['seeds']} seeds, {n['trials']} method trials per run.",
             f"Per run: {n['design_passes']} design passes, {n['design_misses']} misses and "
             f"{n['infeasible_rejections']} infeasible rejections; {n['audited_calls']} simulator calls.",
             f"The recorded exact replay accounts for {n['audited_calls_including_replay']} audited calls in total.",
             f"Of the design passes, {data['fixed_control_passes']} came from fixed-component controls.",
             "An infeasible rejection is validation, not a synthesized design. Fixed controls",
             "and deterministic grid repetitions must not be treated as independent optimization wins.", "",
             "| Method | Feasible trials | Passes | Misses | Rejections | Calls/run |",
             "|---|---:|---:|---:|---:|---:|"]
    for method, row in data["nominal_methods"].items():
        lines.append(f"| {method} | {row['feasible_trials']} | {row['design_passes']} | {row['design_misses']} | "
                     f"{row['infeasible_rejections']} | {row['simulator_calls']} |")
    settings = data["tolerance_settings"]
    lines += ["", "## Component tolerances", "",
              f"Independent uniform perturbations: R +/-{100*settings['resistance_fraction']:g}%, "
              f"C +/-{100*settings['capacitance_fraction']:g}%. These illustrative distributions are not calibrated to hardware.",
              "Nominal search spends training calls on candidates; robust search spends part of",
              "the same budget on perturbations, reducing candidate opportunities. Fresh paired",
              "holdout factors never select the design. Empirical quantiles are descriptive.", "",
              "| Case | Seed | Method | Nominal error % | Holdout q95 error % | Holdout passes | Calls |",
              "|---|---:|---|---:|---:|---:|---:|"]
    for row in data["tolerance_rows"]:
        stats = row["holdout_statistics"]
        lines.append(f"| {row['case']} | {row['seed']} | {row['method']} | {100*row['nominal_relative_error']:.6f} | "
                     f"{100*stats['relative_error']['q95']:.6f} | {stats['target_passes']}/{stats['samples']} | {row['simulator_calls']} |")
    audit = data["local_audit"]
    lines += ["", f"Robust holdout q95 was lower in {data['robust_q95_improvements']} of "
              f"{data['tolerance_pairs']} paired comparisons. This is descriptive, not a general superiority claim.",
              "", "![Measured holdout q95 errors](tolerance-comparison.svg)", "", "## Local-model comparison", "",
              f"{audit['completed_equal_budget_trials']} matched-call comparisons; {audit['model_requests']} model attempts; "
              f"{audit['audited_real_spice_calls']} actual raw-audited SPICE attempts including pilots.",
              f"Reserved tokens: {audit['reserved_tokens']}; known reported tokens: {audit['reported_tokens_known']}; "
              f"unknown-usage requests: {audit['requests_with_unknown_usage']}. Known tokens exclude unknown usage.",
              f"Primary-window completed replay checks: {audit['completed_replay_checks']}; original gate: `{audit['phase6_comparison_status']}`.",
              "Equal SPICE calls exclude additional inference time. This small two-topology study",
              "does not establish general LLM superiority or topology synthesis. The earlier",
              "partial trial is excluded. No expired allowance is reopened by reporting.", "",
              "| Case | Seed | Method | Best error % | Target passed | Calls |",
              "|---|---:|---|---:|---|---:|"]
    for row in data["local_rows"]:
        lines.append(f"| {row['case']} | {row['seed']} | {row['method']} | {100*row['relative_error']:.6f} | "
                     f"{str(row['target_passed']).lower()} | {row['simulator_calls']} |")
    supplement = data.get("replay_supplement")
    if supplement is not None:
        lines += ["", "## Separately authorized local replay supplement", "",
                  f"Composite gate: `{supplement['status']}`; {supplement['completed_replay_observations']} returned observations, "
                  f"{supplement['supplemental_model_requests']} new model requests and {supplement['supplemental_spice_attempts']} new SPICE attempts.",
                  f"This separate window reserved {supplement['supplemental_reserved_tokens']} tokens, reported "
                  f"{supplement['supplemental_known_reported_tokens']} known tokens and retained "
                  f"{supplement['supplemental_unknown_usage']} unknown-usage requests.",
                  f"Exact valid-candidate replays: {supplement['exact_candidate_replays']}. Invalid observations do not become designs.",
                  "The original timeout/deadline and unknown usage remain in their own dataset.",
                  "The new observations do not change comparison scores or establish model efficacy.", "",
                  "| Case | Returned status | Exact valid candidate | Calls | Target error % |",
                  "|---|---|---|---:|---:|"]
        for row in data["replay_supplement_rows"]:
            error = "not measured" if row["relative_error"] is None else f"{100*row['relative_error']:.6f}"
            lines.append(f"| {row['case']} | {row['status']} | {str(row['exact_candidate_replay']).lower()} | {row['simulator_calls']} | {error} |")
    lines += ["", "## Limits and next steps", "",
              "The plots show observations, not confidence intervals or population estimates.",
              "Shared random factors, curated tasks, small training/holdout sets and ideal RC",
              "physics limit generalization. Source/load nonidealities, discrete components,",
              "active circuits and physical boards remain unverified. Numerical same-environment",
              "replay is not a cross-platform promise. Engineering acceptance does not erase",
              "target failures or grant deployment, remote push or a new provider allowance.",
              f"Current Phase 6 evidence status: `{data['phase6_status']}`. The final Phase 7 release is a separate gate.", ""]
    return "\n".join(lines)


def plot(data: dict, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.fonttype"] = "none"
    matplotlib.rcParams["svg.hashsalt"] = "circuforge-research-report-v1"
    import matplotlib.pyplot as plt

    rows = data["tolerance_rows"]
    pairs = list(dict.fromkeys((r["case"], r["seed"]) for r in rows))
    figure, axes = plt.subplots(figsize=(9, 4.8), layout="constrained")
    for offset, method in ((-0.18, "nominal"), (0.18, "robust")):
        indexed = {(r["case"], r["seed"]): r for r in rows if r["method"] == method}
        values = [100 * indexed[p]["holdout_statistics"]["relative_error"]["q95"] for p in pairs]
        axes.bar([i + offset for i in range(len(pairs))], values, width=0.35, label=method.capitalize())
    axes.set_xticks(range(len(pairs)), [f"{case}\nseed {seed}" for case, seed in pairs])
    axes.set_ylabel("Holdout q95 relative cutoff error (%)")
    axes.set_title("Stored tolerance study — matched total SPICE calls")
    axes.legend()
    figure.supxlabel("Paired empirical observations; fewer candidate opportunities for robust search; no confidence claim", fontsize=8)
    figure.savefig(output / "tolerance-comparison.png", dpi=160)
    figure.savefig(output / "tolerance-comparison.svg", metadata={"Date": None})
    svg = output / "tolerance-comparison.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    plt.close(figure)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("benchmark", "robustness", "local", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--replay-supplement", type=Path, help="optional separately approved local replay evidence")
    args = parser.parse_args(argv)
    try:
        data = collect(args.benchmark, args.robustness, args.local, args.replay_supplement)
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "report.md").write_text(render(data), encoding="utf-8")
        (args.output / "summary.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        plot(data, args.output)
        print(f"Exported checked research report; no new model or SPICE calls; Phase 6 evidence: {data['phase6_status']}; Phase 7 release is separate.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as exc:
        print(f"Report blocked: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
