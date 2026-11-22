# CircuForge · Wave2Circuit Research Edition

Version 2.1.0 · assembled 2026-11-22 · architecture assumptions to verify in current environment

P7-C1/C2 documentation/report tasks completed within their explicit prerequisites. Fresh local interface/install acceptance passed 408 tests without skips plus 27 actual installed CLI/HTTP calls (18 raw audited, nine JSON traces matched); checked stored-evidence report/plot preserves negative results. P5-C5 Freebuff handoff accepted separately. Scientific local Llama trial remains four matched comparisons/25 requests/65 raw-audited SPICE attempts, all target misses and incomplete final replay: P6 and final P7 release blocked. Existing model/development cycles closed, no new model calls for reporting/install. GitHub public, only initial main online, no feature push. See docs/OPERATIONS.md and docs/RESEARCH_REPORT.md.

**Unconfirmed premise:** Confirmed project direction: inverse analog circuit design and optimization, not a generic circuit tutoring product. Specific algorithms, hosting and performance targets remain engineering hypotheses.

## Destination and scope

Given a validated filter specification, synthesize constrained analog circuit candidates, simulate them using real ngspice runs, optimize component values, quantify tolerance robustness, and report reproducible evidence. AI is an optional, benchmarked proposal mechanism—not the source of numerical truth.

Research-first MVP with a usable local demo, two supported RC filter families, deterministic baseline optimizers, tolerance analysis, and published reproducible experiments. No 100-user or full PCB promise.

Provisional 12-week two-person, part-time plan (roughly 12–15 team hours per person weekly). Phase gates and actual test evidence take precedence over dates. An MVP may take longer depending on simulator setup.

The estimates are active-work planning assumptions, not model runtime or billing estimates. Current task statuses and evidence follow. Phase dates are relative to kickoff.

### Launch scope

- Local-first Python engine, ngspice executable integration and tested AC-analysis pipeline on RC low-pass, then RC high-pass.
- Structured circuit-design specification; basic validation, units, allowlisted topology templates, parameter bounds and physically meaningful target checks.
- Numerical baseline optimization (grid/random search and SciPy differential evolution); repeatable seeds and a fixed simulation budget.
- Tolerance evaluation of candidate designs with explicit assumptions, reproducible Monte Carlo sampling and valid reference calculations.
- CLI and minimal result visualization/export (CSV/JSON/PNG); compact web UI only after verified core.
- Research benchmark (initially 20 curated cases, expandable to 50–100), baselines, metrics, failure analysis and documentation.

### Deferred scope

- RLC and active topologies after independent fixtures and reviewer validation.
- LLM proposal agent with structured tools, explicit cost caps and measured comparison to non-LLM baselines.
- Manufacturer SPICE models and verified compatibility registry, KiCad schematic export, then constrained 2-layer PCB placement/routing experiments.
- Datasheet RAG, fine-tuning, image/OCR, full schematic editor, real-board hardware tests, production multi-user hosting.

## First 48 hours

### Human: Check workstation and scope

Install Python and ngspice or document the blocking installation issue; agree on Windows support, one selected filter family, budget, and handoff ownership. Avoid adding API credentials.

### Codex: Prove first ngspice run

Create the typed RC low-pass example, run a noninteractive AC sweep with a hard timeout, parse the output, calculate the −3 dB cutoff and check against the analytic RC reference.

### Human: Validate physical assumptions

Review voltage reference, source/load constraints, allowed component ranges, tolerance distributions and meaningful filter targets before the first optimization benchmark.

## Intended user journey

### 1. Specify

Enter filter type, cutoff frequency, source/load assumptions, acceptable error, allowed E-series values and component bounds. Invalid or infeasible specs get explicit reasons.

### 2. Synthesize

Choose an allowed RC topology and generate a safe parameterized SPICE netlist; maintain provenance of every candidate.

### 3. Simulate and optimize

Run bounded ngspice AC sweeps; extract transfer function and measured cutoff, compare against analytic reference and optimize candidates using baseline algorithms.

### 4. Verify and report

Compare target vs simulated response, tolerance sensitivity and search cost; export reproducible artifacts and disclose limitations.

## Phase workflow

Critical path: P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7. P8 is optional after validated research MVP.

Technical phase gates use tested automatic acceptance under the owner delegation recorded in AGENTS.md. A status change alone does not prove completion. Explicit owner approvals for spending, remote publishing and other restricted operations remain separate. Deferred work needs a recorded reason; critical correctness, isolation and data-loss failures must be resolved.

### P0: Review reference circuit

**Window:** Week 1 · Launch path

**Outcome:** Environment, constraints and first executable SPICE proof.

**Phase dependencies:** None

**Exit gate:** ngspice executable detected; one low-pass test netlist generates a valid AC output, or failure logged with installation instructions.

**Gate status:** passed

**Gate evidence:** Owner explicitly confirmed Phase 1 circuit/result review on 2026-11-19; automated evidence: 122 passing tests and eight genuine reference cases. See docs/DECISIONS.md. This is not Phase 2 or push authorization.

#### P0-H1 · Human · Agree boundaries

Status: done · Estimate: 2 active hours

**Action:** Choose supported platform, source amplitude/load assumptions, component ranges and compute budget; review design safety.

**Deliverable:** docs/DECISIONS.md with bounded MVP decisions.

**Acceptance:** No unsupported circuits or implicit idealizations in requirements.

**Depends on:** None

**Evidence:** Project owner explicitly stated on 2026-11-19: بازبینی کردم و Phase 1 را تأیید می‌کنم. Owner acceptance covers the documented ideal-source/load, continuous RC assumptions and circuit/reference results. See docs/DECISIONS.md. No separate peer/hardware signoff asserted.

