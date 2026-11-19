"""Versioned nominal RC experiments with expected feasibility and replay."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Annotated, Literal

from pydantic import Field, ValidationError, model_validator

from circuforge.domain.cases import Case
from circuforge.domain.specs import DesignInputs, DesignSpec, Model
from circuforge.evaluation.acceptance import audit_run, read_json, require
from circuforge.evaluation.records import environment
from circuforge.optimization.baselines import BaselineResult, run_baseline
from circuforge.simulation.ngspice import Ngspice

METHODS = ("random", "grid", "scipy")
POLICY = "phase3-reproducibility-v2"


class BenchmarkCase(Model):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,59}$")
    inputs: DesignInputs
    expected_feasible: Annotated[bool, Field(strict=True)]
    rationale: str = Field(min_length=12)

    def validated_spec(self) -> DesignSpec | None:
        try:
            spec = DesignSpec.model_validate(self.inputs.model_dump())
        except ValidationError as exc:
            errors = exc.errors()
            genuine_infeasibility = len(errors) == 1 and "target infeasible within R/C bounds" in errors[0]["msg"]
            if self.expected_feasible or not genuine_infeasibility:
                raise ValueError(f"{self.id}: unexpected input rejection: {exc}") from exc
            return None
        if not self.expected_feasible:
            raise ValueError(f"{self.id}: declared infeasible but the target is feasible")
        return spec

    @model_validator(mode="after")
    def expected_outcome(self):
        self.validated_spec()
        return self

    def electrical_signature(self):
        data = self.inputs.model_dump()
        for key in ("max_evaluations", "timeout_s"):
            data.pop(key)
        return json.dumps(data, sort_keys=True)

    def normalized_signature(self):
        """Ideal RC scaling and R/C exchange do not create new search tasks."""
        r, c = self.inputs.resistance_ohm, self.inputs.capacitance_f
        widths = sorted((math.log10(r.maximum / r.minimum), math.log10(c.maximum / c.minimum)))
        position = math.log10(2 * math.pi * self.inputs.cutoff_hz * r.minimum * c.minimum)
        return (self.inputs.filter_type, *(round(w, 10) for w in widths), round(position, 10),
                self.inputs.relative_error_tolerance)


class Benchmark(Model):
    version: Literal["1.0", "2.0"]
    provenance: str = Field(min_length=30)
    seeds: tuple[Annotated[int, Field(strict=True, ge=0, le=2**32 - 1)], ...]
    cases: tuple[BenchmarkCase, ...]
    max_spice_calls: Annotated[int, Field(strict=True, ge=1, le=2500)] = 2500

    @model_validator(mode="after")
    def bounded_and_distinct(self):
        if not 20 <= len(self.cases) <= 30:
            raise ValueError("benchmark requires 20–30 cases")
        if not 2 <= len(self.seeds) <= 5 or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("provide 2–5 distinct seeds")
        if len({c.id for c in self.cases}) != len(self.cases):
            raise ValueError("duplicate case identifiers")
        if len({c.electrical_signature() for c in self.cases}) != len(self.cases):
            raise ValueError("duplicated electrical cases, including disguised budget changes")
        if len({c.normalized_signature() for c in self.cases}) != len(self.cases):
            raise ValueError("scale-equivalent normalized RC cases are duplicated")
        feasible = sum(c.expected_feasible for c in self.cases)
        if not 2 <= feasible <= len(self.cases) - 2:
            raise ValueError("include feasible and infeasible cases")
        if self.configured_call_cap > self.max_spice_calls:
            raise ValueError("benchmark exceeds declared per-run call cap")
        return self

    @property
    def configured_call_cap(self):
        return sum(c.inputs.max_evaluations for c in self.cases) * len(self.seeds) * len(METHODS)


def load_benchmark(path: Path) -> Benchmark:
    return Benchmark.model_validate_json(path.read_bytes())


def aggregate(rows: list[dict]) -> dict:
    aggregates = {}
    for method in METHODS:
        group = [r for r in rows if r["method"] == method]
        valid = [r for r in group if r["expected_feasible"]]
        passes = sum(r["converged"] for r in valid)
        aggregates[method] = {"feasible_trials": len(valid), "design_passes": passes,
                              "design_misses": len(valid) - passes,
                              "infeasible_rejections": len(group) - len(valid),
                              "simulator_calls": sum(r["simulator_calls"] for r in group),
                              "simulation_failures": sum(r["failures"] for r in group)}
    return aggregates


def write_summary(path: Path, manifest: Benchmark, manifest_hash: str, rows: list[dict], elapsed: float):
    summary = {"manifest_sha256": manifest_hash, "benchmark_version": manifest.version,
               "configured_call_cap": manifest.configured_call_cap, "seeds": manifest.seeds,
               "completed_trials": len(rows), "planned_trials": len(manifest.cases) * len(manifest.seeds) * 3,
               "actual_calls": sum(r["simulator_calls"] for r in rows), "wall_s": elapsed,
               "acceptance_status": "requires_automated_gate", "manual_review_required": False,
               "environment": environment(), "aggregates": aggregate(rows), "trials": rows}
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return summary


def run_benchmark(manifest_path: Path, output: Path, simulator: Ngspice) -> dict:
    manifest = load_benchmark(manifest_path)
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    started = time.monotonic()
    for seed in manifest.seeds:
        for case in manifest.cases:
            spec = case.validated_spec()
            for method in METHODS:
                trial_start = time.monotonic()
                destination = output / f"seed-{seed}" / case.id / method
                if spec is None:
                    row = {"case": case.id, "seed": seed, "method": method, "expected_feasible": False,
                           "status": "infeasible_rejected", "simulator_calls": 0, "failures": 0,
                           "converged": False, "relative_error": None, "objective": None,
                           "reason": "target infeasible within R/C bounds and declared tolerance",
                           "inputs": case.inputs.model_dump(), "candidate": None}
                    destination.mkdir(parents=True)
                    (destination / "rejection.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
                else:
                    result = run_baseline(spec, simulator, method, seed=seed, output=destination)
                    row = {"case": case.id, "seed": seed, "method": method, "expected_feasible": True,
                           "status": "evaluated", "simulator_calls": result.simulator_calls,
                           "failures": result.failures, "converged": result.converged,
                           "relative_error": result.best.relative_error if result.best else None,
                           "objective": result.best.objective if result.best else None,
                           "candidate": result.best.candidate.model_dump() if result.best else None}
                row["wall_s"] = time.monotonic() - trial_start
                rows.append(row)
                write_summary(output / "summary.json", manifest, digest, rows, time.monotonic() - started)
            print(f"seed={seed} case={case.id} complete", flush=True)
    return write_summary(output / "summary.json", manifest, digest, rows, time.monotonic() - started)


def audit_benchmark(manifest_path: Path, output: Path) -> dict:
    manifest = load_benchmark(manifest_path)
    summary = read_json(output, "summary.json")
    require(summary["benchmark_version"] == manifest.version and summary["manual_review_required"] is False and
            summary["acceptance_status"] == "requires_automated_gate", "incorrect benchmark policy metadata")
    require(summary["manifest_sha256"] == hashlib.sha256(manifest_path.read_bytes()).hexdigest(), "benchmark input changed")
    require(summary["seeds"] == list(manifest.seeds) and summary["configured_call_cap"] == manifest.configured_call_cap,
            "seed/cap mismatch")
    expected = len(manifest.cases) * len(manifest.seeds) * 3
    rows = summary["trials"]
    require(summary["completed_trials"] == summary["planned_trials"] == len(rows) == expected, "incomplete trials")
    indexed = {(r["case"], r["seed"], r["method"]): r for r in rows}
    require(len(indexed) == expected, "duplicate trials")
    expected_env = environment()
    require(summary["environment"] == expected_env, "benchmark environment changed")
    require(math.isfinite(summary["wall_s"]) and summary["wall_s"] >= 0, "invalid batch runtime")
    calls = passes = rejected = 0
    for seed in manifest.seeds:
        for case in manifest.cases:
            spec = case.validated_spec()
            counts = []
            for method in METHODS:
                row = indexed[(case.id, seed, method)]
                require(math.isfinite(row["wall_s"]) and row["wall_s"] >= 0, "invalid trial runtime")
                require(row["expected_feasible"] == case.expected_feasible, "false feasibility label")
                if spec is None:
                    rejection = read_json(output, f"seed-{seed}/{case.id}/{method}/rejection.json")
                    require({k: v for k, v in row.items() if k != "wall_s"} == rejection,
                            "rejection summary differs from evidence")
                    require(rejection["inputs"] == case.inputs.model_dump() and
                            rejection["status"] == row["status"] == "infeasible_rejected" and
                            rejection["simulator_calls"] == row["simulator_calls"] == 0 and
                            not rejection["converged"] and not row["converged"], "incorrect infeasible result")
                    require(row["candidate"] is None and row["relative_error"] is None and
                            row["objective"] is None and row["failures"] == 0,
                            "infeasible rejection reported as a design")
                    require(not (output / f"seed-{seed}/{case.id}/{method}/evaluations").exists(), "infeasible case simulated")
                    rejected += 1
                else:
                    report = audit_run(output / f"seed-{seed}", Case(id=case.id, spec=spec), method, seed, expected_env)
                    require(all(math.isfinite(e.elapsed_s) and e.elapsed_s >= 0 for e in report.history) and
                            sum(e.elapsed_s for e in report.history) <= row["wall_s"], "invalid simulator runtime")
                    require(row["status"] == "evaluated" and row["simulator_calls"] == report.simulator_calls and
                            row["converged"] == report.converged and row["failures"] == report.failures and
                            row["candidate"] == report.best.candidate.model_dump() and
                            row["relative_error"] == report.best.relative_error and row["objective"] == report.best.objective,
                            "benchmark row differs from raw evidence")
                    counts.append(report.simulator_calls)
                    calls += report.simulator_calls
                    passes += int(report.converged)
            require(not counts or len(set(counts)) == 1, "unfair actual method budgets")
    require(calls == summary["actual_calls"] <= manifest.configured_call_cap, "benchmark call count mismatch")
    require(summary["aggregates"] == aggregate(rows), "aggregate summary disagrees with trial evidence")
    require(sum(r["wall_s"] for r in rows) <= summary["wall_s"], "batch runtime shorter than trials")
    return {"cases": len(manifest.cases), "seeds": len(manifest.seeds), "trials": expected,
            "audited_calls": calls, "infeasible_rejections": rejected, "design_passes": passes,
            "design_misses": expected - rejected - passes}


def audit_replay(manifest_path: Path, first: Path, second: Path) -> dict:
    a = audit_benchmark(manifest_path, first)
    b = audit_benchmark(manifest_path, second)
    require(a == b, "replay outcome totals changed")
    manifest = load_benchmark(manifest_path)
    for seed in manifest.seeds:
        for case in manifest.cases:
            if not case.expected_feasible:
                continue
            for method in METHODS:
                path = f"seed-{seed}/{case.id}/{method}/report.json"
                left = BaselineResult.model_validate(read_json(first, path))
                right = BaselineResult.model_validate(read_json(second, path))
                require((left.proposals, left.cache_hits, left.stop_reason) ==
                        (right.proposals, right.cache_hits, right.stop_reason), "replay accounting changed")
                def trace(report):
                    return [(e.candidate, e.status, e.objective, e.measured_cutoff_hz, e.relative_error,
                             e.analytic_relative_error, e.target_passed) for e in report.history]
                require(trace(left) == trace(right), "numerical replay mismatch")
    return {"status": "passed", "policy": POLICY, "acceptance_mode": "automated",
            "manual_review_required": False, "numerical_replay": "exact; elapsed times excluded",
            "audited_calls_including_replay": a["audited_calls"] + b["audited_calls"],
            "executed_at_utc": datetime.now(timezone.utc).isoformat(), **a}
