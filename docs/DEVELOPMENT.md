# Local implementation evidence

## Final local research-MVP acceptance — 2026-11-22

Implemented scripts/capture_demo.py, scripts/audit_demo.py and
scripts/accept_phase7.py. Actual isolated installed CLI generated nine bounded
SPICE calls across three versioned examples, with two passes/one intentional miss.
Full stdout/argument/raw export evidence was captured. The labeled annotated
75-second GIF and draft wording are regenerated from checked results; independent
raw audits and frame/transcript/GIF hashes passed. Ten synthetic corruption/claim
guards passed, then final **438-test suite passed in 158.31s without skips**.
The composite local gate verified scientific/install/report evidence and unchanged
93-file source/test hashes. No new model requests or duplicated demo calls were
made by that gate. P7-C3 supersedes the technical P7-H1 check, without claiming
human CV approval. Exact commands/evidence and interpretation: docs/PHASE7.md.
Optional PCB/advanced work, remote push and deployment remain outside this result.

## Local replay supplement accepted — 2026-11-22

Owner `next` approved the prepared two-request/120-second/two-SPICE local-only
envelope. Executed once without source changes: two generation requests, one
real independently raw-audited SPICE attempt, 62.656s, 4608 reserved/256 known
tokens, no unknown usage and zero provider cost. The original four comparison
trials/25 requests/65 calls, timeout, unknown usage and target misses remain
unchanged. Composite phase6-local-supplemental-replay-v1 passed; original standalone
policy stays blocked. One exact valid high-pass candidate replay; it still missed
target by 81.72176754%. No efficacy claim. The packet is now closed and after-status
reported no loaded models. Final 29 lifecycle/report tests passed in 2.95s.
Exact commands, source snapshot and evidence paths: docs/P6_REPLAY_SUPPLEMENT.md.
Updated the research report read-only with separate supplemental provenance.

## Replay-supplement preparation — 2026-11-22

Prepared a pending, separately bounded two-request local replay policy, guarded
runner and independent read-only composite auditor. No inference or simulator
execution occurred in this preparation. **364 unit tests passed in 19.33s**;
after tightening saved-envelope/unknown-usage handling and clipping simulator
timeouts to the remaining total window, the **28 targeted replay/report tests
passed in 2.14s**. The initially restricted mock-HTTP attempt
stalled during Windows asyncio setup; only identified test processes were
stopped, then mocked tests passed with local-socket permission. The scientific
resource question remains pending; original counters/deadlines are untouched.
See docs/P6_REPLAY_SUPPLEMENT.md and external
Automatic_Acceptance/p6-replay-preparation-unit-2026-11-22.xml.

Also normalized the generated SVG's trailing whitespace. Direct regeneration
from the saved numeric summary matched the versioned chart, and whitespace and
credential checks passed. This changes formatting only; no numerical claim or
raw evidence was altered.

## Documentation, report and fresh installation — 2026-11-22

P7-C1/C2 work follows its explicit P5/P3/P4 task prerequisites while the final
P7 gate still depends on P6. Added source-accurate architecture/flow and the
operation/API/troubleshooting guide. Existing `scripts/accept_phase5.py` was
executed with a new output `Automatic_Acceptance/p7-clean-install-2026-11-22`:
**408 passed in 120.41s**, no skips; newly built wheel/fresh isolated virtualenv
and actual Python -I CLI/loopback HTTP walkthrough passed. **27 actual calls**,
**18 raw CLI/ZIP calls audited**, **nine JSON traces matched**, deliberate miss
preserved, server/temp cleanup verified. See docs/OPERATIONS.md and acceptance.json.

Added `scripts/report_research.py`, nine targeted corruption/overwrite tests,
checked-in report/full-precision input hashes/measured SVG and reproduction guide.
The preliminary expanded unit suite passed **347 tests in 12.70s**. Report export
checked historical accepted summary/manifest/JUnit bindings and re-audited saved
local-model responses/raw traces without new model or SPICE calls. Historical
Phase 3/4 raw audits were not rerun. See docs/RESEARCH_REPORT.md and external
Automatic_Acceptance/research-report-versioned-2026-11-22. No numerical thresholds,
budgets, failures or old evidence were changed. Scientific replay/release remains
blocked; no provider allowance, remote push or deployment was inferred.

## Renewed local trial and public visibility — 2026-11-21

