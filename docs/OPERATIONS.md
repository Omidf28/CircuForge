# Local installation and operation

Use Python 3.11+ and an installed ngspice executable. Windows 11 / Python 3.12.7
were actually exercised; Linux commands are documented but unverified. Install
into a virtual environment and use that environment's interpreter for every
command. Source may be on C while generated evidence uses a separate writable
drive. The core never needs Freebuff, an account, a model download or an API key.

## Minimal Windows workflow

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e '.[test]'
$env:CIRCUFORGE_NGSPICE='C:\path\to\Spice64\bin\ngspice_con.exe'
.\.venv\Scripts\python -m circuforge preflight
.\.venv\Scripts\python -m circuforge design --request examples/design-lowpass.json --output D:\CircuForge-Runs\first-design
```

Choose a new writable output directory. `preflight` reports the actual executable
and version; success does not itself simulate a circuit. The `design` output
contains measured JSON/CSV/PNG, raw call evidence and a checksummed ZIP. Inspect
the result status and target error as well as the process exit code. The example
`design-target-miss.json` deliberately completes with `target_missed` and exit 1;
that negative result is preserved rather than converted to a passing design.

| Situation | Meaning and action |
|---|---|
| ngspice missing | Set `CIRCUFORGE_NGSPICE` to the console executable or add it to PATH; rerun preflight. Skipped integration tests are not acceptance. |
| Configured executable fails | Read the preflight/simulator error and version. An installed-but-failing binary is a failure, not a missing-dependency skip. |
| Output directory exists | Choose a new directory; the program protects prior evidence. |
| Output cannot be created | Use a trusted writable local directory. In this managed workstation, Documents writes may be restricted; external artifact storage is used. Do not disable security settings. |
| Package import fails | Select the installed virtualenv interpreter. An uninstalled source checkout additionally needs `PYTHONPATH=src`; normal installed use does not. |
| Plot/API dependency missing | Install `.[report]` for plots or `.[api]` for HTTP. `.[test]` includes both for verification. |
| Target missed | A completed measurement did not meet the requested tolerance. Inspect the measured error/budget; do not weaken tolerance merely to manufacture success. |
| Cutoff not bracketed | Choose a validated sweep covering the permitted cutoff range. Simulator exit 0 alone does not guarantee a measurable cutoff. |
| pip mirror lacks a package | Retry the install against the official PyPI index with `--index-url https://pypi.org/simple`. |

## HTTP interface

```powershell
.\.venv\Scripts\python -m circuforge.api --port 8765
```

The server binds to `127.0.0.1`. GET `/openapi.json` for its generated
machine-readable request/response schema. Interactive docs routes are disabled.
POST `/v1/designs` accepts the same typed request as the CLI; POST
`/v1/designs/export` returns the complete ZIP. Example from a separate shell:

```powershell
$request=Get-Content -Raw examples/design-lowpass.json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/v1/designs' -ContentType 'application/json' -Body $request
```

This is a loopback research service. Requests cannot select an executable,
filesystem path or arbitrary netlist. Body, sweep, evaluation, timeout and
concurrency guards apply; API temporary artifacts are removed after the response.
Browser-origin requests and remote callers are rejected. A completed target miss
has HTTP 200 and an explicit `target_missed` result: transport success is separate
from numerical success. See [PHASE5.md](PHASE5.md) for limits and error codes.
Stop the foreground service with Ctrl+C when finished.

## Checks and evidence

```powershell
.\.venv\Scripts\python -m pytest -q -ra
.\.venv\Scripts\python scripts/accept_phase5.py --output D:\CircuForge-Runs\fresh-install-check
```

The acceptance checker runs the full suite, builds a source-preserving wheel,
installs pinned tested dependencies in a fresh environment and exercises actual
CLI plus loopback HTTP under `python -I`. It checks raw evidence, ZIP integrity,
JSON agreement and cleanup. It uses real simulator calls and needs ordinary
dependency installation access; it makes no LLM request. Use a new output path.
An `acceptance.json` with `status=blocked` is a blocker, not a successful install.

This check covers supported local interfaces; the separately accepted scientific
replay and final local MVP gate are documented in [PHASE7.md](PHASE7.md).
Historical counts remain dated evidence. Freebuff development
collaboration has separate persisted allowances in
[AGENT_COLLABORATION.md](AGENT_COLLABORATION.md); ordinary CLI/API use never starts it.

## Caller-relative acceptance paths

Phase 2/3/4/5/7 acceptance commands resolve their typed output, manifest and
evidence paths against the directory from which you launch them. The installed
walkthrough likewise resolves `--source` and `--output` before its isolated CLI
changes working directory. Paths containing spaces are supported as single
quoted arguments. The analytic-RC acceptance repair is documented separately in
[ANALYTIC_RC.md](ANALYTIC_RC.md). Existing output directories remain protected;
missing evidence and failed/skipped tests still block acceptance.

