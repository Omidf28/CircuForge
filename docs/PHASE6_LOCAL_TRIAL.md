# P6-H1: proposed local-only trial

Status: **owner approved this local scope on 2026-11-20**. Exact response:
«تأیید آزمایش فقط محلی با همین سقف‌ها». P6-H1 records that explicit decision, not an
automatic waiver. Adapter/runner validation and actual experiment evidence are
separate from permission; no efficacy result is implied. The source remains on C.
The allowance subsequently ended and is closed. See
[observed partial results](PHASE6_LOCAL_RESULTS.md): seven model requests,
15 SPICE attempts, zero completed equal-budget comparisons and zero provider cost.

On November 21 the owner answered `next` to a request for one fresh execution
under the same caps. Its separate renewal packet is now closed too. It produced
four complete matched-call comparisons, 25 model requests and 65 SPICE attempts;
the final replay stage did not complete before its deadline. See
[renewal evidence](PHASE6_LOCAL_RENEWAL.md). These are separate datasets and
neither closed packet authorizes another run.

## Observed inventory — 2026-11-20

Read only `GET http://127.0.0.1:11434/api/tags`, `GET /api/version` and
`POST /api/show` for installed model metadata. During that inventory step, no
`/api/generate` or `/api/chat` request was made. Ollama reported version 0.40.16 and three installed models:
`nomic-embed-text:latest`, `aya-expanse:8b-q4_K_S` and `llama3:latest`.

Proposed model: already-installed `llama3:latest`, 8B/Q4_0, 4661224676 bytes on
disk, reported completion capability. Pin digest
`365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`;
do not pull a newer model or silently substitute a cloud model. Disk size is not
a measured RAM requirement. Metadata discovery needed local-socket tool
permission; the initial sandbox denial was not treated as a missing model.

## Proposed authorization scope

Machine-readable proposal: `examples/local-proposal-trial-v1.json`.

- Provider/API expenditure cap: **zero**, no paid service, credential or download.
- Only `127.0.0.1:11434`, pinned installed model, proxies and redirects refused.
- Only generated numeric RC specs in prompts, no source files or personal data.
- CPU-only request settings, two threads, one request at a time. No server/global
  settings changes, deployment, autonomous tools or GPU requirement.
- At most 32 model requests total: two pilot checks, at most 28 comparison
  proposals and two replay checks. Per request reserve 2048 input plus 256 output
  tokens; global reservation ceiling 73728 tokens. Report actual model usage
  separately; malformed/absent usage retains reservations under P6-C1.
- 60-second client deadline per request and a 600-second total experiment
  deadline. Implementation must limit each request by the remaining total time.
  These are client/runtime settings, not an OS resource quota or a measured
  inference-speed guarantee. A timeout is a failure, not a successful response.
- At most 80 total SPICE attempts for this trial envelope. The planned four
  case/seed trials compare random/grid/SciPy/local proposals at four calls per
  method: 64 comparison attempts maximum, plus up to four pilot/replay attempts.
  The spare cap is not permission to retry indefinitely or change the methods.

Two ideal first-order RC topologies, seeds 7/42 and 0.1% error tolerance are frozen
in the proposal. They share the same analytic cutoff equation; this small trial
cannot establish general topology synthesis or broad model superiority. A model
that fails to produce four distinct valid candidates within its proposal limit
has an incomplete comparison; report the actual smaller call count and failures
without silently replacing its proposals with random search. Passing the target
is separate from engineering execution and fair-budget eligibility. Numerical
results, raw simulator traces, failed proposals, usage, latency and replay
differences must remain visible. No guaranteed determinism or improvement is
assumed before observation.

## Primary references checked for the decision

- [Ollama generate API](https://docs.ollama.com/api/generate): JSON/schema output,
  generation options, prompt/output token counters and completion status.
- [Ollama local FAQ](https://docs.ollama.com/faq): local/cloud distinction, prompt
  privacy, context and residency settings. Local transport plus a verified local
  model is the intended scope; this proposal does not claim to audit every
  background network activity of the installed Ollama application.
- [Installed model's published tag](https://ollama.com/library/llama3:latest).
- [Meta Llama 3 license and acceptable-use terms](https://raw.githubusercontent.com/meta-llama/llama3/main/LICENSE).
  The local metadata reports the matching license heading. This trial proposes
  local inference, not redistribution of model weights; publication/deployment
  remains separately unauthorized. Recording a link is not an owner's acceptance
  of terms or an automatic permission waiver.

`P6-H1` is done for this exact local scope only. Approval authorizes adapter
implementation and this bounded trial, not
external providers, paid tokens, model downloads, pushes or deployment.

The installed optional HTTP client is declared by `.[local-model]`. The trial
runner is `scripts/run_local_trial.py`; it requires recorded approval and a new
output directory, and now refuses the closed source allowance. It is not called
by ordinary `design`/HTTP requests. `scripts/audit_local_trial.py` can audit the
existing dataset without running a model or simulator. A new run would require a
renewed resource decision and a separately identified execution envelope.
