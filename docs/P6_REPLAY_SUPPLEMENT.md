# Proposed bounded replay supplement

Status: **executed once, independently accepted and closed** on 2026-11-22.
The owner answered `next` to the explicit prepared resource request. The default
packet `examples/local-replay-supplement-v1.json` is now consumed and rejects
another execution before simulator/model access. Earlier allowances remain
closed. This is local circuit-model verification,
separate from Freebuff development reviews.

## Exact proposed action

Use only the installed pinned loopback `llama3:latest`, two CPU threads and zero
GPU layers, with **at most two generation requests, 4608 reserved tokens, 120
seconds, two SPICE attempts and zero provider expenditure**. Per-request context,
output cap, seed, temperature, prompt/schema and keep-alive settings match the
original two pilot requests. No download, external provider, personal files,
credentials, new comparison cases, deployment or push is involved. No automatic
retry is allowed. A missing/changed model or failed response stops execution.

This explicitly creates a separate observation window. It does not reopen the
November 21 deadline, erase its timeout, reset its counters or rescore its four
matched-call comparisons. The source result, budget and execution policy are
SHA-256 bound in the proposed packet and independently raw-audited before use.
The original files are read-only inputs. Results use a new directory and smaller
durable counters; existing output ledgers are refused.

One original pilot candidate was invalid. Replay observations may be valid or
invalid candidates, and may differ from the original. Differences are reported;
exact candidate equality is never invented. A valid candidate gets at most one
real independently audited simulation. A malformed, transport-failed or
unknown-usage response cannot count as a completed replay observation; its full
token reservation remains charged.

## Prepared implementation

`scripts/replay_local_trial.py` validates the fresh recorded permission and caps,
checks source linkage, runs only the two original requests and persists raw
request/response, usage, candidate and physical evidence. `ReplayBudget` enforces
the smaller two-request/two-SPICE/120-second ceilings while retaining the existing
adapter's fixed endpoint/digest, request spacing and transport controls.
Each simulation's timeout is shortened to the remaining total window, so a late
proposal cannot start a full-length simulation past the envelope.

The runner always records `phase6_accepted=false`: its own success is not a gate.
`scripts/audit_local_replay.py` independently replays validation from saved model
replies, checks usage/prompt/options/source hashes, all new physical traces and
accounting. Only complete known-returned observations plus the original four
verified matched comparisons can pass the separate composite policy
`phase6-local-supplemental-replay-v1`. The original dataset remains incomplete
under its original policy. No target tolerance or comparison budget changes.

Do not mark P6 accepted before actual execution and this independent audit pass.
An incomplete or inconsistent supplement blocks acceptance. No model efficacy,
general determinism, target success or hardware conclusion follows automatically.
Client timeouts are not OS resource quotas; audit permits only bounded record
cleanup after the request deadline, never another request.

## Executed commands and results

The owner's actual `next` response was recorded before enabling this single
allowance. The following invocation ran once; the now-closed packet refuses a
second execution. Environment used the existing isolated interpreter, PYTHONPATH=src
and the verified ngspice-47 console executable. Paths below are under external
Automatic_Acceptance:

```text
$artifactRoot='C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534'
$python="$artifactRoot/Phase1_Verification/.venv/Scripts/python.exe"
$source="$artifactRoot/Automatic_Acceptance/local-llama3-renewal-2026-11-21"
$output="$artifactRoot/Automatic_Acceptance/local-replay-supplement-2026-11-22"
$env:PYTHONPATH='src'
& $python scripts/replay_local_trial.py --source $source --output $output --ngspice "$artifactRoot/CircuForge/.tools/Spice64/bin/ngspice_con.exe"
& $python scripts/audit_local_replay.py --source $source --input $output
```

After any real attempt the source packet is closed and the exact results are
documented; it cannot authorize a second run in another directory. Policy and
ledger selection remain trusted-coordinator responsibilities, as for the
existing trial. These local guards are not tamper-proof authorization services.

Actual runner and independent auditor both returned exit 0. The supplement made
**two model requests and one real SPICE attempt in 62.656 seconds**, reserved
**4608 tokens**, reported **256 actual tokens**, with **zero unknown-usage
responses and zero provider expenditure**. No extra generation was sent.
Read-only `/api/ps` afterward showed no loaded models.

| Original request | Returned observation | Exact valid candidate | SPICE attempts |
|---|---|---|---:|
| local-lowpass / seed 7 / proposal 1 | invalid_candidate | false; no valid candidate | 0 |
| local-highpass / seed 7 / proposal 1 | accepted | true | 1 |

The valid replay used R=560 ohm and C=6.8e-8 F, measured fc=4179.600653363 Hz,
with analytic-relative error 0.00267022% (physical check passed) and target error
81.72176754% (target failed). Repeating a valid candidate does not establish
general model determinism. The rejected low-pass observation is not a design
or an exact valid-candidate replay. Both observations retain known usage.

The auditor returned `status=passed` under
`phase6-local-supplemental-replay-v1`: four original matched comparisons plus two
separately authorized replay observations, one exact valid candidate. It preserved
the original 25-request/65-SPICE ledger, 600-second failure, unknown usage and all
target misses. Those comparisons were not rescored. The original policy remains
`blocked_incomplete`; the composite engineering policy passes without claiming
model efficacy or changing original budgets/tolerances.

Evidence: `Automatic_Acceptance/local-replay-supplement-2026-11-22` contains
result/budget/acceptance JSON, copied approval, model request/replies, new raw
physical trace and residency check. The sibling `-source` snapshot preserves the
pre-execution package/scripts/policy/tests and environment; source was based on
commit b14e5c7 plus approval/lifecycle-fixture changes. Package SHA-256 remained
`0e320d6e4188c9b3a52b23a3da4f278d9103043b3c07e58f1159f305724a7796`.
No source was edited during the window. Exact stdout logs are sibling
`local-replay-supplement-2026-11-22-execution.log` and `-audit.log`.

The updated research exporter accepts `--replay-supplement`, independently
re-audits the linkage and keeps separate primary/supplement tables and source
hashes. `research-report-with-supplement-2026-11-22` was exported with no new
model or SPICE calls; its summary/report are synchronized to docs/research.
After approval closure and report support, **29 targeted tests passed in 2.95s**.
Earlier 19 approval-guard tests passed in 2.29s before live execution. These are
unit results, separate from prior full-suite/install evidence.

## Offline verification

The regression suite `tests/unit/test_local_replay.py` uses only mock HTTP and
synthetic records, never the installed model or ngspice. It covers pending approval,
expanded limits, persistent caps/deadline/no reset, source changes, returned
invalid observations, no runner self-acceptance and corrupted composite evidence.
Windows asyncio needs local-socket tool permission even with mocked HTTP; a
restricted attempt stalled during event-loop setup, was stopped by its exact
test process identity, then rerun with that permission. This environment issue
does not prove a provider or simulator failure. No resource decision or live
inference is implied by unit tests.

Observed preparation checks on 2026-11-22: **364 unit tests passed in 19.33s**.
After adding unknown-usage/deadline regressions and tightening envelope checks,
the final targeted replay/report suite passed **28 tests in 2.14s** (19 replay,
nine report). No real provider or simulator was used. Unit XML is under external
`Automatic_Acceptance/p6-replay-preparation-unit-2026-11-22.xml`. The installed
interface's earlier 408-test/27-real-call acceptance is a separate completed
check; it is not relabeled as a new full-suite result after this preparation.
