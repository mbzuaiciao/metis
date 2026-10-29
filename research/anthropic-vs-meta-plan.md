# Anthropic versus Meta — no-inference preparation (2026-10-28 PDT)

**Status: protocol only. No model inference authorized or performed.** Production unchanged.

## Research question

Does Claude exhibit materially better *financial judgment* than the existing Muse Spark baseline on identical synthetic portfolio evidence, especially when numerical attribution is available but financing, hedge objectives or causality are not established?

The comparison is exploratory; four cases cannot establish model reliability or statistical superiority. Judge grounded statements, not fluency.

## Preconditions and exact source of truth

- Follow root `AGENTS.md` and `research/RESEARCH_LOG.md`; preserve all previous findings.
- Existing Anthropic support is in `backend/metis/reasoning/harness.py`: `METIS_PROVIDER=anthropic`, `METIS_MODEL`, and `ANTHROPIC_API_KEY`. `.env.example` documents these. A provider option is **not** evidence of active credentials or a successful Claude request.
- Current production baseline is Meta Muse Spark. Do not alter `SYSTEM`, `Interpretation`, provider settings, calculation engine, UI, or verification behavior.
- Existing synthetic questions/expectations: `research/observer-cases.json`; v0.8 report: `research/observer-experiment.md`; archived raw calls may exist only locally in ignored `research/runs/observer-v08-20261028/`. Git does **not** include private raw model responses.
- Existing v1.1 report and private archive cover another four production questions, but do not assume their inputs are interchangeable with the v0.8 cases.

## Four selected existing cases (freeze before any calls)

| ID in observer-cases.json | Question focus | Critical distinction to judge |
| --- | --- | --- |
| 02 | Did a government-rate hedge fail? | Positive rates contribution versus negative total; cannot infer hedge objective, optimality or insufficiency |
| 05 | Is the liquidity buffer adequate? | Cash mark and derivative notional do not establish available liquidity or collateral requirements |
| 09 | Estimate default/counterparty losses | CS01 is not jump-to-default loss; marks/notionals do not establish net exposure; unknown is not zero |
| 10 | Causality of synthetic daily moves | Attribution/co-movement is not identified economic cause; test competing mechanisms and evidence needed to discriminate |

The canonical questions and expected quantitative/economic distinctions are the **existing JSON entries**, not paraphrases above. Expectations must not enter model-facing context. These questions sample different risks; they are not a random sample.

## Zero-cost preflight (allowed now)

1. Confirm current repo HEAD, instructions, fixture contents and whether `research/runs/observer-v08-20261028/` exists locally; do not check in private records.
2. Examine archived original Muse Spark responses for the selected four case IDs, if accessible. Verify case/question/context identifiers or hashes, exact prompt, evidence snapshot, model, output schema, settings, complete output, timing and token usage. Document missing metadata as unavailable.
3. Check whether the existing Anthropic API path can accept the **same financial evidence** and materially comparable output requirements. Different schema enforcement or model reasoning controls are confounders; log them rather than claiming exact matching.
4. Verify locally whether `ANTHROPIC_API_KEY` and a valid Claude `METIS_MODEL` are configured **without printing credentials or making requests**. Do not assume a chat subscription provides API access.
5. Produce a per-case comparison worksheet (expected facts, required caveats, prohibited unsupported conclusions, important omissions). Freeze it **before** future inference; keep private full prompts and responses outside Git.

## Future live phase — requires API access and separate explicit authorization

**Do not execute from this planning task.** If and only if the four archived Meta originals are complete and input-compatible, call Claude once for each exact case (maximum **four** new requests; no retries) and manually compare with the corresponding original Meta answer. Use comparable context, format requirements and stated settings. If archived originals are absent or not comparable, stop and report the blocker; do not silently spend eight calls regenerating both arms.

Capture completion validity, omissions, unsupported claims, numerical/economic errors, response usefulness, prompt/completion/reasoning tokens when reported, latency and monetary cost if known. Absence of reasoning-token usage is not zero. Preserve original mistakes and failures in the evaluation.

## Decision and stopping rule

Stop after the zero-cost preflight for now. Later, stop after four authorized Claude attempts (or earlier on a configuration/archival blocker), even if results are inconclusive. Recommend production integration only on clear material financial-judgment gains without unacceptable failures/cost; never integrate automatically. Preserve Meta baseline and existing hackathon behavior otherwise.

**Research outcome at planning stage:** no performance conclusion; Claude access and archive compatibility remain to be verified locally.
