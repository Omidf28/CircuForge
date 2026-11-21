# Phase 6: renewed local trial — 2026-11-21

Status: **comparison data complete; overall Phase 6 acceptance blocked**.
The four prespecified matched-call comparisons completed. The final model replay
stage did not: its first request timed out at the experiment deadline and its
second request was not run. Integrity acceptance is separate from that gate and
from circuit target success. No manual technical signoff is required.

## Authorization and fixed inputs

The owner answered `next` to the explicit request for one fresh local-only run
with the same limits as the closed November 20 trial. The separate packet is
`examples/local-proposal-trial-renewal-2026-11-21.json`; it is now closed too.
The original dataset remains historical in `PHASE6_LOCAL_RESULTS.md`. These runs
are not pooled. No continuation or source change occurred during this renewal.

Limits remained 32 model requests, 73728 reserved tokens, 600 seconds, 80 SPICE
attempts, zero provider spending, two CPU threads and no GPU layers. The installed
`llama3:latest` digest remained
`365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`.
No download, cloud provider, credentials, private-file transmission or service
configuration change was involved. Loopback transport remained fixed.

Two ideal unloaded RC topologies, seeds 7/42, target 2300 Hz, R=100..10000 ohm,
C=1e-8..1e-6 F and target relative error 0.001 were unchanged. Each method received
four actual SPICE attempts per case/seed, with at most seven model proposals.
Invalid proposals and duplicate cache hits were retained; no substitute search
was used to repair model output. The default sweep was 1 Hz..1 MHz at 100 points
per decade. Both topologies share the same analytic cutoff equation.

## Observed results

- 25 generation attempts: 17 accepted proposals, seven invalid candidates and
  one provider-error timeout. An accepted proposal need not be a new simulation.
- 65 actual SPICE attempts, all independently audited from raw simulator data;
  64 comparison calls and one pilot call. None met the unchanged 0.1% target.
- Four matched-call comparisons, each containing all four methods at four calls.
- 57600 reserved tokens, 3079 known reported tokens and one unknown-usage request.
  Its full 2304-token reservation was retained; 3079 is not total actual usage.
- Final accounting elapsed 600.031 seconds includes cancellation/record cleanup.
  The client stopped at the 600-second limit; this does not authorize an extension
  or claim an OS-enforced resource quota. Provider expenditure was zero.
- One replay request attempted and timed out, zero completed replay observations,
  second replay unrun. Read-only `/api/ps` afterward reported no loaded models.

Best measured relative cutoff error in percent (lower is better):

| Case / seed | Random | Grid | SciPy | Local Llama 3 |
|---|---:|---:|---:|---:|
| Low-pass / 7 | 31.09% | 30.80% | 33.17% | 56.18% |
| Low-pass / 42 | 49.83% | 30.80% | 13.94% | 38.66% |
| High-pass / 7 | 31.09% | 30.80% | 33.16% | 81.72% |
| High-pass / 42 | 49.82% | 30.80% | 13.95% | 35.93% |

All 16 method results missed the 0.1% tolerance. The model did not beat the best
classical result in any of these four cells. This tiny, two-topology study does
not establish a general model-performance conclusion. Equal SPICE attempts do
not imply equal compute or wall time; inference adds runtime. Grid repetitions
are deterministic controls, not independent samples. No hardware claim is made.

## Evidence and exact commands

External artifact root used below:

```powershell
$artifactRoot='C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534'
$python="$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe"
$run="$artifactRoot/Automatic_Acceptance/local-llama3-renewal-2026-11-21"
$env:PYTHONPATH='src'
$env:CIRCUFORGE_NGSPICE="$artifactRoot/CircuForge/.tools/Spice64/bin/ngspice_con.exe"
& $python scripts/run_local_trial.py --policy examples/local-proposal-trial-renewal-2026-11-21.json --output $run --ngspice $env:CIRCUFORGE_NGSPICE
```

That executed once and returned exit 1 at the deadline. **Do not rerun this
command against the spent allowance**; the source packet now refuses execution.
The sibling `local-llama3-renewal-2026-11-21-source` directory preserves the
pre-run source/environment snapshot, based on local commit `9a6d431` plus the
identified renewal packet. Package-source SHA-256 fingerprint:
`0e320d6e4188c9b3a52b23a3da4f278d9103043b3c07e58f1159f305724a7796`.
The policy copy inside the run records its execution-time state; the repository
copy records subsequent closure. There was no numerical-policy change.

Afterward only offline tests and read-only postprocessing ran:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:MPLCONFIGDIR="$artifactRoot/Automatic_Acceptance/matplotlib-cache"
& $python -m pytest -q -ra -p no:cacheprovider tests/unit --junitxml "$artifactRoot/Automatic_Acceptance/local-renewal-unit-2026-11-21.xml" |
  Tee-Object -FilePath "$artifactRoot/Automatic_Acceptance/local-renewal-unit-2026-11-21.log"
& $python scripts/audit_local_trial.py --input $run
& $python scripts/plot_local_trial.py --input $run --output "$run/plots"
```

Observed: **293 unit tests passed in 12.78 seconds**, no skips. This unit run
made no model or simulator calls and is not a new full-suite acceptance replacing
the historical 319-test P6-C1 result. The auditor reconstructed proposal/usage
ledgers from saved model replies and checked all 65 raw physical responses.
`audit.json` reports `integrity_status=passed`, `comparison_data_status=complete`,
`completed_equal_budget_trials=4`, `completed_replay_checks=0` and
`phase6_comparison_status=blocked_incomplete`; intentional auditor exit code 1.
Provider errors cannot count as completed replay observations; regression tests
cover that distinction. Plot export returned exit 0 with 16 measured CSV records.
The resulting PNG was visually inspected for readable labels and values.

Raw evidence includes `result.json`, `audit.json`, model request/response files,
budget ledger, comparison evaluations and `model-status-after.json`. The plots
directory contains `matched-comparisons.csv` and `matched-comparisons.png`.
Artifacts remain local, excluded from Git. Source and Git remain on C; the
existing artifact junction resolves to D as documented in the handoff.

## Remaining gate

P6-H1 records the actual restricted resource decisions; both execution windows
are closed. P6-C2 and Phase 6 remain blocked on the planned replay stage. Missing
evidence is not waived or replaced by coincidentally repeated earlier prompts.
Any additional model execution requires a fresh bounded resource decision.
Offline reporting can proceed without new generation or SPICE calls. Public
repository visibility was separately authorized on November 21; it did not push
these local implementation changes. See `VERSION_CONTROL.md`.
