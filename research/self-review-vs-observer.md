# Self-review versus separate observer (v0.9)

## Protocol defined before new inference

This is a practical product comparison using the **exact ten original v0.8 explanations and factual contexts**, and the **already-generated v0.8 condition C revisions**. Originals and observer results are read-only; neither is regenerated. The ten case expectations and the financial-error/unsupported-conclusion/coverage criteria are reused from [v0.8](observer-experiment.md) and its frozen private protocol. In particular, the existing assessments of A and the observer-assisted comparison are not adapted to favor the new self-review result.

- **A — Original:** v0.8 `NN-initial.json`; one original call per case, reused.
- **B — Self-review:** original plus one new `muse-spark-1.3` review-and-revision call per case. No observer feedback or deterministic verdicts are provided.
- **C — Separate observer:** v0.8 initial plus its independent observer and condition C revision, all reused without new calls.

Thus A/B/C dependency costs are one/two/three calls per case. There are exactly **ten new attempts** in this experiment; failures remain failures without retries or prompt changes. Model settings match v0.8: temperature 0.2, completion budget 8,000 (including reasoning), existing 60s HTTP timeout, same configured Meta chat-completions endpoint and no other sampling overrides.

### Exact self-review instruction and schema

The complete new system prompt is v0.8 `INITIAL_SYSTEM` followed by the following instruction and format suffix. Exact expanded text, schema, settings, source hashes, original-record hashes and per-case input hashes are frozen in the new private `protocol.json` **before the first new live call**. The original user question is unchanged, with no case-specific additions.

```text
Review your previous financial explanation carefully. Check its numerical interpretations, signed exposures, economic logic, unsupported conclusions, and important omissions.

Correct material mistakes and qualify conclusions that the evidence cannot establish. Preserve valid conclusions. Do not invent missing information.

Return the revised explanation and a short account of substantive changes. If no correction is justified, preserve the original conclusions.
```

Exact suffix:

```text
Return substantive_changes as at most five short statements of changes; an empty list is allowed if no substantive change is justified. No private chain-of-thought is requested.
```

The response type is `SelfReview(Interpretation)` with only `substantive_changes: list[str]` (maximum five entries) added. The eight existing interpretation fields, including bounded financial claims, remain. The main model's own change account is recorded but **not used as proof that an error was corrected**.

### Input isolation and record integrity

The runner loads the saved original question, context and response; it does not rebuild facts from a new calculation or generate a new original. The only extra model-context key is `original_explanation`. It does not pass observer feedback, verifier verdicts, expected answers, known mistakes, v0.8 grading notes, condition C, or either report. Case expectations are archived for review outside the model inputs. Posthoc deterministic checks are saved separately and never fed into another call.

All files in `research/runs/observer-v08-20261028/` are hashed before and after. New records must be outside that directory. Missing/incompatible source records cause an explicit stop before inference. The implementation is research-only, reusing the existing Meta adapter and v0.8 helpers without changing the frontend, financial engine or production workflow.

### Manual comparison criteria, unchanged from v0.8

Inspect each explanation against its original case expectations, with special attention to 05 (cash versus MTM/liquidity adequacy), 07 (signed duration and joint credit stress) and 09 (missing evidence, marks versus sensitivities and issuer concentration). For all ten cases, record material financial errors, unsupported conclusions, required mechanism coverage, actual corrections and newly introduced errors/omissions. Preserve the v0.8 distinction between material defects and interpretive cautions. Numerical checks use the original authoritative calculation context; economic judgments are manual, not an LLM judge or a claim-mapping score.

Compare calls, prompt/completion/total tokens and seconds using actual dependency costs. Shared original calls are not counted twice in the unique new experiment total. The archived observer and the new self-review use the **same underlying model**. A separate API call does not establish independent expertise. Instructions, available feedback, output schemas, call counts, execution date/order and stochastic variation differ; this design does not isolate the causal effect of independent observation or establish reliability from ten examples.

## Results

### Execution and availability

