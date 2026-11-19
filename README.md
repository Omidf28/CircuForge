# CircuForge — Wave2Circuit Research Edition

Phase 1 implements typed RC low/high-pass specifications, fixed netlists, real ngspice AC simulation, complex response/cutoff extraction, and bounded measured R/C search. Local CPU only; no accounts required.

Phase 2 adds measured objectives, seeded random/grid and SciPy baselines with identical SPICE-call caps, exact per-run caching and raw per-call evidence. The owner-authorized **automatic acceptance gate passed with 170 tests and 771 freshly audited real calls**. The five-case comparison and its target misses remain documented in [docs/PHASE2.md](docs/PHASE2.md).

Phase 3 adds 20 normalized-distinct nominal benchmark cases and three-seed comparisons. Its automatic gate passed with **198 tests and 3060 audited real calls including exact numerical replay**. Per run, 18 fixed-control designs passed, 126 free-domain results missed the original tolerance and 36 infeasible requests were rejected before simulation. See [docs/PHASE3.md](docs/PHASE3.md). No manual technical review is required.

Phase 4's tolerance-study gate passed with **234 tests and 1536 audited real calls including exact replay**. Nominal and robust methods used matched total simulation budgets and separate holdout samples. No consistent robust improvement was observed; nominal target misses and finite-sample outcomes remain reported in [docs/PHASE4.md](docs/PHASE4.md).

## Acceptance without manual review

After installing the project with its test extra and configuring ngspice, run from project root:

```text
python scripts/accept_phase2.py --output /new/writable/absolute/path
python scripts/accept_phase3.py --output /another/new/writable/absolute/path
python scripts/accept_phase4.py --output /new/tolerance-acceptance/path
```

The command runs all tests, refuses skipped/failed tests, executes a fresh bounded comparison and recomputes physics/metrics/accounting from every raw response. acceptance.json records passed or blocked with reasons. A pass is automatic technical acceptance; target misses remain failures in the design-success counts. Missing or inconsistent evidence is repaired and rerun rather than waived manually. See [docs/AUTOMATIC_ACCEPTANCE.md](docs/AUTOMATIC_ACCEPTANCE.md). Remote pushes and paid/deployment actions retain their separate authorization requirements.

The Phase 3 command uses the versioned 20-case benchmark, seeds 7/42/2026 and 12 calls per method on free domains. It executes the experiment twice and checks exact candidate/metric replay along with the raw physics evidence. Fixed domains use one call; four expected infeasible tasks are rejected before simulation. See [docs/PHASE3.md](docs/PHASE3.md) for configuration, result interpretation and limits. To produce a single dataset, use `python scripts/run_benchmark.py --output /new/benchmark/path`.

Phase 4 adds declared independent uniform component tolerances, matched-call nominal/robust random-search comparison and fresh holdout samples. Use `python scripts/compare_robustness.py --output /new/tolerance-study/path` for one dataset and PNG, or the acceptance command for full tests and independent replay. The `test` extra includes the plotting dependency; `report` installs it separately for reporting without pytest. See [docs/PHASE4.md](docs/PHASE4.md) for the frozen experiment and limitations. Nominal target success and empirical tolerance pass rate are separate measurements.

## Windows setup (Python 3.11+)

From this extracted project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[test]"
```

Extract the Windows portable package from the [official ngspice download page](https://ngspice.sourceforge.io/download.html). Use **Spice64/bin/ngspice_con.exe**, the console executable.

```powershell
$env:CIRCUFORGE_NGSPICE = 'C:\path\to\Spice64\bin\ngspice_con.exe'
.\.venv\Scripts\python -m circuforge preflight
.\.venv\Scripts\python -m pytest -q -ra
.\.venv\Scripts\python -m circuforge simulate --spec examples/lowpass.json --output runs/lowpass
.\.venv\Scripts\python -m circuforge simulate --spec examples/highpass.json --output runs/highpass
.\.venv\Scripts\python -m circuforge simulate --spec examples/search.json --search --output runs/search
```

Use new output directories for each run. If the configured pip mirror lacks pytest, specify `--index-url https://pypi.org/simple` when installing.

## Linux setup (documented, not yet executed)

```bash
sudo apt-get install ngspice python3-venv
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m circuforge preflight
.venv/bin/python -m pytest -q -ra
.venv/bin/python -m circuforge simulate --spec examples/lowpass.json --output runs/lowpass
.venv/bin/python -m circuforge simulate --spec examples/search.json --search --output runs/search
```

Use your distribution's package manager. Windows 11 / Python 3.12.7 / ngspice-47 were actually verified. Global `--ngspice PATH` before the subcommand overrides CIRCUFORGE_NGSPICE; otherwise PATH is searched. Missing binary means exit 2 and explicit integration-test skips, never simulated success. A discovered executable that fails preflight/simulation fails integration tests.

## Results and assumptions

