# Phase 1 implementation evidence — 2026-11-18

## Modules and contracts

- domain/specs.py: immutable Pydantic SI models, finite numbers, topology/policy allowlists, source/load assumptions, bounds, target feasibility and resource limits.
- synthesis/rc.py: fixed two-topology numeric templates. No arbitrary netlist, .control, .include, path or shell input.
- simulation/ngspice.py: executable/version preflight, -n disables startup files, -b batch mode, shell=False, closed stdin, temp files, timeout/kill/wait, return codes, sanitized logs and output guard.
- simulation/metrics.py: normalized complex transfer, gain/phase, independent analytic response, half-power interpolation.
- optimization/search.py: deterministic bounded measured bisection; duplicate detection, strict call cap, convergence flag and candidate/metric history. Analytic formula constrains the bracket; real simulated cutoff drives updates. Not a Phase 2 baseline comparison.
- cli.py: preflight, simulation/search, JSON/CSV/raw evidence, new-directory requirement and explicit exit codes.

## Environment and provisioning

Actually tested: Windows 11 (10.0.26300), Python 3.12.7, NumPy 1.26.4, Pydantic 2.13.4, pytest 9.2.0, ngspice-47 console (Aug 11 2026 build).

The supplied ZIP was planning-only. The existing VideoPlayer workspace is a different application. Documents writes/extraction failed with WinError 2 even on escalation; CircuForge was extracted separately into the authorized visualization workspace. Existing VideoPlayer files were untouched.

ngspice was initially absent; configured package mirror lacked pytest. Resolved locally, without global environment changes:

```text
python -m pip install --index-url https://pypi.org/simple --target .test-deps pytest
python -m pip install --index-url https://pypi.org/simple --target .test-deps py7zr
```

Downloaded https://downloads.sourceforge.net/project/ngspice/ng-spice-rework/47/ngspice-47_64.7z (13,814,879 bytes). Extracted only Spice64/bin members with py7zr into .tools after Windows tar failed to unpack reliably. Sources: [official instructions](https://ngspice.sourceforge.io/download.html), [release directory](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/). py7zr is setup tooling, not an application dependency. .tools/.test-deps/.test-install and build products are ignored and excluded from the source archive.

Actual package installation check:

```text
python -m pip install --no-deps --no-build-isolation --target .test-install .
```

Wheel built and installed successfully. Normal installation is in README.

## Exact verification commands

PowerShell, project root:

```powershell
$env:PYTHONPATH = '.test-deps;src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:CIRCUFORGE_NGSPICE = (Resolve-Path '.tools\Spice64\bin\ngspice_con.exe').Path
python -m circuforge preflight
python -m pytest -q -ra
python -m circuforge simulate --spec examples/lowpass.json --output evidence/lowpass-2026-11-18
python -m circuforge simulate --spec examples/highpass.json --output evidence/highpass-2026-11-18
python -m circuforge simulate --spec examples/search.json --search --output evidence/search-2026-11-18
```

Output directories must be new; choose new paths to repeat. Low-pass evidence predates added search report fields but uses the same validated netlist/parser. Disabling plugin autoload isolates this suite from a globally installed unrelated anyio deprecation warning.

Final observed result: **63 passed**. Eleven integration cases exercise 8 real topology/R/C/amplitude fixtures, 2 repeatable budgeted search cases and 1 CLI export. Offline tests verify numeric assumptions, injection rejection, absent executable, timeout, output cap, launch and nonzero exits. No fabricated electrical output is used for integration.

Earlier absent-binary run: 47 passed / 4 skipped. First real integration run exposed a monotonicity check stricter than printed precision. Measured maximum apparent passband rise was 3.22e-7 dB; fixed allowance is 1e-5 dB. Batch .print has roughly six significant digits on this build despite numdgt in options. Complex fixture tolerance: rtol=2e-5, atol=1e-8; phase tolerance 0.001 degrees. Cutoff tolerance: 0.1%.

Observed low-pass: measured 1591.487745916 Hz vs analytic 1591.549430919 Hz (0.003876% error). High-pass: 1591.612597494 Hz (0.003969%). Search target 2300 Hz: measured 2300.380616684 Hz (0.016549%), 12/24 calls; R=2772.41649025622 ohm, C=2.495429196601475e-8 F. Analytic fc for selected search candidate: 2300.469110976 Hz.

