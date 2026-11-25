# Local baseline comparison report

To run a new comparison and save the audited HTML in the same directory:

```text
python -m circuforge compare --spec examples/fixed-target.json --seed 42 --output comparison-run --html
```

Open `comparison-run/comparison.html` in a browser. The CLI JSON includes
the file path in `report_html` for this option. Cases with no verified best
still produce the report if their diagnostics are complete. The comparison
keeps exit code 1 in that case. A report error returns 2 and leaves the saved
comparison evidence available for inspection and offline re-rendering.

To turn existing evidence into a new standalone HTML file:

```text
python -m circuforge comparison-report --comparison comparison-run --output comparison.html
```

Expand each method to inspect its candidates. The input directory must
contain `comparison.json`, the Random/Grid/SciPy method reports, and their
raw evaluation artifacts. The offline command returns 0 when it writes a
report, even if the original comparison returned 1.

The report shows actual simulator calls against the configured cap, best
measured cutoff, target error, and failure reasons for unverified candidates.
Error bars share a scale across the three methods. Unequal actual call counts
are flagged. A verified candidate can still miss the requested tolerance.
Verification refers to the raw ngspice evidence and the ideal RC reference.

The report uses the existing raw evidence auditor for every candidate marked
verified. Missing or contradictory evidence prevents creation of the page.
For failed simulator attempts, the report checks that the recorded diagnostic
matches the per-call record, simulator metadata and generated netlist. The
saved logs must be present. If ngspice returned a response but measurement or
reference verification failed, the saved response CSV must also be present.
Unverified attempts retain the recorded reason and have no ranked error.
These checks establish consistency within the saved export. They do not
independently prove why the simulator stopped.
The renderer reads at most 16 MiB per method report, 8 MiB per raw evidence
file, and 192 MiB across the raw audit. Existing output files are preserved.
The HTML has no scripts, external assets, or server dependency. Generation
does not launch a browser or call ngspice.

## Verification

Source commit `9fa34c45740dcc946c817860d21eaa301e3847f7` passed the full
suite with **531 tests and zero skips**. The regression cases cover preserved
inputs, no-overwrite output, rejected missing/altered evidence, escaped failure
text, and the unequal-call warning. Outside the checkout, the installed
wheel matched all 38 archived Python files.

The source CLI and installed CLI rendered byte-identical pages from the
five saved Phase 2 comparisons. The existing **771 genuine calls** were audited,
with the fixed-domain pass and all four free-domain misses preserved. Two
fresh installed `compare` commands used **six additional genuine calls**:
three passing measurements and three deliberately unmeasurable candidates.
Rendering both reports required zero additional calls. The reproduction
outputs, wheel digest and JUnit report are under
`Automatic_Acceptance/comparison-report-2026-11-24` in the local artifact
workspace.

## Failure evidence verification (2026-11-25)

On source commit `08b9f56`, four regressions reproduced incorrect report
creation before the fix. They covered a changed failure reason, inconsistent
return code, altered netlist and missing log. The final focused suite passed
15 tests and the full suite passed 536 without skips. The fresh installed
CLI/loopback API walkthrough passed 27 actual simulator calls.

The installed report command reproduced six HTML files byte for byte. These
cover 771 verified calls from the five historical comparisons and three
unmeasurable calls exported by v0.3.1. The same report also worked through a
path containing Persian text. A changed reason and an oversized failure log
were both rejected on copies of the old export. A separate short-budget
comparison produced three real ngspice timeouts and all three were shown as
unverified. Reporting itself ran zero simulator calls. The original legacy
files remained unchanged.

Evidence is in `Automatic_Acceptance/comparison-failure-2026-11-25` in the
artifact workspace, including `full-accept/acceptance.json` and
`installed-replay/verification.json`.

## Integrated export verification (2026-11-25)

Source commit `4baa9be` passed 20 focused tests and 539 default tests
without skips. The focused tests counted actual simulation attempts with and
without `--html`, checked exit code 1 with diagnostics, and preserved saved
raw output on an HTML write error.
The separate fresh CLI/loopback API walkthrough passed 27 real calls.

A fresh core-only Windows installation ran three real comparisons through
`compare --html`. The fixed case passed in three calls. All three methods
returned verified measurements but missed the target in the 72-call free
case. The three-call unmeasurable case retained exit code 1 and generated an
unverified report. Offline rendering reproduced all three pages byte for
byte and made zero new calls. The test used relative paths containing
Persian text or spaces, verified no overwrite, and matched all 38 installed
Python files to the wheel and source. Matplotlib, FastAPI and Tk were absent
from the core installation.

Evidence is in `Automatic_Acceptance/compare-html-2026-11-25` in the
artifact workspace, including `core-proof/verification.json`.