`report.json` records inputs, component values, measured/analytic/target errors, pass flags, environment, actual command, timing and call count. `response.csv` contains frequency, real/imaginary H, gain dB and phase degrees. `circuit.cir`, `stdout.log` and `stderr.log` preserve genuine simulator output. Simulator failures produce `failure.json`. Exit 0 means analytic and target acceptance passed; exit 1 means numerical acceptance failed; exit 2 means input/environment/simulator/artifact error.

Default reference: 1 kohm, 100 nF, ideal zero-ohm voltage source and infinite load. Both RC topologies have fc=1/(2*pi*R*C); phase at cutoff is -45 degrees for low-pass, +45 for high-pass. All fields use SI units. Only continuous values are supported; E-series policies, nonideal source/load and unsupported circuits are rejected.

Half-power cutoff is **-3.0102999566 dB**, relative to known unity passband gain, interpolated in log-frequency/dB. Default sweep: 100 points/decade, 1 Hz–1 MHz. Verified cutoff tolerance: 0.1%. Coarser user-selected grids may fail this check. Batch print rounding is allowed up to 1e-5 dB apparent nonmonotonicity.

The first-slice --search option uses deterministic bisection along log R/C bounds, with measured ngspice objectives, duplicate detection and a hard call budget. Every candidate metric is recorded; raw waveform/log artifacts describe the selected candidate. If a search aborts, failure.json preserves the attempted call count (including the failed attempt), prior measured results, failed candidate/spec, error status and captured logs; no replacement measurements are invented. Generic Phase 2 baselines are separate optimize/compare commands below.

## Phase 2 optimizer commands

With the installed package and ngspice configured:

```text
python -m circuforge optimize --spec examples/search.json --method scipy --seed 42 --output /new/writable/path
python -m circuforge compare --spec examples/search.json --seed 42 --output /new/comparison/path
python scripts/compare_phase2.py --seed 42 --output /new/five-case-review/path
```

Use OS-appropriate absolute paths. Each method gets the spec's max_evaluations cap and its own cache; actual counts are reported. Fully fixed domains use one call. optimize exits 1 when no design meets tolerance. compare can complete successfully while all methods miss target tolerance; inspect converged and target_relative_error. Reports retain all misses and raw call artifacts. No analytic fitness fallback is used.

In the recorded seed-42 review, each method used 64 calls on each of four free cases and one call on the fixed case: **771 genuine AC attempts total**. None met 0.1% tolerance on the free cases; all passed the fixed case. This is single-seed baseline evidence, not a statistical performance claim. The Phase 1 domain-specific bisection remains available.

## Verified milestone

The initial milestone had **63 passing tests**. The latest Phase 1 follow-up has **122 passing tests** in the isolated test environment, including real simulator integration, controlled failure accounting, minimum sample counts and tolerance-aware target feasibility. Fresh package installation was also verified at an earlier milestone. Original saved evidence:

| Case | Measured cutoff | Error | Calls |
|---|---:|---:|---:|
| Low-pass, 1 kohm/100 nF | 1591.487745916 Hz | 0.003876% vs analytic | 1 |
| High-pass, 1 kohm/100 nF | 1591.612597494 Hz | 0.003969% vs analytic | 1 |
| Search, target 2300 Hz | 2300.380616684 Hz | 0.016549% vs target | 12 of 24 |

See `evidence/`, `docs/DEVELOPMENT.md` and `planning/HANDOFF.md`. The owner explicitly accepted the Phase 1 circuit/result review on 2026-11-19; the decision is in `docs/DECISIONS.md`. This approval excludes Phase 2 and feature-branch pushes. No physical hardware performance is established by simulation.

The [Phase 1 review packet](docs/PHASE1_REVIEW.md) contains connectivity diagrams, four distinct R/C reference pairs per topology, acceptance limits and review points. Reproduce all eight real fixtures after installing the package:

```text
python scripts/verify_phase1.py --output /absolute/path/to/new/evidence-directory
```

Use an OS-appropriate absolute path. In this managed session, Python directory creation under Documents is blocked; select an output path in the authorized visualization workspace. The script saves raw evidence and an automated reference-check result. All eight cases passed; maximum measured cutoff error was 0.005891%.

Target feasibility includes the selected relative-error tolerance. A target is rejected when the achievable RC cutoff interval and target*(1±tolerance) are disjoint. This permits rounded targets for fixed components without changing component bounds or claiming exact matching. `examples/fixed-target.json` demonstrates 1 kohm/100 nF with target 1591.5494 Hz and 0.1% tolerance; use it with the simulate command, optionally with --search. Simulation still determines the measured pass/fail result.

Canonical plans: `planning/context.json`, `planning/phase-tasks.json`. Regenerate HTML/Markdown/JSON/CSV using `python planning/render_plan.py`. Browser overrides remain local and require export for sharing. Source: `src/circuforge`; tests: `tests/unit`, `tests/integration`.

No frontend, API, advanced agents, PCB automation, paid service or deployment has been started.

## Version control

See [docs/VERSION_CONTROL.md](docs/VERSION_CONTROL.md) for the private GitHub setup, staged credential scan and feature-branch workflow. Generated simulation evidence stays local and is excluded from Git. The initial main commit was pushed with owner approval; later feature branches remain local until separately approved.
