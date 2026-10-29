# Inference reliability and demo readiness (v1.1)

## Diagnosis from saved v1.0 records

The [v1.0 report](evidence-grounded-reasoning.md) and its ignored private metadata are historical inputs, not a new repetition of that experiment. Six of twenty calls returned `finish_reason=length`, all with 8,000 completion tokens; none timed out. The adapter correctly rejected partial interpretations, retained usage counters and exposed sanitized errors without demonstration fallback.

Failed prompts span 5,210–5,465 tokens; valid prompts 5,205–5,463. Those overlapping ranges do not establish context size as the cause. Truncated completions average 7,546.7 reported reasoning tokens (94.3% of the budget); valid completions average 6,166.4 completion / 4,975 reasoning tokens. In two failures, 7,998/8,000 tokens are reported as reasoning, leaving only two non-reasoning tokens by subtraction. Other failed calls leave 325–1,203 non-reasoning tokens. These counters do not expose a reasoning trace or a complete failed answer.

Valid serialized interpretations span 3,934–6,088 characters, with duplicated totals and date/method caveats across fields. Both conditions for the missing-agreement case (05A/B) fail, but failures also include causal discussion and supported funding/default/current-exposure questions; there is no established question-type failure rate. The plausible mechanism is shared reasoning/visible-output budget exhaustion, sometimes before enough visible JSON can be generated, rather than a demonstrated authentication, parser or input-context-window failure. Repeated visible detail is an opportunity to test, not proof that compactness will solve reasoning-budget consumption.

Meta's [reasoning documentation](https://dev.meta.ai/docs/reasoning) states that reasoning shares the output budget and omission of `reasoning_effort` leaves a model-determined level. Its [Chat Completions parameter documentation](https://dev.meta.ai/docs/protocols/chat-completions#parameters) lists `max_completion_tokens` with a model-dependent default but does not give a pinned Muse Spark maximum there. The [model documentation](https://dev.meta.ai/docs/models#muse-spark) distinguishes a large input context from the requested completion limit. A larger requested budget might leave more visible-output capacity but increase output cost/latency and risk the existing timeout; no larger budget is tested or claimed live-supported here. No temperature or reasoning-effort change is combined with the chosen intervention.

## Frozen intervention and evaluation

**Option A only: compact presentation.** Baseline A is the exact current production `SYSTEM`. B appends only `COMPACT_OUTPUT` from [the research runner](inference_reliability.py), retaining the schema, financial instructions, all factual context and inference settings. The exact suffix is:

```text
Presentation limits: keep the executive summary to two sentences and 55 words; at most three observations of 35 words each; economic interpretation at most 110 words; up to two historical analogies of 35 words each; at most two vulnerabilities of 60 words each, retaining Concern, Why it matters, Available evidence and Next investigation; at most three uncertainty items of 25 words each. State shared synthetic-date and model limitations once, not in every section. Keep up to three existing financial claims with one-sentence statements. Preserve the answer, signed exposures, essential interacting risks and material missing evidence; combine related risks rather than omit them. Do not repeat totals or caveats across fields unnecessarily.
```

Model `muse-spark-1.3`, Meta `/v1/chat/completions`, temperature 0.2, `max_completion_tokens=8000`, strict unchanged `Interpretation` schema, timeout 60s, empty history and unchanged model-determined reasoning effort. No context reduction, budget increase, retry or format fallback. The private preflight records expanded prompts/schema, question/context/source hashes, expectations and decision rule before inference. Four cases run A then B once, maximum eight requests:

1. Exact workstation daily-loss investigation question, using daily shocks. Expected total −$560,770; rates +$412,480, spreads −$407,250, equity −$506,000, FX −$60,000; useful driver/exposure explanation without identified economic cause.
2. Exact workstation selected-scenario question, Broad Risk-Off. Expected total −$3,347,000 versus daily −$560,770; rates +$2,578,000, spreads −$1,975,000, equity −$3,450,000, FX −$500,000. HY spread −$1,112,500 versus net −$872,500.
3. Receive/pay-fixed swaps and hedge interpretation under daily moves. Expected +$224,000 receive, −$96,000 pay, net swaps +$128,000; payer DV01 −$12,000/bp; no unstated mandate/optimum conclusion.
4. Evidence limits under Broad Risk-Off: cash/marks/baskets cannot establish funding adequacy, net counterparty exposure or default loss without relevant agreements, availability, calls/timing, issuer and recovery facts. Spread sensitivity is not default loss.

