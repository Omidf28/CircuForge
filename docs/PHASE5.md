# Phase 5 — shared CLI and loopback API

## Implemented scope

The typed `DesignRequest`/`DesignResult` contract and `application.run_design` are shared by the new `design` CLI command and local FastAPI endpoints. Requests specify validated electrical values and an allowlisted method (`simulate`, `random`, `grid`, `scipy`). Direct simulation requires an explicit candidate; optimizer requests cannot inject one. Source/load assumptions, physical/component constraints and safe ngspice templates remain the verified core. Existing commands and experiments are preserved.

The original CLI/API gate used PNG response plots. The later optional P5-C3 prototype adds a [local HTML baseline comparison](COMPARISON_REPORT.md) for saved reports. P5-H1's technical walkthrough was replaced by the automated P5-C4 gate.

## Install and run

From the extracted source repository with Python 3.11+ and ngspice available:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[api,test]"
$env:CIRCUFORGE_NGSPICE = 'C:\path\to\Spice64\bin\ngspice_con.exe'
.\.venv\Scripts\python -m circuforge preflight
.\.venv\Scripts\python -m circuforge design --request examples/design-lowpass.json --output runs/design-lowpass
.\.venv\Scripts\python -m circuforge design --request examples/design-optimization.json --output runs/design-optimization
.\.venv\Scripts\python -m circuforge design --request examples/design-target-miss.json --output runs/design-target-miss
```

Use new output directories. Linux uses `.venv/bin/python` and a locally installed ngspice; Linux execution remains unverified here. The low-pass example is a direct 1 kohm/100 nF reference simulation. The high-pass grid control has a known reachable corner solution; it is an export/optimizer smoke case, not a new performance benchmark. The third example deliberately retains a grid target miss at a four-call budget. CLI exit codes: 0 passed, 1 target missed, 2 input/dependency/simulation/artifact failure. `status` carries the same distinction in the report.

Each successful measured run exports `request.json`, typed `report.json` with full call history and selected waveform, `response.csv`, `response.png`, chosen netlist/stdout/stderr, `engine/` per-call raw evidence, `manifest.json` and `bundle.zip`. The manifest checksums every included file except itself; the archive contains that manifest and all recorded artifacts. Partial simulation failures retain their call/failure records and ZIP, without inventing a best candidate or response chart. Export errors return an error and may leave the user's new CLI directory for diagnosis; existing directories are never overwritten.

Start the loopback-only service in a terminal:

```powershell
.\.venv\Scripts\python -m circuforge.api --port 8765
# Equivalent installed entry point: circuforge-api --port 8765
```

From another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
$body = Get-Content examples/design-lowpass.json -Raw
Invoke-RestMethod http://127.0.0.1:8765/v1/designs -Method Post -ContentType application/json -Body $body
Invoke-WebRequest http://127.0.0.1:8765/v1/designs/export -Method Post -ContentType application/json -Body $body -OutFile design.zip
```

`GET /health` reports service limits and `simulator=not_checked`; it does not claim a simulation occurred. CLI preflight verifies ngspice. `GET /openapi.json` exposes the machine-readable request/response contract; browser documentation pages/CDNs are disabled. JSON results include aligned complex AC waveform, gain/phase, constraints/reference/target flags, actual call counts and source/environment provenance. The ZIP endpoint executes a fresh design and downloads all artifacts; there are no persistent artifact URLs or background job store.

Valid computations return HTTP 200 for both `passed` and `target_missed`; inspect `status`. A measured simulation failure returns 502 with a typed result on the JSON endpoint and an evidence ZIP on the export endpoint. The ZIP's `X-CircuForge-Status` header repeats the design status. Missing simulator returns 503; invalid input or API compute limits 422; oversized body 413; unsupported media type 415; rejected remote/browser caller 403; invalid host 400; concurrent design 429; body timeout 408; artifact/dependency failure 500. Temporary artifacts are removed after materializing each JSON/ZIP response, including error paths. To retain raw failure evidence locally, use the CLI or save the error ZIP.

## Compute and request boundaries

Shared design export allows <=32 configured calls, <=5 seconds/call, <=60 seconds aggregate configured simulator time and <=2000 AC samples. The API further restricts requests to <=8 calls, <=2 seconds/call and <=1001 samples. Each request body is limited to 16 KiB before JSON parsing, including streamed bodies, with a five-second body-read deadline. One design can run per process; a second is rejected rather than queued. This bounds simulator work; image rendering/export adds small local overhead and is not an OS memory/CPU quota.

The bundled server binds only 127.0.0.1 with one worker and proxy headers disabled. Host headers are restricted to loopback names/addresses; remote clients and all browser Origin headers are rejected. It is a local research API without authentication, not a public or multi-tenant server. No request can choose a netlist, executable, include file, filesystem output path or temporary directory. Trusted executable/temporary-root overrides are server startup settings only. The API uses an isolated TemporaryDirectory per job, preserves simulator guards and imposes archive count/size limits. ZIP extraction in acceptance rejects traversal, absolute/drive paths, symlinks, duplicates and oversize entries before writing.