The frozen run started **2026-10-28 18:42:02 UTC** and finished **18:45:30 UTC**, using `muse-spark-1.3` at `https://api.meta.ai/v1/chat/completions`. Cases ran in order 01–10. Exactly **ten new live requests were attempted: nine valid structured responses and one timeout**. Case 07 timed out after **60.056s**, returning no interpretation or token counters. It was not retried, replaced with demonstration output, or treated as a financial answer. No further inference was performed.

Private records are in `research/runs/self-review-v09-20261028/`, alongside the unchanged v0.8 archive. The new protocol's canonical SHA-256 is `57198aeb86d288ffc4589f8cb366245f2bcb0adee86b07ae19045c5a61b605f9`. All 73 original files match their preflight hashes. The runner, reused helpers, cases, harness and verifier also match the source hashes frozen before inference. All ten saved questions/contexts equal the original question/facts plus that case's exact original explanation. All new record files have mode 0600; both run directories are ignored by Git. Raw explanations are not included in this report.

### Per-case manual financial findings

`F/U` indicates the presence (1) or absence (0) of a material financial error / unsupported material conclusion in the whole response, following the v0.8 criteria. These are case-level flags, not counts of sentences or quality scores. Coverage refers to the predefined economic distinctions, so a response can have complete coverage and still contain an error. `Unavailable` is not a financial failure or an unchanged answer.

| Case | A F/U | B F/U | C F/U | Coverage A → B → C | Verified finding and revision result |
| --- | --- | --- | --- | --- | --- |
| 01 daily attribution | 0/0 | 0/0 | 0/0 | Complete → Complete → Complete | Rates +$412,480, spreads −$407,250, equities −$506,000 and FX −$60,000 sum to −$560,770. B preserves this and explicitly names the pay-fixed swap's −$96,000 drag. No original material error to repair. |
| 02 hedge contribution | 0/0 | 0/0 | 0/0 | Complete → Complete → Complete | B clarifies that +$412,480 includes credit-bond rate gains; Treasury +$145,280 plus net swaps +$128,000 alone is only +$273,280. Credit rates add +$139,200. This removes A/C's summary ambiguity, but their bodies acknowledged credit rates, so the frozen criteria do not count a material repair. No hedge mandate or optimum is established. |
| 03 HY attribution | 0/0 | 0/0 | 0/0 | Complete → Complete → Complete | B preserves A exactly, with no substantive changes claimed. HY rates +$240,000 and spreads −$1,112,500 give net −$872,500. Equity-like/diversification wording retains the same qualification caution as A/C; a conditional co-move does not establish a stable beta. |
| 04 sensitivities | 0/0 | 0/0 | 0/0 | Partial → Partial → Partial | B adds a valid FX delta/mark distinction but still omits the requested disjoint DV01 breakdown: Treasury 18,160 + swaps 16,000 + credit 17,400 = 51,560 USD/bp. Correct aggregate DV01/CS01 and swap mark/notional distinctions do not fill that omission. |
| 05 liquidity | 1/1 | 0/0 | 0/0 | Partial → Complete → Complete | B repairs the central inference that a $6m cash mark provides initial cash/variation-margin cover based on the modeled daily loss. It explicitly separates MTM from cash calls and says adequacy cannot be established. C makes the same material repair and gives more explicit contractual/timing qualifications. F/U in A describe one overlapping issue, not two independent repairs. |
| 06 competing mechanisms | 0/0 | 0/0 | 0/0 | Complete → Complete → Complete | Both opposing Treasury mechanisms, conditional dominance/coexistence and discriminating evidence were already in A and remain in B/C. B's more cautious spillover wording is not counted as a material repair. Some self-reported additions were already present. |
| 07 joint rates/credit | 1/0 | Unavailable | 0/0 | Complete → Unavailable → Complete | A's statement that a rate rally helps all duration positions conflicts with pay-fixed DV01 −$12,000/bp: −50bp produces a **−$600,000** swap loss. Archived C corrects this. B's timeout leaves its ability to correct it unknown. |
| 08 rate-only symmetry | 0/0 | 0/0 | 0/0 | Complete → Complete → Complete | B preserves correct +$2.578m at −50bp and −$2.578m at +50bp, with a −$5.156m difference. Symmetry is a first-order property, not a joint-stress forecast. A/B/C retain a typed claim mapped to the wrong comparison scenario, despite correct prose. |
| 09 missing evidence | 1/1 | 1/1 | 1/1 | Complete → Complete → Complete | B preserves A exactly. Both the market-value/sensitivity conflation and unsupported issuer-concentration assertion survive, as in C. The central refusal to invent default/counterparty loss estimates remains correct. |
| 10 causal identification | 0/0 | 0/0 | 0/0 | Partial → Partial → Partial | B preserves A exactly. It correctly denies causal identification from synthetic co-moves, but does not develop the expected liquidity/positioning alternatives. C also leaves that omission. |

