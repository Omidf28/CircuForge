# Decisions and open questions — 2026-11-18

## Confirmed by project owner

- Main project: CircuForge / Wave2Circuit Research Edition (product + research).
- Differentiator: inverse circuit synthesis, real SPICE verification, numerical optimization; not generic educational circuit analysis.
- Develop with Codex, two students, goal: internship-ready engineering portfolio.
- Start with simple passive circuits; postpone large parts libraries, PCB optimization and fine-tuning.
- Phase 1 local implementation is approved as of this package request.

## Provisional engineering decisions (verify during P0)

- Python local-first core; ngspice + SciPy; bounded AC low-pass then high-pass.
- Ideal 0-ohm source and unloaded RC response for first analytic comparison.
- No production hosting, API/model spending or GPU initially.
- 12-week target is approximate. Proposed partner ownership: AI/optimizer/app vs simulation/components/circuit fixtures.

## Open items for team

- Exact operating system and path to installed ngspice on each workstation.
- R/C ranges, allowed value series, target frequencies, sweep density/interpolation tolerance.
- How to handle finite loads and source impedances beyond initial ideal assumptions.
- Permissions/licenses for any imported SPICE models and datasheets.
- Budget approval and model selection before first LLM experiments.
- Research benchmark case definitions, reviewer and experimental error thresholds.

## Implemented defaults — 2026-11-18 (owner accepted 2026-11-19)

- Verified Windows 11, Python 3.12.7 and ngspice-47 console. Linux remains unverified.
- Ideal zero-ohm source, infinite load, explicitly normalized AC amplitude.
- Default R: 10 ohm–1 Mohm; C: 1 pF–1 mF. Continuous values only; E-series policies are rejected.
- Sweep: 1 Hz–1 MHz, 100 points/decade; half-power cutoff interpolation in log-frequency/dB; 0.1% acceptance.
- Max 1000 evaluations, 30 seconds/call, 20,000 sweep points, 8 MiB combined output. Default 32 evaluations and 10 seconds/call. These local guardrails do not impose a kernel memory quota.
- First-slice search: deterministic log-bounds bisection driven by measured ngspice cutoff. Phase 2 random/grid/SciPy comparisons remain deferred.

## Owner review acceptance — 2026-11-19

Reviewer: project owner, through the explicit review response in this chat. The owner answered: «بازبینی کردم و Phase 1 را تأیید می‌کنم».

The question linked the Phase 1 circuit/result review and stated the ideal zero-ohm source, infinite load, ideal continuous R/C values and 0.1% target error policy, with eight genuine reference cases passing. Record this as owner acceptance of the documented Phase 1 model, connectivity and reference results for P0-H1, P0-H2 and P1-H1. Automated acceptance evidence remains the previously executed 122 passing tests and eight reference cases; no additional test execution is implied by this decision.

This records the owner's declared review. It does not assert a separate teammate/second-reviewer signoff, hardware verification or Linux testing. That review approval explicitly excluded starting Phase 2 and pushing feature-branch commits; those actions were not authorized by the review decision itself. The subsequent continuation is recorded separately below.

## Subsequent continuation — 2026-11-19

After Phase 1 acceptance was recorded, the owner requested next. Continued only the next local roadmap phase: P2-C1/C2/C3 numerical objective and classical baselines. This later continuation is separate from the earlier review approval. P2-H1 is still human-owned; no human Phase 2 acceptance, Phase 3, paid/API/deployment or feature-branch push is inferred.

## Owner delegation to automatic technical gates — 2026-11-19

The owner later instructed: «یه جوری کار کن نیازی به بازبینی دستی نداشته باشه next». This supersedes the requirement for manual technical review before local numerical phase progression. The owner did not claim to have reviewed Phase 2; record automatic acceptance only when its evidence checker passes. Legacy P2-H1 is replaced by P2-C4, not labeled as a completed human review.

Phase 2 automatic policy is phase2-engineering-v1: full tests without failures/errors/skips, five distinct typed cases, bounded fresh real ngspice comparisons, matched actual budgets, complete per-call evidence and raw/CSV/analytic/metric/status consistency. Baseline target misses remain misses. The policy accepts engineering execution/reproducibility rather than requiring every generic optimizer to hit the target at 64 calls. The original case ranges, seed, budgets and 0.1% tolerance remain unchanged.

The delegation applies to technical acceptance. It does not authorize remote pushes, paid/API traffic, credentials, deployment, purchases or destructive actions. Further phase gates may be automated when their actual checkers exist and pass; no later task is automatically marked complete by this decision.

## Phase 3 experiment policy — 2026-11-19

The subsequent next instruction continues the next bounded local roadmap phase. The initial benchmark 1.0 exposed three scale-equivalent pairs during structural review after its numerical run. It is retained as superseded evidence and a rejection regression, not accepted as the final Phase 3 fixture. Current benchmark version 2.0 revises three bounds to remove those normalized duplicates, frozen before v2 execution: 20 curated nominal tasks (16 feasible, including two fixed controls; four expected infeasible), seeds 7/42/2026 and 12 calls per method for free domains. The conservative configured bound is 2160 calls/run under a hard manifest maximum of 2500, with independent replay. This small budget keeps automatic local acceptance bounded; it is a new experiment rather than a replacement for Phase 2's unchanged 64-call pilot. Grid repeats are deterministic controls, not independent random evidence. Thresholds remain 0.1%; no observed target outcome is a reason to change a case or acceptance threshold. See docs/PHASE3.md for the structural correction and normalized uniqueness policy.

