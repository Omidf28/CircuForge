# Phase 2: measured objective and equal-budget baselines

The owner accepted Phase 1 on 2026-11-19 and subsequently requested the next step. Phase 2 local numerical implementation follows P2-C1/C2/C3. Human P2-H1 review is separate; no feature-branch push, deployment or later-phase work is implied.

## P2-C1 objective contract

optimization/base.py rejects out-of-bounds/topology-mismatched typed candidates before simulator calls. It separates constraints, simulator exit status, successful cutoff measurement, analytic verification and target pass/fail. Objective: abs(log(measured_cutoff/target)); the independently reported acceptance error is abs(measured_cutoff/target-1). The analytic RC formula only checks measured correctness; it does not supply fitness measurements.

Simulation, metric and analytic-verification failures receive a finite 1e6 objective penalty and cannot become the best design. Every attempted AC call is charged, including failures. Exact admissible candidate duplicates share a per-run cache (including failed simulations/measurements). Invalid proposals are recorded without simulation. Proposals are separately capped at 20*SPICE_budget+20 to prevent duplicate/invalid loops. A fresh evaluator/cache is used per algorithm. Seven focused objective/budget/cache/failure unit cases passed before baseline implementation.

Best selection prioritizes verified candidates passing target tolerance, then minimizes the log objective. This preserves a passing design near the slightly asymmetric relative-error/log-error boundaries. Target acceptance never comes from the analytic reference alone.

## Baseline algorithms

- random: NumPy default_rng(seed), uniform in log R and log C.
- grid: deterministic rectangular log grid, with an evenly indexed budget-sized subset if the square grid is larger than the budget. Fixed axes have one point; a one-point free axis uses its midpoint. Seed is recorded but unused.
- scipy: public SciPy differential_evolution, best1bin, popsize=5, shared seeded Generator, workers=1, immediate updating, tol=atol=0, polish=False. Exact-energy convergence restarts the population to consume the same available budget. The evaluator cap stops even mid-generation; proposal limit bounds cache-heavy runs.

Reference: [SciPy differential_evolution documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html). SciPy >=1.15 is declared for rng support. Numerical replay requires the same package/simulator versions; versions and source SHA256 are exported.

All methods run to the same call cap rather than stopping at the first target match. Fully fixed domains need only one call and explicitly report domain_exhausted. Compare actual calls, not just configured caps. Finite grids or proposal limits may stop earlier, which is reported. Failed/unbracketed sweeps count against the budget; there is no analytic fallback, silent sweep expansion or shared cross-method cache.

## Run and inspect

From the installed project with ngspice configured:

```text
python -m circuforge optimize --spec examples/search.json --method scipy --seed 42 --output /new/output/path
python -m circuforge compare --spec examples/search.json --seed 42 --output /new/comparison/path
```

Use an OS-appropriate writable absolute output path. The managed Documents write restriction still applies. optimize exits 0 if the selected best design passes target tolerance, 1 otherwise; compare exits 0 if every method produced a verified measured candidate, even when target tolerance was missed, and 1 if any method has no verified candidate. Input/environment/artifact errors exit 2. Review converged and relative_error fields rather than equating comparison completion with design success.

Per-method report.json contains the spec, options, objective/target/reference errors, uncached evaluation history, actual call/proposal/cache/failure counts, stop reason and environment. Invalid proposals are retained; cache hits are counted separately. Every attempted call has an evaluations/call-NNNN directory with generated netlist, raw logs, evaluation metadata and genuine response.csv when available. comparison.json summarizes matched actual calls and outcomes. Existing output directories are preserved.

## Verification log

- P2-C1: 7 focused unit tests passed (controlled analytic fixtures, not electrical evidence).
- Baselines: 17 focused unit cases passed for hard caps 1/7/16, fixed-seed trace replay, failure charging, fixed domains, options and coordinates. Real integration and the five-case comparison are recorded below after execution.

## Observed five-case comparison — 2026-11-19

Executed from the active checkout, with PYTHONPATH=src and CIRCUFORGE_NGSPICE set to the previously verified ngspice-47 console executable:

```text
C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Phase1_Verification/.venv/Scripts/python.exe scripts/compare_phase2.py --seed 42 --output C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Phase2_Verification/seed-42
```

The runner validates up to 8 uniquely identified typed cases before execution and caps the configured batch at 1000 attempted calls. Versioned inputs: examples/phase2-review-cases.json. Configured cap: 960 calls; actual: **771** (four free domains * three methods * 64 calls, plus three fixed-domain calls). All actual per-case method budgets matched. All evaluations completed without simulator/metric/reference failures; missing the target tolerance is reported separately.

| Case | Random error | Grid error | SciPy error | Calls per method |
|---|---:|---:|---:|---:|
| Low-pass 1000 Hz | 5.252691% | 17.571270% | 2.021734% | 64 |
| High-pass 2300 Hz | 5.263007% | 33.606566% | 1.533894% | 64 |
| Low-pass 50 Hz | 14.717531% | 18.646153% | 0.325243% | 64 |
| High-pass 150000 Hz | 0.113167% | 6.107506% | 0.519687% | 64 |
| Fixed 1 kohm/100 nF, rounded target | 0.003874% | 0.003874% | 0.003874% | 1 |

Tolerance: **0.1%**. No method met tolerance on the four free-domain cases at this budget/seed. All three met tolerance on the fixed domain. SciPy had lower error on three of the four free cases, while random search was better on the high-frequency case. These are five single-seed engineering cases, not a statistical benchmark or evidence of general optimizer superiority. No budgets or tolerances were adjusted after observing results. The domain-specific Phase 1 bisection is separate from this generic two-parameter baseline comparison.

Fifteen reports and all 771 raw per-call artifacts were audited for counts, bounds, return codes, response/log presence and best selection. Current passing-first selection agrees with every saved best record. Summary JSON/CSV, per-case comparisons and all raw data remain in the ignored external output directory above.

Environment: Python 3.12.7, NumPy 2.5.5, Pydantic 2.14.3, SciPy 1.18.1, pytest 9.2.0, Windows 11 and ngspice-47. SciPy was installed into the isolated test environment using `python -m pip install --index-url https://pypi.org/simple "scipy>=1.15,<2"`.

Full verification command (same interpreter, PYTHONPATH=src, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, ngspice configured): `python -m pytest -q -ra -o cache_dir=C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Phase1_Verification/pytest-cache`. Observed: **154 passed in 10.51s**, no skips. This includes four genuine baseline integration cases, fixed-seed replay, duplicate-loop bounds and passing-first selection. P2-C1/C2/C3 engineering work is complete; **P2-H1 remains pending owner review**, and no Phase 3 work or push has started.

Package verification: copied the audited source into Phase2_Verification/source-code and installed it into the isolated test environment using `python -m pip install --index-url https://pypi.org/simple --no-deps ./source-code`. Wheel build/install succeeded. From outside the source tree, the installed interpreter with `-I -m circuforge compare` and `-I -m circuforge optimize --method scipy`, both using source-code/examples/fixed-target.json and new output directories, exited 0. The installed comparison exported three one-call, target-passing reports; the installed single optimizer exported one. These packaging smoke cases do not alter the five-case results above.
