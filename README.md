# CircuForge — Wave2Circuit Research Edition

Phase 1 implements typed RC low/high-pass specifications, fixed netlists, real ngspice AC simulation, complex response/cutoff extraction, and bounded measured R/C search. Local CPU only; no accounts required.

Phase 2 adds measured objectives, seeded random/grid and SciPy baselines with identical SPICE-call caps, exact per-run caching and raw per-call evidence. The owner-authorized **automatic acceptance gate passed with 170 tests and 771 freshly audited real calls**. The five-case comparison and its target misses remain documented in [docs/PHASE2.md](docs/PHASE2.md).

Phase 3 adds 20 normalized-distinct nominal benchmark cases and three-seed comparisons. Its automatic gate passed with **198 tests and 3060 audited real calls including exact numerical replay**. Per run, 18 fixed-control designs passed, 126 free-domain results missed the original tolerance and 36 infeasible requests were rejected before simulation. See [docs/PHASE3.md](docs/PHASE3.md). No manual technical review is required.

Phase 4's tolerance-study gate passed with **234 tests and 1536 audited real calls including exact replay**. Nominal and robust methods used matched total simulation budgets and separate holdout samples. No consistent robust improvement was observed; nominal target misses and finite-sample outcomes remain reported in [docs/PHASE4.md](docs/PHASE4.md).

Phase 5 adds a shared typed `design` command and a bounded loopback FastAPI service. Its automatic gate passed with **279 tests and a fresh isolated package install**, followed by **27 real CLI/HTTP calls** (18 raw CLI/ZIP calls audited and nine JSON traces matched). The same request exports JSON/CSV/PNG, raw call history and a checksum-linked ZIP. See [docs/PHASE5.md](docs/PHASE5.md) for setup, HTTP examples, statuses and limits. The optional dashboard remains deferred.

P6-C1 adds the offline proposal contract and conservative usage accounting. Its
task acceptance passed with **319 tests without skips and four freshly audited
real ngspice calls** from fixed local fixtures. A later owner-approved local
Llama 3 trial was renewed once on November 21 with unchanged limits. The renewal
completed **four matched-call comparisons and 65 independently audited SPICE
attempts**, using 25 model requests. All methods missed the 0.1% target. Its
deadline left the final model replay stage incomplete; P6-C2 and Phase 6 remain
blocked. Current adapter/audit checks have **293 passing unit tests**, separate
from historical full-suite acceptance. See
[renewed local results](docs/PHASE6_LOCAL_RENEWAL.md) and
[docs/PHASE6.md](docs/PHASE6.md). The November 20 dataset is retained separately.

## Acceptance without manual review

After installing the project with its test extra and configuring ngspice, run from project root:

Use the same virtual-environment interpreter that installed the dependencies:
on Windows replace `python` below with `.\.venv\Scripts\python`, and on Linux
with `.venv/bin/python`. For an uninstalled source checkout, set `PYTHONPATH=src`
instead of assuming the source package is importable. In managed Windows
sessions, Phase 5's real loopback walkthrough also needs local-socket permission;
an environment denial blocks verification. Use a new writable output directory
for every acceptance run. See [Phase 5 setup and limits](docs/PHASE5.md).

```text
python scripts/accept_phase2.py --output /new/writable/absolute/path
python scripts/accept_phase3.py --output /another/new/writable/absolute/path
python scripts/accept_phase4.py --output /new/tolerance-acceptance/path
python scripts/accept_phase5.py --output /new/installed-cli-api-acceptance/path
```

The command runs all tests, refuses skipped/failed tests, executes a fresh bounded comparison and recomputes physics/metrics/accounting from every raw response. acceptance.json records passed or blocked with reasons. A pass is automatic technical acceptance; target misses remain failures in the design-success counts. Missing or inconsistent evidence is repaired and rerun rather than waived manually. See [docs/AUTOMATIC_ACCEPTANCE.md](docs/AUTOMATIC_ACCEPTANCE.md). Remote pushes and paid/deployment actions retain their separate authorization requirements.

