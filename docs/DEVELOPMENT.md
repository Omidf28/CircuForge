# Phase 1 implementation evidence â€” 2026-11-18

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

Actual simulator arguments: <resolved ngspice_con.exe> -n -b circuit.cir. Exact path/version are recorded per report. Each default sweep contains 601 AC samples, 1 Hzâ€“1 MHz. Temporary-path output is redacted.

## Guardrails and remaining gates

<=20,000 sweep points, <=30 seconds per call (default 10), <=1000 evaluations (default 32), 8 MiB combined output. Output size is polled every 10 ms and can briefly overshoot. This is a trusted local executable guard, not an OS security sandbox or kernel memory quota. Intermediate search candidate raw waveforms are not persisted; best-candidate raw evidence and full metric history are saved.

Linux commands are documented but untested. Finite source/load and E-series are unsupported. No human electrical approval or independent clean-workstation review is claimed. P0-H1/P0-H2/P1-H1 remain open; four distinct R/C fixtures per topology support review. Phase 2 random/grid/SciPy comparisons follow review; PCB/LLM work remains deferred.

## Phase 1 follow-up after version-control setup

Initial commit: `20ef58f` on main. Further changes are on `codex/p1-pipeline-hardening`.

Reproduced a real failure using an allowed 1 Mohm / 1 mF candidate: its cutoff falls below the default 1 Hz sweep start. Previously the CLI left raw logs but reported a generic input/artifact error without failure.json. It now records status `metric_error`, the genuine simulator return code 0, the cutoff-bracketing reason and simulator logs in failure.json; exit code remains 2. Simulator success is thus distinguishable from a measurable cutoff.

The adapter now checks every frequency against a complete logarithmic grid, with relative tolerance 1e-6 and zero absolute tolerance, instead of checking endpoints alone. This catches incorrect interior frequencies and errors hidden by an absolute tolerance on very low-frequency sweeps. Real ngspice-47 noninteger-decade sweeps span both endpoints; that grid and the traditional fixed points-per-decade grid are accepted. Verified real examples: 2–123456 Hz at 100 points/decade (480 rows), 1–1591.55 Hz at 100 (321 rows), and 3–99999 Hz at 17 (77 rows), each with analytic complex-response checks.

Latest full suite with the same environment and command above: **78 passed**, including credential-scanner tests, synthetic grid-corruption unit tests and genuine simulator regressions. Raw simulation outputs remain ignored by Git. No Phase 2 implementation was added.
