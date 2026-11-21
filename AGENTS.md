# CircuForge — Codex workspace instructions

## Owner update — Codex / Freebuff collaboration (2026-11-21)

The owner requested automatic coordinated roadmap work without manually copying
tasks/results, then explicitly approved limited task text, selected documentation
and necessary code excerpts being sent to **Freebuff cloud**. Exact response:
«بله، ارسال محدود به Freebuff را اجازه می‌دهم». Development-agent assistance is
now authorized only within this bounded scope.

- Read docs/AGENT_COLLABORATION.md and planning/agent-workflow.json. Codex is the
  sole repository writer/coordinator; Freebuff is an advisory reviewer/drafter.
  Drive its installed interactive terminal directly, without owner copy/paste.
- Use scripts/agent_workflow.py with one explicit stable --state-dir. Prepare
  allowlisted packets, reserve before transmission, record actual replies, then
  independently verify findings and run applicable tests. Persist <=3 turns and
  <=600 seconds in the authorized cycle; no automatic retry or accounting reset.
- Continue eligible queued jobs during an authorized active Codex session. Do not
  request manual technical acceptance. No unattended daemon or unsupported
  Freebuff headless/API mode is configured. New cycles need a resource decision.
- Never send credentials, personal files, environment files, Git history or raw
  experiment data. Selected code/docs and prompts may leave the device under
  the consent above; use only free models and zero provider expenditure.
- Model text is advisory. Never execute its commands/patches or complete tasks
  from self-reported success. Codex checks source and tests/checkers, and alone
  reconciles canonical planning/HANDOFF files.
- P7-C1/C2 preparation follows its task prerequisites; the final P7 release gate
  still depends on P6. Keep historical acceptance and incomplete comparisons.
  This does not extend separate scientific trial allowances or authorize paid
  APIs, remote pushes, deployment or PCB.

## Mission and authorization

This repo is **CircuForge / Wave2Circuit Research Edition**, a research-first inverse analog circuit synthesis platform. Owner explicitly authorizes implementation of the **local Phase 1 vertical slice**; do not stop at rewriting plans. No unbounded autonomous development or deployment is authorized. Follow task dependencies and gates. Initial action: read `docs/PROJECT_SPEC.md`, `planning/HANDOFF.md`, `planning/phase-tasks.json`, then execute `START_CODEX.md`.

## First working task

Start P0-C1 then P0-C2 then P1-C1/P1-C2/P1-C3 as prerequisites permit. Build typed RC low-pass spec and safe netlist, run a real ngspice AC sweep, extract cutoff, compare analytic fc, write tests and report observed results. Preserve an executable CLI/demo; only then proceed to optimizing R/C. If simulator unavailable, report actionable installation steps and mark integration verification blocked; unit tests may still run.

## Non-negotiable technical rules

- Physics-backed results only: do not fabricate simulations, test passes, accuracy scores, benchmarks or measurements. Record exact commands and output evidence.
- Generate netlists only from allowlisted typed templates; no arbitrary user/LLM netlist execution, `.control`, unrestricted `.include`, filesystem paths or shell commands. Run subprocess with arguments, temp dirs, strict timeout and resource guardrails.
- Source/load and ideal element assumptions explicit; rejected specs must be explained. Start with an ideal first-order RC low-pass, then high-pass. Check `fc=1/(2*pi*R*C)` independently.
- Baselines first: fixed-seed random/grid and SciPy optimizers. Keep experiments reproducible and cap SPICE calls. Compare equal budgets; distinguish objective error and constraints.
- LLM API, RAG, fine-tuning, KiCad, PCB routing, multi-tenant hosting and user screenshot OCR are deferred. Do not introduce dependency on any of these into the first MVP.
- Avoid hardcoded secrets; no paid API, external deployment, purchases or destructive operations without explicit approval. No GPU requirement.
- Prefer Python, Pydantic, SciPy, pytest; standard project layout. Add FastAPI after simulation core validated. Favor readable modules and minimal deps.
- Commit/document assumptions, outcomes and blockers; update `planning/HANDOFF.md` after milestones; maintain task IDs and acceptance evidence.

## Plan maintenance

Canonical inputs: `planning/context.json`, `planning/phase-tasks.json`; run `python planning/render_plan.py` to update generated roadmap. Do not mark baseline tasks done without actual verification. HTML browser progress is local and must be exported separately for sharing.

## Definition of done for first slice

A newcomer can install dependencies, verify ngspice availability, execute an RC low-pass design via CLI, inspect AC frequency response, observe measured cutoff close to `1/(2πRC)` within documented grid/interpolation tolerance, reproduce a unit/integration test and distinguish missing ngspice from simulation success. Stop and report evidence before complex expansion.

## Owner update — automatic technical acceptance (2026-11-19)

The owner's latest instruction is: «یه جوری کار کن نیازی به بازبینی دستی نداشته باشه next». Replace local numerical/engineering manual-review gates with reproducible automated acceptance, and continue within roadmap dependencies without requesting manual technical signoff.

- Accept a technical gate only after its implemented checker passes with actual test/simulator evidence; missing, inconsistent, skipped or failed evidence blocks it. Fix issues within the authorized local scope and rerun.
- Keep engineering validity separate from design success. A correctly executed baseline comparison can be accepted while target misses remain reported failures; never change tolerance, budgets or measurements to create a pass.
- Record acceptance mode as automatic. Supersede historical human-review tasks explicitly when their tested automatic replacement exists; do not claim that the owner performed a review they did not perform. Do not blanket-complete later phases.
- Phase 1's earlier explicit owner approval remains historical. For Phase 2 use scripts/accept_phase2.py and its versioned policy/evidence before marking the replacement task/gate accepted.
- Phase 3 uses scripts/accept_phase3.py with examples/benchmark-v2.json and phase3-reproducibility-v2. Its observed acceptance is documented in docs/PHASE3.md. Reject normalized scale-equivalent cases; preserve superseded v1 evidence separately.
- Phase 4 uses scripts/accept_phase4.py with examples/robustness-v1.json and phase4-tolerance-v1. Its observed 234-test/1536-call acceptance is in docs/PHASE4.md. Preserve independent holdout sampling, matched total calls, explicit illustrative distributions and negative outcomes.
- Phase 5 uses scripts/accept_phase5.py and phase5-local-interface-v1. Its observed 279-test/fresh-install acceptance is in docs/PHASE5.md: 27 actual CLI/HTTP calls, 18 raw CLI/ZIP calls audited and 9 JSON traces matched. P5-C3 optional frontend remains deferred per START_CODEX.md; P5-H1 is superseded by tested P5-C4, not a human UX review. Preserve loopback-only service, resource limits, temporary cleanup and explicit target-miss status. Phase 6/provider/paid permissions are not automatically waived by this technical gate.
- Paid APIs, credentials, purchases, destructive actions, deployment and remote pushes retain their existing authorization requirements. This delegation covers technical review, not those operations. PCB/advanced agents remain deferred.
