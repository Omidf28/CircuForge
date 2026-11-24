"""Separate, prespecified one-call comparison; never rewrites historical benchmarks."""
import hashlib
import json
from pathlib import Path
import time
from typing import Literal

from pydantic import Field, model_validator

from circuforge.domain.cases import Case
from circuforge.domain.specs import DesignInputs, Model
from circuforge.evaluation.acceptance import audit_run, read_json, require
from circuforge.evaluation.benchmark import Benchmark, BenchmarkCase, load_benchmark
from circuforge.evaluation.records import environment
from circuforge.optimization.analytic import analytic_candidate
from circuforge.optimization.baselines import run_baseline
from circuforge.simulation.ngspice import Ngspice

POLICY = "physics-onecall-v1"
METHODS = ("random", "grid", "scipy", "analytic_rc")


class Experiment(Model):
    policy: Literal["physics-onecall-v1"]
    source_benchmark: Literal["benchmark-v2.json"]
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seeds: tuple[Literal[7], Literal[42], Literal[2026]]
    methods: tuple[Literal["random"], Literal["grid"], Literal["scipy"], Literal["analytic_rc"]]
    calls_per_method: Literal[1]
    timeout_s: Literal[5.0]
    repetitions: Literal[2]
    max_total_spice_calls: Literal[500]
    provenance: str = Field(min_length=30)

    @model_validator(mode="before")
    @classmethod
    def strict_caps(cls, data):
        if isinstance(data, dict) and any(type(data.get(name)) is not int for name in
                                         ("calls_per_method", "repetitions", "max_total_spice_calls")):
            raise ValueError("integer resource caps must not be booleans")
        return data


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_experiment(path: Path) -> tuple[Experiment, Benchmark]:
    config = Experiment.model_validate_json(path.read_bytes())
    source = path.parent / config.source_benchmark
    require(digest(source) == config.source_sha256, "source benchmark changed")
    benchmark = load_benchmark(source)
    require(benchmark.version == "2.0", "requires normalized-distinct v2 cases")
    expected_calls = sum(case.expected_feasible for case in benchmark.cases) * len(config.seeds) * len(config.methods)
    require(expected_calls * config.repetitions <= config.max_total_spice_calls, "comparison exceeds fixed total call cap")
    return config, benchmark


def derived_case(case: BenchmarkCase, config: Experiment) -> BenchmarkCase:
    inputs = DesignInputs.model_validate({**case.inputs.model_dump(),
                                         "max_evaluations": config.calls_per_method, "timeout_s": config.timeout_s})
    return BenchmarkCase(id=case.id, inputs=inputs, expected_feasible=case.expected_feasible, rationale=case.rationale)


def row_for(case, seed, method, report=None):
    return dict(case=case.id, seed=seed, method=method, inputs=case.inputs.model_dump(),
                expected_feasible=case.expected_feasible,
                status="evaluated" if report else "infeasible_rejected",
                simulator_calls=report.simulator_calls if report else 0,
                failures=report.failures if report else 0,
                target_passed=report.converged if report else False,
                relative_error=report.best.relative_error if report and report.best else None,
                candidate=report.best.candidate.model_dump() if report and report.best else None)


def aggregate(rows: list[dict]) -> dict:
    result = {}
    for method in METHODS:
        group = [row for row in rows if row["method"] == method]
        feasible = [row for row in group if row["expected_feasible"]]
        fixed = lambda row: all(row["inputs"][part]["minimum"] == row["inputs"][part]["maximum"]
                                for part in ("resistance_ohm", "capacitance_f"))
        result[method] = dict(feasible_trials=len(feasible), design_passes=sum(row["target_passed"] for row in feasible),
                              design_misses=sum(not row["target_passed"] for row in feasible),
                              fixed_control_passes=sum(row["target_passed"] and fixed(row) for row in feasible),
                              free_domain_passes=sum(row["target_passed"] and not fixed(row) for row in feasible),
                              free_domain_trials=sum(not fixed(row) for row in feasible),
                              infeasible_rejections=len(group) - len(feasible),
                              simulator_calls=sum(row["simulator_calls"] for row in group))
    return result


