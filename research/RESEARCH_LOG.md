# Metis research memory and experiment log

Established **2026-10-28 (America/Los_Angeles)**. This is a retrospective index and decision log, not a new experiment. Detailed reports are authoritative; their findings and private records have not been rewritten. Append dated entries for future results, corrections or disagreements rather than erasing earlier conclusions.

## A. Research objectives

Develop an AI-assisted portfolio risk system that produces financially sound, evidence-grounded explanations and recognizes when conclusions are unsupported. Deterministic calculations establish what the synthetic portfolio model implies; model interpretations must distinguish those results from economic hypotheses, assumptions and unknowns.

**Product work** improves investigation, presentation, editable scenarios and bounded verification in the existing six-page workstation. **Research questions** concern financial interpretation, competing mechanisms, evidence grounding and the incremental value/cost of revision. A working interface, valid JSON, fluent economics or correct selected mappings does not establish scientific reliability, independent expertise or causal identification.

All experiments below use synthetic portfolio/market data, generally the dated **2025-03-10** snapshot. Live inference means a live model request, not live market ingestion. Historical analogies are qualitative, not portfolio backtests.

## B. Experiment history

Dates below use PDT when execution timestamps establish it. The causal-workflow report supplies a calendar date without an execution timestamp; that date is retained as reported. For v0.2.1 and v0.4/v0.5, dates identify engineering commits; precise inference dates are not reported and are not inferred from those commits. The early ablation ran on **October 27 PDT / October 28 UTC**. Call counts are unique requests within each entry, not sums of conditions sharing dependencies. Unknown metadata is explicitly unavailable; reasoning tokens are included in completion tokens.

### 2026-10-27 (commit date) — v0.2.1 structured-output diagnosis (engineering validation)