These deliberately representative production-workflow questions are an explicit reliability comparison, not resumption of the completed v0.3/v0.8/v0.9/v1.0 experiments. Expectations never enter model context. Both conditions receive the full production context; no authoritative calculation is removed. Context includes repeated position/calculation information and the schema appears in both user payload and API response format; these are held constant, not optimized simultaneously.

**Predeclared integration rule:** integrate compact guidance only if B yields more complete adequate responses than A, with no material financial/usefulness regression on available pairs and acceptable token/latency cost. Equal completeness or shorter wording alone is inconclusive: preserve baseline. Review numerical consistency, unsupported conclusions, important risk/missing-evidence coverage and whether the actual question is answered. No LLM judge, quality score or statistical reliability claim.

## Integration-check plan

After the paired run/decision, exercise the actual built workstation through the real FastAPI routes using a loopback-only research test host. Three planned live integration calls: daily interpretation, Broad Risk-Off interpretation, Causal Exploration. Combined planned total **11**, below the user's absolute **12** limit. Verification/scenario acceptance/edit calculations require no model calls. A research-only request guard prevents additional inference; an explicit local simulated 502 checks frontend failure behavior with zero upstream calls. Test-host request/response capture goes only to ignored private records. Existing development servers and production code need not be changed.

## Results and decision

### Paired execution and completeness

The frozen run executed **2026-10-28 17:35:58–17:38:12 PDT** (2026-10-29 00:35:58–00:38:12 UTC), at `https://api.meta.ai/v1/chat/completions`. All **eight requests returned complete, strictly validated responses**: A 4/4 and B 4/4; zero truncations, invalid responses, timeouts or retries. The preflight's canonical SHA-256 is `b03866c16f3fe98f91e97e14182198f5fe6221259bd0c09c444c8649b4cccd20`, source base `a2ce11dd180cc4e8219ce0da767b767999ca00ce`. Full prompts/schema and exact four questions/contexts are frozen there. Source hashes, question/context identities and identical schema/settings were checked after inference.

Records remain in ignored `research/runs/inference-reliability-v11-20261028/`, directory 0700 / private records 0600. These results do not replicate the six failed v1.0 requests: this is a small production-context reliability comparison with different questions and more context (about 10.8k prompt tokens). Success here does not erase historical failures or show that larger context prevents truncation.

### Tokens, size and latency

| Condition | Complete / attempts | Prompt tokens | Completion tokens | Reasoning tokens (included) | Total tokens | Summed request seconds | Serialized response characters |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A baseline | 4 / 4 | 43,181 | 21,829 | 16,678 | 65,010 | 69.331 | 21,648 |
| B compact | 4 / 4 | 43,745 | 23,113 | 19,470 | 66,858 | 64.316 | 14,563 |

Paired wall time: **133.700s**; summed calls **133.647s**. B is **32.7% smaller** by consistent JSON serialization, but uses **5.9% more completion tokens**, **2.8% more total tokens**, and **16.7% more reasoning tokens**. Non-reasoning counters decrease from 5,151 to 3,643 (29.3%); serialization size is not an exact tokenizer or raw-envelope length. Observed B call time is 7.2% lower, without a controlled provider-load or ordering comparison. More reasoning counters do not reveal what the private reasoning contains or establish that the suffix caused the difference.

| Question | A seconds / completion / reasoning | B seconds / completion / reasoning |
| --- | --- | --- |
| Daily loss | 18.617 / 5,756 / 4,471 | 19.235 / 6,618 / 5,689 |
| Broad Risk-Off | 14.351 / 4,243 / 3,073 | 14.738 / 4,803 / 3,941 |
| Signed swaps/hedge | 17.705 / 5,526 / 4,149 | 14.179 / 5,394 / 4,454 |
| Missing evidence | 18.658 / 6,304 / 4,985 | 16.164 / 6,298 / 5,386 |

