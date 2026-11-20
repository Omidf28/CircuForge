# Local Llama 3 trial — incomplete, no efficacy conclusion

Observed 2026-11-20 under the owner's explicit P6-H1 approval. The local adapter,
bounded runner and read-only auditor are implemented. **The equal-budget
comparison did not complete; P6-C2 and the Phase 6 gate are blocked.** Engineering
integrity of retained evidence passed its independent audit. Model efficacy,
superiority and general inferiority are not established.

## Observed resources and outcomes

- Existing local Ollama 0.40.16, pinned `llama3:latest` 8B/Q4_0 digest
  `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`.
- Seven generation attempts, six completed usage reports totaling **764 known
  input/output tokens**. One request timed out with unknown usage; its complete
  2304-token reservation was retained, not counted as zero actual consumption.
- **16128 globally reserved tokens**, **15 real SPICE attempts**, **zero provider
  expenditure**. No provider invoice or model download was involved.
- Request settings: two CPU threads, zero GPU layers, 2048 context tokens, 256
  maximum output tokens, no proxy/redirect/cloud fallback, `keep_alive=0`.
  These are requested runtime settings, not independent hardware utilization
  measurements or an OS resource quota.
- The conservatively retained experiment clock ended at **600.028 seconds**,
  including cancellation/record cleanup. No new generation or SPICE request was
  started after its deadline. Final request cancellation occurred after 19.781
  client seconds, within its 60-second per-request maximum. Read-only `/api/ps`
  afterward reported no loaded models.

The initial low-pass pilot proposed 820 ohm and **35.5 microfarad**, outside the
allowed 10 nF–1 microfarad capacitance interval. It was rejected before SPICE.
The high-pass pilot proposed 560 ohm/68 nF: physically verified cutoff
4179.600653363 Hz, an **81.7218%** miss against the unchanged 2300 Hz target.

Only low-pass/seed 7 entered the four-method comparison:

| Method | Actual SPICE attempts | Best target relative error | Passed 0.1% target? |
|---|---:|---:|---|
| random | 4 | 31.0862% | No |
| grid | 4 | 30.8049% | No |
| SciPy | 4 | 33.1705% | No |
| local Llama 3 | 2 | 56.1843% | No |

Its five model proposals were two invalid candidates, two accepted candidates
and a timed-out request. Across pilots and that trial, totals were three invalid
proposals, three accepted proposals and one unknown-usage failure. All 15 measured
circuits failed the target tolerance; all retained responses passed independent
RC physics checks. The low-pass/seed 42 and both high-pass comparisons, plus the
two replay checks, were **unrun**, not failed or zero-valued measurements.

Unequal actual method calls and only one partial trial prohibit a fair efficacy
comparison. The table is descriptive evidence, not a ranking or statistical
claim. There are **zero completed equal-budget trials**.

## Corrected orchestration and preserved provenance

The first controller stopped the entire experiment after the first invalid
pilot. That was an unnecessarily strict orchestration condition: rejection is
expected research data. It was corrected to retain the negative pilot and
continue the prespecified comparison without a synthetic replacement.

One explicit continuation reused the **same directory and request counter**.
It reconstructed the original start from the saved ledger elapsed time and its
file timestamp, adding five conservative seconds. Neither the 600-second window
nor the request/SPICE/token caps were reset. No model, prompt, spec, tolerance,
seed policy or rate setting was changed. The original blocked result and budget
remain `initial-pilot-failure.json` and `initial-budget-before-continuation.json`.
This engineering pause consumed most of the original wall-clock window; reported
elapsed time is not 600 seconds of active model inference.

The two source epochs are recorded rather than presented as an unchanged run:
initial rejected pilot `27bb7feda47336bd1ed8fa277e498a7ed720c5dc2a2efaabf93712db090137d0`,
then `662a4b94ce6804df0389dd3ee669c257202c1c8cd395bca631a651da8a0a420c`.
All 15 actual simulations occurred in the latter epoch. Its exact Python source
snapshot is retained in `source-at-final-execution/`; permission-closure changes
were made only after the run ended. The initial failed pilot's raw request and
response remain intact. Do not claim an exact model replay: replay was unrun.

## Reproduce the read-only audit

From the project checkout, with the test environment or declared dependencies:

```text
python scripts/audit_local_trial.py --input /path/to/the/existing/trial
```

No model or simulator is called. The checker validates the approved policy,
pinned identity, request settings, reservations and reported/unknown token usage;
replays candidate-validation/accounting from saved responses; verifies selection,
cache and per-method counts; and independently recomputes physics/metrics from
every raw waveform. Runtime audited 13 calls before cancellation. The final
read-only pass audited **all 15**; it did not invent two additional simulations.
It returns exit **1** for this dataset, with `integrity_status=passed` and
`phase6_comparison_status=blocked_incomplete`; exit 1 is intentional.

Evidence is at the existing authorized artifact path:
`C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Automatic_Acceptance/local-llama3-trial-2026-11-20`.
`result.json`, `budget.json`, `audit.json`, raw model request/response JSON, raw
SPICE directories, the failed initial result, source snapshot and final model
status are preserved. Treat saved model text as untrusted data.

Current verification: **289 unit tests passed in 9.90 seconds**, including
mock-HTTP transport, quota/deadline/continuation, closed-allowance and tampered
evidence rejection. Those tests made no real model or ngspice calls. The preceding
full-source suite's historical result remains **319 passed** for P6-C1; it was
not relabeled as a fresh full-suite run for this adapter. Live pipeline validation
here is the 15-call actual trial and independent audit.

The owner-approved allowance is now closed in the source configuration to
prevent an accidental fresh run with a new output path. **A new experiment needs
a renewed owner resource decision**, not another manual engineering signoff.
No paid API, credentials, remote push, deployment, frontend, PCB or advanced tool
agent was introduced. Project source and Git remain on C.
