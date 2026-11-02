# Smoke configuration correction 4 — offline validation, 2026-11-01

**GO for a separately authorized retry using fresh `research/runs/ka-modal-smoke-v2-03/`. No launch performed.** Only the offending Modal function option changed: `scaledown_window=1` to `scaledown_window=2` seconds. Function timeout/watchdog840, startup_timeout30, one L40S, retries0, one intentional submission, max_inputs1 and one optimizer step per execution remain unchanged. No runtime/training changes.

## Diagnosis and evidence

The supplied second-attempt failure and existing private diagnostic record locate the primary InvalidError in `app.run()` initialization, `_create_all_objects` → `_load` → `FunctionCreate`, before `smoke.spawn()`. Missing results/identities are consequences, not the primary cause. No successful GPU submission or training result is confirmed. This offline correction cannot establish prior billable usage or a zero bill.

Installed SDK: Modal **1.2.3**, cached Python **3.12**, source `modal/_functions.py`:

- Lines777–778 reject only `scaledown_window <=0` locally, not 1.
- Lines780–785 construct `AutoscalerSettings(scaledown_window=scaledown_window)`.
- Lines1005–1006 serialize function/startup timeouts separately; line1044 serializes the legacy `task_idle_timeout_secs=scaledown_window or 0` alias.
- Lines1116–1128 perform `FunctionCreate` and convert server INVALID_ARGUMENT/FAILED_PRECONDITION into InvalidError. The observed inclusive [2,3600] rule is a **server** rule, not a complete local SDK validation rule.

The official [Function reference](https://modal.com/docs/sdk/py/latest/Function) documents `scaledown_window` as an integer from **2 through 3600 inclusive**. All options were inspected: GPU L40S, CPU(2,2), RAM(32768,32768)MiB, disk51200MiB, timeout840/startup30, retries0, containers min0/max1/buffer0, max_inputs1, serialized=True/include_source=False. Only idle window1 violates that range. Actual local SDK lazy construction accepts the corrected definition, but remote server acceptance remains untested.

## Correction and regression

`modal_smoke.py` adds a documented integer-range preflight before planning/SDK construction. `validate_offline.py` checks accepted endpoints2/3600 and rejection of1/0/3601/nonintegers. It compares every function option with policy_v3 and verifies **only scaledown_window differs**, and the entire runtime is byte-identical.

Against the actual installed SDK (not a replacement validator), an audited child process invokes the native decorator validator, verifies zero is rejected, captures real AutoscalerSettings protobuf construction for1/2/3600/3601, and inspects the actual legacy serialization expression. Native local acceptance of1/3601 is explicitly asserted to document the SDK/server gap; the new local guard separately rejects them. Server validation cannot run offline because its implementation is not shipped in this SDK. No app.run, object hydration, image build or remote call is used.

Known quoted public option names now survive diagnostic redaction, including the offending field. The name-only allowlist follows environment/credential/token/path/structured-data filters; tests ensure private quoted values and credential values remain masked, and a public name matching a secret environment value is still masked. Existing stack-only traceback and line-buffered output filtering remain. Arbitrary provider text remains private and requires review before publication.

## Results

Executed `PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/modal_smoke_v2/validate_offline.py` with `METIS_SMOKE_SDK_PYTHON` set to the already installed Modal1.2.3 interpreter. **16 tests passed, 0 skipped, in0.392s; tool wall0.358s** (test-reported and tool durations are distinct measurements). No installation/download.

The SDK child prohibits socket/DNS/process creation and model-library imports, clears account-related Modal overrides and uses an empty config. It exercises only local definitions/protobufs/output manager. All prior single-submission, no retry, conservative INCONCLUSIVE/history, exclusive-output, phase/error, completion-mask, frozen-base/gradient callback/SFTConfig, one-step/runtime and three-file upload-boundary checks remain. Plan/help have no Modal/model/network access. Runtime reads no financial cases; no production changes.

Intermediate validation failures are retained here: the first run before updating the source manifest correctly rejected changed source hashes (12 pass,1 fail,3 errors;0.135s/tool0.163s). The next run had15 pass/1 fail (0.417s/tool0.426s) because a test assumed only one SDK keyword named task_idle_timeout_secs, while the SDK also has other legacy/update paths. The corrected test targets the specific `scaledown_window or 0` expression; probe function names are now unique. No runtime/config setting was tuned to resolve this test-harness assertion.

## Preservation and freeze

Both private failed reports remain unchanged and ignored; no raw records were copied into public artifacts:

- `...-01/report.json`: SHA-256 `d96a27cb013c14923c8a83110c6e6f9c4dab5964dcce2ba8cda6734b484628c0`.
- `...-02/report.json`: SHA-256 `c0ca4752bb78214fe457e6691685db2ca38daa5f35816941203e3e2a3de69656`.

All six prior preparation files are preserved under [policy_v3](policy_v3/README.md), including prior report/manifest `d541d51a1444fb5997a18dcc641d2cd4637651ce7e9c673fc11762db951394cd`; policy_v1/v2 unchanged. Current [smoke_freeze.json](smoke_freeze.json) binds22 source/document/history entries and has SHA-256 `a663fcb45d0f8597308f659d89ee7a64cdfa5193c615e99be8df688b6decc8a3`. This post-freeze report and log append are excluded from that digest.

Original v1 freeze14 entries and v2 freeze20 entries match; v2 manifest remains `4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91`. No frozen data/protocol/rubric/source change. Existing unrelated changes preserved; no staging, credentials or private records staged. Future output directory -03 does not yet exist; directory reuse fails closed.

## Limits and accounting

**GO only for a separately authorized retry**, exact command in [README](README.md). Remote initialization/image/dependency/model/GPU/mask/gradient/reload/memory feasibility remain untested. Best-effort execution history still cannot establish uninterrupted physical execution, so overall status remains INCONCLUSIVE even if returned technical checks pass. No exactly-once or guaranteed cost claim. Existing conditional one-allocation900s estimate remains $0.4878 GPU / $0.575316 configured compute before build/overhead/egress/tax/plan charges or replacements; this task did not re-quote pricing or incur a provider bill.

This task: **0 Modal submissions/remote operations,0 GPU provisioning,0 model downloads/builds,0 training/inference/model calls/tokens,$0 GPU spending**. Actual GPU memory/latency/prior billing unavailable; authoring assistant tokens/cost,total task duration and CPU monetary cost unavailable. Pre-append research-log prefix:101791 bytes, SHA-256 `bce314758daba71b523e1373dbe66d7fe1a707e282a08ee9814d46fbf4c56ac2`. Stop after offline correction; no execution, commit, push or merge.