#### P0-C1 · Codex · Scaffold tested Python project

Status: done · Estimate: 4 active hours

**Action:** Create pyproject.toml, src package, pytest scaffolding, .gitignore, tooling docs and executable path detection.

**Deliverable:** Installable local package and ngspice preflight command.

**Acceptance:** pytest passes on deterministic tests even if ngspice missing; missing simulator is reported clearly.

**Depends on:** None

**Evidence:** Installable package built and installed locally; pytest unit tests pass; missing simulator preflight tested. See docs/DEVELOPMENT.md.

#### P0-C2 · Codex · Run first SPICE smoke test

Status: done · Estimate: 4 active hours

**Action:** Generate allowed RC netlist in temp directory and call ngspice non-interactively with timeout.

**Deliverable:** Test fixture plus captured AC sweep output.

**Acceptance:** On installed ngspice, genuine exit 0 and numeric sweep; no fake output fallback.

**Depends on:** P0-C1

**Evidence:** ngspice-47 console exit 0; 601 real AC rows; evidence/lowpass-2026-11-18/{stdout.log,response.csv,report.json}.

#### P0-H2 · Human · Review reference circuit

Status: done · Estimate: 2 active hours

**Action:** Review RC low-pass schematic, correct ground, source and load assumptions with teammate.

**Deliverable:** Signed-off idealized fixture and expected fc.

**Acceptance:** Expected fc and assumptions independently confirmed.

**Depends on:** P0-C2

**Evidence:** Project owner explicitly stated on 2026-11-19: بازبینی کردم و Phase 1 را تأیید می‌کنم. Owner acceptance covers the documented ideal-source/load, continuous RC assumptions and circuit/reference results. See docs/DECISIONS.md. No separate peer/hardware signoff asserted.

### P1: Verify RC low/high-pass fixtures

**Window:** Weeks 2–3 · Launch path

**Outcome:** Typed specs, safe netlists and independently checked transfer functions.

**Phase dependencies:** P0

**Exit gate:** RC cutoff and amplitude/phase checks pass analytical fixtures; invalid specs rejected.

**Gate status:** passed

**Gate evidence:** Owner explicitly confirmed Phase 1 circuit/result review on 2026-11-19; automated evidence: 122 passing tests and eight genuine reference cases. See docs/DECISIONS.md. This is not Phase 2 or push authorization.

#### P1-C1 · Codex · Define typed circuit specifications

Status: done · Estimate: 6 active hours

**Action:** Define Pydantic models for RC type, cutoff, source/load, units, ranges and E-series policy; reject invalid.

**Deliverable:** schemas, unit tests and examples.

**Acceptance:** Invalid freq, nonpositive elements, unsupported topology and out-of-range values fail clearly.

**Depends on:** P0-C1

**Evidence:** Pydantic SI schemas, low/high-pass types, continuous-value policy, explicit ideal source/load and bounds/infeasibility/injection tests. Review fixes enforce at least two sweep samples and tolerance-aware target feasibility; 122 tests pass, including four genuine fixed-target CLI cases.

#### P1-C2 · Codex · Implement ngspice adapter

Status: done · Estimate: 8 active hours

**Action:** Subprocess integration with allowlisted templates, timeout, logs, temp dirs, return codes, failure reports.

**Deliverable:** simulator interface and tests.

**Acceptance:** No arbitrary command injection or unrestricted .include; proper failure on absent ngspice.

**Depends on:** P0-C2, P1-C1

**Evidence:** Real ngspice integration plus timeout, output-limit, absent binary, launch and nonzero-exit tests; full frequency grid and partial-search failures verified. Isolated test environment: 122 tests passed, including genuine two-sample sweeps and fixed-target low/high-pass CLI cases. See docs/DEVELOPMENT.md.

#### P1-C3 · Codex · Extract AC metrics

Status: done · Estimate: 7 active hours

**Action:** Parse complex AC response, interpolation of −3 dB cutoff, gain/phase arrays.

**Deliverable:** metrics and analytic comparison tests.

**Acceptance:** Measured cutoff agrees with analytic first-order RC within documented discretization tolerance.

**Depends on:** P1-C2

**Evidence:** Complex response and phase checked against analytic references. Additional eight real electrical review cases span four distinct cutoff scales per topology; all passed with max cutoff error 0.005891%. See docs/PHASE1_REVIEW.md and scripts/verify_phase1.py; owner review accepted on 2026-11-19 (docs/DECISIONS.md).

#### P1-H1 · Human · Verify RC low/high-pass fixtures

Status: done · Estimate: 3 active hours

**Action:** Cross-check both topologies, source/load simplifications and expected phase behavior.

**Deliverable:** Reference examples and review notes.

**Acceptance:** At least 4 reference cases with analytical solutions and independently checked expectations.

**Depends on:** P1-C3

**Evidence:** Project owner explicitly stated on 2026-11-19: بازبینی کردم و Phase 1 را تأیید می‌کنم. Owner acceptance covers the documented ideal-source/load, continuous RC assumptions and circuit/reference results. See docs/DECISIONS.md. No separate peer/hardware signoff asserted.

### P2: Inspect failed optimizations

**Window:** Weeks 4–5 · Launch path

**Outcome:** Target cutoff to optimized RC values under physical constraints.

**Phase dependencies:** P1

**Exit gate:** Two optimizer baselines run on valid test cases with equal simulation budgets.

**Gate status:** passed

**Gate evidence:** Owner delegated technical acceptance to automatic checks. phase2-engineering-v1 passed: 170 tests without skips, 5 cases and 771 fresh raw calls audited, 3 design passes/12 misses retained. P2-H1 is superseded by P2-C4, not a human signoff. See docs/AUTOMATIC_ACCEPTANCE.md.

