# Smoke diagnostic correction 3 — offline validation, 2026-11-01

**Diagnostic correction complete; ready for a separately authorized diagnostic attempt. No remote execution.** The original failure remains unexplained because its message/traceback were discarded. This change adds evidence collection; it does not assert a correction to the unknown InvalidError.

## Preservation

Original failed record `research/runs/ka-modal-smoke-v2-01/report.json` remains byte-identical: SHA-256 `d96a27cb013c14923c8a83110c6e6f9c4dab5964dcce2ba8cda6734b484628c0`. It is not copied into Git-visible artifacts. Its `intentional_submissions=0`, absent acknowledgement/IDs and InvalidError remain historical facts. No results or metadata were rewritten. Future command/default uses the fresh, currently nonexistent `research/runs/ka-modal-smoke-v2-02/`; directory reuse still fails before cloud work.

All original v1 and bound v2 artifacts match their frozen digests; v2 freeze remains `4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91`. Original policy-1 artifacts remain under policy_v1. The six prior policy-2 files are archived byte-for-byte under [policy_v2](policy_v2/README.md), with prior manifest SHA-256 `24d747195caab242996f5adfe8f286586a3878cc7cded8a7bfe65fe8ca5a1cd4`. Archived relative links retain their original-directory meaning. `smoke_runtime.py` is byte-identical to policy 2.

Current [smoke_freeze.json](smoke_freeze.json) SHA-256: `d541d51a1444fb5997a18dcc641d2cd4637651ce7e9c673fc11762db951394cd`. It binds current sources/documents plus both prior preparations. This post-freeze validation report and research-log append are excluded from the digest. No frozen scientific source/config/dataset/rubric was edited.

## Diagnostic behavior

The private report records current `phase`, timestamped `phase_history`, first `error_phase`, exception class, sanitized message and sanitized traceback. The `exceptions` list retains caught-at UTC, phase, exact class/module, message and exception chain with stack basename/line/function. First failure survives cleanup; history/cleanup errors have separate diagnostics. Tracebacks omit locals, source-code lines and absolute paths. These records, including raw run metadata, remain under the ignored private boundary (0700 directory, 0600 files via umask).

Construction and app initialization run within the supported `modal.enable_output()` default context, wrapped in line-buffered stdout/stderr redaction. SDK 1.2.3's `show_progress=False` does not create an OutputManager, so default output is intentional. Token/env-value/path/URL/email/quoted-value/structured-data/opaque-string filtering precedes terminal display and private exception persistence. No environment dump, credential-file read by diagnostic code, frame locals or raw-exception artifact is added. Redaction can hide useful offending values. Arbitrary SDK/provider text cannot be certified public; retain reports privately and review excerpts before sharing. Hard termination, failed writes or signal-handler failures can still leave incomplete diagnostics.

Phases distinguish local_construction, app_initialization, submission, result_retrieval, result_received, call_cleanup, app_shutdown and complete. The original primary exception is captured before cleanup changes phase. Existing single intentional submission/no application retry, L40S/no fallback, 840s watchdog/runtime, one-step-per-execution, four synthetic microbatches, history interpretation and INCONCLUSIVE exit behavior are unchanged. No automatic retry is introduced.

## Actual offline validation

Executed with `PYTHONDONTWRITEBYTECODE=1` and `METIS_SMOKE_SDK_PYTHON` pointing to the already cached Python 3.12/Modal 1.2.3 environment:

`python3 research/knowledge_application_20261101/modal_smoke_v2/validate_offline.py`

**Final: 14 tests passed in 0.429s, tool wall 0.635s.** Earlier passing run: 14/0.437s/tool0.489s. No dependency installation or downloads.

Two earlier test-harness failures are preserved in this account: first, the deliberately long output marker was correctly filtered as an opaque value, so the visibility assertion failed (13 pass/1 fail, 0.370s/tool0.435s); an intermediate mistaken change treated SDK `is_hydrated` as a method rather than a property (13 pass/1 fail, 0.297s/tool0.302s). The test now uses a short nonsecret marker and the installed property API. Neither failure involved app.run, image building, submission, networking or model execution; no original scientific/runtime setting was changed to pass tests.

Checks include:

- All previous mask/config/resource/one-step/restart/ambiguity/private-boundary tests retained. AST comparisons preserve original mask/version/gradient callback/SFTConfig mechanics; runtime source is also byte-preserved from policy 2.
- Mock failures in construction, initialization, submission, retrieval, cleanup and shutdown retain the correct first error phase/type/message/stack without another submission. Saved outputs remain INCONCLUSIVE.
- Known fake environment secrets, private payloads and paths do not appear in saved exception diagnostics. Stack locals/source lines are absent. Credentials split across terminal writes (with intervening flush) remain buffered and redacted. Tests use synthetic sentinels, never real credentials.
- Actual installed SDK version verified as **1.2.3**. The child process blocks socket/DNS/network events, subprocesses and model-library imports; removes account-related Modal environment overrides and uses an empty config at the OS null device. It constructs only lazy local Image/App/Function definitions using the unchanged arguments. App ID is None and Function is unhydrated. No `app.run`, hydrate/resolve, build, submit or remote method is called.
- Actual SDK OutputManager exists within the default output context, emits the short marker through the redaction stream and is removed on exit. This validates local diagnostic API usage, not provider initialization.
- Plan/help remain network/model/Modal-import-free. Default future output is new; three-file remote upload allowlist and ignored private outputs remain unchanged.

Optional installed-SDK check is explicitly skipped without `METIS_SMOKE_SDK_PYTHON`; this final run **did not skip it**. The SDK interpreter path is local environment provenance, not a newly required machine-specific dependency or package-install instruction.

## Limits and decision

**GO for a separately authorized diagnostic attempt using the README command and new output directory; do not launch during this task.** Real account/environment app initialization, remote image builds, downloads, GPU availability, actual masks/gradients/reload and billing remain untested. No hidden SDK-version, GPU, precision, model or optimizer substitution is made. Complete physical history still cannot be established from the best-effort public API, so overall status remains INCONCLUSIVE even when technical checks pass. This diagnostic patch neither resolves the earlier error nor establishes GPU fit or zero prior billing.

This task: **0 remote Modal operations, 0 new submissions, 0 GPUs, 0 model downloads, 0 image builds, 0 optimizer steps, 0 model forward/generation calls, 0 inference tokens, $0 GPU spending**. Installed SDK import/local-definition/output-context checks only, under network prohibition. Actual GPU usage/memory/latency/billing and historical underlying InvalidError text remain unavailable. Authoring assistant tokens/cost, total task duration and CPU monetary cost unavailable. No production change, staging, commit, push or merge.

Pre-append log-prefix SHA-256: `0575f456885a1250abf6190ce29d65f0fdbe92d8b474e743e14be70cce7ab368`. Stop after corrections/offline validation.