One explicitly renewed local-only run completed four matched-call comparisons
under unchanged caps: 25 model attempts, 65 independently raw-audited SPICE
attempts, no target passes. Final model replay timed out before the second check;
integrity/comparison data passed but the full Phase 6 gate remains blocked.
Latest offline verification: **293 unit tests passed in 12.78 seconds**. No new
full-suite acceptance is claimed. Exact commands, source fingerprint, known vs
reserved token usage, negative outcomes and external artifacts are recorded in
[PHASE6_LOCAL_RENEWAL.md](PHASE6_LOCAL_RENEWAL.md). Both spent packets refuse
execution; no new model/SPICE calls occurred during reporting.

The owner separately requested public GitHub visibility. Verified public after
scanning initial remote history with the common-credential checker; only initial
main remains online. No feature branch was pushed. See
[VERSION_CONTROL.md](VERSION_CONTROL.md).

## Approved local Llama 3 trial — 2026-11-20

P6-H1's explicit local-only approval followed the read-only inventory/proposal in
commit a4808d4. On codex/p6-local-ollama-trial, implemented the optional fixed
loopback adapter, persistent shared experiment budget, bounded controller and
read-only audit. Standard design CLI/API and numerical algorithms remain intact.
The first model output violated the declared C bounds. The initial controller's
stop-on-invalid-pilot condition was corrected: preserve the negative observation
and continue the same window, without changing prompts/specs/tolerance or
resetting counters. Five conservative seconds were added during original-start
reconstruction; both source epochs and the failed initial result remain archived.

Commands actually run from the C source checkout (with trusted ngspice and the
same artifactRoot/interpreter variables as the following P6-C1 section):

```powershell
$run = "$artifactRoot/Automatic_Acceptance/local-llama3-trial-2026-11-20"
& "$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe" scripts/run_local_trial.py --policy examples/local-proposal-trial-v1.json --output $run --ngspice $env:CIRCUFORGE_NGSPICE
& "$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe" scripts/run_local_trial.py --policy examples/local-proposal-trial-v1.json --output $run --ngspice $env:CIRCUFORGE_NGSPICE --continue-rejected-pilot
& "$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe" scripts/audit_local_trial.py --input $run
```

The initial run exited 1 after one invalid proposal/no SPICE. The explicit
continuation exited 1 when the original client window ended: **7 requests,
16128 reserved tokens, 764 known reported tokens plus one unknown-usage timeout,
15 real SPICE attempts**, zero provider cost. Final read-only audit exits 1 with
integrity passed/comparison blocked_incomplete. Runtime had audited 13 calls;
the independent read-only pass audited all 15. No extra simulation was used to
manufacture an audit pass. Actual counts were 4/4/4/2 for the one entered
low-pass/seed7 comparison, plus one high-pass pilot call; all targets missed.
Other comparison trials/replay were unrun. See docs/PHASE6_LOCAL_RESULTS.md.

The final verification command was `python -m pytest -q -ra -p no:cacheprovider
tests/unit --junitxml <artifactRoot>/Automatic_Acceptance/local-trial-unit-release-2026-11-20.xml`,
with PYTHONPATH=src, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and existing MPLCONFIGDIR.
Actual stdout was captured alongside that XML via Tee-Object: **289 passed in
9.90 seconds**. It made no real model or ngspice calls. Earlier focused 58/59/22
runs were controlled mock-HTTP/unit checks, not additional live model usage.
The prior full suite remains historical 319 passed for P6-C1; no fresh full-suite
or Phase 6 acceptance is claimed. Afterward only GET /api/ps was queried; no models
were loaded. Closed-allowance CLI tests reject before simulator/output creation.
No actual inference was repeated after the deadline.

Exact execution source snapshot/fingerprint, both code epochs, approved policy,
raw requests/responses, ledger, physical traces, result.json/audit.json and final
model status are preserved under $run. The current source allowance is closed;
these historical commands are not permission to rerun it. Source/Git remain on C;
ancillary execution artifacts still use the preexisting C-path junction to D.
No paid/cloud call, download, push, deployment or advanced tool agent was added.

## P6-C1 offline contract acceptance — 2026-11-20

Continued the next eligible local task on `codex/p6-offline-proposal-contract`.
Implemented strict explicit candidate JSON, a provider-neutral synchronous
interface, bounded request/token/cost/rate accounting, conservative unknown usage
and fail-closed usage-overrun handling. No provider SDK/network adapter, API key,
agent loop or comparison experiment was added. All source/Git changes remain at
`C:/Users/Home/Documents/ChatGPT/Implement CircuForge`.