#### P2-C1 · Codex · Define objective and feasibility

Status: done · Estimate: 6 active hours

**Action:** Implement target cutoff/response objective and constraint handling; return infeasible reasons.

**Deliverable:** objective tests and schema.

**Acceptance:** No optimization of invalid netlists or unsupported targets; units consistent.

**Depends on:** P1-C3

**Evidence:** Typed objective/evaluation records distinguish constraints, simulator exit, reference verification and target error. Seven focused unit cases passed for bounds/topology rejection, objective, failures, caching and hard call caps; see tests/unit/test_objective.py and docs/PHASE2.md.

#### P2-C2 · Codex · Seeded random and grid baselines

Status: done · Estimate: 7 active hours

**Action:** Build deterministic baseline with budgets, E-series optional, call counting and structured output.

**Deliverable:** baseline algorithm and tests.

**Acceptance:** Repeat with fixed seed yields identical candidate list and metrics.

**Depends on:** P2-C1

**Evidence:** Seeded random and deterministic log-grid baselines verified by budget/replay tests and real ngspice integrations. Five-case review: 64 calls per method on four free domains, 1 on the fixed domain. Actual calls matched across all three methods; see docs/PHASE2.md.

#### P2-C3 · Codex · SciPy differential evolution

Status: done · Estimate: 8 active hours

**Action:** Run bounded differential evolution and compare on same max SPICE calls; cache duplicate points.

**Deliverable:** optimizer interface and comparative report.

**Acceptance:** Budget cap respected, results exportable and comparable.

**Depends on:** P2-C2

**Evidence:** Public SciPy differential_evolution with seeded Generator, no polishing, serial execution, exact cache and hard mid-generation call cap. Full suite: 154 passed. Five-case single-seed comparison exported 15 reports and 771 genuine call artifacts; misses are reported. P2-H1 review remains pending.

#### P2-H1 · Human · Inspect failed optimizations

Status: deferred · Estimate: 3 active hours

**Action:** Review infeasibility and performance failures against expectations; decide ranges.

**Deliverable:** Failure-mode notes and accepted constraints.

**Acceptance:** At least 5 varied cases with human review and no fabricated wins.

**Depends on:** P2-C3

**Evidence:** Owner explicitly requested removal of manual technical review on 2026-11-19. Replaced by tested automatic P2-C4; no human review is claimed. See docs/DECISIONS.md and docs/AUTOMATIC_ACCEPTANCE.md.

#### P2-C4 · Codex · Automatic technical acceptance

Status: done · Estimate: 4 active hours

**Action:** Run full tests without skips, fresh bounded comparisons and raw-response/physics/metric/budget audit; block on missing or inconsistent evidence.

**Deliverable:** scripts/accept_phase2.py, evaluation/acceptance.py and machine-readable acceptance.json.

**Acceptance:** A complete fresh run passes phase2-engineering-v1 without manual review while preserving measured target misses; corrupted/skipped/failed evidence blocks it.

**Depends on:** P2-C1, P2-C2, P2-C3

**Evidence:** Observed automatic acceptance on 2026-11-19: 170 full-suite tests passed without skips; 771 fresh real calls audited; 3 target passes and 12 misses preserved; manual_review_required=false. See docs/AUTOMATIC_ACCEPTANCE.md and external Automatic_Acceptance/phase2-2026-11-19/acceptance.json.

### P3: Reproducible benchmark and automatic audit

**Window:** Weeks 6–7 · Launch path

**Outcome:** Versioned cases, repeatable multi-seed comparisons and saved evidence.

**Phase dependencies:** P2

**Exit gate:** At least 20 benchmark cases run with logged seeds/configs/results and readable summary.

**Gate status:** passed

**Gate evidence:** phase3-reproducibility-v2 passed with 198 tests, 20 normalized-distinct cases, 3 seeds and 3060 real calls across two audited runs. Equal budgets and exact numerical replay verified; 18 passes/126 misses/36 rejections per run preserved. P3-H1 superseded by P3-C3; no human signoff.

#### P3-C1 · Codex · Benchmark schema and cases

Status: done · Estimate: 7 active hours

**Action:** Create 20 curated RC tasks spanning cutoff and feasible bounds; no duplicated disguised cases.

**Deliverable:** JSON cases and provenance.

**Acceptance:** Every case has target, bounds, accepted error and expected feasibility.

**Depends on:** P2-C1

**Evidence:** Benchmark v2.0 validates 20 distinct normalized RC tasks, 16 feasible including 2 fixed controls and 4 expected infeasible. Original v1 scale duplicates are retained as a rejection regression. Full suite 198 passed; see examples/benchmark-v2.json and docs/PHASE3.md.

#### P3-C2 · Codex · Evaluation harness

Status: done · Estimate: 9 active hours

**Action:** Run fixed-seed trials with equal call budgets, log runtime, failures, environment and configs.

**Deliverable:** benchmark runner and result files.

**Acceptance:** Re-run yields same numerical results within documented tolerances.

**Depends on:** P3-C1, P2-C3

**Evidence:** Observed real 20-case x 3-seed x 3-method run and independent replay: 180 trials and 1530 calls per run, 3060 audited calls total. Candidate/metric traces match exactly, latency excluded. All method budgets matched; see docs/PHASE3.md and external Automatic_Acceptance/phase3-v2-2026-11-19.

#### P3-H1 · Human · Audit baseline fairness

Status: deferred · Estimate: 4 active hours

**Action:** Audit 5 cases, acceptance logic, runtime measurement and success definitions.

**Deliverable:** Audit notes and correction list.

**Acceptance:** Clear definition of simulation success, numerical success and invalid candidate.

