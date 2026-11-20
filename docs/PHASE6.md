# Phase 6: offline proposal contract (P6-C1)

Only the provider-neutral interface is implemented. It contains no provider SDK,
network transport, credentials, agent loop or paid traffic. P6-C2's comparative
model experiment is unrun and needs the separate P6-H1 provider/budget decision.
The phase gate is not passed by this task's acceptance. The existing design CLI,
API, baselines, physics thresholds and SPICE budgets remain unchanged.

## Contract and boundaries

`circuforge.proposals` exposes `ProposalProvider`, `ProposalRequest`,
`ProviderReply` and `ProposalSession`. A caller injects a trusted synchronous
Python adapter and supplies a validated design spec, seed, token reservation,
declared prices and session limits. This is an extension interface, not an OS or
network sandbox: arbitrary Python adapters must be trusted. A real adapter needs
its own transport deadlines, actual tokenization, provider permissions and price
policy before use; this task does not provide or authorize one.

Each reply contains candidate JSON and adapter-supplied token usage. The JSON
must explicitly include topology, resistance in ohms and capacitance in farads.
It is limited to 4096 UTF-8 bytes. Duplicate keys, nonfinite values, missing or
extra fields, netlists, paths, unsupported/mismatched topologies, physical-range
violations and candidates outside the original spec are rejected. A candidate
cannot change the spec, select an executable or execute a netlist. No raw reply
or adapter exception text is stored in the attempt ledger.

The session returns a validated `CircuitCandidate` only for `status=accepted`.
The caller may then pass it to the existing `Evaluator`; accepted proposals are
not verified circuits until their actual simulation/reference checks pass.
Proposal attempts and SPICE attempts have separate budgets. Duplicate accepted
proposals still consume proposal quota; the existing evaluator can cache their
physical measurement. No automatic retry/search, CLI switch or HTTP provider
endpoint has been introduced.

## Accounting

Before each adapter call, reserve the declared maximum input/output tokens and
their worst-case cost. Defaults model a free offline fixture: 16 calls, 65536
total tokens and zero micro-USD. An optional monotonic minimum interval rejects
early calls without sleeping. Busy/reentrant calls and exhausted request/token/
cost budgets are rejected before adapter invocation and do not add attempts.

Valid adapter usage settles the reservation, including invalid candidate JSON.
An adapter exception, interruption or malformed usage retains the full token/
cost reservation with `accounting=reserved`; this is unknown usage, not invented
zero consumption. Reported usage above the reservation is recorded without
clipping, with `status=usage_overrun`, and permanently blocks further calls in
that session. Interruptions retain accounting and propagate to the caller.

Prices use declared integer micro-USD per input/output token. They are local
accounting parameters, not live provider prices or independent invoice evidence.
Future real-price integration must use a conservative rounded rate or explicitly
version a finer pricing contract; fractional micro-USD prices are not silently
rounded down. Fixture token counts are synthetic adapter reports, not actual
model tokens or measurements of tokenization. Cost/request caps do not grant
permission to contact a provider.

## Reproduce automatic task acceptance

With the installed test/API extras and ngspice configured, run from the source
checkout into a new writable directory:

```text
python scripts/accept_proposals.py --output /new/writable/proposal-acceptance
```

Policy `p6-c1-offline-contract-v1` executes the complete test suite, rejects
failed/errored/skipped evidence, and runs four genuine ngspice calls using fixed
offline low/high-pass controls. For each topology it rejects an unsupported
proposal before simulation, measures an accepted reference, reuses one duplicate
measurement, and measures a deliberate target miss. Independent auditing checks
raw stdout, CSV, template, physics, metrics, status and accounting. The output
preserves tests.xml/tests.log, acceptance.json and per-case ledgers/reports/raw
calls. Missing ngspice is blocked, never replaced by analytic simulation.

This acceptance demonstrates contract/guardrail integration, not model efficacy,
an equal-budget ablation, paid billing accuracy, hardware performance or full
Phase 6 completion. Historical Phase 1-5 results remain in their own documents.

## Observed task acceptance — 2026-11-20

`p6-c1-offline-contract-v1` passed: **319 complete-suite tests in 131.88 seconds,
without skips**, and **four additional genuine ngspice calls** independently
audited from raw output. The suite includes 40 new proposal/command tests; its
integration fixture calls are separate from those four acceptance calls. Windows
11, Python 3.12.7, ngspice-47; numerical dependency versions remain unchanged.

| Topology | Reference measured cutoff (Hz) | Deliberate miss cutoff (Hz) | Actual calls | Duplicate cache hits |
|---|---:|---:|---:|---:|
| Low-pass | 1591.487745916 | 795.759309340 | 2 | 1 |
| High-pass | 1591.612597494 | 795.790170336 | 2 | 1 |

Eight offline fixture requests produced two invalid-topology rejections before
simulation, two reference passes, two duplicates and two genuine target misses.
Reference errors were 0.003876% and 0.003969%; misses remain near 50% error against
the unchanged target/tolerance. There were **zero actual LLM/provider calls**;
the 40 reported fixture tokens are synthetic, and the zero-cost ledger is not a
provider invoice or experiment result.

Evidence is under the existing authorized artifact path:
`C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Automatic_Acceptance/p6-c1-2026-11-20`.
It retains tests.xml/tests.log, acceptance.json and both raw per-topology traces.
Package source fingerprint:
`8f6a80088cc9520fe00488023acb0f0acea264936b8f4a5fb25bfdc7ffc97550`.

Only P6-C1 is marked done. P6-H1 remains an explicit permission decision and is
now a dependency of blocked/unrun P6-C2. The Phase 6 gate remains pending. Project
source/Git stay on C; project migration was canceled. Ancillary artifacts retain
the preexisting C-path junction to D; they were not deleted or relocated during
this coding task.
