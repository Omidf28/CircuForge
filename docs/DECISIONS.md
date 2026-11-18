# Decisions and open questions — 2026-11-18

## Confirmed by project owner

- Main project: CircuForge / Wave2Circuit Research Edition (product + research).
- Differentiator: inverse circuit synthesis, real SPICE verification, numerical optimization; not generic educational circuit analysis.
- Develop with Codex, two students, goal: internship-ready engineering portfolio.
- Start with simple passive circuits; postpone large parts libraries, PCB optimization and fine-tuning.
- Phase 1 local implementation is approved as of this package request.

## Provisional engineering decisions (verify during P0)

- Python local-first core; ngspice + SciPy; bounded AC low-pass then high-pass.
- Ideal 0-ohm source and unloaded RC response for first analytic comparison.
- No production hosting, API/model spending or GPU initially.
- 12-week target is approximate. Proposed partner ownership: AI/optimizer/app vs simulation/components/circuit fixtures.

## Open items for team

- Exact operating system and path to installed ngspice on each workstation.
- R/C ranges, allowed value series, target frequencies, sweep density/interpolation tolerance.
- How to handle finite loads and source impedances beyond initial ideal assumptions.
- Permissions/licenses for any imported SPICE models and datasheets.
- Budget approval and model selection before first LLM experiments.
- Research benchmark case definitions, reviewer and experimental error thresholds.

## Implemented defaults — 2026-11-18 (human review pending)

- Verified Windows 11, Python 3.12.7 and ngspice-47 console. Linux remains unverified.
- Ideal zero-ohm source, infinite load, explicitly normalized AC amplitude.
- Default R: 10 ohm–1 Mohm; C: 1 pF–1 mF. Continuous values only; E-series policies are rejected.
- Sweep: 1 Hz–1 MHz, 100 points/decade; half-power cutoff interpolation in log-frequency/dB; 0.1% acceptance.
- Max 1000 evaluations, 30 seconds/call, 20,000 sweep points, 8 MiB combined output. Default 32 evaluations and 10 seconds/call. These local guardrails do not impose a kernel memory quota.
- First-slice search: deterministic log-bounds bisection driven by measured ngspice cutoff. Phase 2 random/grid/SciPy comparisons remain deferred.
