# Local handoff bundles

## CircuForge 0.4.0 Windows handoff — 2026-11-25

The artifact workspace contains
`Releases/CircuForge-0.4.0-local-a1f170b-py312.zip` (555,886 bytes).
Its SHA-256 digest is `f15405559ca3ecb8e749a9c061c2b564bf8a654620478c855fafc145a26af114`.
The ZIP contains the wheel, source from `a1f170beffcc1781d07006f9cfdb075f19b7c8e5`,
tested constraints, example reports, checksums and `QUICKSTART.md`.
Use Python 3.12 and a separately installed ngspice executable. The desktop
also requires Tcl/Tk. Pip installs the Python dependencies.

This release adds `compare --html` and checks that failure diagnostics
match the per-call evidence before rendering. The original offline
`comparison-report` command still accepts saved comparisons.

The source suite passed 539 tests with no skips. A fresh installed
CLI/loopback API walkthrough completed 27 real calls. On the same wheel,
three installed comparisons used 78 real calls. The fixed case passed,
the free case retained all target misses and 29 unverified attempts, and
the unmeasurable case retained exit code 1. Offline rendering reproduced
the same three pages without running the simulator. All 38 runtime files
matched, and an independent build from the same source and timestamp
produced the identical wheel.

The verification artifacts are under `Releases/v040` in the local workspace.
The first independent build hit a Windows junction error and succeeded
when rebuilt from the resolved path. The final release binary uses the
verified wheel digest `a4fec9d66f48dd221aced0adc4ee679cbfad19ce15640ad3551a1f4074e91546`.

The final ZIP was unpacked and installed into a separate Windows environment.
All eight listed checksums matched. The quickstart comparison performed
three real calls and reproduced the example HTML. A withdrawn desktop
check performed one additional raw-audited call and passed.

## CircuForge 0.4.0rc1 local preview

The local artifact workspace contains
`Releases/CircuForge-0.4.0rc1-local-9bcc9d9-py312.zip` (550,529 bytes).
Its SHA-256 digest is `6b6a6333122a795477fb9f0225f13d66e8c71d1777c3828ef4982a2a0cabf6a6`.
Extract it and follow `QUICKSTART.md` for Windows with Python 3.12 and a
separately installed ngspice console executable. The desktop also needs
Tcl/Tk. Pip installs the Python dependencies using the included constraints.

The preview combines the audited HTML baseline comparison with the fix
that identifies diagnostic files after an unsuccessful desktop simulation.
The ZIP contains the wheel, the 180-file tracked source archive from
`9bcc9d90299ac9017b33df3657889f4dc77d20be`, example HTML reports,
checksums and a machine-readable verification summary. All 38 runtime
Python files matched across source, wheel and the candidate installation.

The source suite passed 531 tests with no skips. The installed walkthrough
made 27 real CLI/HTTP calls (18 raw audited and nine JSON traces matched).
The withdrawn desktop check made three real calls, and the separate
failure-and-retry test passed with one real retry. Two installed baseline
comparisons made six real calls split between measured passes and
unmeasurable candidates. One archived comparison re-audited 192 historical
calls and reproduced the same HTML bytes. Rendering made zero new calls.

Evidence is under `Releases/rc040` in the local artifact workspace.
The first installation attempt timed out downloading a dependency. Its
record remains in `accept/acceptance.json`. Installation from a local
wheelhouse and the independently rerun CLI/HTTP audit passed, with the
original test and wheel evidence retained in `recovered-cli-http.json`.

The final ZIP was extracted into a separate folder with a space in its path.
All eight member checksums matched, a fresh `[gui]` install passed
`pip check`, and the quickstart comparison with three additional real
calls reproduced the bundled example HTML byte for byte. A withdrawn desktop
test from that same installation made one additional raw-audited call.
The final archive digest and all 38 installed runtime files matched again.
Evidence is in `final-zip-smoke.json`.

## Historical v0.2.0 handoff

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
