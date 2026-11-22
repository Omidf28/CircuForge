"""Shared physics verification, objective, exact cache and hard call accounting."""
import math
import json
from pathlib import Path
import time
from typing import Literal

from circuforge.domain.specs import CircuitCandidate, DesignSpec, Model
from circuforge.evaluation.records import write_response
from circuforge.simulation.metrics import analytic_cutoff, cutoff_hz
from circuforge.simulation.ngspice import Ngspice, SimulationError
from circuforge.synthesis.rc import netlist

FAILURE_PENALTY = 1e6


class BudgetExhausted(RuntimeError):
    """No new simulator attempt is permitted."""


class ProposalLimit(RuntimeError):
    """Bound duplicate/invalid proposals independently of simulator calls."""


class Evaluation(Model):
    candidate: CircuitCandidate
    status: Literal["evaluated", "invalid_candidate", "simulation_error", "metric_error", "verification_error"]
    objective: float = FAILURE_PENALTY
    constraints_satisfied: bool
    simulator_exit_ok: bool = False
    verified: bool = False
    target_passed: bool = False
    measured_cutoff_hz: float | None = None
    relative_error: float | None = None
    analytic_relative_error: float | None = None
    simulator_call: int | None = None
    elapsed_s: float = 0.
    failure_type: str | None = None
    reason: str | None = None
    artifact: str | None = None


class Evaluator:
    def __init__(self, spec: DesignSpec, simulator: Ngspice, output: Path | None = None):
        self.spec, self.simulator, self.output = spec, simulator, output
        self.calls = self.proposals = self.cache_hits = 0
        self.proposal_limit = 20 * spec.max_evaluations + 20
        self.history: list[Evaluation] = []
        self.cache: dict[tuple, Evaluation] = {}
        if output is not None:
            output.mkdir(parents=True, exist_ok=False)

    def evaluate(self, candidate: CircuitCandidate) -> Evaluation:
        if self.proposals >= self.proposal_limit:
            raise ProposalLimit("candidate proposal limit reached")
        self.proposals += 1
        try:
            self.spec.validate_candidate(candidate)
        except (ValueError, TypeError) as exc:
            if not isinstance(candidate, CircuitCandidate):
                raise TypeError("candidate must be a typed CircuitCandidate") from exc
            evaluation = Evaluation(candidate=candidate, status="invalid_candidate",
                                    constraints_satisfied=False, reason=str(exc), failure_type="bounds_or_topology")
            self.history.append(evaluation)
            return evaluation
        key = (candidate.topology, candidate.resistance_ohm, candidate.capacitance_f)
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        if self.calls >= self.spec.max_evaluations:
            raise BudgetExhausted("SPICE call budget reached")
        self.calls += 1  # Charge every attempt, including launch/timeout/parse failures.
        started = time.monotonic()
        result = None
        failure = None
        data = dict(candidate=candidate, constraints_satisfied=True, simulator_call=self.calls)
        try:
            result = self.simulator.simulate(self.spec, candidate)
        except SimulationError as exc:
            failure = exc
            evaluation = Evaluation(**data, status="simulation_error", simulator_exit_ok=exc.returncode == 0,
                                    failure_type=exc.status, reason=str(exc), elapsed_s=time.monotonic() - started)
        else:
            try:
                measured = cutoff_hz(result.response, candidate.topology)
            except ValueError as exc:
                evaluation = Evaluation(**data, status="metric_error", simulator_exit_ok=True,
                                        failure_type="cutoff_unmeasurable", reason=str(exc), elapsed_s=result.elapsed_s)
            else:
                error = abs(measured / self.spec.cutoff_hz - 1)
                reference_error = abs(measured / analytic_cutoff(candidate) - 1)
                verified = reference_error <= .001
                evaluation = Evaluation(**data, status="evaluated" if verified else "verification_error",
                                        objective=abs(math.log(measured / self.spec.cutoff_hz)) if verified else FAILURE_PENALTY,
                                        simulator_exit_ok=True, verified=verified,
                                        target_passed=verified and error <= self.spec.relative_error_tolerance,
                                        measured_cutoff_hz=measured, relative_error=error,
                                        analytic_relative_error=reference_error, elapsed_s=result.elapsed_s,
                                        failure_type=None if verified else "analytic_mismatch",
                                        reason=None if verified else "measured cutoff differs from independent RC reference")
        if self.output is not None:
            name = f"call-{self.calls:04d}"
            directory = self.output / name
            directory.mkdir()
            if result is not None:
                write_response(directory, result)
            else:
                (directory / "circuit.cir").write_text(netlist(self.spec, candidate), encoding="ascii")
                (directory / "stdout.log").write_text(failure.stdout, encoding="utf-8")
                (directory / "stderr.log").write_text(failure.stderr, encoding="utf-8")
            evaluation = evaluation.model_copy(update={"artifact": name})
            payload = {**evaluation.model_dump(), "spec": self.spec.model_dump(),
                       "ngspice_version": self.simulator.info.version,
                       "command": [self.simulator.info.executable, "-n", "-b", "circuit.cir"],
                       "returncode": result.returncode if result is not None else failure.returncode}
            (directory / "evaluation.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        self.cache[key] = evaluation
        self.history.append(evaluation)
        return evaluation

    @property
    def best(self) -> Evaluation | None:
        verified = [e for e in self.history if e.verified]
        # Target acceptance uses a relative-error interval, whose log-space
        # boundaries are slightly asymmetric. Preserve any passing design.
        return min(verified, key=lambda e: (not e.target_passed, e.objective)) if verified else None