For example, from a separate writable directory:

```powershell
& 'C:\path\to\venv\Scripts\python.exe' 'C:\path\to\CircuForge\scripts\accept_phase5.py' --output '.\fresh install' --ngspice 'C:\path\to\Spice64\bin\ngspice_con.exe'
```

Replace the interpreter, script and simulator paths with your installed paths.
The child tests/build/install/walkthrough run from the project, while results
stay in the caller's `fresh install` directory. This command builds a package,
installs dependencies and performs 27 actual interface simulation calls in
addition to test fixtures. It makes no model request. A path repair does not
reaccept historical scientific gates with different source/environment bindings.

## Observed v0.2 caller-path verification — 2026-11-22

P7-C7 passed `local-gate-caller-paths-v1`. Five controlled filesystem/process
regressions reproduced missing JUnit before the repairs; all five and the
existing failure/skip gate protections passed afterward (31 targeted tests in
1.57 seconds). Fixture audits intentionally raise a blocked result. They prove
path handling, not scientific acceptance.

Actual verification ran from the separate external
`Automatic_Acceptance/gate-caller-paths-2026-11-22` directory:

- Full suite: **480 passed in 136.87 seconds** (pytest total), zero skips/errors/
  failures. JUnit suite time was 133.576 seconds.
- `accept_phase5.py --output "fresh install"` built a wheel and installed it in
  a fresh Python 3.12 virtualenv, then passed the real 27-call installed
  CLI/JSON/ZIP walkthrough and independent raw audit.
- The installed interpreter then ran `walkthrough_phase5.py --source examples
  --output "relative walkthrough"` from the same caller directory. Both paths
  were relative; this second actual 27-call walkthrough also passed its raw audit.
- Combined: **54 actual interface calls**, **36 raw CLI/ZIP calls audited** and
  **18 JSON traces matched**. In each walkthrough two examples passed and the
  intentional target miss retained CLI exit 1/HTTP 200/`target_missed`. Both
  servers stopped and request temporary storage was empty.
- All **102 Python source/script/test hashes** remained unchanged during the
  check. All **33 package Python files** match source, wheel and fresh installed
  bytes. No model request was made. Test-fixture simulator calls are separate
  from the 54 installed-interface calls.

Evidence root: `acceptance.json`, `source-before.json`, the archived verification
driver, `fresh install/` (JUnit, build/install logs, source snapshot, wheel and
first walkthrough) and `relative walkthrough/` (second raw exports and logs).
The top-level acceptance records the exact commands/caller and hash map.
The package fingerprint remains
`68e902d97160e487ca29e1fa49806810d073aef1e749cd13c4b3de6c4c221cf3`.
The newly built wheel SHA-256 is
`59fb63fdcb5d2ed36e78281b820c26c00713fa50e890a1da098d445f44be874f`.
Its package bytes match the previous installed source; a rebuilt archive need
not have the same wheel digest. The 60b1ff9 release ZIP was not replaced.

This is script/interface maintenance. Historical Phase 2/3/4/6/7 scientific
acceptance is not rerun or relabeled; the model/Freebuff cycles remain closed.
Runtime behavior, circuit families, numerical policies and historical target
misses remain unchanged. No remote publication or deployment was performed.

## Historical v0.1 checkout verification — 2026-11-22

Executed the existing `scripts/accept_phase5.py` checker with the isolated
Phase1_Verification interpreter, ngspice-47 and a new external output directory:
`Automatic_Acceptance/p7-clean-install-2026-11-22`. It returned exit 0:

- Full suite: **408 passed in 120.41 seconds**, no skips.
- A newly built wheel was installed into a fresh virtualenv with tested pinned
  top-level dependencies. The installed module was imported from that environment's
  `site-packages` under `python -I`, outside source import paths.
- Actual installed CLI/JSON HTTP/ZIP walkthrough: **27 simulator calls**, with
  **18 raw CLI/ZIP calls audited** and **nine JSON traces matched**. Both reference
  examples passed; the intentional target miss stayed `target_missed`/CLI exit 1.
- The walkthrough server stopped and API temporary storage was empty.

`acceptance.json`, `tests.xml`, `tests.log`, `build.log`, `install.log`, constraints,
the source snapshot/wheel and walkthrough artifacts remain in that evidence root.
The package-source fingerprint was
`0e320d6e4188c9b3a52b23a3da4f278d9103043b3c07e58f1159f305724a7796`;
wheel SHA-256 was
`98efc43bb72b7fb80eddea843fbfcf7365e6e382004509c8a7de3b85b7e1a454`.
These are fresh interface/install results, not a repeated Phase 3/4 experiment or
a renewed model trial. Unit/integration fixture calls are separate from the
27-call installed walkthrough. Source and Git remain in the existing C checkout.
