# Post-MVP ideal-RC numerical follow-up

This is a new bounded local follow-up on `codex/physics-guided-rc`, after the
accepted/published v0.1.0 MVP. Historical 438-test/Phase 2-7 acceptance and raw
datasets remain tied to their original source snapshots. Current v0.2.0 passed
its own `physics-onecall-v1` acceptance; old evidence is not relabeled as current.
No model/provider/development-agent cycle, PCB or new circuit family is involved.

## Method and prespecified comparison

`analytic_rc` uses the known ideal unloaded continuous RC equation
`fc=1/(2*pi*R*C)`. It selects the requested RC product clamped to the achievable
product interval, then a geometric R midpoint within the feasible interval.
This resolves non-unique component splits deterministically. It also handles
tolerance-only feasibility, where exact target cutoff lies just outside the
achievable domain. Typed constraints and ordinary safe templates still apply.

The analytic result is only a proposal. One real ngspice evaluation checks the
complex response, measured cutoff and original target tolerance; failures or
target misses cannot be replaced with a claimed closed-form success. Seed is
explicitly unused by this deterministic method. It stops after one actual call,
even if a caller supplies a larger cap; no padding or hidden retries occur.
The original `compare` command's three classical methods remain unchanged.

`examples/physics-onecall-v1.json` was frozen before the real follow-up run. It
hash-pins the original normalized-distinct benchmark-v2.json, preserving all 20
domains, targets, sweeps, topologies, feasibility labels and 0.1% tolerances.
Only this separate experiment derives `max_evaluations=1`, `timeout_s=5`.
Methods: random, grid, SciPy and analytic_rc; seeds: 7, 42, 2026. Each feasible
trial spends exactly one actual SPICE attempt; infeasible cases spend zero.

There are 240 method trials/run, 192 expected real attempts and 48 expected
infeasible rejections. Two independent runs account for 384 comparison attempts
under a fixed 500-call combined cap. Test fixture calls are a separate population.
The analytic method uses privileged known physics whereas classical methods use
black-box measured objectives. This pilot therefore cannot establish general
optimizer/AI superiority. Grid/analytic seed repetitions are deterministic
controls, not independent population samples. No hardware claim is made.

## Interfaces

```text
python -m circuforge optimize --spec examples/search.json --method analytic_rc --output /new/analytic-run
python -m circuforge design --request examples/design-analytic-rc.json --output /new/analytic-design
```

The shared design request supports the same method in the bounded loopback API.
It accepts no user candidate for optimizer methods, no new netlist/path fields,
and no source/load assumptions beyond the validated ideal models.

## Observed automatic acceptance — 2026-11-22

`scripts/accept_analytic_rc.py` passed with **472 tests, zero failures/errors/skips**
(JUnit suite time 142.587 seconds), unchanged hashes for 100 Python source/script/
test files, and **384 independently raw-audited simulator calls** across two runs.
Each run contains 240 trials: 192 one-call feasible trials and 48 infeasible
rejections without simulation. The combined benchmark cap was 500; test fixtures
are separate from that benchmark budget. First/replay run times were 21.719 and
22.563 seconds. Numerical rows and optimizer traces matched exactly after excluding
elapsed times. No model requests were made.

Counts below describe **one run**, not two independent studies:

| Method | Free-domain passes | Fixed-control passes | Infeasible rejections | Actual calls |
| --- | ---: | ---: | ---: | ---: |
| random | 0/42 | 6/6 | 12 | 48 |
| grid | 0/42 | 6/6 | 12 | 48 |
| scipy | 0/42 | 6/6 | 12 | 48 |
| analytic_rc | 42/42 | 6/6 | 12 | 48 |

All target misses remain misses. These are 14 free-domain and two fixed feasible
cases repeated over three seeds, plus four infeasible cases. Repeated deterministic
controls are not additional independent cases. A one-call budget gives classical
methods no opportunity to refine their first proposal. The result supports this
known-physics proposer for these ideal continuous RC cases; it does not establish
performance for discrete parts, tolerance robustness, nonideal loading, other
topologies or hardware. Historical Phase 3/4/6 results remain unchanged.

The recorded environment was Python 3.12.7, CircuForge 0.2.0, NumPy 2.5.5,
Pydantic 2.14.3 and SciPy 1.18.1. Package source SHA-256:
`68e902d97160e487ca29e1fa49806810d073aef1e749cd13c4b3de6c4c221cf3`.
Original artifacts are outside Git under the existing artifact root at
`Automatic_Acceptance/physics-onecall-2026-11-22/`: `acceptance.json`,
`tests.xml`, command logs, `first/`, `replay/` and `free-domain-passes.png`.
The acceptance JSON includes the exact executed interpreter paths/commands,
environment, manifest hash, simulator version and checked source hashes.

To reproduce in a new writable directory with ngspice configured:

```text
python scripts/accept_analytic_rc.py --output /new/physics-onecall-acceptance --ngspice /path/to/ngspice
```

Install the `test` extra first. A source checkout needs `PYTHONPATH=src`; use the
same environment interpreter throughout. The checker refuses existing output
directories, skipped tests, incomplete evidence, unmatched actual budgets or
changed numerical replay. No manual technical approval substitutes for it.

## Fresh installed interfaces

Built a wheel from the frozen accepted snapshot and installed `[api,test]` into
a new Python 3.12 environment using the recorded numerical constraints. Ran the
installed interpreter with `-I`, outside the checkout, and verified import from
its own `site-packages`. The installed and accepted source fingerprints match;
all 33 package Python files match the checkout, snapshot and wheel byte for byte.
Wheel: 63,230 bytes, SHA-256
`bc572be74a244f14cddb96ac2dda607ce5c5805fc51e9001b0669e012218c295`.

The new example was executed once through installed CLI and twice over actual
loopback HTTP (JSON and ZIP): **three additional real simulator calls**, separate
from the 384-call benchmark. Raw CLI/ZIP responses were independently audited
and the JSON trace matched. All passed with one call each; target 2300 Hz,
measured 2299.913312912917 Hz, relative error 0.000037690037862248005
(approximately 0.00377%). HTTP responses were 200, CLI exit was zero, the server
stopped and temporary request storage was empty.

`installed-walkthrough/acceptance.json`, `installed-provenance.json`,
`installed-install.log`, `installed-freeze.txt` and the byte-identical archived
`installed-verifier.py` retain commands, provenance and results under the same
external acceptance directory. This is current v0.2 install evidence; the older
v0.1 release bundle and its demo remain historical. P7-C4 is complete locally;
the feature branch has not been pushed.
