# Live Meta preset-question diagnostic — 2026-11-04

[Issue #58](https://github.com/mbzuaiciao/metis/issues/58). **Observed:** all three live requests completed, but substantive responsiveness differed: baseline adequate; position ranking partial; recession-versus-inflation comparison inadequate as phrased. A common presentation does not imply identical answers, and valid structured claims do not certify the prose.

## Protocol and controls

Read `AGENTS.md`, [research memory](RESEARCH_LOG.md), [inference reliability](inference-reliability.md), [truncation diagnosis](meta-inference-truncation-diagnosis.md), [effort experiment and corrections](reasoning-effort-experiment-20261029.md), and [live integration check and qualification](live-meta-integration-check-20261029.md) before execution. This is the newly authorized three-question diagnostic, not a replication of those completed studies.

Base: main `3185af1d9e14da3b509e616415ae457e31321292`. Existing FastAPI `/api/reasoning` route invoked through TestClient, with the real unmodified HTTPProvider reaching Meta. Current Portfolio, October 30, 2026, $100m marked NAV, 12 synthetic positions; daily scope, full context, empty history, no investigation reference. Each was a new independent investigation. All three used identical backend daily shocks: rates **−10bp**, IG **+12bp**, HY **+35bp**, equities **−1.5%**, EUR/USD **−0.5%**. The independently selected historical stress was not used.

Configured provider `meta`; model `muse-spark-1.3`; endpoint `https://api.meta.ai/v1/chat/completions`; temperature **0.2**, maximum completion tokens **8,000**, reasoning effort **low**, timeout **60s**, strict API JSON schema and local `Interpretation` validation. No provider, prompt, schema, context, application behavior or calculation changes. No retry, alternate provider, demo response, observer or LLM judge. Evaluation criteria were frozen before inference: baseline total/offsets/caveats; named ranked net position amounts and factors; direct conditional regime comparison without invented calculations or historical causality.

Private protocol, execution-only runner, persistent per-question pre-dispatch intents and complete responses: ignored `research/runs/issue58-live-questions-20261104/` (directory 0700, files 0600). No raw responses are included here. Canonical JSON SHA-256 (sorted keys, Python default JSON serialization):

- Provider context, identical in all three returned snapshots: `726b53afbdf2f595faf71383d9d68ccce1d0abcee1cd9dedd29ce03807d90062`.
- System prompt: `8a3e3e48c7e22c7c4a5f87f128391a4a3a52ac78f35975b25ede21a60a1858c0`.
- Local output schema: `e71a1d102688adc2951c00002a22f5558e0d4b50313de13cebdb1e0ea823d513`.

The private protocol also freezes application, engine, rendering and input-file hashes. The provider adds the same evidence-ID constraints to its strict schema for each call. Source hashes were unchanged after execution.

## Exact questions and execution

1. Baseline, exact frontend `dailyQuestion`:

   > Explain the illustrative daily portfolio loss. Why did positive government-rate P&L fail to offset credit-spread, equity and FX losses? Identify the important positions and exposures. Separate calculated facts from economic interpretations, and identify vulnerabilities and missing evidence worth investigating. The scenario supplied with this question uses the daily snapshot shocks, not the separately selected stress scenario.

2. Exact preset:

   > Which positions and risk factors contributed most to the selected daily P&L?

3. Exact preset:

   > How could a recession-driven rally differ from an inflation-driven rally?

Executed sequentially **07:49:29–07:50:48 PDT** (15:49:29–15:50:48 UTC), November 4. **Exactly 3 fresh live requests, 1 per question, 0 retries.** All HTTP 200, complete validated interpretations, captured daily investigations, returned `mode=meta`, `model=muse-spark-1.3`: the fields used for LIVE META/model badges. No browser badge inspection was performed; identity was checked on actual endpoint responses, not inferred from HTTP status.

| Case | Prompt tokens | Completion tokens | Reasoning tokens (included) | Total tokens | Route latency, seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 11,488 | 2,423 | 754 | 13,911 | 25.231 |
| Position ranking | 11,434 | 1,948 | 506 | 13,382 | 21.123 |
| Regime comparison | 11,432 | 2,587 | 881 | 14,019 | 32.807 |
| Total | 34,354 | 6,958 | 2,141 | **41,312** | **79.161** |

Latency covers the application route, including upstream inference and local handling; separate upstream latency and monetary cost are unavailable. There were no timeouts, truncation, schema/provider errors or incomplete answers. All nine model-selected numerical mappings were Verified, with original prose Not checked.

## Numerical reference

Existing engine output, not model-generated calculations: total **−$282,200 (−0.2822% NAV)** = rates **+$501,000**, spreads **−$333,200**, equities **−$390,000**, FX **−$60,000**. Factor and position sums reconcile.

| Position | Net daily P&L | Relevant factor legs |
| --- | ---: | --- |
| EQ-US | −$255,000 | Equity |
| EQ-DM | −$135,000 | Equity |
| IRS-P | −$100,000 | Rates, negative DV01 |
| HY-US | −$66,000 | +$32,000 rates −$98,000 spreads |
| HY-EU | −$60,000 | +$24,000 rates −$84,000 spreads |
| FX-EUR | −$60,000 | FX |
| IG-EU | −$7,200 | +$63,000 rates −$70,200 spreads |
| IG-US | −$6,000 | +$75,000 rates −$81,000 spreads |
| CASH | $0 | No modeled contribution |
| IRS-R | +$245,000 | Largest positive net offset, rates |
| UST10 | +$144,000 | Rates |
| UST2 | +$18,000 | Rates |

Net equity delta is **+$26m**, net DV01 +$50,100/bp, CS01 +$17,800/bp. Spread-only IG/HY losses are −$151,200/−$182,000; their net losses are −$13,200/−$126,000. Supplied alternatives are rate-only rally +$2.505m, rate-only selloff −$2.505m, spread-only widening −$1.41m, Broad Risk-Off −$4.24m. These are synthetic first-order implications, not actual market returns.

## Manual question–answer review

**1 — Baseline: adequate core answer.** Explains the correct loss and factor offsets, names both equity baskets and the receive/pay swap and Treasury contributions, correctly separates HY spread and net P&L, and explicitly identifies synthetic October data and linear-model limitations. Competing growth-scare and credit-led explanations include missing evidence and no established causality. Sanitized conclusion: duration helped, but spread/equity/FX losses exceeded that gain. Limit: calling equities unhedged is stronger than the supplied cross-asset evidence establishes; no hedge mandate or complete hedge inventory is supplied. Comparing cash to stress MTM is only a proposed investigation, not demonstrated funding adequacy.

**2 — Position ranking: partially responsive.** Correctly orders loss factors and names EQ-US −$255k before EQ-DM −$135k; identifies IRS-R +$245k, UST10 +$144k and IRS-P −$100k, plus long-EUR FX −$60k. This is useful specific content, not merely macro commentary. However, it never presents the major net position detractors in order: IRS-P belongs third after the equity baskets; HY-US −$66k and HY-EU −$60k are not individually named with net amounts. It instead emphasizes spread buckets and aggregate HY net loss. Sanitized conclusion: useful factor attribution and selected position amounts, incomplete requested position ranking. The statement that equities and HY spreads moved together is imprecise: equity prices fell while spreads widened. No incorrect checked numerical amount was identified; existing alternative totals cited in vulnerabilities match the engine. All three selected claims repeat baseline total/rates/equities rather than checking the missing position ranking.

**3 — Regime comparison: inadequate distinction, plus a sign error.** It changes the content: three hypotheses (growth scare, dovish policy repricing, flows), more inflation discussion and a 2022 analogy. However, its summary and economic interpretation describe an inflation-driven rally as rising yields and joint bond/credit/equity losses. This substitutes an inflation selloff for the requested rally without clarifying which asset rallies or considering a falling-yield inflation-relief/disinflation regime. A responsive comparison could conditionally distinguish recession-related falling yields with weaker earnings/wider spreads from benign disinflation-related falling yields with potentially firmer equities/tighter spreads, while recognizing ambiguity. Those are evaluation interpretations, not newly calculated scenarios or observed causes.

The third answer also describes equity delta as **−$26m**, contradicting the engine's **+$26m**. Its stated −$390k equity loss is correct, so the negative exposure sign is internally inconsistent with a −1.5% return. The erroneous exposure is outside its three Verified mappings. It retains explicit synthetic/causality limits, does not invent separately computed regime shock vectors or portfolio totals, and labels the supplied rate-only alternative incomplete as an inflation scenario. Sanitized conclusion: recession duration offset versus inflation hedge reversal; that answers a different comparison.

## Presentation, interpretation and decision

Source inspection of `InvestigationResults.tsx` shows the same three-stage wrapper for every question. “What happened?” is engine-generated attribution, not proof the model answered the question. Hypothesis mechanisms and proposed checks appear in stages two/three. Model summary, economic interpretation and principal observations are under expandable supporting details. Thus correct detailed position amounts and the third answer's explicit regime contrast are partly hidden. This is a source-based visibility assessment; no new browser usability study was run.

**Interpretation:** these answers overlap substantially because evidence and instructions are shared, but are not identical. Question-specific differences exist; neither format validity nor the generic wrapper establishes substantive responsiveness. The ranking omission and regime substitution remain even after reading all model fields.

**Decision:** stop at three calls, preserve application code/prompts/reasoning behavior. Optional smallest follow-on: separately authorize a narrow question-responsiveness instruction to request net-position ordering and clarification of rally direction/asset, then evaluate it under a new bounded protocol. A presentation-only exposure of the original summary might improve visibility but would not fix these content errors. Neither option is implemented here.

Three non-blinded cases, one sample each, with shared synthetic context and an unpinned hosted model, are diagnostic observations, not reliability estimates or evidence of causal question effects. No extra inference or replication is authorized by this note. Validation is endpoint identity/completeness, identical context and unchanged source checks, numerical reconciliation, manual prose review and documentation/privacy review; no application test suite rerun was needed for documentation-only changes. Initial ordinary `git fetch` was sandbox-denied before fetching; authorized escalation succeeded. Final privacy validation initially caught the private runner at 0644; it was changed to 0600 and the full ledger/source/permissions/ignore/link/scope check passed. Raw response files were already 0600. The existing TestClient deprecation warning remained. No inference failure was concealed.