There is no demonstrated completeness gain and no observed completion-token saving. No monetary cost is estimated. The two arms differ only in the documented presentation suffix, adding 141 prompt tokens per case; temperature, effort omission, budget, timeout and context remain unchanged.

### Manual financial and usefulness review

All eight preserve correct core totals and directional rates-versus-total distinctions. Their 24 model-selected mappings are Verified against backend evidence; this does **not** validate every sentence or omitted claim.

| Case | Adequate core answer / numerical consistency | Unsupported claims, errors and tradeoffs |
| --- | --- | --- |
| 01 daily loss | Both identify equities/spreads overwhelming rates, correct daily total and swap signs. B is easier to scan. | Both call the hedge **undersized** without an objective. A additionally calls HY most intense per bp: IG CS01 is $11,500/bp versus HY $4,450/bp, and IG is also larger per invested dollar. The prescribed larger HY shock does not establish greater per-bp sensitivity. Shorter B omits that statement but is not a reliable correction mechanism. |
| 02 Broad Risk-Off | Both distinguish hypothetical stress from daily and preserve the core rate/spread/net accounting, including an explicit HY position net/spread example. | A claims linear CS01 **understates** default/illiquidity without issuer/recovery evidence. B's phrase about spreads and equities falling together should refer to credit prices: spread shocks widen. B also reduces default-specific investigation detail to general omissions. Compactness preserves the central answer but does not establish better financial quality. |
| 03 signed swaps/hedge | Both correctly give receive +$224,000, pay −$96,000, opposing DV01s and unknown effectiveness without a stated mandate. | No incorrect core arithmetic found. B's hedge-scope phrase should distinguish hedging risk factors from dollar P&L offsets; a rate gain can offset other-factor losses arithmetically. Neither establishes hedge optimality. |
| 04 evidence limits | Both correctly decline to estimate funding adequacy, net counterparty exposure or default loss from marks/CS01 and identify missing terms/data. | B combines concerns more concisely, with less instrument-specific detail. No unjustified withdrawal of a supported monetary conclusion was found; the missing-evidence conclusion is appropriate. Historical citations remain qualitative rather than claim-level validation. |

These assessments use supplied engine evidence and source scope, not an LLM judge or the model's confidence. The compact arm retains the main executive answer, important exposures, economics, material vulnerabilities and structured claims in these samples, but some detailed next-investigation information is compressed. Existing unsupported judgments and economic wording errors remain. No quality advantage is inferred from fewer characters or more Verified selected mappings.

### Integration decision: preserve production baseline

The predeclared criterion requires a completeness improvement, not merely shorter responses. **A and B both complete 4/4**, so the evidence is inconclusive for reliability; B also consumes more completion/total tokens. The compact suffix is **not integrated**. Production `SYSTEM`, model parameters, timeout, schema, context assembly, financial analytics, verification semantics, Causal Exploration and frontend remain unchanged. No larger-budget, reasoning-effort or context-reduction experiment is added after seeing results.

### Actual workstation checks (three further live calls)

The unchanged production build and actual FastAPI routes were exercised through a temporary research-only host at `127.0.0.1:8002`, leaving the user's existing development servers untouched. A persistent pre-dispatch intent ledger permits only three additional inference attempts; restarting the host does not reset it. UI actions, not direct scripted model responses, triggered these calls:

| Live integration action | Complete | Prompt / completion / reasoning / total tokens | Request seconds |
| --- | --- | --- | ---: |
| Overview → Explain the daily loss | Yes | 10,804 / 5,307 / 3,924 / 16,111 | 16.902 |
| Broad Risk-Off → Interpret this scenario | Yes | 10,808 / 6,388 / 5,046 / 17,196 | 19.975 |
| Causal Exploration: recession fears vs inflation relief, shared −50bp | Yes | 7,542 / 4,046 / 2,881 / 11,588 | 13.845 |

