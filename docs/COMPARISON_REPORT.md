# Local baseline comparison report

After running `compare`, turn its saved evidence into one standalone HTML file:

```text
python -m circuforge compare --spec examples/fixed-target.json --seed 42 --output comparison-run
python -m circuforge comparison-report --comparison comparison-run --output comparison.html
```

Open `comparison.html` in a browser and expand each method to inspect its
candidates. To inspect a previous run, use only the second command. The input
directory must contain `comparison.json`, the Random/Grid/SciPy method
reports, and their raw evaluation artifacts. Run the report command even if
`compare` returned 1 with complete reports but no verified best.

The report shows actual simulator calls against the configured cap, best
measured cutoff, target error, and failure reasons for unverified candidates.
Error bars share a scale across the three methods. Unequal actual call counts
are flagged. A verified candidate can still miss the requested tolerance.
Verification refers to the raw ngspice evidence and the ideal RC reference.

The report uses the existing raw evidence auditor for every candidate marked
verified. Missing or contradictory evidence prevents creation of the page.
Unverified candidates are shown with their recorded reasons and no ranked error.
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
