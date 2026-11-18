# Phase 1 electrical review packet

Automated fixture results support P0-H1, P0-H2 and P1-H1 review. They do not record human approval. Each reviewer should record their name/date and comments in docs/DECISIONS.md before changing human task statuses.

## Connectivity and reference

Both sources are ideal voltage sources connected from `in` to ground `0`. Output is measured from `out` to `0`, with infinite load.

```text
Low-pass:                       High-pass:
in ---- R ----+---- out          in ---- C ----+---- out
              |                                |
              C                                R
              |                                |
              0                                0
```

Low-pass: H(jw)=1/(1+jwRC). High-pass: H(jw)=jwRC/(1+jwRC). In both cases fc=1/(2*pi*R*C). Half-power gain is -3.0102999566 dB. Expected phase at cutoff: -45 degrees (low-pass), +45 degrees (high-pass). Source amplitude is normalized out of H.

## Four reference pairs, each tested in both topologies

| R (ohm) | C (F) | Analytic cutoff (Hz) |
|---:|---:|---:|
| 10000 | 1e-6 | 15.9154943092 |
| 3300 | 1e-7 | 482.2877063391 |
| 1000 | 1e-7 | 1591.5494309190 |
| 1000 | 1e-9 | 159154.9430918953 |

Inputs are versioned in examples/phase1-fixtures.json. These cover four distinct cutoff scales, rather than multiple component pairs with the same RC product. Default sweep is 1 Hz–1 MHz, 100 points/decade. Acceptance: relative cutoff error <=0.1%, complex response rtol=2e-5/atol=1e-8, gain at reference cutoff within 0.001 dB, phase within 0.02 degrees. Interpolation uses log frequency. These are numerical fixtures, not manufacturing tolerance or hardware claims.

From project root after installation, with ngspice configured:

```text
python scripts/verify_phase1.py --output /absolute/path/to/new/evidence-directory
```

On Windows supply a Windows absolute output path. In this managed session, Python writes to Documents are blocked; use the authorized visualization workspace for output. The script accepts at most 16 trusted typed reference cases, validates all inputs before simulator execution, and saves each case's spec, raw netlist/logs, complex CSV and CLI report. summary.json records each check, command, source fingerprint and pending human review. It is updated after each case. No simulator fallback is used.

## Human review points

- Confirm ground, output polarity, source/load assumptions and units against the netlists.
- Recalculate the four cutoffs independently and check expected phase signs.
- Decide whether continuous component values and the declared R/C bounds are acceptable for this initial idealized model.
- Inspect measured/analytic differences and raw response data; distinguish simulator success, numerical success and physical verification.
- Record review comments or corrections. The scripts must not mark human tasks done.
