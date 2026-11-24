# Paste this into Codex after opening the extracted CircuForge folder

## Current continuation (2026-11-24)

P5-C3 has a tested local HTML prototype for archived baseline comparisons.
Use `comparison-report` after `compare` and see docs/COMPARISON_REPORT.md and
planning/HANDOFF.md. Keep the laptop screen free. Existing research gates and
the published desktop bundle retain their own source and evidence.

## Current continuation (2026-11-23)

Owner needs the laptop screen free. Do not use native mouse/keyboard automation,
screen capture or visible test windows without a new explicit request. P5-C7/
v0.3.1 compact layout passed screen-independent acceptance: 525 core tests,
four earlier layout checks and raw-audited withdrawn source/installed widget
runs with the matching fresh runtime. New pixel QA is not claimed. Read current
HANDOFF and docs/DESKTOP.md; older source-bound milestones below remain history.

## Current continuation (2026-11-22)

Owner explicitly chose a simple local graphical interface. P5-C6/v0.3.0 passed
phase5-simple-desktop-v1 on codex/local-desktop-ui: 516 tests, fresh matching
installation and 31 actual GUI/CLI/HTTP calls. Read HANDOFF and docs/DESKTOP.md;
only external final-acceptance-v3 is accepted, with earlier failed drafts retained.
This overrides earlier frontend exclusion only for that bounded desktop. Full
optimizer dashboard, model cycles, PCB and publication remain deferred/separate.

Latest maintenance P7-C7 extends caller-path repair across remaining acceptance
and installed-walkthrough scripts. Actual outside-checkout verification passed
480 tests, fresh installation and 54 CLI/HTTP calls with raw/JSON/cleanup checks.
Read the current HANDOFF and docs/OPERATIONS.md first. Earlier P7-C6 numerical
replay (475 tests/384 calls) and packaged source counts remain dated evidence.

P7-C5 also supplies a checked local v0.2 Python 3.12 handoff from accepted commit
60b1ff9. See docs/LOCAL_RELEASE.md for the exact ZIP identity and quickstart;
packaging added no numerical/model cycle and did not publish the branch.

Read AGENTS.md and planning/HANDOFF.md first. The local MVP and bounded numerical
follow-up P7-C4 are accepted; current v0.2.0 has 472 tests and its own audited
one-call/replay and fresh installed-interface evidence. v0.1 was published via
PR #1; the new feature branch remains local. All model/Freebuff cycles below are
consumed and closed. Earlier continuation text is historical, not a new cycle.
Report this local result before complex expansion. See docs/ANALYTIC_RC.md.

## Current continuation (2026-11-21)

The original first-slice instructions below are historical. Read AGENTS.md,
planning/HANDOFF.md, planning/phase-tasks.json and docs/AGENT_COLLABORATION.md.
Continue the bounded Codex/Freebuff queue in planning/agent-workflow.json without
owner copy/paste or manual technical signoff. Use one stable explicit --state-dir,
reserve before dispatch, keep the original cycle caps and record actual advisory
replies. Codex alone edits source and accepts evidence. No background daemon or
paid SDK is configured. Keep Phase 6 experiment permissions separate; the full
P7 release gate still depends on accepted P6 evidence.

## Historical first local slice

Read `AGENTS.md`, `README.md`, `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `planning/HANDOFF.md`, and relevant `planning/phase-tasks.json` tasks.

I authorize you to **implement the first local CircuForge MVP vertical slice now**, not merely plan it. Respect task dependencies and `AGENTS.md`.

1. Inspect current files and confirm this is a planning-only repository; don't claim software already exists.
2. Set up a clean, minimal Python package with pytest, typed specs and ngspice preflight detection.
3. Implement an allowlisted RC low-pass SPICE netlist and execute it using locally installed ngspice with subprocess timeout and safe temp files; capture the real AC simulation data.
4. Parse complex frequency response and measure the -3 dB cutoff. Validate against analytical `fc = 1/(2*pi*R*C)` with documented frequency sweep resolution and tolerance.
5. Provide one runnable CLI example, one analytic unit test and one real ngspice integration test (skip/block clearly when ngspice isn't installed, never fabricate output).
6. After tests pass, implement bounded R/C parameter search for a specified target cutoff with measured results and a call counter.
7. Write installation/run instructions for Windows and Linux and update `planning/HANDOFF.md` with completed tasks, exact test commands, outcomes and next steps.

**Do not** build the frontend, large component library, PCB layout, LLM agents, OCR, fine-tuning or cloud deployment during this task. Do not spend money, request credentials, or install unnecessary infrastructure. If ngspice cannot run, provide precise preflight/installation instructions and implement testable offline components without claiming end-to-end success.

At the end, summarize modified files, assumptions, commands/tests actually executed, observed results, blockers and suggested next task IDs.