**Depends on:** P3-C2

**Evidence:** Superseded under owner's automatic technical-review delegation by tested P3-C3. No human review is claimed. Physics, fairness, failure definitions, runtimes and all 20 cases are automatically audited.

#### P3-C3 · Codex · Automatic benchmark acceptance

Status: done · Estimate: 5 active hours

**Action:** Reject duplicate normalized tasks, run complete tests and two fresh benchmarks, audit raw physics/accounting and exact numerical replay.

**Deliverable:** scripts/accept_phase3.py and versioned machine-readable acceptance.json.

**Acceptance:** phase3-reproducibility-v2 passes without skips, missing/inconsistent evidence or manual waiver; target misses and expected infeasible rejections remain distinct.

**Depends on:** P3-C1, P3-C2

**Evidence:** Observed 2026-11-19: 198 tests without skips, 20 cases/3 seeds, 3060 fresh final-dataset calls audited across two exact numerical replays. Per run 18 control design passes, 126 misses, 36 expected infeasible rejections; zero simulation failures. See docs/PHASE3.md.

### P4: Tolerance experiment and automatic audit

**Window:** Week 8 · Launch path

**Outcome:** Demonstrate robust vs nominal design tradeoffs.

**Phase dependencies:** P3

**Exit gate:** Robustness runs reproduce quantiles and performance comparison with declared tolerance model.

**Gate status:** passed

**Gate evidence:** phase4-tolerance-v1 passed: 234 tests, declared independent uniform tolerance model, two cases/two seeds, matched 96 calls/method/trial and 1536 raw calls including exact replay. Quantiles/pass rates and negative tradeoffs preserved. P4-H1 deferred/superseded by P4-C3, not human-approved. See docs/PHASE4.md.

#### P4-C1 · Codex · Monte Carlo model

Status: done · Estimate: 7 active hours

**Action:** Seeded tolerance sampling, explicit distributions and sampling budget; compute quantiles and pass rate.

**Deliverable:** robustness module and tests.

**Acceptance:** Fixed-seed Monte Carlo repeatability; nominal vs tolerance statistics shown separately.

**Depends on:** P3-C2

**Evidence:** Typed independent uniform R +/-1% / C +/-5% multiplicative model, separate training/holdout RNG streams, explicit simulation envelopes, measured empirical quantiles and pass rates with failed-sample blocking. Full suite: 234 tests without skips; real raw-data statistics reproduce. See docs/PHASE4.md.

#### P4-C2 · Codex · Robust objective experiment

Status: done · Estimate: 8 active hours

**Action:** Add tolerance-aware penalty and comparison under matched total simulation budgets.

**Deliverable:** ablation report and plots.

**Acceptance:** Report measured tradeoffs without claiming improvement if unsupported.

**Depends on:** P4-C1

**Evidence:** Prespecified two-case/two-seed nominal-vs-robust random-search comparison: 64 training +32 fresh holdout calls/method/trial. Each run has 8 trials and 768 actual calls; 1536 audited calls including exact replay. Report/PNG retain negative tradeoffs; no robust superiority claimed. See docs/PHASE4.md.

#### P4-H1 · Human · Review tolerance assumptions

Status: deferred · Estimate: 3 active hours

**Action:** Choose tolerance ranges, correlation assumptions and interpretation limits.

**Deliverable:** Assumptions and research decision log.

**Acceptance:** No simulated confidence described as hardware performance guarantee.

**Depends on:** P4-C1

**Evidence:** Superseded by tested automatic P4-C3 under owner delegation. Explicit illustrative distribution, independence/pairing, sample budgets and interpretation limits are recorded in docs/DECISIONS.md and docs/PHASE4.md. No human signoff or hardware guarantee asserted.

#### P4-C3 · Codex · Automatic tolerance-study acceptance

Status: done · Estimate: 4 active hours

**Action:** Run full tests and two fresh declared tolerance experiments; independently audit raw physics, factors, objective/selection, holdout partitions/statistics, equal budgets and exact replay.

**Deliverable:** scripts/accept_phase4.py, robust_acceptance.py, acceptance.json and comparison plots.

**Acceptance:** phase4-tolerance-v1 passes without skipped/failed/inconsistent evidence; no optimizer win or manual waiver required, and failures/limitations remain explicit.

**Depends on:** P4-C1, P4-C2

**Evidence:** Observed on 2026-11-19: 234 tests without skips, 1536 real raw calls audited across two exact numerical replays; 96 actual calls/trial for both methods. All nominal designs missed 0.1%; each method had 3 passes in 128 paired holdout observations, not a hardware-yield estimate. See docs/PHASE4.md and external Automatic_Acceptance/phase4-final-2026-11-19/acceptance.json.

### P5: Local CLI/API and automatic install walkthrough

**Window:** Weeks 9–10 · Launch path

**Outcome:** CLI/API and optional UI make verified results inspectable.

**Phase dependencies:** P4

**Exit gate:** Automatic clean-install walkthrough reproduces complete CLI and real loopback API examples with plots, raw results, traceable configuration and consistent statuses.

**Gate status:** passed

**Gate evidence:** phase5-local-interface-v1 passed: 279 tests, fresh isolated wheel install and real installed CLI/HTTP walkthrough. 27 actual calls, 18 archived/raw-audited plus 9 JSON traces matched; target miss preserved and server/temp cleanup verified. P5-H1 superseded by P5-C4; optional P5-C3 deferred per START_CODEX.md. No human review/deployment/push approval asserted.

#### P5-C5 · Codex · Bounded Codex and Freebuff development handoff

Status: done · Estimate: 3 active hours

