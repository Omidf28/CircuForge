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