**Total new inference: 11 calls**, all complete, no retries; **176,763 total reported tokens** across comparison and integration. The three integrations contribute 44,895 tokens / 50.722 request seconds. The twelfth allowed request was not used. No synthetic failure or deterministic scenario calculation consumes an inference slot.

Verified in the actual interface:

- Daily and stress answers show **LIVE META · muse-spark-1.3**, a readable executive conclusion and their original captured calculations. Daily −$560,770 and stress −$3,347,000 remain distinct. Three selected claims in each integration reasoning answer are Verified using backend paths; original prose remains Not checked.
- The three reproducible verification examples show **Contradicted**, **Verified** and **Not established**, with backend evidence visible. These local checks invoke no model.
- Causal hypotheses show the live badge, explicitly uncalibrated editable assumptions and missing-evidence/alternative-explanation sections. Initial recession shocks are rates −50bp, IG +60bp, HY +180bp, equities −6%, FX −1%; inflation-relief shocks −50/−15/−40/+4/+1. Proposed shocks have no calculated result until explicit acceptance.
- Acceptance yields **−$393,000 / +$3,948,500**. Editing recession equities from −6% to −8% clears **both** displayed results. Reacceptance yields **−$853,000 / +$3,948,500**. Sending accepted A shocks to Independent Shocks reproduces **−$853,000**. Every captured scenario response equals direct `calculate(load_positions(), Shocks(...))`, including position/factor attribution.
- After all three allowed calls, a research-only simulated **502** displays a plainly labeled failure with **no Meta request** and **no demonstration fallback**. It adds no answer; the two prior live answers remain labeled with their original evidence while current controls show the edited stress. This tests frontend handling, not upstream model reliability. Existing mocked adapter tests separately cover actual categorized truncation/network errors.

The live scenario interpretation still asserts defaults would exceed first-order spread losses without issuer/recovery facts, despite its correct principal P&L and selected mappings. Demo functionality therefore passes these checks, but **financial content remains subject to review**; a green transport badge is not a whole-answer financial certification. Causal narratives plausibly distinguish weaker-growth and benign-disinflation channels with conditional FX, relevant diagnostics and uncertainty, not identified actual causes or calibrated magnitudes.

### Resolved test-host failure, validation and limitations

The first acceptance of both causal scenarios exposed a race in the new **research capture middleware**: parallel responses chose the same private output filename, causing one local HTTP 500. A missing static asset also exposed absent HTTP-exception handling in that test host. Both were corrected locally (reserve unique record IDs before awaiting dispatch; handle static HTTP exceptions). A regression test now covers simultaneous scenario requests and static 404. Original records were preserved. The host restarted with its three-call ledger intact, and acceptance/edit/import checks were repeated successfully with **zero additional inference**. No production defect or model failure is claimed from that recording error.

Validation: **138 backend tests**, **12 frontend tests**, production frontend build, live workflow checks and deterministic replay pass. Existing Starlette/httpx deprecation and large-bundle warnings remain. New tests cover representative production contexts, baseline/candidate identity, protocol before dispatch, eight attempts with no retry, existing-directory refusal, persistent integration guard, simulated failure and concurrent calculation capture. Screenshots and full outputs remain local/ignored. Prior reports and data are unchanged; no credentials or generated files are committed. The temporary test host is stopped after checks.

Limits: four fixed-order pairs, one completion per condition, manual non-blinded assessment, unpinned hosted model and uncontrolled latency/reasoning allocation. Compactness guidance is not a hard visible-token reservation or JSON-field enforcement; the schema permits longer content. v1.0 failed response bodies/traces are unavailable, so diagnosis uses counters rather than invented partial-text or private-reasoning detail. No larger completion ceiling was established live, and no causal effect of presentation length, context size or question category is measured. Saved history and selected source narratives can lead economic interpretations. Small successful demo samples do not establish consistency across unseen questions.

**Stopped after one bounded intervention, an inconclusive integration decision and eleven total live requests.** The production baseline is preserved; residual truncation risk and financial-grounding weaknesses remain documented rather than claimed fixed.
