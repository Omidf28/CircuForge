# CircuForge / Wave2Circuit Research Edition — project specification

## Problem and vision

Inverse analog circuit design: map user-defined electrical performance requirements to candidate circuit topologies and component values; run a physics-based simulator; optimize and verify them. This is an engineering research product—not an LLM chat website and not a generic tutorial circuit analyser.

## Success path and scope

MVP: user specifies RC low-pass desired cutoff frequency, permitted R/C ranges and ideal-source/load assumptions. System validates, generates trusted SPICE, performs ngspice AC sweep, computes complex transfer function and -3 dB cutoff, compares target, searches for better R/C values, and exports result + evidence. Extend to RC high-pass when tests pass. Each run records software/tool versions, inputs, output and reason for failures.

For ideal unloaded low-pass: `H(jω)=1/(1+jωRC)`, `fc=1/(2πRC)`. State assumptions: source impedance 0 and effectively infinite load unless explicitly modeled. If finite source/load is introduced, update reference model or stop using ideal formula.

Important distinctions: **circuit synthesis/optimization** ≠ **PCB placement/routing**. PCB is a later, constrained EDA research project, not a guarantee of optimal PCB for arbitrary circuits. No design should be described as physically verified from simulation alone.

## Product requirements

- Typed/validated target: filter kind, cutoff (Hz), source amplitude/impedance, load, R/C bounds, permitted values and max evaluations.
- Trusted, allowlisted netlist templates and bounded local simulator; reject arbitrary SPICE directives/input paths.
- Explainable results: response curves, cutoff interpolation, difference from target, component values, runtime, number of simulator calls, warnings and source data.
- Repeatable algorithms with random seeds, deterministic fixtures and documented failure cases.
- CLI first. Backend/UI follow only after scientific core is validated.

## Research questions

1. Compared with equal-budget seeded random/grid and SciPy optimization, does guided proposal improve target matching and evaluation efficiency?
2. Do robust objectives improve probability of passing target specifications under realistic, explicitly modeled component tolerances?
3. Does an optional structured LLM agent yield an improvement over non-LLM baselines when measured with the same compute/SPICE-call budgets, including token costs?

Benchmarks: start 20 curated feasible/infeasible cases; scale toward 50–100 when baseline and fixture validation are stable. Metrics: target cutoff error and pass rate, constraints satisfaction, simulator calls, wall time, failed simulation proportion, tolerance pass rate/quantiles, LLM token/cost. Compare multiple seeds and publish raw outputs. A negative result remains valid.

## Deferred features

Broader passive/active topologies; constrained topology generation; SPICE model registry and licensing; data-sheet RAG; LLM tool calling; optional fine-tuning; KiCad schematic output, PCB layout/DRC and physical assembly. A symbol or footprint is not a verified SPICE model; model syntax compatibility/pin mapping must be checked.

## Practical constraints

Two students, Codex-assisted implementation, limited budget, primarily Windows PCs. Local CPU simulation expected; no GPU or paid model subscription is a requirement. Estimate ~12 weeks for research MVP but do not claim certainty. Separate human engineering approval from generated suggestions and verify every numerical conclusion.

## Safety and integrity

No unrestricted subprocess/shell execution from user or model inputs. Whitelisted values/topologies, subprocess timeouts and temporary workspace isolation. No secrets committed, no fabricated benchmark findings, no guarantee of actual hardware/PCB behavior without physical verification.
