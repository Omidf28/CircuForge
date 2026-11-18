# CircuForge — Wave2Circuit Research Edition

Phase 1 implements typed RC low/high-pass specifications, fixed netlists, real ngspice AC simulation, complex response/cutoff extraction, and bounded measured R/C search. Local CPU only; no accounts required.

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

The starter-authorized first-slice search uses deterministic bisection along log R/C bounds, with measured ngspice objectives, duplicate detection and a hard call budget. Every candidate metric is recorded; raw waveform/log artifacts describe the selected candidate. If a search aborts, failure.json preserves the attempted call count (including the failed attempt), prior measured results, failed candidate/spec, error status and captured logs; no replacement measurements are invented. Random/grid/SciPy comparative baselines remain Phase 2 work.

## Verified milestone

The initial milestone had **63 passing tests**. The latest Phase 1 follow-up has **122 passing tests** in the isolated test environment, including real simulator integration, controlled failure accounting, minimum sample counts and tolerance-aware target feasibility. Fresh package installation was also verified at an earlier milestone. Original saved evidence:

| Case | Measured cutoff | Error | Calls |
|---|---:|---:|---:|
| Low-pass, 1 kohm/100 nF | 1591.487745916 Hz | 0.003876% vs analytic | 1 |
| High-pass, 1 kohm/100 nF | 1591.612597494 Hz | 0.003969% vs analytic | 1 |
| Search, target 2300 Hz | 2300.380616684 Hz | 0.016549% vs target | 12 of 24 |

See `evidence/`, `docs/DEVELOPMENT.md` and `planning/HANDOFF.md`. Human electrical reviews remain open. No physical hardware performance is established by simulation.

The [Phase 1 review packet](docs/PHASE1_REVIEW.md) contains connectivity diagrams, four distinct R/C reference pairs per topology, acceptance limits and review points. Reproduce all eight real fixtures after installing the package:

```text
python scripts/verify_phase1.py --output /absolute/path/to/new/evidence-directory
```

Use an OS-appropriate absolute path. In this managed session, Python directory creation under Documents is blocked; select an output path in the authorized visualization workspace. The script saves raw evidence and a summary with human review explicitly pending. All eight cases passed; maximum measured cutoff error was 0.005891%.

Target feasibility includes the selected relative-error tolerance. A target is rejected when the achievable RC cutoff interval and target*(1±tolerance) are disjoint. This permits rounded targets for fixed components without changing component bounds or claiming exact matching. `examples/fixed-target.json` demonstrates 1 kohm/100 nF with target 1591.5494 Hz and 0.1% tolerance; use it with the simulate command, optionally with --search. Simulation still determines the measured pass/fail result.

Canonical plans: `planning/context.json`, `planning/phase-tasks.json`. Regenerate HTML/Markdown/JSON/CSV using `python planning/render_plan.py`. Browser overrides remain local and require export for sharing. Source: `src/circuforge`; tests: `tests/unit`, `tests/integration`.

No frontend, API, advanced agents, PCB automation, paid service or deployment has been started.

## Version control

See [docs/VERSION_CONTROL.md](docs/VERSION_CONTROL.md) for the private GitHub setup, staged credential scan and feature-branch workflow. Generated simulation evidence stays local and is excluded from Git. Push the initial commit only after explicit owner approval.