Actual simulator arguments: <resolved ngspice_con.exe> -n -b circuit.cir. Exact path/version are recorded per report. Each default sweep contains 601 AC samples, 1 Hz–1 MHz. Temporary-path output is redacted.

## Guardrails and remaining gates

<=20,000 sweep points, <=30 seconds per call (default 10), <=1000 evaluations (default 32), 8 MiB combined output. Output size is polled every 10 ms and can briefly overshoot. This is a trusted local executable guard, not an OS security sandbox or kernel memory quota. Intermediate search candidate raw waveforms are not persisted; best-candidate raw evidence and full metric history are saved.

Linux commands are documented but untested. Finite source/load and E-series are unsupported. No human electrical approval or independent clean-workstation review is claimed. P0-H1/P0-H2/P1-H1 remain open; four distinct R/C fixtures per topology support review. Phase 2 random/grid/SciPy comparisons follow review; PCB/LLM work remains deferred.

## Phase 1 follow-up after version-control setup

Initial commit: `20ef58f` on main. Further changes are on `codex/p1-pipeline-hardening`.

Reproduced a real failure using an allowed 1 Mohm / 1 mF candidate: its cutoff falls below the default 1 Hz sweep start. Previously the CLI left raw logs but reported a generic input/artifact error without failure.json. It now records status `metric_error`, the genuine simulator return code 0, the cutoff-bracketing reason and simulator logs in failure.json; exit code remains 2. Simulator success is thus distinguishable from a measurable cutoff.

The adapter now checks every frequency against a complete logarithmic grid, with relative tolerance 1e-6 and zero absolute tolerance, instead of checking endpoints alone. This catches incorrect interior frequencies and errors hidden by an absolute tolerance on very low-frequency sweeps. Real ngspice-47 noninteger-decade sweeps span both endpoints; that grid and the traditional fixed points-per-decade grid are accepted. Verified real examples: 2–123456 Hz at 100 points/decade (480 rows), 1–1591.55 Hz at 100 (321 rows), and 3–99999 Hz at 17 (77 rows), each with analytic complex-response checks.

Latest full suite with the same environment and command above: **78 passed**, including credential-scanner tests, synthetic grid-corruption unit tests and genuine simulator regressions. Raw simulation outputs remain ignored by Git. No Phase 2 implementation was added.

## Active workspace and interrupted search evidence

The repository now also exists at `C:/Users/Home/Documents/ChatGPT/Implement CircuForge`, the active project folder, with its complete local Git history and private origin preserved. The earlier visualization-workspace copy remains intact as the source of locally provisioned test dependencies/ngspice and original ignored evidence. Work continues on `codex/p1-search-failure-evidence`; no feature branch was pushed.

The search now raises a structured SearchFailure on simulator or cutoff-metric failure. It retains previous measured evaluations, the attempted call count including the failed call, the failed candidate/spec, simulator status/return code and logs. CLI failure.json includes that context; circuit.cir and logs describe the failed attempt. The failed attempt has no fabricated cutoff. Eleven controlled unit tests cover first/later timeout, nonzero exit, parse and launch failures, metric failure, CLI evidence and budget exhaustion. Latest suite: **89 passed**.

This managed Windows environment still denies Python directory creation under Documents, even after escalation. The real CLI's attempt to create runs/active-workspace-check failed with WinError 2; pytest cache creation emitted the same environmental warning. File checkout via Git and edits via the file tool work. Use an absolute output/cache path in the authorized visualization workspace for execution evidence; do not disable Windows protections. This limitation is separate from simulator success. External-tool paths are supplied through environment variables, not hardcoded in application code.

## Fresh installation and eight-case electrical packet

Created a new virtual environment (without system-site-packages) at `C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Phase1_Verification/.venv`. A source snapshot of the active repository, excluding ignored files and Git metadata, is under the same directory's source/. Installed it using:

```text
.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple "./source[test]"
```

This built and installed the wheel with fresh NumPy 2.5.5, Pydantic 2.14.3 and pytest 9.2.0 on Python 3.12.7. Verified `python -I` imports circuforge from the virtualenv's site-packages, not the active source tree. The installed console entry point passed preflight. From the verification directory:

