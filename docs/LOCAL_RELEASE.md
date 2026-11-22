# Local handoff bundle — 2026-11-22

The accepted source snapshot `1ea9bd2` is packaged locally as
`Releases/CircuForge-local-mvp-1ea9bd2-20261122-py312.zip` under the existing external
artifact workspace. The application version remains 0.1.0. No source or runtime
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