Technical policy phase3-reproducibility-v2 requires normalized task distinctness, complete tests without skips, all declared trials, per-call physical/record audits, matched actual method budgets, no unexpected simulation/verification failures and exact replay of numerical traces within the recorded environment. Runtime is measured but excluded from numerical equality. Expected unreachable targets are rejected before optimization; rejection never counts as successful circuit synthesis. The implemented gate replaces P3-H1 only after its observed successful execution. No human signoff, hardware guarantee, Phase 4 result or publication permission is asserted.

## Phase 4 declared tolerance policy — 2026-11-19

The next continuation authorizes the next bounded local roadmap phase. Prespecified robustness-v1.json uses independent uniform multiplicative R +/-1% and C +/-5% errors, ideal zero-ohm source/infinite load and the unchanged 0.1% target tolerance. These illustrative distributions are not manufacturer/hardware measurements. Unsupported correlation models are rejected. No clipping is allowed: nominal bounds constrain nominal design values; an explicit validated simulation envelope covers realized component values. Source/load/topology and simulator isolation stay unchanged.

Each method gets 64 training plus 32 independent holdout calls; two cases and seeds 7/42 produce 768 calls/run, independently replayed. Robust random search evaluates eight nominal candidates with seven common perturbations each, scoring nominal log error plus measured perturbation q95 log error. Nominal random search spends its 64 training calls on 64 nominal candidates from the same proposal stream. Candidate opportunity counts therefore differ visibly under equal total simulation cost. Fresh paired holdout factors never select the design. Small empirical linear quantiles/pass rates are reported separately from nominal success, without confidence or hardware-yield guarantees. Model assumptions, pairing and budget were fixed before the production run; no optimizer win is required.

The owner delegated technical review to automatic checks. P4-H1 can be superseded by P4-C3 only after phase4-tolerance-v1 actually passes full tests, raw physics/factor/objective/budget/statistics audits and exact numerical replay. No human signoff or changed push/spending/deployment authorization is implied. Phase 5 needs its own implementation and acceptance evidence.

## Phase 5 local interface policy — 2026-11-19

The next continuation implements P5-C1 then P5-C2 against the accepted scientific core. Both use one typed application contract and measured engine; the legacy commands and experiment results remain unchanged. HTTP is loopback-only with one active design, strict JSON/body/compute limits, trusted templates and per-request temporary cleanup. No public hosting, authentication system or persistent artifact store is introduced. Request bodies cannot select executables or filesystem paths. HTTP 200 for a completed target miss is an explicit transport/result distinction, with a target_missed status and CLI exit 1; simulation failures remain failed results.

Optional P5-C3 is deferred, as START_CODEX.md excludes a frontend and CLI/API plus exported plots satisfy the phase's inspectable-result goal. P5-H1's technical clean-install/reproducibility checks are replaced by automatic P5-C4 only after the implemented checker passes. The fresh installed wheel must run under Python -I outside source import paths; actual HTTP, CLI and downloaded raw artifacts must agree. Record the 27 actual walkthrough calls separately from the 18 archived/raw-audited CLI/ZIP calls and nine JSON calls matched by numerical traces. No independent human usability review or hardware/deployment signoff is invented. Paid API/provider permissions and the deferred advanced-agent/PCB scope remain unchanged.

## Offline proposal continuation — 2026-11-20

After canceling project migration, the owner requested continuation of CircuForge
on C. Implemented only the next eligible task P6-C1: an isolated offline proposal
contract with fixture providers, strict candidate validation and bounded usage
accounting. Automatic task policy p6-c1-offline-contract-v1 passed 319 tests
without skips and four raw-audited genuine SPICE calls. This is not an LLM or
equal-budget provider experiment; no model-token or actual billing measurement
is claimed. Invalid proposals, duplicate measurements and deliberate misses
remain visible. Model efficacy and the full Phase 6 gate are unaccepted.

P6-C2 now explicitly depends on P6-H1, matching the preexisting rule requiring a
separate owner provider/privacy/budget decision before actual experiments. No
provider, price, credential or nonzero spending cap was selected. Advanced
agents, frontend, PCB, deployment and feature-branch pushes remain deferred.

## Explicit local-model decision and observed partial trial — 2026-11-20

For P6-H1 the owner answered «تأیید آزمایش فقط محلی با همین سقف‌ها» after being
shown the installed llama3 proposal: zero provider expenditure, <=32 requests,
10 minutes, <=80 SPICE attempts and two CPU threads, without downloads or sending
personal files outside the machine. The detailed proposal reserves at most 73728
tokens and disables GPU layers/cloud/proxies/redirects. This is actual limited
owner permission, not a delegated technical-review waiver or paid-provider consent.

The resulting one-window trial ended with seven model requests and 15 real
SPICE attempts. An invalid pilot was retained across one documented orchestration
correction/continuation; the original counters and deadline were not restarted.
Inputs, prompts, thresholds and seeds were unchanged; source epochs are recorded.
Final raw/usage integrity passed, but zero matched-call comparisons completed and
no target pass or efficacy conclusion is claimed. The spent allowance is closed
in the source configuration; another run requires a renewed resource decision.
P6-H1 is done for its actual decision; P6-C2 and the Phase 6 gate remain blocked.
See docs/PHASE6_LOCAL_RESULTS.md for exact outcomes and verification limits.
