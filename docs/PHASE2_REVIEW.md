# Phase 2 technical review — 2026-11-19

Reviewed source revision fa0d5a4, the objective/cache/budget paths, baseline implementations, the comparison runner and the stored five-case reports. No additional blocking defect was identified in the paths reviewed. Runtime code is unchanged in this review; the last full executed suite remains 154 passed, no skips.

## Accounting and acceptance

- Five cases * three methods produced 15 reports. Four free domains used exactly 64 attempted AC calls per method; the fully fixed domain used one per method. Total: 771. Actual method budgets matched in every case.
- All 771 attempts yielded verified measured responses. Target misses are separate from simulator/measurement failures: all 12 free-domain runs missed the 0.1% tolerance; the three fixed-domain runs passed.
- The shared evaluator rejects invalid bounds/topology before execution, charges unsuccessful attempts, caches exact admissible repeats and separately caps proposals. Reported best designs prioritize passing verified candidates, then minimize the measured log objective.
- SciPy runs serially without polishing. Mid-generation objective calls obey the same cap. Numerical fixed-seed replay is tested; timestamps/latency are not expected to repeat.
- Raw artifacts and reports were previously audited. The single-seed five-case result is engineering evidence, not a population benchmark or a claim of general superiority.

## Independent diagnostic witnesses

To check reachability of the targets, constructed a separate ideal RC reference for each case using R=sqrt(R_min*R_max), C=1/(2*pi*R*target), clamping C to its declared bounds for the fixed rounded-target case. Each candidate then underwent one genuine ngspice AC sweep through the same evaluator/reference/target checks. These are analytic diagnostic constructions, not additional baseline proposals or fitness fallbacks.

| Case | Measured diagnostic cutoff (Hz) | Target error |
|---|---:|---:|
| Low-pass 1000 Hz | 1000.000000000 | <0.000001% |
| High-pass 2300 Hz | 2300.088192902 | 0.003834% |
| Low-pass 50 Hz | 49.998795835 | 0.002408% |
| High-pass 150000 Hz | 150009.426754312 | 0.006285% |
| Fixed rounded target | 1591.487745916 | 0.003874% |

All five diagnostic designs satisfy the original component bounds and 0.1% target tolerance. These five extra calls are stored separately at the visualization workspace's Phase2_Verification/diagnostics-2026-11-19. The original comparison remains unchanged at 771 calls; diagnostic constructions are excluded from its scores, budgets and algorithm comparisons. The reachability checks support interpreting the free-domain misses as finite-budget search outcomes.

Reproducer (Python, installed dependencies and ngspice configured, from project root):

```python
import json, math
from pathlib import Path
from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.optimization.base import Evaluator
from circuforge.simulation.ngspice import Ngspice

adapter = Ngspice()
for case in json.loads(Path("examples/phase2-review-cases.json").read_text()):
    spec = DesignSpec.model_validate({**case["spec"], "max_evaluations": 1})
    r = math.sqrt(spec.resistance_ohm.minimum * spec.resistance_ohm.maximum)
    c = 1 / (2 * math.pi * r * spec.cutoff_hz)
    c = min(spec.capacitance_f.maximum, max(spec.capacitance_f.minimum, c))
    candidate = CircuitCandidate(topology=spec.filter_type, resistance_ohm=r, capacitance_f=c)
    evaluation = Evaluator(spec, adapter).evaluate(candidate)
    assert evaluation.verified and evaluation.target_passed
    print(case["id"], evaluation.measured_cutoff_hz, evaluation.relative_error)
```

The executed version also saved each call's generated netlist, logs, response.csv, evaluation metadata, source commit and environment. No measurements were substituted from the analytic formula.

## P2-H1 owner decision remains open

Review the five cases and misses in docs/PHASE2.md together with these reachability checks. Decide whether the declared ranges, 64-call pilot budget, 0.1% tolerance and the recorded negative results are accepted as the current baselines, or whether additional Phase 2 work is requested. Set any future experiment budget before running it and preserve the existing results. One seed cannot establish success probabilities.

This technical review does not mark P2-H1 done, authorize Phase 3 or authorize a push. Those require the owner's separate decision. Phase 1's earlier acceptance remains unchanged.
