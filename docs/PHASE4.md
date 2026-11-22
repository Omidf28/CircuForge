# Phase 4 — declared component-tolerance experiment

## Model and prespecified design

`examples/robustness-v1.json` defines this bounded pilot before execution. The two tasks are a 1000 Hz low-pass and a 2300 Hz high-pass with distinct variable R/C bounds, seeds 7/42 and the original 0.1% target tolerance. Source remains ideal zero ohms, load infinite, components ideal and continuous. Existing Phase 2/3 experiments and their thresholds are unchanged.

R errors are uniform in [-1%, +1%]; C errors are uniform in [-5%, +5%]. Component errors and draws within each sampling stream are independent by declared model. This is an illustrative assumption, not a fit to a manufacturer or a hardware guarantee. Correlated, Gaussian and other distributions are rejected. Sampling is multiplicative, with no clipping. Nominal design constraints apply to selected nominal components. Toleranced realizations may cross those nominal bounds and are simulated under an explicitly derived expanded envelope; global physical/safety limits remain enforced. A sweep must bracket the full envelope before execution.

Each method receives **64 training calls and 32 holdout calls**, or **96 actual SPICE calls per trial**. Two cases, two seeds and two methods give **768 calls per run**, below the declared 2000-call hard maximum. Independent replay doubles this to 1536. Every call uses the trusted templates, strict timeout/output limits and isolated simulator. Failed attempts count; incomplete, cached or failed trials cannot pass the acceptance gate.

- Nominal method: log-uniform random search over 64 nominal candidates, selecting minimum measured absolute log cutoff error.
- Robust method: the same proposal stream's first eight nominal candidates. Each consumes one nominal and seven perturbation calls. Its objective is nominal absolute log cutoff error plus the empirical 95th percentile of the seven perturbation log errors (weight 1).
- Both methods evaluate their chosen design with 32 fresh holdout perturbations. The selected candidate's existing nominal measurement is reused explicitly, without spending a hidden extra nominal call. All 32 holdout realizations require fresh measured calls.

RNG streams derive from SeedSequence([seed, stream]): 0 proposals, 1 training factors, 2 holdout factors. Training uses common random factors across candidate proposals, and holdout factors are shared across the paired methods for comparison. The same normalized factors are reused across cases of a seed. These paired/common-random-number observations must not be described as independent population samples. Holdout observations never select or tune a candidate. Seven training samples and 32 holdout samples are deliberately small; quantiles and pass rates are empirical estimates without confidence or hardware-yield guarantees.

Cutoff and target-relative-error q05/q50/q95 use NumPy's explicitly declared linear empirical quantiles. Nominal target success is separate from holdout pass count/rate. Simulation or verification failures cannot disappear from the denominator or become successful designs; statistics block if a required sample failed. Unit data and small integration fixtures are separate from the production experiment and its call counts.

## Reproduce and automatically accept

Install the project and simulator as in README. Core use does not require plotting; the `report` extra provides Matplotlib for these experiment plots and the `test` extra includes it for the full integration suite:

```powershell
python -m pip install -e ".[test,report]"
$env:PYTHONPATH = 'src'
python scripts/compare_robustness.py --output evidence/tolerance-run
python scripts/accept_phase4.py --output evidence/phase4-acceptance
```

Use new writable output directories and optionally `--ngspice` / `--manifest`. In this managed session, generated artifacts must use the authorized visualization workspace. The automatic command runs the full suite with no skips, executes the declared experiment twice and checks every raw response against independent ideal RC physics. It reconstructs proposal/factor streams, training/holdout call partitions, objective penalties, chosen designs, quantiles, pass rates, summary rows, timings and equal total budgets. Exact numerical replay excludes elapsed times; it is an observed same-environment result, not a cross-platform bitwise promise. Tests have a 240-second subprocess timeout; each experiment has a 600-second limit in addition to per-call limits.

Policy `phase4-tolerance-v1` accepts a correctly executed and reproduced experiment without requiring the robust method to win. Missing or inconsistent evidence blocks the gate; technical acceptance does not require manual waiver. The automatic checker supersedes P4-H1 only after actual acceptance. Publication, remote push and spending permissions remain separate.

## Artifacts and interpretation

