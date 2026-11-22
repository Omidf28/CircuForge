# Automatic technical acceptance

Current accepted milestone: Phase 5, policy phase5-local-interface-v1. `python scripts/accept_phase5.py --output /new/writable/path` runs all tests, builds a wheel, installs it with tested pinned top-level dependencies in a fresh isolated environment, then invokes installed Python -I through CLI and actual loopback HTTP. Observed: **279 tests without skips; 27 actual calls, 18 complete raw CLI/ZIP calls audited plus nine JSON traces matched**. Two reference examples pass and one target miss remains per interface. Raw physics, metrics/selection, JSON/CSV/PNG/ZIP integrity, installed-package provenance, rejection guards, server shutdown and temporary cleanup passed. P5-H1 is deferred/superseded by P5-C4; optional P5-C3 is deferred per START_CODEX.md. This is automatic technical acceptance without an invented independent human UX review. See docs/PHASE5.md. Paid/provider, push and external deployment permissions remain separate.

Prior accepted milestone: Phase 4, policy phase4-tolerance-v1. Run `python scripts/accept_phase4.py --output /new/writable/path` with the test/report dependencies and ngspice configured. Observed: **234 tests without skips and 1536 real calls audited including exact replay**. The checker validates the declared distribution, all measured physical responses, seeded perturbations, objective/selection, separate holdout samples, empirical quantiles/pass rates, actual matched budgets, plots and replay. Each method uses 64 training plus 32 holdout calls per trial; no optimizer win is required. All nominal designs missed target, and robust q95 was worse in three of four pairs; these outcomes remain visible. P4-H1 is deferred/superseded by P4-C3 under owner delegation, with no human/hardware signoff. See docs/PHASE4.md. Earlier Phase 2/3 sections are historical.

Prior accepted milestone: Phase 3, policy phase3-reproducibility-v2. Run `python scripts/accept_phase3.py --output /new/writable/path` from the project root. It runs all tests and two fresh executions of examples/benchmark-v2.json, then independently audits raw physics, budgets, outcomes, runtimes, normalized case distinctness and exact numerical replay. Observed final run: **198 tests without skips, 20 cases, three seeds, 3060 audited calls including replay**; each run retains 18 control passes, 126 target misses and 36 expected infeasible rejections. See docs/PHASE3.md for exact evidence, environment, commands and the superseded v1 structural correction. Legacy P3-H1 is explicitly deferred/superseded by P3-C3; no human review is claimed. Earlier Phase 2 evidence below remains historical and unchanged.

Owner policy (2026-11-19): local technical gates use reproducible automated evidence; manual review is not required. This does not assert a human review or hardware certification. Each phase requires its own implemented and tested checks. No blanket acceptance of future work, remote push or paid/deployment action is implied.

## Phase 2 command

Install the project with its test extra and configure ngspice as in README, then from project root:

```text
python scripts/accept_phase2.py --output /new/writable/absolute/path
```

Use an OS-appropriate path; this managed Windows session requires output in the authorized visualization workspace. An optional --ngspice override selects the trusted executable. Output directories must be new and existing evidence is preserved.

The command performs preflight, runs the full source test suite with external plugin autoload disabled, checks JUnit for real nonempty executed tests with no failures/errors/skips, executes a fresh seed-42 five-case comparison, then audits every raw call. Test and comparison subprocesses each have a 180-second wall-clock limit; comparison inputs are capped at 1000 configured attempted calls. Unit/integration tests have their own bounded fixtures and are recorded separately from the comparison count.

## phase2-engineering-v1 checks

- Five to eight distinct typed case specifications; exact input fingerprint, completed case count and unchanged declared target tolerance/budget.
- Same current package source/environment fingerprint in every report, including Python/NumPy/Pydantic/SciPy versions.
- Complete histories, bounded proposals/cache counts, no charged duplicate admissible candidates, consistent per-call IDs and actual budgets: full cap for free domains and one call for a fully fixed domain.
- Each call's spec, trusted generated netlist, ngspice version/arguments and return code agree with the report.
- Raw .print output is parsed again; CSV frequencies/complex transfers/gain/phase agree with it. Complete frequency grids match the requested sweep.
- Independent ideal-RC complex response and half-power cutoff checks pass; objective, relative/reference errors, target flags and chosen best are recomputed.
- Summary totals, method outcomes and actual per-case budgets match all raw evidence.

Any missing or inconsistent artifact, stale source/environment, wrong count, failed/errored/skipped test or unsupported execution blocks acceptance. The command exits 1 after an allocated blocked run, 2 on setup/input failure, and 0 only on acceptance. acceptance.json and logs explain the result; a failure calls for repair and rerun, not a manual waiver. Tests cover corrupt/missing CSV, altered objective/convergence flags, wrong counts/fingerprints, failed/skipped/timed-out tests, missing simulator and unsafe artifact paths.

## Meaning of a pass

acceptance.json records status, acceptance_mode=automated, manual_review_required=false, the policy, environment, test count, audited call count and each measured target outcome. Passing this gate means the baseline comparison was executed and reported correctly. Design success is a separate count: the original 64-call free-domain misses remain misses. No threshold is relaxed and no analytical value substitutes for measured fitness.

This is a consistency/physics audit of freshly executed trusted local code, not a cryptographic attestation of an arbitrary simulator binary or an approval of manufactured hardware. The explicit trust boundary remains the configured local ngspice executable and repository code.

## Plan status

P2-H1 is historical manual-review work superseded by P2-C4 automatic acceptance under the owner's delegation. P2-C4 can be done and the P2 gate passed only after an observed successful run. Later tasks remain uncompleted until their own implementation and acceptance evidence exists.

## Executed acceptance — 2026-11-19

Ran the command from the active checkout using the isolated interpreter, PYTHONPATH=src and the verified CIRCUFORGE_NGSPICE executable, with output:

```text
C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Automatic_Acceptance/phase2-2026-11-19
```

Observed acceptance.json: status=passed, policy=phase2-engineering-v1, acceptance_mode=automated, manual_review_required=false, tests_passed=170, cases_checked=5, raw_calls_checked=771, design_passes=3, design_misses=12. This is a fresh comparison; the original seed-42 evidence remains intact. Full commands, environment fingerprint, per-method outcomes and all audit inputs are retained in acceptance.json, tests.xml, tests.log, comparison.log and comparison/ beneath that directory.

Twelve focused audit tests and four orchestrator failure tests were also executed before the full run. The full run included all of them. P2-C4 is accepted automatically on this observed result; the old manual P2-H1 is deferred/superseded, with no claim of human review.

Standalone reference/comparison producers no longer label new outputs as awaiting human review: Phase 1 labels its reference checks as automated; Phase 2 labels comparison data as requiring the automatic gate. Producers do not silently pass the overall gate. Existing historical evidence, including its old producer metadata, remains unchanged; acceptance.json is the authoritative acceptance decision for this run.

Package check: built/installed the source snapshot from Automatic_Acceptance/source-code into the isolated environment with pip --no-deps. The installed checker, invoked with Python -I from outside the source checkout, re-audited the production evidence successfully (170 tests / 771 calls). Separately labeled metadata smoke runs executed 15 one-call baseline attempts on a temporary case file and eight reference sweeps; new producer metadata is manual-review-free while preserving measured outcomes. These 23 packaging/metadata smoke calls are not added to the production comparison or its scores.