Actual command from that checkout, with local socket permission for the existing
API tests:

```powershell
$artifactRoot = 'C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534'
$env:PYTHONPATH = 'src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:CIRCUFORGE_NGSPICE = "$artifactRoot/CircuForge/.tools/Spice64/bin/ngspice_con.exe"
& "$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe" scripts/accept_proposals.py --output "$artifactRoot/Automatic_Acceptance/p6-c1-2026-11-20" --ngspice $env:CIRCUFORGE_NGSPICE
```

Observed exit 0: **319 passed in 131.88 seconds**, no skips/warnings in the final
test log, then **four raw-audited real calls**. Both topology fixtures preserved
a reference pass and a deliberate miss, rejected invalid topology before SPICE
and reused one duplicate measurement. Eight fixture proposals cost zero in the
declared offline ledger; 40 synthetic fixture tokens are not actual LLM usage.
See docs/PHASE6.md and acceptance.json for exact commands/source fingerprint.
An earlier focused run passed 37 tests but emitted a sandbox cache-rename
warning; the final complete command disables the optional pytest cache provider.
The 40 new tests cover malformed/injected/ambiguous candidates, unknown usage,
exact/exhausted quotas, interruptions, overruns, rate and reentrancy, plus missing
simulator and preserved existing evidence. P6-C2 remains unrun awaiting P6-H1;
no efficacy, paid billing, deployment or full Phase 6 acceptance is claimed.

Regenerated canonical planning outputs with `python planning/render_plan.py
--output-dir <artifactRoot>/Automatic_Acceptance/p6-c1-plan-2026-11-20` and
synchronized the generated text back to the source tree through the file-edit
tool, preserving checkout newline handling because of the existing Documents
write restriction. Nine phases and 35
tasks passed dependency validation; P6-C2 now explicitly depends on P6-H1.

## Phase 5 automatic installed CLI/API acceptance — 2026-11-19

Implemented shared bounded DesignRequest/DesignResult/Waveform contracts, a measured application use case, design CLI and local FastAPI JSON/ZIP endpoints with raw evidence, plots, checksum manifests, body/compute/concurrency limits and temporary cleanup. Optional API/test dependencies were installed from official PyPI. Existing commands and numerical experiments remain unchanged. The optional frontend is deferred per START_CODEX.md.

Executed from the active checkout (PowerShell) with local socket permission:

```powershell
$artifactRoot = 'C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534'
$env:PYTHONPATH = 'src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:CIRCUFORGE_NGSPICE = "$artifactRoot/CircuForge/.tools/Spice64/bin/ngspice_con.exe"
$env:MPLCONFIGDIR = "$artifactRoot/Automatic_Acceptance/matplotlib-cache"
& "$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe" scripts/accept_phase5.py --output "$artifactRoot/Automatic_Acceptance/phase5-2026-11-19" --ngspice $env:CIRCUFORGE_NGSPICE
```

Observed exit 0, **279 tests without skips**, fresh source-byte-preserving wheel and independent virtual environment installation under output/installed. The gate removed PYTHONPATH for build/install/walkthrough and invoked the installed package using Python -I. Real loopback Uvicorn/HTTP and CLI agreed across three examples: **27 actual calls**, **18 full raw CLI/ZIP calls independently audited**, **nine JSON calls matched by numerical traces**. Two passing reference/smoke examples and one deliberate four-call target miss per interface were retained. Server shutdown and empty temporary storage were verified. The PNG was visually inspected. Exact build/install/test/walkthrough arguments, constraints, versions, wheel/source hashes and outputs are preserved in acceptance.json and adjacent logs/artifacts; details are in docs/PHASE5.md.

Focused runs before the final command: 25 initial boundary tests, seven initial real-export checks, then 43 extended tests. The sandbox initially stalled Windows asyncio in its internal socketpair before dispatching a request; a faulthandler traceback identified the environment restriction. Those test processes were stopped and the same tests passed with local loopback tool permission. No fabricated pass, altered electrical threshold or manual technical waiver. No deployment, provider/LLM traffic, advanced agent, PCB work or feature-branch push.

## Phase 4 automatic acceptance — 2026-11-19