- **Question/setup:** why did a successful Meta HTTP request fail interpretation validation? `muse-spark-1.3`, existing adapter and Broad Risk-Off workflow. The [README diagnosis](../README.md#v021-structured-output-diagnosis) records an HTTP 200 response ending with `finish_reason=length`: partial JSON, not a Markdown wrapper or authentication failure.
- **Cases/calls/findings:** one reproduced failure and one corrected live workflow are documented there; a full integration-call census, usage and latency are not reported. The 3,000-token completion budget included reasoning and was exhausted. A subsequent request validated with an 8,000-token budget and API-level JSON schema.
- **Limits/decision:** structural success does not verify financial content. Retain categorized safe diagnostics, strict schema/evidence validation and explicit errors without demonstration fallback. This is a transport correction, not an experiment showing better financial reasoning.
- **Provenance:** [implementation commit](../../../commit/8b70353342f973be6767437e750b6c70d8447442).

### 2026-10-27 — v0.3 Full Context versus Evidence Only, initial pair

- **Question/setup:** can the model synthesize portfolio risk without prewritten economic interpretations? One Broad Risk-Off case, two conditions, **2 successful live calls**, A then B at 19:14 PDT. `muse-spark-1.3`, temperature 0.2, completion budget 8,000, same question/schema/system prompt. B removes five narrative fields while retaining quantitative evidence, historical facts/references and conventions.
- **Observed:** both identify credit/equity losses exceeding duration gains; daily loss −$560,770 and stress loss −$3,347,000 remain distinct. B mislabels HY net −$872,500 as spread loss (spread-only is −$1,112,500; rates add +$240,000) and calls first-order CS01 second-order. Historical support is weaker than valid reference IDs imply.
- **Cost/failures:** no execution errors. A uses 9,400 prompt + 5,659 completion tokens; B 9,241 + 5,478. Latency is not tabulated in the report.
- **Interpretation/decision:** no clear deterioration in the central synthesis after removing these narratives, but no overall ranking or proof of independent reasoning. Keep the minimal context mode; allow only the explicitly requested reverse-order replication. One scenario/sample per condition, common prompt cues and selected history confound interpretation.
- **Provenance:** [report, initial-pair sections](financial-reasoning-ablation.md#initial-pair-observations-from-the-recorded-responses); [commit](../../../commit/8ceb3154219997425c43609659296344efd2d469).

### 2026-10-27 — v0.3 reverse-order replication; ablation stopped

- **Question/setup:** do principal findings persist with B then A? Same one case, **2 new successful calls** at 19:24 PDT; exact corresponding contexts, question, settings, schema and numerical-input hashes checked against the initial pair. Four calls across the entire two-pair ablation; no retries.
- **Observed:** principal risks, totals and relevant qualitative analogies remain stable. Replication B does not repeat the HY label error, but omits the disputed aggregate amount; this is not demonstrated repair. B repeats second-order terminology and gives overlapping/incomplete DV01 components. A incorrectly makes positive rates P&L contingent on other factors not moving adversely; rates contribution and portfolio profitability are distinct.
- **Cost/failures:** B 9,241 + 5,053 tokens; A 9,400 + 3,703. No execution failures; latency not tabulated. Both pass structural validation despite financial issues.
- **Interpretation/decision:** useful synthesis without the five narratives is observed across four samples; neither condition is uniformly correct. No causal execution-order effect or statistical superiority is established. **Stop after this second pair; do not resume the ablation by default.**
- **Provenance:** [replication and final conclusions](financial-reasoning-ablation.md#reverse-order-replication-verified-controls-and-metadata); [commit](../../../commit/222903964d38313b5ac5ac84cfc127080b9fd02e).

### 2026-10-27 (commit dates) — v0.4/v0.5 investigation and financial judgment (product validation)

- **Question/setup:** can the workstation carry users from loss attribution to interpretation, scenario exploration and evidence-led investigation? The README documents daily/Broad Risk-Off live checks with `muse-spark-1.3` in each milestone. These are workflow checks, not new ablation conditions; v0.5 retains provider settings and data.
- **Cases/calls:** two documented live interpretations in v0.4 and two in v0.5. Complete attempt counts, token usage and latency are not reported; do not infer a full call census from the successful examples.
- **Observed/failures:** v0.4 keeps earlier response evidence attached when current shocks change (−$3,347,000 retained while current stress becomes −$3,604,800). v0.5 prioritizes executive judgment, measured losses and conditional investigation guides; an initial ordering preamble prompted a presentation/prompt clarification. The documented stress response distinguishes HY net/spread and rates contribution/total result correctly.
- **Limits/decision:** keep these product improvements for the demonstration; topic guides and priority wording do not verify every model claim or rank unmeasured losses. No evidence of general reliability or reopening of the ablation.
- **Provenance:** [v0.4 walkthrough](../README.md#v04-investigation-walkthrough), [commit](../../../commit/e880818fe99aa76e7f5c10198df4c1dcb78b1e23); [v0.5 judgment](../README.md#v05-financial-judgment-and-investigation-priorities), [commit](../../../commit/3a8f4819e53618884be7d1515aa41a1da0e565be).

### 2026-10-28 (report date) — v0.6 Causal Exploration workflow

- **Question/setup:** can two economic hypotheses explain the same yield move with different cross-asset consequences? **2 live requests**, each returning a pair: recession/inflation relief and liquidity stress/custom supply normalization. `muse-spark-1.3`, temperature 0.2, completion budget 8,000; common hypothetical −50bp yield anchor, editable uncalibrated shocks and deterministic calculations after acceptance.
- **Observed:** first pair totals −$29,500 / +$3,948,500. Editing recession equities from −6% to −8% clears stale results and yields −$489,500, reproduced in Independent Shocks. Second pair totals −$309,500 / +$3,698,500. All requests pass structure/evidence validation on first attempt.
- **Unexpected behavior/limits:** liquidity explanation underdevelops forced Treasury selling and rising yields, compressing cash demand and haven buying into a falling-yield story. Sign-consistent structure does not ensure complete economic mechanisms. Magnitudes are assumptions, not calibrated causal effects. Usage/latency are not tabulated.
- **Decision:** preserve accepted-assumption/engine separation and editable workflow. Treat competing-channel omissions as research questions, not a reason to assert the opposite mechanism. No benchmark or further ablation authorized.
- **Provenance:** [focused report](causal-exploration.md); [commit](../../../commit/e572ac3bc9388d765019a51f9362bb71e767e522).

### 2026-10-28 — v0.6 guided competing liquidity mechanisms

- **Question/setup:** explain explicitly supplied flight-to-safety and forced-liquidation mechanisms, coexistence and distinguishing evidence. **1 successful request returning both mechanisms**, 01:22 PDT. Same Muse Spark model, temperature 0.2, budget 8,000, strict causal schema; research-only prompt bypasses the application's shared-yield constraint. Only rates differ (−50/+50bp); IG +60bp, HY +150bp, equities −6%, EUR/USD −1.5% remain fixed.
- **Observed:** plausible conditional mechanisms and relevant diagnostics; exact shocks copied correctly. Engine totals −$309,500 / −$5,465,500 differ by −$5,156,000, a linear DV01 comparison, **not an estimated causal effect**. The model was instructed not to calculate P&L; engine accuracy is not model arithmetic evidence.
- **Cost/failures:** 7,871 prompt + 6,099 completion = 13,970 tokens; execution 08:22:01–08:22:22 UTC. No retries/fallback/errors.
- **Limits/decision:** mechanisms, signs and diagnostic examples were supplied. CS01 does not establish default/liquidity sensitivity; diagnostics lack identifying thresholds and some basis/tenor detail. Evidence supports prompted synthesis only. Stop after this pair; preserve application architecture and original yield-anchor behavior.
- **Provenance:** [report](liquidity-causal-mechanisms.md); [commit](../../../commit/be57a500037491c9807c71ae6785b41aeb4a1d87).

### 2026-10-28 — unguided liquidity-crisis reasoning

- **Question/setup:** will mechanisms appear without explicit labels or indirect prompt leakage? **1 successful live call**, 05:42 PDT, same model/temperature/budget. Neutral research system and existing interpretation schema; retains factual positions, levels and sensitivity conventions, excludes history, daily moves, scenario assumptions/labels and competing-mechanism instructions. Complete request audited before inference.
- **Observed:** volunteers both safety buying and cash-driven Treasury sales, phase/policy dependence, relevant diagnostics and cross-market implications. Rounded numerical illustrations match engine components. Neither mechanism required explicit naming in this particular completion. The $6m cash description as a limited buffer remains unsupported without contractual liquidity/funding information.
- **Cost/failures:** 2,558 + 3,613 = 6,171 tokens; execution 12:42:32–12:42:48 UTC. No retries/errors. No numerical inconsistency found; generic historical archetypes are not empirical evidence.
- **Limits/decision:** context/system/schema differ from the guided run, intentionally removing cues. One response cannot isolate prompting effects, establish reliable mechanism discovery or separate pretrained narratives from independent reasoning. Keep this as research-only evidence; stop after one response with no feature change.
- **Provenance:** [report and leakage audit](unguided-causal-reasoning.md); [commit](../../../commit/e8ce6fb607719bb7121c560f73ad2aaa73de81b4).

### 2026-10-28 — v0.7 bounded financial claim verification

- **Question/setup:** which explicit financial assertions can be checked against authoritative engine snapshots without another LLM? **14 fixed mappings** manually reviewed, including three reproducible demonstrations. Local verifier makes **0 model calls**. Integration report separately documents **3 daily live attempts + 1 causal request** with `muse-spark-1.3`, temperature 0.2, completion budget 8,000.
- **Observed/failures:** initial daily response uses unknown `kind=value`, correctly left Not checked; a later six-claim response truncates visibly. Supported schema labels and a three-claim cap yield a successful final daily response with three Verified mappings. Separate causal workflow still succeeds. Unsupported cash adequacy is Not established; a deliberately mismapped profitable sentence has a Verified negative-P&L mapping while original wording remains Not checked.
- **Cost:** deterministic checks require no inference; integration usage/latency are not tabulated. These documented integration calls are separate from the earlier v0.6 cases and do not expand their research samples.
- **Limits/decision:** retain bounded claims, explicit precision/coverage, authoritative backend truth and original prose. Never label an entire answer verified. Model-selected omissions and statement/mapping disagreement remain; unmodeled loss is unknown, not zero. No semantic extraction or automatic prose repair was implemented.
- **Provenance:** [verification scope and observations](financial-claim-verification.md); [commit](../../../commit/ce789293083f25ba9cf331b7240373604a1020a3).

### 2026-10-28 — v0.8 independent observer and revision

- **Question/setup:** does observer feedback plus revision add financial corrections beyond deterministic annotations? **10 frozen cases, 40 successful unique live calls**, 07:36–07:43 PDT. Model `muse-spark-1.3`, temperature 0.2, completion budget 8,000, 60s timeout. A original; B same prose plus verifier; C original + observer + revision; D same original/observer + revision also receiving verifier findings. Expectations fixed before inference; manual review, no LLM judge.
- **Observed:** A/B have material financial errors in 3 cases; C/D in 1. C/D correct 05's MTM-as-cash-cover inference and 07's all-duration-positions-benefit claim despite negative pay-fixed DV01. They miss 09's marks/sensitivities conflation and unsupported issuer concentration; 04/10 omissions remain. Three objections across two cases are all accepted; no demonstrated rejection of wholly false advice. No new material regressions identified across 20 revisions.
- **Cost/failures:** 385,680 unique reported tokens; 391.364s wall time; no failed/truncated inference or retries. Per ten-case dependency: A/B 10 shared calls, 100,177 tokens; C 30 calls, 281,595; D 30 calls, 288,888. These rows share dependencies and must not be summed. Preflight import-path collection failure was corrected before live inference.
- **Limits/decision:** no verifier-plus-revision-only control; revision, feedback and extra calls are confounded. Same Muse Spark model in every role; separate calls are not independent expertise. Ten non-blinded synthetic cases do not measure reliability. **Do not integrate an always-on observer.** Stop this study; consider simpler correction approaches only under a new explicit research scope.
- **Provenance:** [report](observer-experiment.md), [frozen cases](observer-cases.json); [commit](../../../commit/4393e1555773eb7ca8896fd18824f93b573bed76). Private archive: ignored `research/runs/observer-v08-20261028/`.

### 2026-10-28 — v0.9 self-review versus archived observer revision

- **Question/setup:** can one extra self-review call match the practical benefit of two extra observer/revision calls? Reuses all **10 exact v0.8 originals and C revisions**, without regenerating them. New B gets only original question/facts/explanation plus a frozen generic self-review instruction and minimal change-account field. Same model/settings as v0.8, no observer/verifier/expected-answer feedback.
- **Calls/failure:** **10 new attempts, 9 valid responses** at 11:42–11:45 PDT. Case **07 times out after 60.056s**; no retry or replacement. Its quality is unavailable, not a successful correction or a financial error. Preflight interactive import failed before inference; documented script invocation works. All 73 original archive files remain unchanged.
- **Observed:** on the matched nine, B/C both correct 05 and leave 09's material error and unsupported conclusion. Both retain 04/10 coverage omissions; no new material regressions observed in B's nine outputs. B improves 02's summary clarity but this is not a material repair under the fixed criteria. Full-ten equivalence is untested: archived C corrects 07, whose B answer is missing.
- **Cost:** new requests report 60,031 prompt + 37,982 completion = **98,013 tokens plus unknown timeout usage**; 208.106 summed request seconds / 208.196 wall seconds. Matched-nine additional stages: self-review 9 calls / 98,013 tokens / 148.050s; observer+revision 18 calls / 160,169 tokens / 151.887s. About 39% fewer additional reported tokens and half the calls, but similar latency. Full-ten B dependency latency is longer because of the timeout; no monetary saving is established.
- **Limits/decision:** archived/new runs differ in time, instructions, feedback and stochastic output. This is a practical comparison, not the causal effect of independent observation. **Neither approach yet justifies trusted workflow integration.** Self-review is the lower-call future candidate, not proven sufficient; no incremental material observer benefit is observed on the matched nine, with 07 unresolved. Stop after the ten attempts.
- **Provenance:** [report](self-review-vs-observer.md); [commit](../../../commit/8dac3287966f8fd2fd5becec75ec297564d55467). Private records: ignored `research/runs/self-review-v09-20261028/`.

### 2026-10-28 — v1.0 evidence-grounded initial explanations; keep baseline

- **Question/setup:** do seven concise grounding rules improve initial explanations over the exact current production prompt? Ten fresh isolated synthetic fixtures; identical evidence/calculations and `Interpretation` schema, A then B, `muse-spark-1.3` at `https://api.meta.ai/v1/chat/completions`, temperature 0.2, completion budget 8,000, 60s timeout. Expectations and source/input hashes frozen before inference; manual financial review, no observer/self-review or LLM judge.
- **Calls/failures:** 20 attempts at 15:37–15:45 PDT; A 8 valid / 2 truncated, B 6 valid / 4 truncated. Failures A05/A08/B05/B06/B07/B10 all reach the token cap; no timeouts, retries, substitutions or further inference. Only five complete pairs. Preflight fixture-test/dotenv errors and an authorization-review rejection were resolved before requests; they are distinct from inference failures.
- **Findings:** B qualifies 03's unsupported gross-margin-flow inference, but omits 02's explicit missing-hedge-objective distinction and asserts unsupported CS01/default underestimation. In unpaired 08B, correct numerical results coexist with reversed USD/EUR economics and unsupported margin-over-mark language. Available supported-data responses retain useful scoped conclusions; A already handles 07's funding coverage, 09's mandate and 10's current exposure. No clear net B financial improvement demonstrated; incomplete pairs limit comparison.
- **Checks/cost:** research-only typed evidence gates distinguish facts, conditional hypotheses and unsupported assertions; manually mapped supplemental funding/default/concentration/hedge/current-exposure results can be supported without claiming prose verification. Production mappings still miss scope/semantics. A 117,275 tokens / 230.682 request seconds; B 123,330 / 240.562; total 240,605 / 471.244 (471.333s wall), including 80,106 tokens in failed requests. All usage captured; reasoning included in completion. No monetary-cost or statistical-reliability inference.
- **Decision/limits:** **Keep baseline**; no production prompt, verifier, engine or UI integration. Prototype remains research-only; legal/completeness assumptions and some unreconciled replacement-cost/book-mark inputs limit its scope. Stop after the paired evaluation. This narrows the proposed grounding-instruction hypothesis without rewriting earlier findings or authorizing backlog work.
- **Provenance:** [detailed report](evidence-grounded-reasoning.md), [fresh cases](evidence-grounded-cases.json), [runner](evidence_grounded_experiment.py), [bounded prototype](evidence_grounding.py). Private records: ignored `research/runs/evidence-grounded-v10-20261028/`. Validation: 135 backend / 12 frontend tests and production build pass; prior reports preserved. The v1.0 commit containing this entry provides its Git provenance.

### 2026-10-28 — v1.1 inference reliability and demo readiness; baseline preserved

- **Diagnosis/setup:** v1.0 truncations average 7,546.7/8,000 reasoning tokens with overlapping failed/valid prompt sizes; no private reasoning trace is inferred. Option A only: compact presentation suffix, unchanged production baseline instructions, full context, schema, `muse-spark-1.3` / Meta chat-completions, temperature 0.2, 8,000 completion budget, 60s timeout and model-set reasoning effort. Four representative production questions, frozen expectations/settings/hashes, A then B once; explicit reliability comparison, not reopening earlier studies.
- **Results/cost:** eight paired calls all complete (4/4 each), no truncations/timeouts/retries. A 65,010 tokens / 69.331 request seconds; B 66,858 / 64.316. B serialized responses 32.7% smaller but completion tokens 5.9% higher; fewer words do not establish reliability. Correct core arithmetic coexists with unsupported undersizing/default language and economic wording errors. No LLM judge or statistical claim.
- **Decision:** preserve production baseline under predeclared rule: no observed completeness gain, so compactness alone does not justify integration. No budget, effort or context-reduction follow-up is added; production behavior unchanged.
- **Actual workstation checks:** three further live UI requests (daily, Broad Risk-Off, Causal Exploration) all complete; 44,895 tokens / 50.722s. Total **11** new calls / **176,763** reported tokens, below12; no retries. Live labels, executive conclusions, deterministic verdict evidence, explicit editable causal assumptions, stale-result invalidation and Independent Shocks replay verified. Accepted causal totals −$393,000/+ $3,948,500; edited A −$853,000 reproduced. Simulated local502 adds no answer or Meta call, with no demo fallback.
- **Failures/limits:** research-host concurrent filename capture caused a local500 during first acceptance; fixed and regression-tested, then calculation checks repeated without inference. Static404 handling fixed too; prior records preserved. Live scenario prose still overstates default losses beyond supplied evidence. These are operational demos with human review, not proof of general financial correctness or reliability; v1.0 truncation risk remains.
- **Provenance/validation:** [report](inference-reliability.md), [paired runner](inference_reliability.py), [bounded temporary host](demo_readiness_host.py); ignored `research/runs/inference-reliability-v11-20261028/`. 138 backend / 12 frontend tests, production build and integration checks pass; existing warnings remain. Prior reports/data unchanged. Commit containing this entry supplies Git provenance.

## C. Cumulative lessons — observations versus hypotheses

| Topic | Demonstrated observations in these records | Not established / hypothesis requiring another study |
| --- | --- | --- |
| Financial reasoning with Muse Spark | Core risk synthesis often matches engine attribution; component-label, signed-exposure and contribution-versus-total mistakes still occur with valid JSON. | General financial reliability, independent expertise or consistent superiority of a context mode. |
| Competing causal hypotheses | Guided and one leakage-audited unguided response express both safety demand and cash-driven Treasury selling. The generic anchored example underdevelops the second channel. | Reliable spontaneous discovery, identification of the dominant real mechanism or calibrated causal effects. |
| Numerical versus semantic verification | Typed checks detect supported arithmetic/sign/overlap errors. Correct mappings can coexist with misleading prose, absent periods or wrong scenario scope. | That Verified means the original sentence or full explanation is correct. Structured evidence-to-prose checking may help, but is untested. |
| Observer-assisted correction | v0.8 repairs two material issue cases, misses another and important omissions; all objections accepted. | Robust bad-advice rejection, independent expertise, or an observer-only causal advantage over revision alone. |
| Self-review | v0.9 repairs 05 like C on the matched nine, misses 09 and leaves omissions; 07 times out. | Full-ten equivalence, sufficient trust for an optional reviewed-analysis product, or a reliable error-correction rate. |
| Accuracy versus inference cost | More calls can add useful corrections, but leave material misses. Matched-nine self-review uses fewer tokens/calls with similar latency; timeout usage is unknown. | Proportional latency reduction, monetary ROI or a cost-optimal model/architecture. |
| Evidence grounding | Citation IDs and model-selected claims do not verify historical scope, cash adequacy, issuer concentration, hedge objectives or causal claims. | That fluent qualifications or no observer objections establish completeness; that missing model coverage proves no real loss. |

These are observations about recorded outputs and manual financial assessments, not evidence about private internal reasoning. Later results narrow earlier optimism without erasing it: v0.9's matched-nine similarity does not negate v0.8's two observed observer repairs; it changes the practical comparison and leaves 07 unanswered.

## D. Open research questions

- Can the model reliably identify unsupported conclusions without explicit prompting?
- Can structured evidence checks identify misleading prose that numeric verification misses, including sentence-to-mapping disagreement and omitted assertions?
- Does specialized financial observation outperform general self-review when criteria, inputs and costs are controlled?
- Can fine-tuning improve financial interpretation and evidence grounding without sacrificing uncertainty handling or introducing regressions?
- Can smaller open-weight models act as cost-effective financial observers, including rejection of incorrect criticism?
- How reliably can AI distinguish competing economic mechanisms and propose evidence that separates confounded explanations?

All remain open. Existing examples motivate them; they do not answer them statistically.

## E. Current engineering decisions — recorded 2026-10-28

- **Keep deterministic financial calculations authoritative.** The model interprets captured evidence; it does not replace the engine or estimate omitted funding/default/liquidity losses.
- **Preserve bounded claim verification.** Show supported mapping verdicts and explicit scope limits alongside original prose; do not imply semantic verification or silently repair answers.
- **Do not integrate an always-on observer yet.** v0.8's specific repairs do not justify its cost or establish broad coverage.
- **Do not integrate self-review as a trusted workflow yet.** v0.9 leaves material defects and an important unavailable case; matched-nine parity is insufficient.
- **Avoid unnecessary multi-agent orchestration.** No observed result requires a general agent framework; separate calls to the same model are not independent financial expertise.
- **Favor measurable financial correctness and evidence grounding over architectural complexity.** Predeclare evaluation criteria, retain failures and compare real dependency costs.
- **Preserve the existing Metis application for hackathon demonstration.** Keep live/demo distinctions, explicit errors, accepted editable assumptions, the existing six pages and synthetic-data limitations. Research recommendations do not authorize product changes.

## F. Prioritized candidate experiments — proposals only

No inference, compute provisioning, Modal deployment, training or additional experiment is authorized by this backlog. Proposed budgets below are planning caps, **not measured cost estimates or current service-price quotations**. Any future task must freeze its own data, protocol, criteria, call/compute/stop bounds and access requirements before execution. USD costs are unknown.

| Priority / proposal | Why it matters | Expected resource cost / proposed cap | Result that would justify implementation |
| --- | --- | --- | --- |
| 1. Offline structured evidence/prose alignment check | Cases 05/09 and deliberate mismapping show why numeric verdicts miss misleading prose. Start with existing synthetic statements and manually labeled unsupported/mismatched claims. | Initially 0 live calls; manual labeling and local deterministic prototypes. Any semantic model phase requires separate authorization and a new cap. | Detects defined unsupported/mismapped assertions while leaving ambiguous statements explicitly unresolved; held-out manual review shows no misleading whole-answer Verified label. |
| 2. Frozen targeted general self-review versus specialized financial observer comparison | Resolve signed-exposure/unsupported-evidence gaps, distinguish added feedback from revision, and include erroneous-advice rejection. This must have an explicit new replication/control purpose, not silently resume v0.8/v0.9. | Planning cap 10 new synthetic cases, at most 30 additional calls if originals are reusable; exact arm/dependency plan must be set first. Record timeout usage as unknown when unavailable. | Material repairs beyond the simpler arm on predeclared criteria, no new material regressions in inspected outputs, useful rejection of bad advice, and an explicit token/latency budget acceptable for optional use. |
| 3. Modal-hosted smaller open-weight observer evaluation | Test whether a different, smaller model can provide useful bounded financial criticism more cheaply; hosted Muse Spark calls do not test this. | Access/license and deployment review first; proposed cap 2 GPU-hours and 20 inference requests, plus manual review. Model, hardware, warm-up/loading and actual billing unknown. No hosting is provisioned now. | Useful held-out corrections and calibrated abstention versus false objections at lower measured total cost/latency, including cold starts; no claim of expertise from model size alone. |
| 4. Small LoRA evidence-grounding pilot, potentially on Modal | Test whether training addresses attribution, signed exposure, unsupported conclusions and uncertainty rather than memorizing case wording. Requires a suitable licensed trainable base and separate training data. | Data creation/review dominates; proposed cap one adapter run, 4 GPU-hours and 20 held-out inference requests. Dataset size/hardware feasibility and USD cost must be determined before authorization. | Improvement over the same untuned base on untouched, leakage-audited financial cases, with uncertainty preservation and regression review; beating training examples alone does not justify integration. |

No aggregate score or automatic LLM judge is implied. Fine-tuning and smaller observers are hypotheses, not conclusions or commitments. Do not train on the ten evaluation expectations and then report those same cases as held-out evidence.

## Maintenance and provenance

New entries should record date/timezone, question, frozen model/endpoint/settings/prompts/schema/source hashes, cases and evaluation criteria, successful/failed attempts, actual tokens/latency (including shared dependencies), manual financial findings, limitations, decisions and report/commit links. Record negative results and operational failures. If metadata was not captured, say unavailable rather than reconstructing or inventing it.

Completed detailed reports and private experimental records are historical records. Add a dated correction/disagreement with source references and possible explanations; preserve both old and new findings. Local `research/runs/` records may be necessary for a future authorized comparison but must remain ignored, as must credentials and raw private model responses. If required originals are unavailable, report that and stop dependent work rather than regenerate them silently.

**2026-10-28 documentation task:** created this central log and the root research-maintenance instructions. No model inference, experiment, application change or alteration of prior reports/records was performed. Validation for this task is documentation/source/link and Git-scope review; historical test counts in the linked reports are not new test runs.

### 2026-10-29 — scoped audit corrections (engineering validation; no inference)

- **Scope/observations:** H-2 corrected with provider-aware Demo template selectors and a pre-request guard; custom Meta hypotheses preserved. H-3 corrected with explicit structured-assertion verdict labels and separate unchecked original prose. M-1 not reproduced within the existing documented scope: two rising-rate fixtures and one zero-move control pass numerical/sign checks; falling-yield composites are Contradicted and unknown rising-yield labels are Not checked. Exact external audit fixture unavailable.
- **Decision/limits:** preserve verifier logic and its existing composite vocabulary; no semantic verifier, new research inference or changed financial assumptions. These deterministic observations do not establish model reliability or prose truth. Existing completed research findings remain unchanged.
- **Validation/cost:** 145 backend tests, 16 frontend tests and production build pass. Reported durations: backend 3.67s, frontend 0.388s, Vite build 3.38s; existing warnings remain. Model/settings not exercised or changed; 0 model calls / 0 inference tokens; inference latency not applicable, UI latency unavailable. Mocked Meta adapter coverage only, no live claim.
- **Provenance:** [scoped dispositions, fixtures and evidence](audit-corrections.md), `tests/test_causal.py`, `tests/test_verification.py`, `frontend/tests/causal.test.mjs` and `frontend/tests/interface.test.mjs`; commit containing this entry supplies Git provenance.
