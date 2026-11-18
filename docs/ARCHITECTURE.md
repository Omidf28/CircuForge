# Initial architecture and interface contracts

Implementation update (2026-11-18): domain, synthesis, simulation, CLI and a bounded first-slice search now exist and pass real Windows ngspice tests. See docs/DEVELOPMENT.md for the actual contracts/evidence. Evaluation records currently use CLI JSON rather than a separate evaluation package. SciPy baselines and product/API layers remain later-phase work.

## Candidate directories (create during implementation)

```text
src/circuforge/
  domain/specs.py         # Pydantic specs, units, validity
  synthesis/rc.py        # trusted topology templates -> netlist
  simulation/ngspice.py  # executable preflight, bounded subprocess, parser
  simulation/metrics.py  # complex transfer function, cutoff, errors
  optimization/base.py   # candidate/objective/fitness and budget
  optimization/baselines.py # seeded random + SciPy later
  evaluation/records.py  # reproducible experiment result schema
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