Implemented typed independent uniform component-error sampling, explicit perturbed simulation envelopes, measured nominal/robust objectives, separate holdout samples, empirical quantiles/pass rates and a raw-data/replay checker. Matplotlib is optional for core use and declared in report/test extras for experiment plots. The shared raw evaluation audit still passes all historical baseline integrations. Prespecified model/configuration and outcomes are in docs/PHASE4.md.

Executed from the active checkout (PowerShell):

```powershell
$artifactRoot = 'C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534'
$env:PYTHONPATH = 'src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:CIRCUFORGE_NGSPICE = "$artifactRoot/CircuForge/.tools/Spice64/bin/ngspice_con.exe"
$env:MPLCONFIGDIR = "$artifactRoot/Automatic_Acceptance/matplotlib-cache"
& "$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe" scripts/accept_phase4.py --output "$artifactRoot/Automatic_Acceptance/phase4-final-2026-11-19" --ngspice $env:CIRCUFORGE_NGSPICE
```

Observed exit 0: **234 full-suite tests without skips**, policy phase4-tolerance-v1 passed, two cases/two seeds/two methods, 768 calls/run and **1536 raw calls audited including exact numerical replay**. Every method/trial spent 64 training plus 32 independent holdout calls. All selected nominal designs missed the original 0.1% tolerance. Robust holdout q95 was lower once and higher three times; neither general superiority nor hardware yield is established. Both methods had 3 passes among 128 paired holdout observations. No unexpected simulation/verification failures or cached calls. Exact commands/tool versions/outcomes are in acceptance.json; tests.xml/tests.log and both raw datasets/plots are retained. Earlier 36 focused tests passed before the full run; their fixture calls are separate from the production count.

Built/installed a byte-preserving source snapshot with no dependency upgrades to the numerical stack. Optional Matplotlib 3.11.2 and its declared dependencies were installed in the isolated environment. Python -I outside the checkout validated the installed module and independently re-audited a complete existing 96-call robust trial (zero additional SPICE calls), with matching source fingerprint; package-check.json records the result. The PNG was visually checked. Repaired legacy UTF-8 prose in planning/HANDOFF.md and docs/PHASE3.md without altering numerical evidence. Final EOF whitespace cleanup was followed by a complete fresh acceptance run against the final package fingerprint; the earlier phase4-2026-11-19 run remains separate and unchanged. Counts above refer to the final dataset, not pooled reruns. No Phase 5 implementation or remote push.

## Phase 3 automatic acceptance — 2026-11-19

Implemented typed expected-feasibility benchmarks, normalized duplicate rejection, bounded multi-seed experiments and an independent raw-data/replay checker. The initial v1 numerical run passed but a structural audit found three scale-equivalent pairs; v1 remains superseded evidence. Revised v2 bounds were declared before the new run, with unchanged seeds, budgets and tolerances. See docs/PHASE3.md for complete configuration and outcomes.

Executed from the active checkout (PowerShell):

```powershell
$env:PYTHONPATH = 'src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$artifactRoot = 'C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534'
$env:CIRCUFORGE_NGSPICE = "$artifactRoot/CircuForge/.tools/Spice64/bin/ngspice_con.exe"
& "$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe" scripts/accept_phase3.py --output "$artifactRoot/Automatic_Acceptance/phase3-v2-2026-11-19" --ngspice $env:CIRCUFORGE_NGSPICE
```

Observed: exit 0, phase3-reproducibility-v2 passed, **198 full-suite tests without skips**, 20 cases, three seeds, 180 trials/1530 actual calls per run and **3060 calls audited including exact numerical replay**. Per run: 18 fixed-control target passes, 126 free-domain target misses, 36 expected infeasible rejections, zero simulation failures. Complete argument arrays and simulator version are preserved in acceptance.json; tests.xml/tests.log and first/replay raw artifacts remain untouched. The structural v1 rejection is separately saved in Automatic_Acceptance/phase3-v1-structural-audit.json.

Built/installed a local snapshot in the isolated environment. The initial no-build-isolation attempt failed on absent setuptools; normal isolated building from official PyPI succeeded. Python -I outside the checkout validated the v2 manifest and independently re-audited 13 existing call artifacts, matching the source/environment fingerprint and adding zero SPICE calls. package-check.json records this verification. No Phase 4 implementation or feature-branch push.

## Original Phase 1 evidence — 2026-11-18

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
