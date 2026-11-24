# Local handoff bundle — 2026-11-22

## Current v0.2.0 handoff

P7-C5 packages the accepted `60b1ff9c31cfc3e99d294260b6dbfbbc44b2317a`
snapshot as `Releases/CircuForge-0.2.0-local-60b1ff9-20261122-py312.zip`
under the existing external artifact workspace. Size: **704988 bytes**.
SHA-256: `d2454298cec0709724d480610c02545979557b9c41ae2a551e37b0e6020350c6`.
This is a new local handoff; the historical v0.1 bundle below is unchanged.

The 18-member ZIP contains the 162-file tracked source archive, verified
63,230-byte v0.2 wheel, tested constraints, the analytic-RC request, a PowerShell
quickstart, the actual one-call installed CLI export and acceptance/summary
evidence. All **100 accepted source/script/test hashes** match the archived
commit; all **33 package Python files** match source, wheel and installed bytes.
The source fingerprint and wheel hash are recorded in [ANALYTIC_RC.md](ANALYTIC_RC.md).
Nested archives were CRC-tested and checked for unsafe paths, symlinks,
duplicates, private/generated files and common credential signatures. Every
outer member was compared to the prepared bytes; a separate native PowerShell
SHA-256 check also passed for all 17 members listed in `CHECKSUMS.sha256`.
The checksum file excludes itself. All three PowerShell quickstart blocks parse.

Use Python **3.12**, a separately installed ngspice console executable and a new
writable result directory. Extract the outer ZIP and follow `QUICKSTART.md`:
verify checksums, create a virtualenv, install the local wheel with tested
constraints, set the simulator path and execute `design-analytic-rc.json`.
The acceptance reproduction command uses an absolute output path because its
subprocesses run from the archived project directory. Dependencies still need
installation access; Python/ngspice/model weights are not bundled. This is not
an offline executable. Windows/Python 3.12.7 are the verified platform.

The included acceptance is unchanged historical evidence from that exact source:
472 tests without skips, 384 raw-audited benchmark calls including exact replay,
and three separate installed-interface calls. Packaging performed **zero new
tests, simulations or model requests**. Benchmark summaries and one complete CLI
example are included; the complete raw benchmark datasets remain separate.
Original records retain their workstation paths. The original JUnit XML also
stays separate: its credential-scanner test names intentionally contain dummy
credential signatures. `evidence/test-results-summary.json` retains the original
XML hash and suite counts without those parameter strings; it is explicitly a
summary. Original XML and negative research results were not altered.

Earlier preparation directories are retained separately; the final filename and
hash above identify the checked handoff. Its `-checks.json` companion records
archive counts/hash/provenance. Source/Git remain on C; the existing ancillary
artifact junction is unchanged. No upload, remote release, push or deployment
was performed. Later documentation commits do not change the explicit source
identity of this bundle.

## Historical v0.1.0 handoff

The accepted source snapshot `1ea9bd2` is packaged locally as
`Releases/CircuForge-local-mvp-1ea9bd2-20261122-py312.zip` under the existing external
artifact workspace. That archived application version is 0.1.0. No source or runtime
feature was changed by packaging; no new model, simulator, download, deployment
or remote push was performed.

## Contents and verification

- `CircuForge-source.zip`: 151 Git-tracked source/document/example/test files,
  taken from the exact accepted commit. Git history, environments, downloaded
  tools and generated raw simulator data are excluded.
- `circuforge-0.1.0-py3-none-any.whl`: the wheel already validated by the fresh
  installed CLI/API check; all 31 package Python files match the archived source.
- `demo.gif`: the accepted 75-second annotated replay of real installed CLI
  output; its digest matches the independent demo acceptance.
- `constraints-tested.txt`, `QUICKSTART.md`, original acceptance/JUnit records,
  `release-manifest.json` and `CHECKSUMS.sha256`.

All **93 accepted source/test hashes** were checked against the archived bytes.
The source's package fingerprint matches
`0e320d6e4188c9b3a52b23a3da4f278d9103043b3c07e58f1159f305724a7796`.
The common-credential scanner found zero signatures across all 151 archived
files; forbidden local/private paths, symlinks and duplicate/unsafe ZIP entries
were rejected. The outer ZIP was CRC-tested and every enclosed file compared
byte-for-byte to the prepared release folder.

The final bundle is **791661 bytes**. SHA-256:
`538f18e0a93b8918fc7a0edbc071b026d54f2933e4dec97e9edb0b35fbf0807a`.
Its manifest retains the full source commit and individual member/source hashes.
The original 438-test acceptance remains historical evidence, not a newly run
test suite during packaging. No numeric outcomes or prior evidence were changed.

## Installation

Extract the outer ZIP and follow `QUICKSTART.md`. It creates a virtualenv,
installs the wheel with the tested constraints, extracts the source/examples and
runs preflight followed by a measured design. Use **Python 3.12** with the supplied
constraints and a separately installed ngspice console executable. Installed
NumPy/SciPy metadata confirms these exact numerical pins require Python >=3.12;
the source project's >=3.11 declaration permits different compatible dependency
resolution, not use of these pins on Python 3.11. Dependencies are installed by
pip; this is a Python handoff bundle, not a self-contained offline executable.
Windows 11/Python 3.12.7 were verified; Linux remains documented but unverified.

The first packaging draft was retained separately. Its generic Python minimum
was corrected in the final quickstart/manifest after inspecting installed
dependency metadata; accepted source/wheel bytes remain unchanged. Final checksums
and all outer ZIP members were verified again.

Raw research datasets and model weights are not included. Some unchanged original
acceptance records refer to local evidence paths; repeating every research audit
requires those separate inputs. Core CLI/API use needs no account, key or model.
The source README and docs/OPERATIONS.md describe simulator installation, statuses
and resource limits. Closed model/development-agent packets remain closed.

This handoff is local only. Publication, a new scientific-model allowance or
optional feature expansion is not implied. Repository documentation added after
packaging does not change the bundle's explicit `1ea9bd2` source identity.
