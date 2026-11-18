# Version control

The standalone CircuForge folder is the Git repository. It is separate from the unrelated VideoPlayer project. The initial verified implementation is committed on main. Development after the initial commit uses branches named codex/<task-id>-<description>.

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