Each trial retains `report.json` with original/expanded specs, nominal/training group identities and scores, selected group, fresh holdout identities, all measurements, counts, runtime, environment and simulator version. Each `evaluations/call-NNNN/` retains netlist, stdout/stderr, response CSV and measured metadata. Partial training or failed trials remain blocked records. `summary.json` compares nominal target errors with holdout statistics. `comparison.png` plots holdout q95 target error and empirical pass rate, using the same paired observations.

A robust training objective pays for uncertainty measurements with fewer candidate opportunities. Under relative independent tolerances, ideal RC variability is controlled by the product of the two multiplicative factors; redistributing nominal R/C at the same cutoff does not inherently reduce that relative variability. Any measured improvement or deterioration must be reported with the budget and finite-sample limitations. No real-board performance, distribution calibration, confidence guarantee or general optimizer superiority follows from this pilot.

## Observed results

Executed on 2026-11-19 using Windows 11, Python 3.12.7, ngspice-47, NumPy 2.5.5, Pydantic 2.14.3, SciPy 1.18.1 and Matplotlib 3.11.2. **phase4-tolerance-v1 passed: 234 tests without skips and 1536 audited real calls including exact numerical replay.** Each run completed all eight trials and 768 actual calls. Every trial spent exactly 64 training plus 32 holdout calls, with no simulation/verification failures or cache hits.

| Case | Seed | Method | Nominal target error | Holdout q95 target error | Holdout passes |
|---|---:|---|---:|---:|---:|
| lp-narrow | 7 | nominal | 0.208861% | 5.32127% | 0/32 |
| lp-narrow | 7 | robust | 0.678508% | 5.24715% | 1/32 |
| hp-asymmetric | 7 | nominal | 0.442508% | 5.23818% | 1/32 |
| hp-asymmetric | 7 | robust | 0.910681% | 6.0605% | 1/32 |
| lp-narrow | 42 | nominal | 0.144311% | 4.33761% | 1/32 |
| lp-narrow | 42 | robust | 3.00872% | 7.0138% | 0/32 |
| hp-asymmetric | 42 | nominal | 0.156766% | 4.51129% | 0/32 |
| hp-asymmetric | 42 | robust | 4.25585% | 8.2105% | 1/32 |

All eight selected nominal designs missed the unchanged 0.1% target tolerance. Across the four paired comparisons, robust q95 target error was slightly lower once and higher three times; there is no consistent robust advantage in this pilot. Both methods had three target-passing holdout observations among 128 observations each. Those are descriptive finite-sample totals with common random factors, not independent population estimates or manufacturing-yield claims. The larger robust errors are retained and consistent with the reduced candidate opportunities and small training sample size; this experiment cannot isolate their individual contributions.

First/replay batch wall times: 60.313/54.890 seconds, including measured evaluation and raw artifact writing, excluding the outer tests/audit and plot generation. These are observed local timings, not performance guarantees. Package source SHA-256: `8bca950cc1d286f5433991e8e0e4b7d00addb5093b5521e4dfd57ac2198bc8ca`.

Evidence directory:

```text
C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Automatic_Acceptance/phase4-final-2026-11-19
```

acceptance.json stores the exact executed argument arrays, tool versions and every paired outcome. tests.xml/tests.log record the full suite; first/ and replay/ retain raw artifacts and comparison.png. Their summary manifests are hash-linked to examples/robustness-v1.json. The small unit/integration fixtures and their calls are excluded from the production comparison counts.

The package was built/installed from a byte-preserving source snapshot. Python -I outside the checkout validated the installed model/checker and independently re-audited one complete 96-call robust trial, including quantiles and selection, with the matching source fingerprint. This package check made zero new SPICE calls; package-check.json records the installed module path. The chart was also visually inspected for readable labels, units and agreement with its source data. P4-C1/C2/C3 are complete; P4-H1 is deferred as superseded, with no claim of human review. Phase 5 and remote pushes remain unstarted.

An earlier accepted run remains unchanged in Automatic_Acceptance/phase4-2026-11-19. After final EOF whitespace cleanup, the full suite and both complete physical runs were repeated against the final source bytes. Outcomes and chart match the earlier run exactly. All counts above refer to the final dataset only; repeated executions are not pooled into the comparison.
