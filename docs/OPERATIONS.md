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

The server binds to `127.0.0.1`. Open `http://127.0.0.1:8765/docs` for the generated
request/response schema or GET `/openapi.json` for machine-readable OpenAPI.
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

## Observed current-checkout verification — 2026-11-22

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