**Case 05 qualification:** B still says that only swaps and the FX forward create variation margin. Given absent financing/contractual information, this is over-absolute; the snapshot does not establish every possible collateral or funding arrangement. Its central conclusion remains explicitly that cash adequacy is unknown. Under the same conservative materiality criteria used in v0.8, this is recorded as a qualification caution, not a newly quantified shortfall or a new material regression. C's netting/collateral/settlement discussion is more explicit. Neither the $6m cash mark nor the derivative MTM arithmetic (+$128,000 swaps −$60,000 FX = +$68,000) establishes available liquidity or an actual net cash receipt.

**Case 07 numerical baseline:** portfolio rates +$2.578m and spreads −$3.6625m give total −$1.0845m. Receive-fixed gains $1.4m while pay-fixed loses $600,000. IG's +$630,000 rate cushion and HY's +$240,000 do not offset their spread losses; net IG is −$807,500 and HY −$1,985,000. C restores signed-position consistency. There is no new B response to assess, and its missing result must not be credited with C's correction or counted as evidence of financial inconsistency.

**Case 09 residual errors:** market values are levels, not first-order rate/spread sensitivities. The explanation groups them with CS01 as sensitivity measures. It also asserts concentrated issuer jump risk for the aggregate IG/HY baskets without issuer breakdowns. Neither the self-review nor the observer-assisted revision repairs either statement. A correct refusal to estimate missing losses therefore coexists with a material financial error and an unsupported conclusion.

### Corrections, omissions and regressions

Across the **same nine cases with available B responses**, A has material errors in two cases (05/09) and unsupported conclusions in two (05/09). B and C each have one case with a material error (09) and one with an unsupported conclusion (09). Coverage improves from six complete / three partial in A to seven complete / two partial in both B and C. Both repair the **one central material liquidity issue** in 05; both leave 04's decomposition and 10's mechanism omissions. No new material error, unsupported conclusion or removal of a required economic distinction was identified in these nine B revisions. This does not mean all wording or claim mappings are correct.

Over all ten archived cases, A has three cases with material errors and C one: C also repairs 07. B has only nine assessable responses, so comparing its one residual error with A's three would misleadingly credit the unavailable case as a repair. Matched-nine parity is evidence of comparable observed financial outcomes on that subset, not proof of full-ten equivalence.

Posthoc typed checks do not replace this manual review. Case 06 still references an absent scenario period; case 08 still maps its second outcome into the first scenario. These are pre-existing scope/coverage defects, shared with C, rather than evidence that correct prose amounts are wrong. No verifier verdicts were supplied to B. Nor are B's short change accounts evidence of actual repairs: 04 still omits a required breakdown despite its account of improved derivative coverage.

### Calls, tokens and latency

The nine successful self-reviews report **60,031 prompt + 37,982 completion = 98,013 total tokens** (completion includes provider reasoning tokens). The timeout reports no usage; any consumed/billed tokens for it are **unknown**, not zero. The ten requests took 208.106 summed request seconds, including the 60.056s timeout; total run wall time was 208.196s. No price or monetary cost is inferred.

Full requested ten-case dependency accounting includes reused originals:

| Approach | Dependency calls | Reported total tokens | Summed request seconds | Availability |
| --- | --- | --- | --- | --- |
| A original | 10 archived successful | 100,177 | 134.221 | 10 explanations |
| B self-review | 10 archived + 10 new attempts | 198,190 known **plus unknown timeout usage** | 342.327 | 9 revisions; 07 unavailable |
| C observer-assisted | 30 archived successful | 281,595 | 313.739 | 10 revisions |

