# Reproducible research report

The executable exporter is `scripts/report_research.py`. It reconciles the final
nominal benchmark, component-tolerance study and November 21 local-model trial.
It generates `report.md`, `summary.json` and measured PNG/SVG tolerance plots.
The exported tables retain misses, infeasible rejections and incomplete replay.
This is P7-C2 reporting work; the local MVP release is checked separately by
[PHASE7.md](PHASE7.md). The report snapshot preceded final P7 acceptance, so its
`phase7_release_accepted=false` is historical rather than a current release verdict.

## Export from existing evidence

Install `.[test,report]` as described in README. Supply the existing evidence
directories, not new experiment directories:

```text
python scripts/report_research.py --benchmark /path/to/phase3-v2-2026-11-19 --robustness /path/to/phase4-final-2026-11-19 --local /path/to/local-llama3-renewal-2026-11-21 --output /new/writable/report-directory
```

The exporter runs no provider, simulator, shell command or network request. It
requires the historical accepted policies, their actual JUnit cases, matching
manifest hashes, complete first/replay summaries, method counts and holdout
outcomes. It also runs the existing read-only local-trial auditor against saved
model replies and all raw electrical traces. Missing/failed/inconsistent evidence
blocks export. Existing output directories are preserved and refused.

To include the separately accepted November 22 replay, add
`--replay-supplement /path/to/local-replay-supplement-2026-11-22`. The independent
composite auditor checks its raw data and primary linkage. The original timeout
stays visible; supplemental counts/scores are never pooled into comparisons.

Historical Phase 3/4 raw physics audits remain historical. Checking their stored
summaries and acceptance/test records is not a fresh raw re-audit or evidence of
current cross-platform replay. The report's `summary.json` identifies every
summary/manifest/test input by absolute path and SHA-256. Raw evidence stays local
and must be supplied separately on another machine; it is not bundled or uploaded
by this command. No generated text alone accepts a scientific gate.

## Observed export — 2026-11-22

Actual input directories under the existing external `Automatic_Acceptance` root:

- `phase3-v2-2026-11-19`: final normalized-distinct benchmark only.
- `phase4-final-2026-11-19`: final tolerance experiment only.
- `local-llama3-renewal-2026-11-21`: renewed model trial only.

Current output: `research-report-with-supplement-2026-11-22`. Earlier exports
remain separate. Export made zero model requests or SPICE calls.
The measured chart was visually inspected for correct units, paired labels and
readable values. See the checked-in [report](research/report.md) and its
[source hashes and full-precision summaries](research/summary.json).

The report gives methods, results, failure analysis and threats to validity.
Historical benchmark passes came from fixed-component controls; free-domain
optimization misses remain misses. Robust search's smaller candidate opportunity
count, shared holdout factors and illustrative independent tolerances are explicit.
The original local-model window has complete matched-call data and incomplete
replay, with unknown usage retained separately. A separately authorized supplement
completed the two replay observations and passed the composite engineering gate;
this does not create a model-efficacy or design-success claim.
No general model/optimizer advantage, hardware yield or manufacturing confidence
claim is supported by these small studies.

Engineering acceptance, circuit target success and permission to spend or publish
remain separate. Source/load nonidealities, discrete component policies, active
circuits, PCB and physical hardware remain outside the validated scope.
