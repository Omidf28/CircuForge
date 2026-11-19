# Initial architecture and interface contracts

Implementation update (2026-11-19): domain, synthesis, simulation, CLI, first-slice bisection and Phase 2 classical baselines are implemented and tested. optimization/base.py owns constraint/measurement/reference/target evaluation and budgets; optimization/baselines.py owns seeded random/grid/SciPy. evaluation/records.py exports genuine responses and environment fingerprints. See docs/DEVELOPMENT.md and docs/PHASE2.md. Product/API layers remain deferred.

## Candidate directories (create during implementation)

```text
src/circuforge/
  domain/specs.py         # Pydantic specs, units, validity
  domain/tolerance.py     # typed independent multiplicative errors and RNG streams
  synthesis/rc.py        # trusted topology templates -> netlist
  simulation/ngspice.py  # executable preflight, bounded subprocess, parser
  simulation/metrics.py  # complex transfer function, cutoff, errors
  optimization/base.py   # candidate/objective/fitness and budget
  optimization/baselines.py # seeded random + SciPy later
  optimization/robustness.py # matched-call nominal/robust study with untouched holdout
  evaluation/records.py  # reproducible experiment result schema
  evaluation/acceptance.py # shared raw physics/evidence audits
  evaluation/benchmark.py # typed feasible/infeasible fixtures, multi-seed runs, exact replay
  evaluation/statistics.py # empirical quantiles/pass rates; failures block statistics
  evaluation/robust_acceptance.py # sampling, raw-physics, objective, holdout and replay audit
  evaluation/robust_plot.py # optional Matplotlib scientific artifact
  cli.py                 # command-line demo
 tests/{unit,integration}/
 examples/
 docs/
```

Dependencies: Python 3.11+ (planning target), NumPy, SciPy, Pydantic, pytest; FastAPI only after core. `ngspice` is a separate external executable, not assumed preinstalled. Detect executable using PATH / documented override; never hardcode personal paths.

## Contracts

`DesignSpec`: filter_type enum, cutoff_hz positive, allowed topologies, R/C bounds with units, source and load assumptions, tolerance policy, simulation/evaluation limits.

`CircuitCandidate`: topology id, component values, netlist generated from internal template, provenance, parameter validity.

`SimulationResult`: status enum, ngspice version, return code, stdout/stderr (sanitized), frequency_hz, complex transfer arrays, elapsed time, error reason.

`EvaluationResult`: target, measured cutoff, error, constraint status, simulator call count, latency, artifact paths, warnings.

`ExperimentRecord`: case ID, optimizer, code/config versions, seed, budget, candidate, result, failure type, token/cost where applicable.

## Test pyramid

1. Analytic RC formula and validation unit tests without simulator.
2. Trusted netlist generation golden tests and input-injection rejection.
3. ngspice real executable integration test (must visibly skip/fail if binary absent).
4. Equal-budget optimizer tests and replay.
5. Robustness sampling tests, benchmark regression and optional API/UI integration.

Record exact simulator commands, package/environment versions and reproducible fixtures. No numeric assertions based on LLM text.

Phase 3 adds a versioned bounded manifest and experiment/replay harness; see docs/PHASE3.md. DesignInputs validates supported, well-formed electrical requests before DesignSpec checks achievable target feasibility. This allows intentionally infeasible benchmark constraints without bypassing safety validation. All simulated candidates still require DesignSpec and the existing trusted adapter. The shared audit_run checker verifies every method's raw data, independently of benchmark summary generation. scripts/accept_phase3.py combines full tests, two fresh runs and exact numerical replay; target misses and expected pre-simulation rejections remain separate outcomes.

Phase 4 reuses Evaluator for every nominal and perturbed measurement. Original nominal bounds remain the optimizer contract; a typed expanded simulation spec represents permitted tolerance realizations and preserves topology, target/error policy, source/load and simulator guardrails. Independent RNG streams separate proposals, shared training factors and fresh holdout factors. The measured nominal objective and tolerance penalty use actual SPICE cutoff errors. Raw audit_evaluation is shared by the historical baseline and new tolerance checkers; Phase 4 additionally reconstructs all perturbations, call partitions, selection and holdout statistics. Full tests and source fingerprints tie acceptance to the executed code. See docs/PHASE4.md; API/UI remain deferred.
