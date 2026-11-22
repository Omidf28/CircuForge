# Version control

## Current local milestone — 2026-11-22

The validated local research MVP is complete on feature branches through
`codex/p7-captured-demo`; evidence and automatic acceptance are documented in
docs/PHASE7.md. These changes are committed locally. No later feature branch has
been pushed, and no remote history has been overwritten. Public visibility alone
did not publish this development history; only the initial main commit was online
at the last authorized remote operation. A new push retains its separate owner
approval requirement.

## Current visibility — 2026-11-21

The owner explicitly requested «repo رو پابلیک کن». Changed
Omidf28/CircuForge from private to public with GitHub CLI and independently read
back `private=false`, `visibility=public`. At that point only remote main existed,
at `20ef58fe266cee5837ed27f24ce6b60d60951c78`; its one reachable commit and 46 blobs
were checked with the project's common-credential scanner, with zero findings.
GitHub reported zero Actions runs. This is a common-signature check, not a claim
to detect every conceivable secret.

Direct CLI API access initially timed out. The command succeeded using the
already-enabled Windows loopback proxy only for that shell process; no system
proxy/security settings changed. No new commit/branch was pushed and no remote
history was overwritten. The following private-repository setup notes are
historical; future visibility changes still require an explicit owner request.

Public repository: https://github.com/Omidf28/CircuForge. Later local phases are
not published by changing visibility alone; feature pushes retain their separate
authorization requirements.

The standalone CircuForge folder is the Git repository. It is separate from the unrelated VideoPlayer project. The initial verified implementation is committed on main. Development after the initial commit uses branches named codex/<task-id>-<description>.

Active checkout: `C:/Users/Home/Documents/ChatGPT/Implement CircuForge`. It was populated from the complete local history; the previous visualization-workspace copy is retained with ignored simulator tools/evidence. Current Phase 1 follow-up branch: `codex/p1-search-failure-evidence`. New local commits on that branch are not covered by the earlier initial-push approval and remain unpushed.

Local setup evidence (2026-11-18): initial commit `20ef58f` is on `main`; follow-up Phase 1 commit `a20044f` is on `codex/p1-pipeline-hardening`. The initial staged scan checked 46 files with no common credential signatures. The hook ran successfully during both commits.

GitHub CLI authentication is confirmed as `Omidf28`. Created and connected [Omidf28/CircuForge](https://github.com/Omidf28/CircuForge); GitHub reports `isPrivate: true`. `origin` uses the HTTPS URL without credentials. A local credential-helper setting invokes GitHub CLI; no token is stored in the repository or remote URL. The remote was verified empty before the initial push.

The owner explicitly approved pushing initial commit `20ef58f`. Executed `git push -u origin main` successfully on 2026-11-18. Remote `refs/heads/main` is `20ef58fe266cee5837ed27f24ce6b60d60951c78`; main tracks origin/main. The repository remains private. Follow-up feature-branch commits have not been pushed; approval covered the initial main commit only. No force-push or remote overwrite occurred.

## Credentials and generated files

.gitignore excludes Python/Node dependencies, virtualenvs, local environment/configuration files, private keys, credential files, downloaded tools, temporary files and generated simulation evidence. Source, tests, examples, canonical plans and generated roadmap documents are versioned. Numerical summaries and reproducibility commands remain in docs; raw evidence remains local under evidence/ and can be shared separately after inspection.

The tracked pre-commit hook scans staged blobs for common credential signatures without printing secret values. Enable it after cloning:

```text
git config --local core.hooksPath .githooks
python scripts/check_secrets.py --staged
```

Inspect git diff --cached before each commit. Keep passwords, tokens and keys in ignored local files or the operating system credential store. Never add credentials with git add -f. The scanner checks common patterns; reviewing staged changes remains necessary.

## Connect GitHub

GitHub CLI authentication is completed by the owner in its browser login flow. Do not paste credentials into this chat or repository:

```text
gh auth login --hostname github.com --git-protocol https --web
```

Once authenticated, inspect the account and whether CircuForge already exists. If absent, create a private, empty repository (without a remote README, .gitignore or license):

```text
gh api user --jq .login
gh repo create OWNER/CircuForge --private --description "CircuForge — Wave2Circuit Research Edition"
git remote add origin https://github.com/OWNER/CircuForge.git
gh repo view OWNER/CircuForge --json nameWithOwner,isPrivate,url
git ls-remote origin
```

OWNER is the actual authenticated account or organization selected by the owner, not a literal placeholder to run. If the repository or origin already exists, inspect it first; preserve remote changes. Do not change an existing repository's visibility automatically.

**Push only after the owner's explicit approval of the concrete initial commit and target private repository.** Then use a normal push:

```text
git push -u origin main
```

Never use --force, --force-with-lease, destructive resets or remote branch deletion for this setup. If the remote has commits, fetch/inspect and reconcile through a branch or PR; do not overwrite them.

## Future work

Create a feature branch before editing product code:

```text
git switch -c codex/p1-followup
```

Commit focused changes with task IDs after tests pass. Pushes and publication remain subject to the owner's instructions. No credentials are stored in remote URLs.