**Action:** Codex drives the existing interactive free-model terminal with selected packets; persist limits and source hashes, receive advisory output, independently check edits and continue eligible jobs automatically within one authorized cycle.

**Deliverable:** planning/agent-workflow.json, scripts/agent_workflow.py, regression tests and docs/AGENT_COLLABORATION.md with real turn evidence.

**Acceptance:** Fail-closed tests cover prerequisites, consent, changed packets, concurrent/duplicate dispatch, persistent caps and untrusted replies; actual Freebuff receipt recorded separately from engineering acceptance. No paid SDK, daemon or full P7/Phase 6 acceptance claim.

**Depends on:** P5-C4

**Evidence:** Accepted automatically 2026-11-22 after explicit owner next authorized a separate one-turn/600-second verification cycle. 338 actual unit tests passed in 17.59s without skips, including 45 coordination guards; one real Freebuff response recorded 57.46s after reservation with matching prompt/source/reply hashes and no legacy/unbound receipt. Existing audit passed, cycle closed at 1/1 turns; useful trust-boundary wording was independently checked and adopted. The November 21 late-receipt cycle remains blocked with original counters/evidence. See docs/AGENT_COLLABORATION.md and 2026-11-22-verify-01/acceptance.json. No scientific, clean-install or full P7 gate acceptance implied.

**Advisor:** Freebuff · Codex retains writing and automatic acceptance.



#### P5-C1 · Codex · CLI and report export

Status: done · Estimate: 8 active hours

**Action:** CLI accepts structured spec and produces JSON/CSV/PNG and traceable simulation log.

**Deliverable:** CLI command, example and tests.

**Acceptance:** Reproduce an example from README with no secrets or service account.

**Depends on:** P2-C3, P4-C1

**Evidence:** Shared bounded DesignRequest/DesignResult, new design CLI and JSON/CSV/PNG/checksummed ZIP with full raw history. Three installed examples reproduce direct simulation, grid control and a preserved target miss. Full suite 279 tests without skips. See docs/PHASE5.md.

#### P5-C2 · Codex · Add minimal FastAPI service

Status: done · Estimate: 8 active hours

**Action:** Validated endpoint with bounded compute, response schemas and safe temp cleanup.

**Deliverable:** local HTTP API plus tests.

**Acceptance:** Integration test response consistent with CLI, no arbitrary netlist execution.

**Depends on:** P5-C1

**Evidence:** Loopback-only FastAPI JSON/ZIP endpoints use the same engine, validate requests before compute, cap body/calls/timeout/sweep/concurrency, reject injected netlists/paths and clean temporary data. Real installed HTTP matches CLI; error/guard/concurrency/cleanup tests passed. See docs/PHASE5.md.

#### P5-C3 · Codex · Engineering dashboard (optional)

Status: deferred · Estimate: 10 active hours · Optional

**Action:** Minimal plot and comparison view after engine passes gates; keep core package usable without UI.

**Deliverable:** working prototype with baseline comparison.

**Acceptance:** Shows verified vs unverified candidates and failure reasons.

**Depends on:** P5-C2

**Evidence:** Explicitly optional dashboard deferred: START_CODEX.md excludes a frontend; CLI/API and PNG exports meet the inspectable scientific-result gate without unnecessary UI. No dashboard completion is claimed.

#### P5-H1 · Human · User acceptance walkthrough

Status: deferred · Estimate: 3 active hours

**Action:** Attempt clean install, complete example and review UX / interpretation.

**Deliverable:** Recorded walkthrough and issues.

**Acceptance:** External reviewer can identify objective, circuit and evidence from output.

**Depends on:** P5-C1

**Evidence:** Owner's automatic technical-review delegation replaces the install/result walkthrough with tested P5-C4. Fresh installed Python -I, real loopback HTTP and independent export checks passed. No independent human or subjective UX review is claimed.

#### P5-C4 · Codex · Automatic installed CLI/API acceptance

Status: done · Estimate: 5 active hours

**Action:** Run all tests, build a source-byte-preserving wheel, install it in a fresh isolated environment and compare real CLI/JSON/ZIP outcomes with raw physics/integrity and cleanup checks.

**Deliverable:** scripts/accept_phase5.py, scripts/walkthrough_phase5.py and machine-readable acceptance evidence.

**Acceptance:** phase5-local-interface-v1 passes without skips, source-import leakage, hidden target misses, unsafe exports, leaked server/temp state or manual waiver.

**Depends on:** P5-C1, P5-C2

**Evidence:** Observed 2026-11-19: 279 tests without skips; fresh wheel/venv and Python -I walkthrough passed through real loopback HTTP. 27 actual calls: 18 full raw CLI/ZIP calls independently audited and 9 JSON calls matched numerically. Two passing reference examples and one target miss per interface preserved; server stopped and temp storage empty. See docs/PHASE5.md and external Automatic_Acceptance/phase5-2026-11-19/acceptance.json.

### P6: Approve API trial and spending

**Window:** Week 11 · Launch path

**Outcome:** Test whether structured LLM suggestions add measurable value.

**Phase dependencies:** P5

**Exit gate:** If paid key/provider inaccessible, mark experiment deferred and preserve reproducible non-LLM result; no claims without trials.

**Gate status:** blocked

**Gate evidence:** November 21 renewal integrity passed for 25 model requests/65 real SPICE attempts; all four matched-call comparisons complete, no target passes. Final model replay stage incomplete (one timeout, second unrun), so overall acceptance remains blocked_incomplete. P6-C1 historical full-suite acceptance remains distinct from latest 293 unit tests. P6-H1 records explicit local-only resource decisions; both windows closed, datasets not pooled. No full Phase 6 or model efficacy acceptance.

#### P6-C1 · Codex · Provider-neutral proposal interface

