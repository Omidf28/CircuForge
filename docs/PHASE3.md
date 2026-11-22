# Phase 3 — versioned nominal RC benchmark

## Prespecified experiment

`examples/benchmark-v2.json` is the current curated version 2.0 fixture. Its revised bounds were frozen before v2 execution. It contains 20 distinct tasks: 14 free continuous R/C domains, two fixed-domain controls and four intentionally unreachable targets. Both low-pass and high-pass are represented. Free target frequencies span 10 Hz to 400 kHz. These are engineering fixtures, not a random population of real-world applications. One task explicitly reuses Phase 2 target/bounds for continuity; this experiment has its own declared budget and must not replace the Phase 2 scores.

Every case states target, R/C bounds, source/load, sweep, allowed relative target error, expected feasibility and rationale. Assumptions remain ideal zero-ohm voltage source, infinite load and ideal continuous components. Target tolerance is 0.001 (0.1%); independent measured/analytic cutoff tolerance is also 0.1%. Malformed/unsupported inputs cannot be disguised as expected infeasibility. Cases differing only by timeout or evaluation count are rejected as duplicates. A dimensionless signature also rejects scale-equivalent search tasks: topology, sorted log10 component widths, log10(target/max achievable cutoff) and target tolerance, with logarithms rounded to ten decimal places. Sorting catches exchanged R/C widths. Sweep differences alone cannot disguise a duplicate normalized task.

The superseded v1 fixture is retained for a rejection regression. Its initial numerical/physics/replay gate passed (195 tests, 3060 audited calls), but a subsequent structural check found three equivalent pairs: lp-10hz/lp-1000hz, hp-120hz/hp-12000hz and lp-300hz/lp-30000hz. It therefore does not satisfy the current distinctness policy and is excluded from current scores. V2 changes the latter case's bounds in each pair, without changing seeds, budgets or thresholds; the revision addresses mathematical redundancy rather than optimizer outcomes. Original v1 evidence remains untouched.

The predefined seeds are 7, 42 and 2026. Each method receives 12 attempted SPICE calls on each free case, with separate caches and no early target stop. Fixed domains use exactly one call per method; expected infeasible cases use zero calls and never enter the optimizer. Thus the configured conservative cap is 2,160 calls per run, below the enforced maximum of 2,500. Expected actual execution is 1,530 calls, 180 trials per run, including 36 infeasible rejections; the independent replay doubles these call/trial counts. Grid ignores seeds by design, so its repetitions must not be treated as independent random samples. Differential evolution's population is 10 in the two-dimensional free domains; 12 calls is a small pilot budget, not an optimizer convergence claim.

## Run and automatic acceptance

From the repository root, after following README installation/preflight:

```powershell
$env:PYTHONPATH = 'src'
python scripts/run_benchmark.py --output evidence/benchmark-v2
python scripts/accept_phase3.py --output evidence/phase3-acceptance
```

Supply `--ngspice` for a trusted executable override and `--manifest` for a different validated experiment. Output directories must be new. No API credentials or network service are needed. The acceptance command runs the complete pytest suite without skips, then executes the manifest twice, with a 600-second timeout on each benchmark process. Tests have a 180-second timeout; each simulator attempt retains its spec timeout, bounded output, trusted template and proposal/call limits.

`phase3-reproducibility-v2` first enforces the strengthened case distinctness checks, then audits every trial against the manifest hash and current source/environment fingerprint, checks matched actual method budgets, and independently recomputes complex RC response, cutoff, objective, constraint/verification/target flags and chosen best candidate from raw ngspice output. It cross-checks CSV data, history and summary aggregates. Runtime must be finite, nonnegative and consistent with nested recorded times. The two runs must have exactly equal candidate/metric/status traces and proposal/cache/stop accounting. Wall-clock timings are recorded and excluded from numerical replay. Exact replay is only asserted in the recorded environment; no cross-platform bitwise guarantee is implied.

Failures, missing/skipped tests, changed inputs/source, incomplete runs, corrupted records or numerical replay differences block acceptance with `acceptance.json` status `blocked`. This gate automates P3-H1's technical checks under the owner's delegation, without inventing human signoff or extending publication/spending permissions.

## Interpret the output

Each `seed-N/case/method/report.json` contains typed configuration, optimizer settings, environment, full call history and best candidate. `evaluations/call-NNNN/` contains the trusted netlist, stdout/stderr, response CSV and evaluation metadata. Infeasible tasks instead contain `rejection.json`; they never count as successful circuit designs. `summary.json` records each trial and per-method aggregates, elapsed time and failure counts. The manifest stays versioned in Git. Raw evidence is generated locally and excluded from source archives.

