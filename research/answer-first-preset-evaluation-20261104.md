# Answer-first presets — November 4, 2026

[Issue #62](https://github.com/mbzuaiciao/metis/issues/62). **Implemented the two scoped improvements; offline validation passes. BLOCKED — live network unavailable. Both authorized application attempts failed to reach Meta, so no new model answers exist to evaluate and no model-quality improvement is established. No retries or fallback.**

Read `AGENTS.md`, [research memory](RESEARCH_LOG.md), the [#58 evaluation](live-meta-preset-questions-20261104.md) and [#60 trace](preset-ranking-trace-20261104.md). Base: merged main `6893f06`. This newly authorized evaluation tests the targeted correction; it does not reopen earlier experiments.

## Changes and preserved boundaries

- `InvestigationResults` immediately displays the returned exact question, full summary and principal observations before the existing investigation stages. These fields occur once; economic interpretation, numerical evidence, position details, verification, uncertainties and references remain in supporting disclosures. The redundant collapsed question is removed; investigation identity, LIVE META/model and DETERMINISTIC DEMO badges, captured scope and follow-ups remain. Visible text distinguishes unchecked model prose from deterministic demo templates.
- The existing system instructions prioritize the actual question in summary/observations. Conditional guidance requests ordered signed net-position detractors and positive offsets, ties and separate credit rate/spread legs; rally comparisons clarify asset/direction and conditionally compare recession and disinflation relief; signed exposure remains distinct from signed P&L. No hardcoded position amounts or final answers were added.
- Engine, inputs, response schema, strict evidence validation, verification, request routing, provider parameters and investigation behavior remain unchanged. Application/prompt sources were frozen before the two attempts and hash-checked unchanged afterward. No tuning followed the failures.

## Offline validation, before live attempts

- Backend/research: `.venv/bin/python -m pytest tests research/test_historical_macro_context.py research/test_meaning_alignment.py -q --tb=short`: **240 passed, 4.86s**. Existing mocked provider contract covers model settings, strict schema and evidence allowlist; no paid inference.
- Frontend: `npm test` with `METIS_SAVED_ANSWERS` pointing to authorized ignored #58 call 2: **58 passed, 5.406s**. Actual component renders check exact question matching, summary/observations before stages and outside disclosures, no duplicate returned text, model/demo labels, unchanged input, evidence/verification retention and collapsed supporting details. Optional saved-response test prohibits fetch and copies no private fixture into Git.
- `npm run build`: TypeScript and Vite pass, **3.15s Vite**. `git diff --check` passes. Existing Starlette/httpx deprecation and Vite bundle-size warnings remain.
- Initial frontend run caught the removed historical scope label; restored the visible scope eyebrow while removing only the redundant collapsed question, then reran successfully. One edit command used unavailable `python` from the frontend directory; corrected to the repository virtual environment. No inference occurred during these corrections.

This is source/server-render validation, not a new interactive browser or usability study. The saved #58 answer is historical evidence: its incomplete ranking remains incomplete, now immediately visible. It is not a new answer from the modified prompt.

## Frozen live protocol and observed failures

Same Current Portfolio, October 30, 2026 daily snapshot, full context, empty history, independent investigations via existing FastAPI `/api/reasoning` using TestClient and the real HTTPProvider. The provider context and output-schema hashes match #58. Daily shocks remain −10bp rates, +12bp IG, +35bp HY, −1.5% equities, −0.5% EUR/USD.

Configured identity: **Meta `muse-spark-1.3`**, `https://api.meta.ai/v1/chat/completions`, temperature **0.2**, maximum completion tokens **8,000**, reasoning effort **low**, timeout **60s**, strict JSON schema. Configuration preflight passed without exposing credentials. No configuration changes, alternate provider, demo, observer or LLM judge.

Exactly **2 application attempts**, sequentially **08:50:02 PST / 16:50:02 UTC**, November 4; **one per exact preset**, **0 retries**:

| Question | Observed outcome | Route latency |
| --- | --- | ---: |
| Which positions and risk factors contributed most to the selected daily P&L? | HTTP 502: cannot reach live Meta endpoint; no interpretation | 0.052s |
| How could a recession-driven rally differ from an inflation-driven rally? | HTTP 502: cannot reach live Meta endpoint; no interpretation | 0.019s |

Both application errors explicitly report no demonstration fallback. Neither response has mode/model badges or structured interpretation to inspect. **Two attempted dispatches are not two completed inferences.** Upstream receipt, billable call count, tokens, reasoning tokens, upstream latency and monetary cost are unavailable; do not record unknown usage as zero. The runtime restricts network access; the application exposes only a sanitized transport error, so the precise transport cause is unavailable. No further attempt was made after the failures, including with different network permissions.

Private one-shot runner, pre-dispatch intents, frozen criteria/settings/context/source fingerprints, failed results and completion ledger remain only in ignored `research/runs/issue62-answer-first-20261104/`, directory 0700/files 0600. File creation is exclusive for protocol/intents/results, preventing accidental reruns. No raw response or credentials are committed.

## Financial evaluation and decision

Criteria frozen before dispatch use the existing engine, not model arithmetic:

- Position answer must order major net detractors **EQ-US −$255k, EQ-DM −$135k, IRS-P −$100k, HY-US −$66k, HY-EU −$60k tied FX-EUR −$60k**; separately name positive offsets **IRS-R +$245k, UST10 +$144k**. HY-US legs are +$32k rates/−$98k spread; HY-EU +$24k/−$84k. Net losses must not be confused with spread losses. Factors are +$501k rates, −$333.2k spreads, −$390k equities, −$60k FX; total −$282.2k.
- Regime answer must clarify the rally and compare recession-related falling yields with disinflation/inflation-relief falling yields, with conditional credit/equity effects and unknown causes. Supplied equity delta is **+$26m**, distinct from its negative daily contribution. No invented regime shock calculations or portfolio totals.

**Both cases: not assessable**, because no new answer was returned, either in the immediately displayed fields or elsewhere in the structured interpretation. No financial success, ranking correction, sign correction or causal prompt effect can be claimed. Offline UI success establishes visibility only. Prior #58 content failures remain the last observed model evidence; two planned samples would not establish reliability even if successful.

**Engineering decision:** retain the scoped UI/instruction changes for review, disclose the blocked live evaluation, stop after the two failed attempts, and open a PR against main without merging. Any fresh live evaluation requires new explicit authorization; this report does not authorize it.