Status: done · Estimate: 7 active hours

**Action:** Define structured candidate interface with validation, rate/cost caps, mock tests; optional real provider adapter.

**Deliverable:** LLM proposal plugin isolated from core.

**Acceptance:** Invalid topology rejected; no required API key for basic design.

**Depends on:** P2-C1

**Evidence:** P6-C1 only accepted automatically 2026-11-20 under p6-c1-offline-contract-v1: 319 tests without skips and 4 fresh raw-audited ngspice calls; 8 offline fixture requests, 2 invalid topologies rejected, 2 cached duplicates, 2 reference passes and 2 deliberate misses preserved. Strict candidate JSON, request/token/cost reservations, rate/concurrency guards and failure/overrun accounting tested. No network adapter, SDK, credentials, real model traffic or efficacy claim. See docs/PHASE6.md and external Automatic_Acceptance/p6-c1-2026-11-20/acceptance.json.

#### P6-C2 · Codex · Equal-budget agent ablation

Status: blocked · Estimate: 9 active hours

**Action:** Run available LLM proposals vs baselines under stated budgets, track tokens, costs, failures and seeds.

**Deliverable:** experiment results and limitations.

**Acceptance:** Comparative evidence provided or explicitly marked unrun due to access.

**Depends on:** P6-C1, P3-C2, P6-H1

**Evidence:** Observed renewal 2026-11-21: four matched-call comparisons at 4 actual SPICE attempts/method, 25 model requests/65 raw-audited SPICE attempts; all target checks missed. Seventeen accepted/seven invalid proposals/one unknown-usage timeout; 57600 reserved tokens/3079 known tokens. Final replay timed out, second unrun; original gate blocked. Both original allowances closed, November 20 data separate. On November 22 prepared a separate <=2-request/120-second/2-SPICE local replay envelope, runner and independent composite auditor, currently pending owner resource approval and unexecuted. 364 unit tests plus final 28 targeted replay/report tests passed without model/simulator use. See docs/P6_REPLAY_SUPPLEMENT.md and docs/PHASE6_LOCAL_RENEWAL.md. No actual supplemental result or gate acceptance claimed.

#### P6-H1 · Human · Approve API trial and spending

Status: done · Estimate: 2 active hours

**Action:** Review pricing/privacy/terms and set maximum expenditure; do not commit secrets.

**Deliverable:** approved or declined budget decision.

**Acceptance:** No paid traffic without explicit approval.

**Depends on:** P6-C1

**Evidence:** Explicit owner response 2026-11-20: تأیید آزمایش فقط محلی با همین سقف‌ها. On November 21 owner answered next to the explicit request for one fresh execution under unchanged caps. Installed local llama3 only, zero provider expenditure, <=32 requests, <=73728 reserved tokens, 600 seconds, 80 SPICE attempts and two CPU threads per window. Both execution windows have ended and their source packets are closed. No paid/cloud/download/personal-file transmission/push/deployment permission from this decision; more model execution needs a fresh bounded resource decision. See docs/PHASE6_LOCAL_TRIAL.md and docs/PHASE6_LOCAL_RENEWAL.md.

### P7: Verify demo and claims

**Window:** Week 12 · Launch path

**Outcome:** Documented repo, demo, findings and truthful CV-ready evidence.

**Phase dependencies:** P6

**Exit gate:** Clean setup, tests, reproducible benchmark, demo and research report.

**Gate status:** blocked

**Gate evidence:** P7-C1/C2 documentation/report tasks accepted within their explicit prerequisites with fresh installed CLI/API evidence and checked stored-data report. Final P7 release remains blocked on P6's incomplete model replay and the unfinished demo/claims task P7-H1; no release, push or deployment approval.

#### P7-C1 · Codex · Engineering documentation

Status: done · Estimate: 7 active hours

**Action:** README, architecture diagrams, API docs, installation troubleshooting, reproducibility commands and known limits.

**Deliverable:** complete technical documentation.

**Acceptance:** Clean-room developer can reproduce at least one supported design.

**Depends on:** P5-C1, P3-C2

**Evidence:** 2026-11-22: corrected implemented architecture/contracts and added flow diagram plus local operations/API/troubleshooting guide. Existing phase5-local-interface-v1 freshly passed 408 full-suite tests without skips (120.41s), built a wheel, installed a fresh isolated venv and reproduced CLI/real loopback HTTP with Python -I. 27 actual calls: 18 raw CLI/ZIP calls audited and nine JSON traces matched; target miss retained, server/temp cleanup verified. docs/OPERATIONS.md and external p7-clean-install-2026-11-22/acceptance.json. Completes documentation/install task only; final P7 gate still depends on P6.

**Advisor:** Freebuff · Codex retains writing and automatic acceptance.

Freebuff audits/drafts selected documentation packets; Codex verifies commands, applies changes and runs clean-setup acceptance. Task dependencies permit documentation preparation while final P7 gate remains dependent on P6.

#### P7-C2 · Codex · Technical research report

Status: done · Estimate: 8 active hours

**Action:** Write method, baselines, results, confidence limits, failure analysis, threats to validity and next steps.

**Deliverable:** research report with real plots.

**Acceptance:** Every numeric statement derived from stored experiment data; no fabricated results.

**Depends on:** P3-C2, P4-C2

**Evidence:** 2026-11-22: executable scripts/report_research.py checked accepted historical manifests/JUnit/first-replay summaries, counts and holdout outcomes, and independently re-audited local saved replies/65 raw traces without model or SPICE execution. Nine targeted corruption/overwrite regressions passed; 347 unit tests and later 408 full-suite/interface tests passed. Generated versioned report, input hashes/full-precision JSON and visually checked measured SVG in docs/research; reproduction/limits in docs/RESEARCH_REPORT.md. Final report preserves fixed-control wins, target misses, shared factors, unequal candidate opportunities and blocked P6 replay. No fresh historical raw Phase 3/4 audit or full P7 acceptance claimed.