## Automatic acceptance and trust boundary

```powershell
$env:PYTHONPATH = 'src'
python scripts/accept_phase5.py --output /new/writable/absolute/path
```

In this managed Windows session the command needs tool permission for local sockets, including asyncio's internal socketpair; without it, Windows blocks event-loop creation before requests run. Evidence/output must use the authorized visualization workspace. This environment limitation is distinct from service/simulator failure. The earlier stuck sandbox test processes were stopped; with loopback enabled the same tests passed.

The gate runs the full source suite without skips, builds a source-byte-preserving wheel, creates a fresh virtual environment with no shared site-packages, installs the wheel/API/test dependencies pinned to tested top-level versions from official PyPI, then removes source import paths and invokes the installed package with Python `-I`. Build/install/test commands and logs, constraints, wheel hash and package location are retained. Installation requires access to dependencies or their pip cache; absence blocks the gate rather than fabricating a clean install.

The installed walkthrough starts an actual loopback Uvicorn server, exercises three examples through CLI, JSON HTTP and downloaded ZIP, tests rejection guards, checks temporary cleanup and stops the server. Independent auditing recomputes raw physics/cutoffs/objectives and selection for CLI/ZIP traces, checks CSV/JSON/chart/archive integrity and compares numerical results across all interfaces, excluding elapsed times. There are 27 actual calls in this walkthrough: 18 retain fully audited raw CLI/ZIP traces, and the nine JSON-interface calls are checked against those complete numerical traces and selected complex waveforms. Do not relabel all 27 as independently archived raw calls. Unit/integration fixture calls are separate.

Policy `phase5-local-interface-v1` accepts observed engineering/install/interface checks, preserving the deliberate target miss. It does not assert human usability review, cross-platform compatibility, hardware performance or public-service readiness. The configured local simulator and trusted source remain the measurement trust boundary.

Implementation references: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [Starlette middleware](https://starlette.dev/middleware/) and [HTTPX ASGI transport](https://www.python-httpx.org/advanced/transports/#asgi-transport). Tests use HTTPX ASGITransport directly; the installed walkthrough additionally uses real HTTP sockets.

## Observed acceptance

Observed on 2026-11-19: **phase5-local-interface-v1 passed with 279 tests, no skips**, a fresh wheel/venv install and isolated installed CLI plus actual loopback HTTP. Windows 11 / Python 3.12.7 / ngspice-47; NumPy 2.5.5, Pydantic 2.14.3, SciPy 1.18.1, Matplotlib 3.11.2, FastAPI 0.165.0, Uvicorn 0.54.0 and HTTPX 0.28.1. Starlette 1.10.0 is recorded in install.log.

| Example | CLI status/exit | HTTP JSON/ZIP | Calls per interface | Measured cutoff | Target error |
|---|---|---|---:|---:|---:|
| design-lowpass | passed / 0 | 200 / 200 | 1 | 1591.487745916 Hz | 0.00387384% |
| design-optimization | passed / 0 | 200 / 200 | 4 | 1591.612597494 Hz | 0.00397082% |
| design-target-miss | target_missed / 1 | 200 / 200 | 4 | 1591.612597494 Hz | 30.7995% |

The walkthrough executed **27 real calls** total across CLI/JSON/ZIP. **18 complete raw CLI/ZIP calls were independently audited**, and the other **nine JSON-interface traces and selected complex waveforms matched**. These counts exclude test fixtures. The two passing examples are reference/smoke controls; the deliberately missed four-call grid case remains target_missed in every interface. The local server stopped and its temporary storage was empty after every request and at completion. The response plot was visually inspected for readable axes/units and correct measured/target markers.

Evidence directory:

```text
C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Automatic_Acceptance/phase5-2026-11-19
```

Fresh installed interpreter: `C:/Users/Home/.codex/visualizations/2026/11/18/01a1ee7a-3b9d-7eb0-9f38-c053c726b534/Automatic_Acceptance/phase5-2026-11-19/installed/Scripts/python.exe`. It can run the documented commands without PYTHONPATH when invoked from the source repository with the example files. No service is left running automatically.

Package source SHA-256: `aade37bb9e2d900bdd360e8012cb08831aebf7092cf0ff9b5a44c778440873d8`. Built wheel SHA-256: `511e26ebaba311a8ae9178d86b6c2bb2ca8712ac76f1cb3f2449ebc5028365c0`. acceptance.json retains exact commands, versions, source fingerprint and per-interface outcomes; tests.xml/tests.log, build.log, venv.log, install.log, constraints.txt, the wheel, fresh environment and walkthrough/ preserve reproducibility evidence. The walkthrough records installed module/prefix and Python -I invocations, making source-checkout imports a gate failure.

Earlier focused checks passed (25 initial boundary tests; seven initial measured-export checks; then 43 extended tests) before the full 279-test run. Sandbox asyncio initialization was diagnosed with a traceback before rerunning with local socket permission; those stalled processes were stopped and are not counted as passing runs. No source or numerical threshold was changed to manufacture acceptance. No frontend, external deployment, remote push, paid/provider experiment or advanced agent was started.