```text
.venv/Scripts/circuforge.exe preflight
.venv/Scripts/python.exe -I -m circuforge simulate --spec source/examples/lowpass.json --output installed-lowpass
.venv/Scripts/python.exe -I -m circuforge simulate --spec source/examples/search.json --search --output installed-search
```

Both installed-package demos exited 0. Low-pass cutoff remained 1591.487745916 Hz; bounded search remained 2300.380616684 Hz in 12 calls. With CIRCUFORGE_NGSPICE set to the previously verified ngspice-47 executable and PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, ran `../.venv/Scripts/python.exe -I -m pytest -q -ra` from source/: **97 passed**. Pytest importlib mode prevents module-name collisions between unit/integration tests.

Added examples/phase1-fixtures.json, scripts/verify_phase1.py and docs/PHASE1_REVIEW.md. The runner validates the complete typed input before output creation or SPICE calls, caps reference cases at 16, rejects unsafe/duplicate IDs and inconsistent tabulated cutoffs, and preserves existing output directories. Six unit tests verify these guards. It records progress after each case, source fingerprint, actual commands and independent response/phase/gain/cutoff comparisons.

Executed `python scripts/verify_phase1.py --output C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Phase1_Verification/fixtures` from the active project. All eight real cases passed. Summary and per-case raw evidence are under that output. Maximum relative cutoff error: 5.8908193419249244e-5 (0.005891%). Tested source fingerprint: `1d2a8d5f1fa3a0e44dabb03f43e3fb284db026926a57580dd52e64a0be7cb9b0`. The review summary explicitly leaves human review pending.

Search failure records also include preflight version and attempted command. A real AC run followed by an intentionally missing executable verifies that the first genuine measurement survives the next real launch failure. Missing simulator during search preflight records zero AC attempts. No fixture results are substituted for failed simulations.

For the Documents write restriction, the roadmap renderer now supports `--output-dir`. Ran `python planning/render_plan.py --output-dir C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Phase1_Verification/generated` successfully: 9 phases/31 tasks, dependencies validated. Generated files were synchronized back using the file-edit tool; canonical source JSON remains in the active repository. Human task statuses were preserved.

## Review regression: minimum AC sample count

The Phase 1 review reproduced an accepted sweep from 100 to 100.000001 Hz at 100 points/decade. Its count was 1; genuine ngspice exited 0 with one data row, then Response rejected the data with parse_error. Sweep validation now requires expected_points >=2, matching the response/metric contract. The invalid request is rejected before output allocation and before constructing the simulator, including the --search CLI path.

Added eight unit cases: three frequency scales reject single-sample sweeps, three density settings accept exactly one interval/two samples, and both CLI modes reject before preflight. Two new real integration cases verify that the minimum two-sample grid around a 101 Hz cutoff remains usable for low/high-pass, within 0.1% interpolation error.

Executed the isolated virtualenv interpreter from the active checkout with PYTHONPATH=src, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, CIRCUFORGE_NGSPICE pointing to the verified ngspice-47 binary, and `-m pytest -q -ra -o cache_dir=C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Phase1_Verification/pytest-cache`: **107 passed in 6.83s**, no skips. This run imports the updated source rather than the preceding installed wheel. Human approval and Phase 2 remain unchanged.

## Review regression: tolerance-aware feasibility

The next review reproduced a rounded target of 1591.5494 Hz being rejected for fixed 1000 ohm / 1e-7 F bounds. The analytic reference is 1591.5494309189537 Hz; the existing real low-pass measurement 1591.4877459159616 Hz has relative error 3.873840424839514e-5 against that target, below the selected .001 tolerance. Exact-range validation incorrectly rejected an acceptable specification.

The schema now rejects a target only when achievable [fc_min,fc_max] and accepted [target*(1-tolerance),target*(1+tolerance)] intervals are disjoint. Component bounds, target-inside-sweep validation, measured-error acceptance and analytic verification are unchanged. This is a Phase 1 schema correction, not implementation of Phase 2 optimizer baselines.

Added eleven unit cases covering below/above, fixed/varying R bounds, acceptance/rejection, touching intervals and tightened tolerance; four genuine CLI integration cases verify direct simulation and bounded search for both RC topologies, each with exactly one call at fixed bounds. Added examples/fixed-target.json for reproduction. Using the same interpreter/environment and pytest command as the preceding section: **122 passed in 6.68s**, no skips. Human reviews remain open; nothing pushed.
