# Proposed bounded replay supplement

Status: **prepared, not approved or executed**. The default packet
`examples/local-replay-supplement-v1.json` rejects execution before constructing a
simulator or contacting a model. Existing scientific and development-agent
allowances remain closed. This proposal is local circuit-model verification,
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

## Commands after explicit resource approval

The coordinator must first record the owner's actual response in the versioned
packet and enable only this allowance; the commands below currently refuse it.
Use new writable paths, the verified simulator and the installed local-model
dependency:

```text
python scripts/replay_local_trial.py --source /existing/local-llama3-renewal-2026-11-21 --output /new/local-replay-supplement --ngspice /trusted/ngspice
python scripts/audit_local_replay.py --source /existing/local-llama3-renewal-2026-11-21 --input /new/local-replay-supplement
```

After any real attempt the source packet is closed and the exact results are
documented; it cannot authorize a second run in another directory. Policy and
ledger selection remain trusted-coordinator responsibilities, as for the
existing trial. These local guards are not tamper-proof authorization services.

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
