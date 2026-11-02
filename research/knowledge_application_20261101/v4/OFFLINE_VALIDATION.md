# V4 offline validation — 2026-11-02

Scientific freeze **f1324b29108af9216c9eb140035dcdd99698af21052764e34d902f5493edddb1**;execution manifest **ed947bd8f3065f3df957a284a10f32dc0234a2b8e6142246b9e76ba54e2287d6**. Previous v1/v2/v3/source/adapter/private run inventory preserved byte-identically;prior log content retained. These are preparation results,no remote execution evidence.

## Tests and evidence

- V4 scientific8/8pass,0skip,4.659s:byte-identical data/rubrics/prompts/order;onlystudyidentity/no_repeat_ngram_size20config change;originalv3adapter binding;private raw IDs/termination;EOS151645retained;alternative151643diagnostic only;save truncated output and stop;missing/hash/config/raw-token baseline rejection;no training entrypoint/scoring change.
- V4 execution13/13pass,0skip,8.990s:resource AST/single spawn/no training;budget/acceptance/history gates;exact-evidence rejection;freshv4only baseline;originaladapter-only transfer excludesv3responses;safe artifact paths/diagnostics. Synthetic C plumbing success and non-EOS failure exercised with fabricated data and stubbed modules/subprocesses,not an actual model/runtime. Failure saves output and stops after one command.
- Actual installed Modal1.2.3 lazy function definitions for both stages validated under network/DNS/process/model-import prohibition,empty Modal configuration. No hydration,from_id call,app.run,build,spawn or provider access.
- Actual CPU Transformers4.56.2/Torch2.8.0 regression14checks passed. Includes original12synthetic mechanism checks,identicalA/B/C/idempotent prepared config,and full effective config equality to greedyv3except no_repeat_ngram_size20. Real configuration resolution and logits-processor construction,no weights/forward/generate/model responses. Private report research/runs/ka-v4-generation-regression/report.json is accepted by actual v4launcher. Initial config-only stub lacked a bound _prepare_generation_config method;fixed before final freeze/passing tests,not a model failure.
- Unchanged v3 scientific19/19pass0skip4.441s and execution16/16pass0skip0.404s,including actual pinned regression/SDK definitions. No historical frozen tests modified.
- Pure launch prerequisites verify original report/ZIP and11adapter files;adapter-only bundle13entries (11files+originalmanifest/binding),47446094bytes. Adapter model SHA1963de65f0bcc6b3ddbb68d7c243ce0b024938be81ec4b481b4d66f3c6d14751. New public ADAPTER_IMPORT.json explicitly binds originalv3training,notv4training. No adapter merging/re-saving/retraining.
- Actual local launcher invoked under network/process/model/Modal-import guards with pending acceptance:rejects before Modal import or output creation. No launch attempt. Config/source/freeze/regression/accounting pass;pending amendment correctly blocks.

## Costs,acceptance and limitations

Private0600/Git-ignored ka-v4-acceptance.json accurately carries unchanged financial/rubric acceptance provenance,independent-review claimfalse,amendmentacceptedfalse/null reviewer/time. Explicit human acceptance of this specific freeze/post-held-out repair/repetition and EOS risks/originaladapter/512stop/Modalhistory remains required;previousv3acceptance is not v4approval. No request for another independent financial review.

Private0600/Git-ignored ka-v4-accounting.json includes tenth historical report (failedv3C96.9056sremote/113.3557slocal);priorv3accounting unchanged. Historical estimates$7→$8,3900→4200GPU seconds;extrareserve$5unchanged. Freshbaseline+C6840sat existingassumed$0.00063924/s gives$4.3724016;projectedtotal**$17.3724016/$20**,11040s/14400s. Actual provider charges,billable seconds,image-build costs,currentcreditsunknown. Dated prior dashboard observations remain workspace-wide;no new price verification or guaranteed cloud cap. Refresh afterbaseline beforeC.

No-repeat20blocks exact20token repetition acrossprompt+output,including legitimate phrases and potentiallyEOS;it does not guarantee completion/financial correctness. Subsequent varied repetition/truncation remains possible;512stop/no retry preserved. Raw IDs remain private and outside unchanged human scorer packets. Repair selection followed held-outv3failure;not untouched confirmation. Full runtime reload/termination/latency/memory remain unverified forv4.

## Exact changed files

New v4 files:
- ADAPTER_IMPORT.json
- CASE_REVIEW.md
- COMMANDS.md
- INHERITED_V2_PROTOCOL.md
- INHERITED_V3_PROTOCOL.md
- KNOWLEDGE_RUBRIC.md
- MATCHED_CONTENT.json
- PROTOCOL.md
- QWEN_GENERATION_DEFAULTS.json
- RUBRIC.md
- SPLIT_AUDIT.md
- V3_MANIFEST.json
- common.py
- config.json
- evaluate.py
- freeze.json
- generation_regression.py
- heldout.jsonl
- requirements.txt
- score.py
- train.jsonl
- validate_offline.py

Also new in v4:OFFLINE_VALIDATION.md (this report).

New execution_v4 files:execute.py,validate_offline.py,READINESS.md,execution_freeze.json,OFFLINE_VALIDATION.md. Only pre-existing file changed in this task:research/RESEARCH_LOG.md (dated append). New private records:ka-v4-acceptance.json,ka-v4-accounting.json,ka-v4-generation-regression/report.json,ka-v4-preparation-validation/report.json. Scientific freeze excludes this validation report to avoid self-reference;execution freeze binds source/tests/readiness. Existing unrelated Git changes preserved;no staging/commit/push/merge.

**Technical preparation GO;execution NO-GO pending explicit v4amendment acceptance and separate baseline authorization.** C additionally requires complete freshv4A/B,reconciled accounting and separate authorization. Exact future commands are in READINESS.md. Stop before billable work.