**Advisor:** Freebuff · Codex retains writing and automatic acceptance.

Freebuff may draft from explicitly approved evidence summaries; Codex checks every numeric claim against stored records and preserves failures. No raw experiment uploads or scientific-gate delegation.

#### P7-H1 · Human · Verify demo and claims

Status: todo · Estimate: 4 active hours

**Action:** Record 60–90s demo and approve accurate CV wording.

**Deliverable:** video/demo and review log.

**Acceptance:** Demo shows actual system, not illustrative simulations.

**Depends on:** P7-C1, P7-C2

**Evidence:** Not recorded

### P8: Decide constrained PCB research

**Window:** After validated core · Optional after launch

**Outcome:** Constrained topology extension and KiCad/PCB feasibility research.

**Phase dependencies:** P7

**Exit gate:** Explicit feasibility decision with validated model, export test and no industrial claims.

**Gate status:** pending

**Gate evidence:** Not recorded

#### P8-C1 · Codex · Component registry and model compatibility

Status: todo · Estimate: 8 active hours

**Action:** Prototype versioned R/C/L records, SPICE model compatibility flags, licensing metadata and pin mapping.

**Deliverable:** verified registry schema and 20-model smoke-test report when appropriate.

**Acceptance:** Compatibility evidence, not claim all PSpice models work.

**Depends on:** P1-C2

**Evidence:** Not recorded

#### P8-C2 · Codex · KiCad export proof of concept

Status: todo · Estimate: 10 active hours

**Action:** Export one permitted schematic/netlist and inspect resulting editable project; no promised PCB auto-layout.

**Deliverable:** demo plus constraints report.

**Acceptance:** Schematic pins and netlist connectivity reviewed; errors detectable.

**Depends on:** P8-C1

**Evidence:** Not recorded

#### P8-H1 · Human · Decide constrained PCB research

Status: todo · Estimate: 4 active hours

**Action:** Specify board layers, DRC, routing restrictions and when PCB work would be justified.

**Deliverable:** go/no-go decision.

**Acceptance:** Scope remains two-layer simple boards, not arbitrary optimal PCB.

**Depends on:** P8-C2

**Evidence:** Not recorded

## Codex and Freebuff collaboration

**Policy:** planning/agent-workflow-verification-2026-11-22.json

**Guide:** docs/AGENT_COLLABORATION.md

**Mode:** Codex-driven interactive terminal; finite queue during an active session

**Limits:** Verification allowance: 1 turn, 600 seconds, zero provider spend, no retry; consumed and closed. Original 3-turn cycle remains separately closed/blocked.

**Acceptance:** Automatic handoff audit passed on a separately authorized one-turn verification; 338 unit tests, matching hashes and timely receipt. Advisory text alone is not engineering acceptance.

**Data consent:** Owner explicitly approved selected task text, documentation and necessary code excerpts to Freebuff cloud on 2026-11-21; secrets, personal files, environment files, Git history and raw experiments excluded

P5-C5 accepted after real one-turn verification. Codex drives bounded terminal handoffs without owner copy/paste during an active session. Existing cycles are closed; no daemon or automatic new cycle. Later P7-C1/C2 documentation/report tasks completed with fresh install evidence; final P7 gate still depends on P6 and the unfinished demo.

## Proposed architecture

### Domain and specification

Pydantic typed structures for design targets, sources, loads, component bounds, E-series values, candidate topologies and validation; unit conversions centralized.

### Synthesis and safe netlists

Start with a finite allowlist of RC low-pass/high-pass topology templates; generate SPICE from trusted templates, never execute arbitrary LLM instructions, include directives or filesystem paths.

### Simulation adapter

Call locally installed ngspice via subprocess using argument lists, per-run temporary directories, timeouts, return-code checks and sanitized output; extract AC magnitude/phase into structured results. Set deterministic numeric configurations.

### Optimization / robust design

Separate objective calculation from simulator adapter; implement seeded random search, grid search and SciPy differential evolution with explicit evaluation budgets. Count simulator calls and cache identical candidates.

### Evaluation and research

Version benchmark instances; record seeds, environment, package versions, simulation settings, failure codes, objective components, runtime and token spend. Use analytic RC response as an independent oracle for initial fixtures.

### Product API and UI

Add FastAPI, React/TypeScript and plots only after CLI + deterministic tests work. Backend remains local-first and does not require GPU/cloud. Docker is optional and must handle ngspice executable paths explicitly.

## Intelligence and fine-tuning decisions

### Physics over language

Nonnegotiable

An LLM may propose specifications or topologies but cannot certify electrical correctness. Only independent analytic checks and successful bounded ngspice simulations support verification.

### LLM proposal stage

After numeric baseline

Evaluate LLM-guided structure selection using typed JSON/tool schemas; malformed outputs, timeouts and unsupported topologies are rejected without simulator execution. Compare against equal-budget random/classical baselines.

### Component library

Small verified registry first

Distinguish symbol, footprint, and SPICE model. Start generic R/C, then verified L and manufacturer models; track compatible simulator syntax, license, pin mapping and model provenance.

### RAG / fine-tune

Defer

RAG may later retrieve licensed datasheets with source attribution. Fine-tuning is not required for MVP; only consider it after a benchmark demonstrates a repeated failure that simpler tools cannot fix.

## Distinctive techniques

### Analytic baseline

P1

For ideal unloaded first-order RC low-pass use fc=1/(2πRC), and measure the −3 dB magnitude relative to passband gain with documented sweep resolution.