- Simulation success: ngspice exits successfully and produces the expected frequency response.
- Numerical verification: raw response and cutoff agree with the independent ideal RC model.
- Design success: a verified candidate also satisfies the original 0.1% target tolerance.
- Expected infeasible rejection: valid typed constraints cannot reach the tolerance interval; no simulator call is spent.
- Invalid input/candidate or unexpected execution failure: a separate error, never a target success or expected rejection.

Acceptance means the experiment and its numerical replay passed these engineering checks. Target misses remain misses. Small curated nominal experiments do not establish hardware robustness, optimizer superiority or manufacturing performance. Phase 4 tolerance experiments remain separate.

## Observed evidence

Executed on 2026-11-19 using Windows 11, Python 3.12.7, ngspice-47, NumPy 2.5.5, Pydantic 2.14.3 and SciPy 1.18.1. Final acceptance: **passed**, policy **phase3-reproducibility-v2**, **198 tests without skips**, **3060 raw calls audited** including replay. Each run completed all 180 trials across 20 cases and three seeds, with 1530 actual calls and exact numerical trace equality. The 36 infeasible rejections per run spent zero calls.

| Method | Feasible trials | Design passes | Target misses | Infeasible rejections | Actual calls | Simulation failures |
|---|---:|---:|---:|---:|---:|---:|
| random | 48 | 6 | 42 | 12 | 510 | 0 |
| grid | 48 | 6 | 42 | 12 | 510 | 0 |
| scipy | 48 | 6 | 42 | 12 | 510 | 0 |

All 18 successful designs per run are fixed-domain controls. All 126 free-domain trials missed 0.1% at the predefined 12-call budget. No optimizer superiority or convergence is established. These misses are preserved in acceptance.json and summaries; all physical measurements nevertheless passed independent analytic verification.

Median best target relative error across all three seeds (percent; grid repeats are identical):

| Case | Random | Grid | SciPy |
|---|---:|---:|---:|
| lp-10hz | 8.84314% | 59.1488% | 7.34391% |
| hp-30hz | 22.5205% | 3.9122% | 8.67547% |
| lp-50hz | 26.7478% | 47.7413% | 11.7431% |
| hp-120hz | 3.82557% | 32.6344% | 19.814% |
| lp-300hz | 34.7559% | 14.2888% | 2.19562% |
| hp-750hz | 8.61696% | 112.215% | 4.89275% |
| lp-1000hz | 15.289% | 8.3584% | 2.0516% |
| hp-2300hz | 31.0861% | 30.7995% | 13.9514% |
| lp-5000hz | 19.4411% | 31.4267% | 57.3187% |
| hp-12000hz | 17.8765% | 25.7334% | 29.9716% |
| lp-30000hz | 13.3271% | 6.29664% | 15.1396% |
| hp-90000hz | 20.4099% | 76.8458% | 21.8156% |
| lp-180000hz | 20.2178% | 90.4813% | 43.35% |
| hp-400000hz | 17.2696% | 14.2721% | 23.3441% |
| lp-fixed | 0.00387578% | 0.00387578% | 0.00387578% |
| hp-fixed | 0.00521957% | 0.00521957% | 0.00521957% |
| lp-unreachable-fixed | rejected | rejected | rejected |
| hp-below-range | rejected | rejected | rejected |
| lp-above-range | rejected | rejected | rejected |
| hp-unreachable-fixed | rejected | rejected | rejected |

First/replay batch wall times were 107.375/103.563 seconds, including simulation, evaluation and artifact writing; the outer acceptance command also includes tests and audits. Timings are observations, not portable performance guarantees. Package source SHA-256: `b75bfab66c376aac5b33e582c47c60a9d5771b9f5fd5b179ecd39dc05d04ef10`.

Final evidence directory:

```text
C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Automatic_Acceptance/phase3-v2-2026-11-19
```

acceptance.json retains exact interpreter/test/benchmark argument arrays and simulator version; first/ and replay/ retain untouched raw data, manifests are hash-linked, and tests.xml/tests.log document the full suite. The earlier superseded v1 is under Automatic_Acceptance/phase3-2026-11-19; its later structural rejection is recorded in phase3-v1-structural-audit.json. Neither is mixed into final v2 scores or call counts.

Packaging: built and installed a source-byte-preserving snapshot into the isolated environment using pip build isolation. An initial --no-build-isolation attempt correctly failed because setuptools was absent there; normal isolated building fetched the build requirement and succeeded. Python -I from outside the checkout validated all 20 v2 cases and re-audited 13 existing call artifacts (one free run and one fixed run), with the same source/environment fingerprint. No additional simulator calls were made by this package check; package-check.json records the installed module location.
