# Phase 7: captured CLI demo and local research-MVP gate

Status: **accepted automatically on 2026-11-22** under
`phase7-local-research-mvp-v1`, for the validated local research scope only.

The final technical task uses reproducible automatic acceptance under the owner's
manual-review delegation. It checks the supported local research scope; it does
not publish a repository/site, approve personal CV use or extend PCB/agent work.

## Actual installed CLI capture

`scripts/capture_demo.py` invokes the isolated interpreter from the earlier fresh
installation with `python -I`, outside source import paths. The recorded identity
must match the current package environment and an installed `site-packages` path.
It runs exactly the three versioned example requests below with trusted ngspice,
captures complete JSON stdout, stderr, return codes, arguments and per-call raw
exports, then audits each against independent RC physics.

| Example | Expected observed status | Actual simulator calls |
|---|---|---:|
| design-lowpass | passed | 1 |
| design-optimization | passed | 4 |
| design-target-miss | target_missed, CLI exit 1 | 4 |

These **nine real calls** belong to the demo, separate from scientific-model
windows, prior install checks and unit/integration fixtures. No model is called.
The target miss remains visible; successful simulation and target success are
different outcomes.

The exporter renders five annotated frames from the captured typed results and
their measured response charts. `demo.gif` is a **75-second looping replay**, with
15 seconds per frame. Presentation timing is deliberately selected, not inference
latency or wall-clock CLI performance. Every frame labels this as captured output
with annotations, not a live screen recording. Full transcripts and raw data stay
beside the animation; no illustrative circuit measurements are substituted.

`scripts/audit_demo.py` independently checks every raw electrical trace and JSON
stdout against the typed request/result, expected command/interpreter, exit/status
and actual call budgets. It re-renders frames from those checked records, compares
lossless image pixels and encoded animation bytes, checks five frames/75 seconds,
and verifies source/transcript/artifact hashes. Incorrect calls, hidden target
misses, changed plots/text, unsupported live-capture claims and invented owner
approval block acceptance.

`claims.md` is evidence-backed draft portfolio wording. It does not claim hardware
verification, AI superiority, public deployment or an owner CV review. The checker
preserves `owner_cv_approved=false` and `remote_published=false`.

## Reproduce the capture and independent audit

Use an installed interpreter, current matching source/environment and new writable
output directory. The report/test extra provides the existing Matplotlib/Pillow
dependencies; no video encoder or new service is required.

```text
python scripts/capture_demo.py --python /isolated/environment/python --source examples --output /new/demo --ngspice /trusted/ngspice
python scripts/audit_demo.py --source examples --input /new/demo
```

The actual November 22 capture is external
`Automatic_Acceptance/p7-captured-demo-2026-11-22`, using the installed interpreter
under `p7-clean-install-2026-11-22/installed`. Capture and independent audit both
returned exit 0: nine independently raw-audited calls, two example passes and one
intentional miss. The low-pass and target-miss frames were visually inspected.
Animation SHA-256:
`2c14304c27af42c5a9bd0e52a82cae3f0eda36577a22df4799939722266ea6df`.

The ten synthetic artifact/claim regressions passed in 6.60 seconds after final
interpreter linkage checks. Synthetic fixture images are not experimental data.

## Final automatic gate

`scripts/accept_phase7.py` checks accepted task prerequisites, the earlier fresh
installation's actual tests/environment, the independently accepted scientific
composite gate and the research report's input hashes. It runs the entire current
suite without skips, independently re-audits the recorded installed demo and
requires source/test hashes to remain unchanged during acceptance. It does not
start another model or rescore previous scientific comparisons.

```text
python scripts/accept_phase7.py --output /new/phase7-acceptance --demo /existing/demo --interface-evidence /existing/p7-clean-install-2026-11-22 --primary-trial /existing/local-llama3-renewal-2026-11-21 --replay-supplement /existing/local-replay-supplement-2026-11-22 --ngspice /trusted/ngspice
```

The output contains acceptance.json, fresh tests.xml/tests.log, exact test command,
source hashes, installed-interface/report hashes and nested demo/scientific gate
decisions. Missing, inconsistent, failed or skipped evidence blocks acceptance.
Numerical same-environment checks are not a Linux/cross-platform guarantee.
Core package behavior is unchanged from the fresh installed package; source and
Git remain on C and generated evidence uses the existing artifact workspace.

The technical replacement supersedes P7-H1 only after this implemented gate
actually passes. It never records an owner review or CV approval that did not
happen. PCB, advanced agents, public hosting, paid traffic and remote pushes keep
their separate authorization boundaries.

## Observed final acceptance

The final checker returned exit 0: **438 tests passed in 158.31 seconds without
skips**, followed by an independent nine-call raw demo audit and exact animation/
transcript checks. It verified the accepted scientific composite, research input
hashes and the existing fresh installed package. All **93 source/test files**
hashed by the checker remained unchanged during acceptance. Package fingerprint:
`0e320d6e4188c9b3a52b23a3da4f278d9103043b3c07e58f1159f305724a7796`.

Exact workstation commands (invocations executed once with new output paths):

```powershell
$artifactRoot='C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534'
$python="$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe"
$env:PYTHONPATH='src'
$env:MPLCONFIGDIR="$artifactRoot/Automatic_Acceptance/matplotlib-cache"
$simulator="$artifactRoot/CircuForge/.tools/Spice64/bin/ngspice_con.exe"
$demo="$artifactRoot/Automatic_Acceptance/p7-captured-demo-2026-11-22"
& $python scripts/capture_demo.py --python "$artifactRoot/Automatic_Acceptance/p7-clean-install-2026-11-22/installed/Scripts/python.exe" --source 'C:/Users/Home/Documents/ChatGPT/Implement CircuForge/examples' --output $demo --ngspice $simulator
& $python scripts/audit_demo.py --source 'C:/Users/Home/Documents/ChatGPT/Implement CircuForge/examples' --input $demo
& $python scripts/accept_phase7.py --output "$artifactRoot/Automatic_Acceptance/phase7-local-mvp-2026-11-22" --demo $demo --interface-evidence "$artifactRoot/Automatic_Acceptance/p7-clean-install-2026-11-22" --primary-trial "$artifactRoot/Automatic_Acceptance/local-llama3-renewal-2026-11-21" --replay-supplement "$artifactRoot/Automatic_Acceptance/local-replay-supplement-2026-11-22" --ngspice $simulator
```

Evidence roots: `p7-captured-demo-2026-11-22` contains complete captured command
arguments/stdout/raw exports, five PNG frames, demo.gif, draft claims and its
independent acceptance.json. `phase7-local-mvp-2026-11-22` contains the final
438-test XML/log and composite acceptance. The full gate reuses and re-audits the
nine existing demo calls; `new_demo_spice_calls=0` means it did not capture them
again. Full-suite integration fixture calls remain a separate test population.
No new model request was made by capture, audit or final acceptance.

P7-C3 supersedes the engineering/demo/claim-verification portion of legacy P7-H1
under the owner's automatic-review instruction. P7-H1 is deferred as superseded,
not marked as a completed human review. Personal CV use remains the owner's
choice; no owner CV approval or external publication is recorded. This completes
the local research MVP gate, while preserving negative scientific results and
all documented ideal-RC/platform limitations. Optional P8 PCB/EDA work remains
unstarted and requires its separate scope decision.