### Fixed-budget comparisons

P3–P6

Compare classical optimizers using equal ngspice evaluation counts; repeat seeds, collect success rates and distributional statistics rather than cherry-picked examples.

### Tolerance robustness

P4

Use explicit independent or correlated R/C distribution assumptions; report failure probabilities and quantiles with a declared sample size; distinguish simulated variability from measured manufacturing variability.

### Research ablation

P6

With vs without LLM topology suggestions; with vs without robustness penalty; compare accuracy, SPICE calls, elapsed time and cost, noting confounders.

## Provider choices and constraints

### ngspice

Required simulator, locally installed

Use the executable through a Python adapter. Validate installation and supported command-line semantics on Windows and Linux before implementation claims. [ngspice official website and documentation](https://ngspice.sourceforge.io/)

### SciPy

Required numerical methods

Differential evolution and response processing; use deterministic seeds and bound physical parameters. [SciPy differential evolution documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html)

### KiCad

Deferred optional EDA export

Do not block core inverse design on symbols, PCB footprints or a complete component library. Use official export interface after a verified MVP. [KiCad documentation](https://docs.kicad.org/)

### LLM API

Optional measured experiment

Do not require a paid key for Phase 1; use provider-neutral interface and token/cost budgets when activated.

## Capacity and budget assumptions

- Research-first MVP with a usable local demo, two supported RC filter families, deterministic baseline optimizers, tolerance analysis, and published reproducible experiments. No 100-user or full PCB promise.
- Research MVP is local-first. API spending defaults to $0; set an explicit cap when an LLM phase starts. Hosting is optional. No cloud compute or GPU purchase required for early RC simulation.

## Validation gates

All targets below are proposed. Only tested artifacts count as evidence.

### Simulator correctness

ngspice AC sweep and parsed −3 dB cutoff agree with analytic RC reference under declared sweep resolution and tolerances.

### Safety and reproducibility

Reject malformed inputs and unsupported topologies; per-run timeout, sandboxed temporary files, seed and environment information recorded.

### Optimization evidence

A target fc can be reached within predefined error and SPICE-call budgets; report failures, not only wins.

### Robustness evidence

Monte Carlo estimates reproducible under fixed seeds with explicitly documented R/C tolerances and sample counts.

### Product usability

Another student can run the CLI/demo from README on a clean system, inspect plots and reproduce a documented benchmark.

### Research integrity

All claims backed by versioned fixtures, baseline comparisons, experimental settings and raw CSV/JSON results.

## Human / Codex working agreement

### Codex and Freebuff collaboration

Codex alone writes the repository, coordinates dependencies and verifies automatic acceptance. Freebuff reviews allowlisted packets via the installed interactive terminal. scripts/agent_workflow.py persists source hashes, consent, pre-dispatch reservations and advisory receipts in an explicit stable ledger directory. Follow planning/agent-workflow.json and docs/AGENT_COLLABORATION.md; continue bounded eligible jobs during an active Codex session without owner copy/paste. No permanent unattended or paid-provider path is configured.

### Two-person division

Partner A: AI/optimization/backend/evaluation. Partner B: circuit models, ngspice integration, physical fixtures and component compatibility. Both review tests, design constraints and research claims.

### One vertical slice at a time

Start with spec → RC netlist → ngspice AC → cutoff extraction → optimize → verify. Do not introduce frontend, PCB, agents or broad parts libraries before this end-to-end slice passes.

### Evidence-driven completion

Codex implements only authorized unblocked tasks. A task is complete only after running relevant tests, recording exact commands/results and identifying unverified behavior; no fictional benchmark numbers.

### Agent permissions

Implement local code and tests now; ask before paid API use, external deployments, purchasing services, introducing new secrets, modifying out-of-scope files or destructive actions.

## Where the plan should live

Maintain canonical context.json, phase-tasks.json, generated roadmap files and progress evidence in Git. Use task IDs in commits and GitHub Issues if desired. [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects)

Use task IDs as issue titles. Fields: phase, owner, status, dependency IDs, estimate, deliverable, acceptance and evidence link. The issues.csv is an exchange table; GitHub Projects does not provide a guaranteed native one-click CSV import.

The HTML stores progress only in the browser. Export JSON to share statuses and evidence. Export an HTML snapshot for a self-contained visual copy. Git commits or a shared issue tracker reconcile changes; this file is not a multi-user database.

## Agent handoff prompt

```text
Read AGENTS.md and planning/HANDOFF.md. P7-C1/C2 completed documentation/report prerequisites: fresh 408-test/install acceptance plus 27 installed CLI/API calls (18 raw audited/nine JSON traces matched); read-only report reconciles historical data and preserves P6 incompleteness. Actual local-model study remains 25 generation attempts/65 raw-audited SPICE attempts, four matched comparisons, 3079 known tokens/one unknown usage, 57600 reservations; final replay incomplete and original windows closed. Prepared an unexecuted two-request/120-second/two-SPICE replay supplement with independent auditor; owner resource question pending, inference flag false. 364 unit tests then final 28 targeted replay/report checks passed without model/simulator use. P5-C5 accepted separately; development cycles closed. P6/final P7 release blocked, no paid traffic/PCB/deployment/feature push. GitHub public, initial main only. Source/Git stay on C; ancillary artifacts retain their existing C-path junction to D.
```

## Sources

Reference links aid implementation; verify current versions and local environment before making claims. Goals are engineering assumptions, not validated results.

- [ngspice official website and documentation](https://ngspice.sourceforge.io/)
- [SciPy differential evolution documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html)
- [KiCad documentation](https://docs.kicad.org/)
- [pytest documentation](https://docs.pytest.org/)
- [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
