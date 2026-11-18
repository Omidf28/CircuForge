# CircuForge — portable handoff

Updated 2026-11-18. Phase 1 automated numerical acceptance passes on Windows with real ngspice-47. Formal human gate review remains pending.

## Completed tasks

- P0-C1: installable Python package, pytest, executable discovery/preflight, missing-binary behavior.
- P0-C2: real fixed-template low-pass sweep, exit 0, 601 AC samples; evidence/lowpass-2026-11-18/.
- P1-C1: typed SI specs for RC low/high-pass, explicit source/load, bounds/feasibility/resource limits, continuous value policy and rejection tests.
- P1-C2: isolated fixed-template subprocess adapter; startup files and shell disabled; timeout, logs, output guard, failure and real integration tests.
- P1-C3: complex AC response, magnitude/phase and half-power cutoff verified against analytic responses for four R/C fixtures per topology, with amplitude normalization.

The starter's bounded first-slice search was implemented after core tests passed. It uses measured bisection; Phase 2 random/grid/SciPy tasks remain todo.

## Evidence

Exact commands, environment, corrected failure and implementation limits: docs/DEVELOPMENT.md. Newcomer setup: README.md.

Initial suite: python -m pytest -q -ra, with PYTHONPATH=.test-deps;src, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and CIRCUFORGE_NGSPICE pointing to .tools/Spice64/bin/ngspice_con.exe: **63 passed** including 11 real integration cases. Latest follow-up: **89 passed**; see the milestone log and docs/DEVELOPMENT.md.

- Low-pass measured 1591.487745916 Hz vs analytic 1591.549430919 Hz: 0.003876% error.
- High-pass measured 1591.612597494 Hz: 0.003969% error.
- Search target 2300 Hz reached 2300.380616684 Hz: 0.016549% error, 12 of 24 calls.
- Acceptance tolerance 0.1%; sweep 100 points/decade, 1 Hz–1 MHz. Genuine JSON/CSV/netlists/logs saved under evidence/.

## Open reviews and next tasks

P0-H1, P0-H2, P1-H1 remain todo. No human agreement/signoff is fabricated. Defaults: ideal zero-ohm source, infinite load, ideal continuous components. Four distinct R/C cases per topology are provided in tests.

After electrical review, proceed to P2-C1 objective/constraint contract, P2-C2 seeded random/grid, P2-C3 SciPy differential evolution with equal budgets. No frontend, API, PCB, LLM, robustness benchmark or deployment has started.

Initial simulator absence and package mirror issue were resolved with official portable ngspice and PyPI. No local simulator blocker remains. Linux is documented but unverified. Documents writes failed with WinError 2; implementation is in the authorized visualization workspace; existing VideoPlayer source is untouched. Source ZIP excludes tools/dependencies/build products; install from README on other machines.

## Plan maintenance

Canonical sources: planning/context.json, planning/phase-tasks.json. Run python planning/render_plan.py for HTML/Markdown/JSON/CSV. Renderer now permits actual statuses and requires evidence for done tasks. Browser defaults to canonical status/evidence but keeps local overrides, which still require export for sharing.

## Milestone log

- 2026-11-18: read planning-only package, implemented offline core; simulator initially missing, integration visibly skipped.
- 2026-11-18: provisioned official ngspice-47, verified low-pass, fixed print-quantization monotonicity check; 51 tests passed; saved genuine demo evidence.
- 2026-11-18: added high-pass after low-pass passed, bounded measured search, replay/budget/CLI tests; 63 passed; updated task statuses/evidence and generated plans. Human reviews remain open.
- 2026-11-18: owner requested Git/private GitHub setup and continued Phase 1 work. Prepared main, Python/Node/credential/artifact ignores and a staged credential pre-commit check. Suite now has 71 passing tests, including 8 credential-scanner tests. GitHub CLI is not authenticated; repository creation/connection awaits owner sign-in. No push is authorized until explicit approval. No Phase 2 product code was added; next code changes use a codex/ feature branch.
- 2026-11-18: created initial commit `20ef58f` on main with the credential hook enabled. Continued Phase 1 on `codex/p1-pipeline-hardening`: persisted explicit metric-error evidence for unbracketed cutoffs and verified the entire returned AC frequency grid. Added actual noninteger-decade ngspice regression cases and synthetic grid-corruption tests. Latest suite: **78 passed**. GitHub sign-in/remote creation and explicit push approval remain pending; nothing has been pushed.
- 2026-11-18: GitHub login confirmed as Omidf28; created private https://github.com/Omidf28/CircuForge and connected origin. Verified `isPrivate: true` and empty remote refs with `git ls-remote origin`. Local Phase 1 hardening is committed as `a20044f` on its feature branch. Initial main commit `20ef58f` is ready for push; explicit owner push approval is still pending. No code has been pushed. Automated Phase 1 acceptance remains verified (78 tests); human electrical reviews remain open, and Phase 2 is not started.
- 2026-11-18: owner explicitly approved the initial push. `git push -u origin main` succeeded; verified remote main is `20ef58fe266cee5837ed27f24ce6b60d60951c78` and repository remains private. Only initial main was pushed; follow-up work on `codex/p1-pipeline-hardening` remains local. No force-push or remote overwrite. Git/GitHub setup is complete. Phase 1 numerical acceptance remains verified, with human electrical review tasks still open.
- 2026-11-18: imported complete local history into the previously empty active `Implement CircuForge` workspace; original copy retained. Created `codex/p1-search-failure-evidence`. Added structured partial-search failures and call accounting, with eleven controlled regression tests: **89 passed**. Repaired mojibake in generated development prose. Python output creation under Documents remains environment-blocked, so execution evidence/cache use the authorized visualization workspace. No feature branch push; human reviews and Phase 2 remain open.
