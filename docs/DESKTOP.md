# Simple local desktop — v0.3.0

The owner selected this bounded local graphical interface on 2026-11-22.
It calls the same measured design engine as the CLI. Tkinter provides the window
and existing Matplotlib provides the chart; there is no web server or model in
this flow. Full optimizer-comparison dashboard P5-C3 remains deferred.

## Install and open

Use an environment with Python Tk support and the optional `gui` extra. The
verified workstation has Windows 11, Python 3.12.7 and Tcl/Tk 8.6. Linux/macOS
desktop behavior has not been verified. The ordinary CLI/API never imports Tk.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e '.[gui]'
$env:CIRCUFORGE_NGSPICE='C:\path\to\Spice64\bin\ngspice_con.exe'
.\.venv\Scripts\python -m circuforge.desktop
```

The installed `circuforge-desktop` command opens the same app. Choose a results
folder with Browse, or supply `--output-root C:\your\results`. Supply `--ngspice`
to override the environment/PATH console executable. The default results root
is `CircuForge-Runs` in your home directory. No files are created until you run
a valid design and simulator preflight succeeds. Dependencies/ngspice must be
installed separately; this is a Python desktop app, not a bundled executable.

If Tk is absent or the display cannot be opened, the GUI exits with a dependency/
display error and status 2. The CLI remains usable. Matplotlib is optional for
core imports; installing `[gui]` supplies the plotting dependency.

## Design and inspect

1. Choose low-pass or high-pass. Enter cutoff in **Hz** and allowed error in
   **percent**. `0.1` means 0.1%, matching the original 0.001 relative tolerance.
2. In **Analytic design**, enter R bounds in **ohm** and C bounds in **nF**.
   The existing continuous ideal-RC proposer generates one candidate and one
   actual ngspice sweep measures it. Infeasible or invalid bounds are rejected.
3. In **Simulate R/C**, enter the actual resistor in ohm and capacitor in nF.
   The fixed candidate is measured even if it misses the target. Domain bounds
   are the existing physical R/C limits, not a claimed optimizer search domain.
4. Run measured design. Inputs are disabled while the background job runs; the
   window remains responsive. Each run allows one actual simulator attempt,
   <=2 seconds for that simulation and <=1001 frequency samples. Preflight and
   file/plot export take additional time. No automatic retries occur.
5. Inspect measured cutoff, relative target error, call count, circuit values
   and measured gain/phase. The chart marks target and measured cutoff.
   **PASSED**, **TARGET MISSED** and **SIMULATION FAILED** are distinct outcomes.
   A failed preflight/export is shown as a run error, not a successful circuit.
6. Open results folder to inspect the ordinary raw/exported evidence. Every run
   gets a new unique subdirectory; prior results are not overwritten.

Editing inputs marks the retained chart/metrics as the last saved result until
another run completes. Starting a new run clears the old chart/metrics. Invalid
input never starts a job; an existing chart remains explicitly labeled as old.
Closing during a job waits for the current bounded simulation/export to finish.

## Physics and scope

The model is ideal first-order RC with zero-ohm source, infinite load and
continuous ideal components. The diagram is the supported topology, not a PCB
or schematic editor. Both analytic and manual modes still use the existing
allowlisted template, complex-response parser, independent RC reference check,
target tolerance and raw evidence exports.

The GUI chooses a focused sweep around the target (and the known RC reference
for manual components), spanning roughly two decades each side and limited to
the existing frequency/sample bounds. A target may land exactly on an AC sample,
so extremely small displayed error is a grid-aligned numerical result, not a
general accuracy claim. This is separate from historical benchmark sweeps and
does not change or pool their outcomes. No hardware performance is claimed.

## Verification

Targeted tests cover conversion, bad/nonfinite/infeasible inputs, background
single-job enforcement, failure delivery, optional Tk imports and actual
low/high-pass/missed-target raw audits. The real window has also been operated
with Windows Computer Use: two analytic passes, one measured manual target miss,
busy and stale-result states, invalid input and normal close were observed.
Screenshots are actual app captures, not mockups. This is agent verification;
no completed owner UX review is claimed.

P5-C6 passed `phase5-simple-desktop-v1` on 2026-11-22:

- Current full suite: **516 passed in 126.36 seconds** (JUnit suite 126.335s),
  zero failures/errors/skips; all **111 Python source/script/test hashes** match.
- Fresh isolated installation passed its 509-test suite and real CLI/HTTP
  walkthrough: **27 simulator calls**, 18 raw CLI/ZIP audited, nine JSON matched.
  Later changes affected only the acceptance checker and its tests. All **37
  runtime package files** still match source, wheel and installed bytes.
- Actual button-driven GUI runs: **four simulator calls**, independently audited
  from raw responses/exports. Three used source and one used the fresh installed
  interpreter with `-I`. Invalid input created no fourth source run.

| Origin | Filter / mode | Measured cutoff | Status | Calls |
| --- | --- | ---: | --- | ---: |
| Source window | Low-pass / analytic | 2300 Hz | passed | 1 |
| Source window | High-pass / analytic | 2300 Hz | passed | 1 |
| Source window | High-pass / 1000 Ω, 100 nF | 1591.654910 Hz | target_missed | 1 |
| Installed window | Low-pass / analytic | 2300 Hz | passed | 1 |

The manual case retained its approximately 30.7976% target error. The original
CLI/API deliberate miss also remained a miss. Combined operational evidence is
**31 actual calls: 22 raw audited and nine JSON matched**; test-fixture calls
are separate. No model request or historical benchmark rerun is implied.

Evidence is external under `Automatic_Acceptance/desktop-ui-2026-11-22`:
`fresh-install/`, `current-checker-tests-v3/`, `visible-runs/`,
`installed-visible-runs/`, native `screenshots/`, and the accepted
**`final-acceptance-v3/acceptance.json`**. The source fingerprint is
`7c983eed84135d5b4a64212dda568cfe4d5c84d7607013cee1280e11646588ae`;
wheel SHA-256 is
`41f32d78ae95f2a5b0b1e961f565a1237ec6f2dbae94de6061344874313de8a2`.
Final record, fresh-install record and actual wheel hashes were independently
compared. The metadata checker never launches a model or simulator.

The initial capture check blocked because native JPEG bytes had been named
`.png`. Original drafts were retained; `.jpg` copies are byte-identical, with no
image editing/transcoding. A second draft's wheel-hash field incorrectly held
an image digest; it is explicitly superseded in `v2-provenance-defect.json` and
must not be used as acceptance. Regression tests cover native image formats,
corrupt/mislabeled captures and wheel provenance. Only final v3 is accepted.

To repeat the read-only final audit with an equivalent fresh evidence packet:

```text
python scripts/accept_desktop.py --interface-evidence /evidence/fresh-install --tests-evidence /evidence/current-checker-tests-v3 --source-hashes /evidence/current-checker-tests-v3/source-before.json --gui-evidence /evidence --installed-gui /evidence/installed-visible-runs --output /new/desktop-acceptance
```

`accept_phase5.py` creates the fresh installation/interface evidence; the actual
desktop supplies GUI runs and native window captures. The checker independently
audits numerical exports, package bytes and current tests, refusing skipped,
stale or incomplete evidence. Screenshot encoding/dimensions/integrity/hashes
are checked; visual semantics were inspected by the agent through Windows
Computer Use, not claimed as automatic pixel recognition or owner UX approval.
Original v0.1/v0.2 scientific evidence and release bundles remain source-bound.
