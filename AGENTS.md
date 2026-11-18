# CircuForge — Codex workspace instructions

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