The Phase 3 command uses the versioned 20-case benchmark, seeds 7/42/2026 and 12 calls per method on free domains. It executes the experiment twice and checks exact candidate/metric replay along with the raw physics evidence. Fixed domains use one call; four expected infeasible tasks are rejected before simulation. See [docs/PHASE3.md](docs/PHASE3.md) for configuration, result interpretation and limits. To produce a single dataset, use `python scripts/run_benchmark.py --output /new/benchmark/path`.

Phase 4 adds declared independent uniform component tolerances, matched-call nominal/robust random-search comparison and fresh holdout samples. Use `python scripts/compare_robustness.py --output /new/tolerance-study/path` for one dataset and PNG, or the acceptance command for full tests and independent replay. The `test` extra includes the plotting dependency; `report` installs it separately for reporting without pytest. See [docs/PHASE4.md](docs/PHASE4.md) for the frozen experiment and limitations. Nominal target success and empirical tolerance pass rate are separate measurements.

For the new shared interface after installation:

```text
python -m circuforge design --request examples/design-lowpass.json --output runs/design
python -m circuforge.api --port 8765
```

`runs/design` must not already exist. Choose a new output directory on each run;
an absolute writable path is useful when the working directory is restricted.
Relative paths are supported. The `test` extra already includes FastAPI and
plotting; `api` and `report` let non-test installations select those features.

Install `.[api,test]` for API development/acceptance; `.[api]` provides the service and `.[report]` provides CLI plots without the API/test tools. The service binds only 127.0.0.1, accepts JSON at `/v1/designs` and downloads complete evidence at `/v1/designs/export`. It rejects request-supplied netlists/paths, browser origins, excessive compute and concurrent designs; temporary data is removed after each response. A completed target miss remains `status=target_missed`, HTTP 200 and CLI exit 1. Use examples/design-target-miss.json to reproduce it. This is a local research service, with no deployment or account needed.

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

Use your distribution's package manager. Linux remains documented but unverified.

## Executed platform and simulator selection

Windows 11 / Python 3.12.7 / ngspice-47 were actually verified. Global `--ngspice PATH` before the subcommand overrides CIRCUFORGE_NGSPICE; otherwise PATH is searched. Missing binary means exit 2 and explicit integration-test skips, never simulated success. A discovered executable that fails preflight/simulation fails integration tests.

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

## Historical Phase 1 milestone

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

The local API is available. P6-C1 adds an isolated offline proposal contract with
strict candidate validation and request/token/cost accounting; reproduce its task
checks with `python scripts/accept_proposals.py --output /new/writable/path`.
See [docs/PHASE6.md](docs/PHASE6.md), the separate
[November 20 partial dataset](docs/PHASE6_LOCAL_RESULTS.md), and the
[November 21 renewed comparison](docs/PHASE6_LOCAL_RENEWAL.md). Both resource
windows are now closed; the datasets are retained separately, and the renewal's
incomplete replay still blocks P6-C2/Phase 6 acceptance. A new scientific trial
needs a renewed resource decision. Frontend, circuit-design tool agents, PCB
automation, paid providers and external deployment remain deferred.

## Codex and Freebuff development assistance

The owner separately authorized bounded free-model development assistance.
Codex sends selected packets to Freebuff, checks its advisory output, applies
justified edits, runs automatic tests and reconciles the roadmap without owner
copy/paste. The versioned queue is [planning/agent-workflow.json](planning/agent-workflow.json);
roles, data scope, persistent caps and current execution evidence are in
[docs/AGENT_COLLABORATION.md](docs/AGENT_COLLABORATION.md). It runs during an active
Codex session; no permanent background service or paid SDK is configured.

P5-C5's handoff acceptance passed on 2026-11-22: **338 unit tests**, one actual
Freebuff advisory and a prompt-bound receipt persisted within the declared time
cap. The earlier late-receipt cycle remains separately recorded as blocked.
Both development cycles are closed; this does not renew scientific experiments
or complete the final P7 gate. See the collaboration guide for reproducible audit
commands and the separately authorized verification policy.

## Version control

See [docs/VERSION_CONTROL.md](docs/VERSION_CONTROL.md) for the GitHub setup, owner-requested public visibility, staged credential scan and feature-branch workflow. Generated simulation evidence stays local and is excluded from Git. The initial main commit was pushed with owner approval; later feature branches remain local until separately approved.