def run_comparison(manifest: Path, output: Path, simulator: Ngspice) -> dict:
    config, source = load_experiment(manifest)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    rows = []

    def save():
        result = dict(policy=POLICY, manifest_sha256=digest(manifest), source_sha256=config.source_sha256,
                      environment=environment(), planned_trials=len(source.cases) * len(config.seeds) * len(config.methods),
                      completed_trials=len(rows), actual_calls=sum(row["simulator_calls"] for row in rows),
                      wall_s=time.monotonic() - started, rows=rows, aggregates=aggregate(rows))
        (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return result

    for seed in config.seeds:
        for original in source.cases:
            case = derived_case(original, config)
            spec = case.validated_spec()
            for method in config.methods:
                destination = output / f"seed-{seed}" / case.id / method
                report = run_baseline(spec, simulator, method, seed=seed, output=destination) if spec else None
                row = row_for(case, seed, method, report)
                if spec is None:
                    destination.mkdir(parents=True)
                    (destination / "rejection.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
                rows.append(row)
                save()
            print(f"seed={seed} case={case.id} completed", flush=True)
    return save()


def audit_comparison(manifest: Path, output: Path) -> dict:
    config, source = load_experiment(manifest)
    data = read_json(output, "summary.json")
    expected = len(source.cases) * len(config.seeds) * len(config.methods)
    require(data["policy"] == POLICY and data["manifest_sha256"] == digest(manifest) and
            data["source_sha256"] == config.source_sha256 and data["environment"] == environment(),
            "experiment metadata/source/environment differs")
    rows = data["rows"]
    require(len(rows) == data["completed_trials"] == data["planned_trials"] == expected, "incomplete comparison")
    indexed = {(r["case"], r["seed"], r["method"]): r for r in rows}
    require(len(indexed) == expected, "duplicate trial")
    calls = rejected = 0
    for seed in config.seeds:
        for original in source.cases:
            case = derived_case(original, config)
            spec = case.validated_spec()
            counts = []
            for method in config.methods:
                row = indexed[(case.id, seed, method)]
                root = output / f"seed-{seed}"
                if spec is None:
                    require(row == row_for(case, seed, method) == read_json(root, f"{case.id}/{method}/rejection.json"),
                            "false infeasible rejection")
                    require(not (root / case.id / method / "evaluations").exists(), "infeasible case simulated")
                    rejected += 1
                else:
                    report = audit_run(root, Case(id=case.id, spec=spec), method, seed, data["environment"])
                    require(row == row_for(case, seed, method, report), "summary differs from raw-audited report")
                    if method == "analytic_rc":
                        require(report.history[0].candidate == analytic_candidate(spec) and
                                report.optimizer_settings.get("analytic_seed_used") is False,
                                "analytic candidate/seed policy differs")
                    calls += report.simulator_calls
                counts.append(row["simulator_calls"])
            require(len(set(counts)) == 1 and counts[0] == int(spec is not None), "unmatched actual one-call budgets")
    totals = aggregate(rows)
    require(data["actual_calls"] == calls and data["aggregates"] == totals, "incorrect aggregate/counts")
    require(calls * config.repetitions <= config.max_total_spice_calls, "total call cap exceeded")
    return dict(cases=len(source.cases), seeds=len(config.seeds), trials=expected,
                audited_calls=calls, infeasible_rejections=rejected, aggregates=totals)


def audit_replay(manifest: Path, first: Path, replay: Path) -> dict:
    a = audit_comparison(manifest, first)
    b = audit_comparison(manifest, replay)
    require(a == b, "numerical outcome totals differ on replay")
    require(read_json(first, "summary.json")["rows"] == read_json(replay, "summary.json")["rows"],
            "candidate/metric replay differs")
    for path in first.rglob("report.json"):
        left, right = read_json(path.parent, path.name), read_json(replay / path.relative_to(first).parent, path.name)
        for record in (left, right):
            for entry in [*record["history"], *([record["best"]] if record["best"] else [])]:
                entry.pop("elapsed_s", None)
        require(left == right, "optimizer/candidate trace differs on replay")
    return dict(status="passed", policy=POLICY, acceptance_mode="automated", manual_review_required=False,
                numerical_replay="exact in recorded environment; timings excluded",
                audited_calls_including_replay=2 * a["audited_calls"], **a)