For the **matched nine only (exclude 07 from every condition)**:

| Approach | Dependency calls | Prompt tokens | Completion tokens | Total tokens | Summed request seconds |
| --- | --- | --- | --- | --- | --- |
| A original | 9 | 53,339 | 35,702 | 89,041 | 117.032 |
| B original + self-review | 18 | 113,370 | 73,684 | 187,054 | 265.082 |
| C original + observer + revision | 27 | 167,166 | 82,044 | 249,210 | 268.919 |

The **additional** matched-nine self-review stage uses 9 calls / 98,013 tokens / 148.050s, versus 18 calls / 160,169 tokens / 151.887s for observer plus revision. Self-review uses about **39% fewer additional reported tokens** and half as many additional calls, yet observed latency is similar. Including the common originals, B uses about 25% fewer reported tokens on this subset. Fewer calls did not yield a proportional latency reduction; on all ten attempts the timeout makes B's observed request time longer than archived C's. These are sequential summed durations from different runs, not a controlled service-latency comparison. Provider load, generated lengths, reasoning-token use and stochastic variation are uncontrolled. The matched-nine table excludes the failure only to compare available financial outputs; the full table retains its operational cost.

### Interpretation and recommendation

**Neither approach yet justifies integration as a trusted reviewed-analysis feature.** Self-review is the lower-call candidate if Metis later explores an optional, explicitly qualified review, but this run does not establish that it is sufficient: 07 is unavailable, 09's substantive defects persist and required omissions remain. Do not add either workflow to the workstation on this evidence.

A separate observer showed **no additional material financial benefit on the matched nine** under the predefined criteria, although its liquidity explanation is more explicit. Its archived correction of 07 is useful, but there is no B answer with which to compare it. Consequently the experiment supports testing the simpler approach before paying for observer orchestration, not a claim that an observer has no value or that self-review is equivalent across all cases. Deterministic checks and human financial review remain necessary safeguards; the existing bounded claim verifier does not cover every prose assertion.

These responses demonstrate some financial synthesis and a useful self-correction of MTM versus funding logic. They do not establish independent expertise, general reliability or a causal benefit from either architecture. Both use Muse Spark, and the new self-review starts with the original model's answer in context rather than independent evidence or an independent model.

### Limitations and stopping point

There are ten predefined examples, nine available new revisions, no repetitions and subjective materiality judgments. The missing 07 is especially consequential because it contains a known signed-exposure error. A/C are reused from an earlier run; inference time/order, feedback availability, instructions, response additions and number of calls differ. Temperature 0.2 does not make results deterministic. Financial conclusions remain conditional on a synthetic portfolio and first-order engine with no default, funding or executable-liquidity model. No statistical reliability, prompting causality or observer-only causal effect can be inferred.

The experiment stops after the ten attempts. There is no retry of 07, added case, LLM judge, prompt optimization or workstation integration. The smallest justified future research step, **outside this completed experiment**, is a separately authorized test focused on unresolved signed-exposure and unsupported-evidence statements, with operational failure handling specified in advance. The present results alone do not warrant additional research infrastructure.

### Reproduction and validation

With the original ignored v0.8 records and local Meta environment configuration available, the research-only command is `uv run python research/self_review_experiment.py --output-dir research/runs/NEW-UNUSED-DIRECTORY`. It requires the same endpoint/model and refuses missing source records, overwriting an existing output directory, or writing beneath the original archive. Running it would make ten new calls; **it was run only once for this experiment**. The frozen protocol preserves the exact expanded system prompt, schema and every input hash. Existing case definitions and expectations are unchanged in `observer-cases.json`.

Backend: **125 tests passed**, including record reuse, context isolation/deep copying, absent-source refusal and single-attempt error handling. Frontend: **12 tests passed**. Production build passed, with the existing large-chunk warning; backend retained the existing Starlette/httpx deprecation warning. A preliminary interactive import without the research script directory on `sys.path` failed before any inference; the documented script invocation and tests use the correct path. No production backend, financial calculations, frontend, v0.8 report or source records were changed. Credentials and raw inference files remain ignored and excluded from the commit.
