# Evidence-grounded initial financial reasoning (v1.0)

## Protocol fixed before live inference

This is a research-only comparison of initial explanations, not an observer/self-review workflow. No production prompt, verifier, analytics, data or frontend changes are proposed by the implementation. Prior reports remain historical records. The weaknesses motivating the test are the [bounded verifier's semantic coverage gap](financial-claim-verification.md), [observer misses and repairs](observer-experiment.md), and [self-review's residual unsupported conclusions and timeout](self-review-vs-observer.md); they are not assumed to generalize.

**A** uses the exact current `metis.reasoning.harness.SYSTEM`. **B** uses that same text with only the following suffix, defined in `evidence_grounded_experiment.py`:

```text
Evidence-grounding discipline: Before concluding, check signed exposures. Distinguish asset marks, risk sensitivities, realized cash flows and contractual collateral needs. CS01 measures spread sensitivity, not default or liquidity loss. Judge hedge success/failure only against a stated objective; a positive hedge contribution need not offset total losses. Do not infer issuer concentration or net counterparty exposure without the relevant position-level, netting and collateral evidence. Separate market movements from proposed causes. When a material conclusion is not established, name the missing evidence and give the strongest useful scoped conclusion the evidence supports. Preserve supported conclusions; avoid blanket caution, repetitive disclaimers and case-specific assumptions.
```

The full expanded A/B prompts, identical `Interpretation` JSON schema and exact questions/contexts are saved in an immutable private preflight protocol before the first call. There is no schema addition or evidence-check instruction in either condition. Both use `muse-spark-1.3`, temperature 0.2, `max_completion_tokens=8000` (reasoning included), 60s HTTP timeout, strict API-level JSON schema, empty conversation history, and the existing Meta adapter. No seed or other sampling overrides. A then B once per case, 01–10; maximum twenty requests, no retries or prompt changes after results. No LLM judge, feedback or answer reuse.

## Ten fresh cases and authoritative calculations

[Fixture definitions](evidence-grounded-cases.json) contain the exact ten questions, isolated positions, shocks, supplemental inputs and predefined financial distinctions. They do not reuse the v0.8/v0.9 questions or outputs. Research CSV-equivalent rows are passed to the unchanged engine; production data is untouched. All amounts are USD. Shock tuples below are government rates / IG / HY in bp, equities / EURUSD in percent. Inputs are synthetic, dated 2026-10-20; only case 06 labels its moves as illustrative observations, not real observations. Others are hypothetical scenarios. Both conditions receive the same factual context without expectations, evaluator notes, prior answers or check verdicts.

| Case / focus | Shocks | Rates | Spreads | Equities | FX | Total engine P&L |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 01 opposing swaps, net negative DV01 | +35/+40/+110/−4/+2 | +161,000 | −344,000 | −280,000 | −60,000 | −523,000 |
| 02 hedge contribution without objective | −25/+30/+90/−7/−1 | +260,000 | −270,000 | −490,000 | +30,000 | −470,000 |
| 03 cash marks versus collateral | +70/+15/+50/−2/+1 | −938,000 | −143,000 | −140,000 | −30,000 | −1,251,000 |
| 04 baskets without issuer detail | +10/+20/+60/−1/0 | −104,000 | −216,000 | −70,000 | 0 | −390,000 |
| 05 missing counterparty agreements | −15/−10/−20/+2/+3 | +156,000 | +74,000 | +140,000 | −90,000 | +280,000 |
| 06 competing causes of synthetic moves | +15/+25/+70/−3/+1 | −126,000 | −217,000 | −210,000 | −30,000 | −583,000 |
| 07 known one-day funding requirements | +20/+10/+30/−2/−1 | −208,000 | −90,000 | −140,000 | +30,000 | −408,000 |
| 08 complete look-through/default scenario | −10/+35/+100/−4/+2 | +104,000 | −307,000 | −280,000 | −60,000 | −543,000 |
| 09 explicit hedge mandate | −40/+20/+60/−8/0 | +416,000 | −180,000 | −560,000 | 0 | −324,000 |
| 10 enforceable current netting sets | +30/+5/+15/−1/−2 | −312,000 | −45,000 | −70,000 | +60,000 | −367,000 |

Predefined distinctions include signed receive/pay-fixed offsets (01), gains versus total and unknown objective (02), marks versus cash requirements (03), missing issuer/default support (04), missing netting/collateral support (05), at least two plausible mechanisms without causal identification (06), and justified scoped conclusions (07–10). The frozen protocol includes every position/factor result, exposure and expectation before inference.

Supported supplemental calculations are separate from first-order market-factor P&L:

- 07: unencumbered cash $1.5m + drawable committed facility $0.4m = $1.9m; exhaustive specified next-day margin $1.1m + other outflows $0.3m = $1.4m. Headroom $0.5m; supports coverage **only for that stated horizon**.
- 08: exhaustive $16m credit look-through has issuer marks $6.4m/$4.8m/$4.8m. Largest share 40% exceeds the supplied 25% policy threshold. A separately specified $6.4m issuer face, 100% default fraction and 35% recovery imply **$4.16m scenario loss**, not a forecast or a CS01-derived default estimate. It is not added to engine spread losses as a combined scenario.
- 09: designated government-bond/receive/pay sleeve gains $80,000; the nonhedge sleeve loses $404,000. Offset 19.80198% misses the stated 25% requirement, without establishing optimal hedge size or general failure across regimes.
- 10: two exhaustive, nonoverlapping enforceable sets give max($1.2m replacement cost − $0.9m eligible collateral, 0) + max(−$0.1m − $0, 0) = **$0.3m current exposure**. This does not establish future exposure or expected default loss.

## Separate bounded evidence-check prototype

`evidence_grounding.py` accepts a human-specified `EvidenceClaim`, outside the production model schema and verifier. It never extracts sentences, assigns semantic equivalence, modifies responses or supplies inference feedback. The production verifier runs unchanged on each returned `financial_claims` list. Experimental mappings are audited separately after prose review; evaluator mappings are not additional model-generated claims.

| Category | Minimum evidence for the supported scope |
| --- | --- |
| Funding/liquidity adequacy | Unencumbered available cash, drawable committed facility, exhaustive contractual margin and other outflows for the same specified horizon. This cash-requirement test does not verify market liquidation capacity. |
| Issuer concentration | Exhaustive issuer-level marks reconciled to the credit positions, denominator and a stated concentration threshold. |
| Counterparty | Exhaustive nonoverlapping current replacement-cost netting sets, enforceability, eligible collateral and a current-exposure scope. No PFE or credit-loss claim supported. |
| Default | Specified issuer face, default fraction, recovery and an explicit issuer-default scenario scope. No probability inferred. |
| Hedge effectiveness | Explicit designated positions, loss-offset objective/threshold and matching scenario engine results. Optimality is unsupported. |
| Established causation | Identification design, exogenous variation, outcomes, confounder controls and uncertainty at minimum. Even if fields are present, the prototype cannot validate identification: expert review remains required. |

A finite scalar fact can be compared with an explicit context path (`Supported fact`/`Contradicted`), without upgrading it into a risk conclusion. An explicitly conditional mapping is a `Conditional hypothesis`, not verified economics or a violation. Acknowledged missing evidence is `Not established`, not a violation. A definitive assertion missing required data is `Not established`. Exact supported scenario conclusions are checked against the corresponding small calculation (`Supported scoped conclusion`/`Contradicted`). Unknown assertions or scope are `Not checked`. Every result keeps original prose **Not checked**. These are typed scope gates/calculations, not arbitrary financial prose verification; human mapping can omit or misrepresent assertions.

## Predefined manual review

For every A/B output inspect material financial errors, definitive unsupported assertions, required distinctions omitted, whether the question is answered, unnecessary weakening of supported conclusions, numerical consistency and costs. Compare factual amounts to the frozen engine/supplemental calculations; do not reward length or caution. Record concrete improvements/regressions, not an aggregate model-quality score. Review bounded-check outcomes separately from prose judgments. Ten synthetic cases, fixed A-before-B order, unpinned hosted model and non-blinded manual review cannot establish statistical reliability or a causal mechanism of improvement.

## Results and decision

### Execution, availability and integrity

The one run completed **2026-10-28 15:37:42–15:45:33 PDT** (22:37:42–22:45:33 UTC), against `https://api.meta.ai/v1/chat/completions`. Exactly **20 requests** were attempted; **14 valid interpretations** and **6 truncations**, with no timeouts, retries, demonstration substitution or subsequent inference. A returned 8/10 valid responses and B 6/10. These are observed availability counts, not reliability estimates.

Failures: **A05, A08; B05, B06, B07, B10**, all categorized `truncated` with `finish_reason=length` at 8,000 completion tokens. Their usage and latency were captured; no partial interpretation was accepted or graded. Both responses are available for only **01, 02, 03, 04 and 09**. A alone is available for 06/07/10; B alone for 08; neither for 05. Missing answers are not correct, incorrect, repaired or needlessly cautious financial answers.

Private records: ignored `research/runs/evidence-grounded-v10-20261028/` (directory 0700, all record files 0600), including immutable protocol, responses/errors, token counters, posthoc production checks, manual findings and separate evidence mappings/probes. No raw output is committed. Frozen protocol canonical SHA-256: `c5f52ce684f97d1d9a09b9436bbe4acfda5a1abb8e17feed94d37536c1ef3866`.

The baseline source commit is `74e589264537ca9cdc855877c17663e2ceb29f19`; the exact A prompt is its unchanged [`SYSTEM`](../backend/metis/reasoning/harness.py), whose complete source file SHA-256 is `8c63a0a457a3b209e2add139ed9b1039ba70af1b61fca22cc156f851492c6da2`. Canonical JSON-string prompt digests are A `32f5e020f386199329f22e81f278881cd12e970b83c72ddd94d4da9268b97259`, B `a0248ecfb25e96208424d65694b835b4f2f4307d82b3e4f3cc7cf3dda1a311a1`. The suffix above is the entire experimental prompt difference. The full strings and schema are in the preflight; both prompts and all frozen source hashes matched after inference. All ten question/context identities and A/B context equality were checked. Expectations stayed outside inputs; no prompt, case or setting changed after results.

### Per-case financial review

This table records substantive findings, not automated grades. Numerical consistency means comparison with frozen position/factor/supplemental results, not verification of every economic sentence. Main-question coverage and unnecessary weakening are assessed separately from structural validation and availability.

| Case | A finding | B finding | Improvement/regression, question coverage and numerical consistency |
| --- | --- | --- | --- |
| 01 opposing swaps | Correct PX +$1,015,000 / RX −$315,000, net DV01 −$4,600/bp, rates +$161,000 and total −$523,000; short-EUR loss is separate. | Same correct signs, separate legs and total. | Both answer fully; no material improvement or withdrawal of supported conclusions. B should attribute net exposure to signed DV01, rather than its loose “notional dominates” wording. |
| 02 missing hedge objective | Correct figures and explicitly states mandate/objective is needed to judge adequacy/size. Summary's “not a rates-hedge failure” is compressed; body supplies the required qualification. | Correct rates +$260,000 / total −$470,000, but omits the explicit missing-objective qualification. It says linear CS01 **understates** jump-to-default and liquidity freeze, an unsupported definitive magnitude relation. | B loses a required economic distinction and introduces an unsupported assertion; A answers more fully. Excluding a channel does not prove its magnitude exceeds a spread approximation. Neither typed numerical verification nor more fluent risk prose resolves that assertion. |
| 03 marks versus calls | Correct figures and central conclusion that cash adequacy is unknown, but says gross notionals **imply large two-way variation-margin flows**, without contracts/netting/timing. | Correct figures and insufficiency conclusion; gross-payment and cross-counterparty mismatch are explicitly possibilities, with missing terms named. | A substantive subsidiary overstatement is qualified in B. Both answer the main question; no arithmetic error found. This is a useful local improvement, not a general correction rate. |
| 04 issuer evidence absent | Correct −$216,000 spreads / −$390,000 total; no issuer concentration or default loss inferred from baskets/CS01. | Same sound central distinction and figures. Two typed claims use absent `daily` scope. | Both answer fully; no material prose gain. B loses verification coverage through mapping, rather than giving false numerical prose. |
| 05 unknown counterparty | Truncated. | Truncated. | No interpretation to assess; unknown-netting/collateral question remains unevaluated in both. No substitution or repair credited. |
| 06 competing causes | Identifies liquidity selling, inflation/term-premium repricing and growth alternatives with missing diagnostics; no cause identified. Correct −$583,000 total. | Truncated. | A answers; B comparison unavailable. A summary loosely says pay-fixed only partly offsets government-bond losses: +$210,000 exceeds the single bond's $105,000 loss, but not all long-rate losses; body correctly includes RX/credit legs. Scope caution, not a wrong total. |
| 07 supported funding conclusion | Correctly states $1.9m covers $1.4m with $0.5m headroom for next day only. | Truncated. | A preserves a genuinely supported scoped conclusion without blanket refusal. B's ability to do so is unknown. Production headroom mapping is outside scope. |
| 08 supported issuer/default conclusions | Truncated. | Correct 40/30/30% shares, policy breach, separate $4.16m default scenario and −$543,000 engine total. **Incorrectly says USD strength hurts a short-EUR forward**: the +2% EUR/USD shock is EUR strength/USD weakness. It also claims funding/margin exposure exceeds marks and that notionals create calls without terms. | B answers the principal issuer/default question and retains its supported scoped conclusions, but has a material FX economic sign error and unsupported funding assertion. These are not paired regressions because A is missing. No false numerical total found. Default-unquantified boilerplate is inconsistent with the separately supplied scenario calculation. |
| 09 stated hedge mandate | Correct sleeve +$80,000 / rest −$404,000, 19.8% below 25%, optimality unknown. | Same correct mandate failure; explicitly gives $101,000 required. | Both answer fully and preserve the supported failure conclusion; no material improvement. A's mapped hedge claim checks portfolio rates, not semantic equivalence to designated-sleeve wording. B's broader-optimality caveat should distinguish the supplied mandate from missing global optimization inputs. |
| 10 supported current exposure | Correct $300,000 current exposure and per-set flooring, distinguished from PFE/expected loss. Ancillary defects: calls gross positive marks unavailable despite supplied swap marks, and describes realized loss as depending on default probability, where that probability belongs to the expectation. Earlier ECL description is correct. | Truncated. | A answers the main scoped question, but these qualification/expected-versus-realized slips should not be hidden. B comparison unavailable. Book-positive swap marks are $0.8m; that is distinct from the independently supplied net replacement-cost sets. |

The strongest paired local benefit is 03's conditional treatment of unmeasured flows. The clearest paired regressions are 02's missing hedge-objective distinction and categorical default/liquidity-understatement language. Cases 01/04/09 show no material improvement. That mixed five-pair evidence does not justify ranking general financial reasoning quality. The current production baseline already includes HY attribution, first-order CS01, disjoint DV01 and hedge-contribution safeguards; this tests incremental instructions against that baseline, **not** against the shorter v0.8 research prompt.

No incorrect engine headline total was identified in the 14 valid responses. That does not establish economic correctness: 08B's FX explanation reverses the economic meaning of an otherwise correctly copied −$60,000 result. Similarly, 10A's expected/realized-loss terminology and available-gross-marks caveat remain defects despite its correct main formula. Important required coverage is missing in 02B; the failed cases cannot be counted as complete. For returned supported-data cases (07A, 08B, 09A/B, 10A), the principal scoped conclusion is not withheld, though boilerplate about missing information sometimes overstates what is unavailable. The omissions, unsupported assertions and ancillary cautions above are manually judged; a stricter classification of borderline wording would not remove the truncations or establish a clear net B benefit.

### Evidence checks evaluated separately

Unchanged production checks return **A: 22 Verified, 2 Not checked**; **B: 15 Verified, 2 Not checked, 1 Not established**, across 24/18 model-selected mappings respectively. These counts cover different available answers and selected assertions, so they are not comparative quality scores.

- 04B maps two true assertions into absent `daily` context: both are Not checked.
- 07A's supported headroom and 10A's supported current exposure use `kind=other`: Not checked by production, not financially false.
- 08B's correct $4.16m specified-issuer loss is Not established by production's `unmeasured_risk` rule: the linear engine excludes default, and that rule does not interpret the supplemental issuer scenario. This is a **scope boundary**, not evidence against the separate arithmetic. The research check supports the typed supplemental calculation; production was not changed.
- 09A's hedge mapping checks the portfolio rate factor's sign, not whether the original wording correctly refers to the designated sleeve. It happens to have the same gain direction; semantic equivalence remains unchecked.

The research audit saves **12 manually selected mappings** from the actual available outputs: six supported scoped conclusions, five Not established and one conditional hypothesis. Examples include 07A's defined funding coverage, 08B's concentration/default calculations, 09A/B's stated mandate failure and 10A's current exposure. Missing evidence flags 03A's gross-flow inference, 02B's default-magnitude assertion and 08B's margin-over-mark inference; acknowledged uncertainty in 04A/06A is also Not established **without being a violation**. A possible gross-payment channel in 03B remains conditional, not falsely rejected. Compound source sentences are copied intact while the mapping covers only the specified assertion; the checker does not establish sentence/mapping equivalence.

A separate posthoc diagnostic set of **23 analyst probes**, not extra financial cases or model calls, exercises six missing-evidence categories in definitive/conditional/unknown stances plus five supported scope calculations: 12 Not established, six conditional hypotheses, five supported scoped conclusions. These are coverage demonstrations, not false-positive/negative rates. Regression tests independently check false amounts, incomplete issuer coverage, unestablished netting, and causation fields that still require expert review.

**Limits:** the prototype cannot discover omitted statements, validate arbitrary prose, detect 08B's FX narrative error, or certify causal identification. Fact equality does not substantiate an attached adequacy assertion. Completeness, legal enforceability, eligible collateral and contractual horizon are assumed synthetic inputs, not independently established facts. The current-exposure calculation does not reconcile each replacement-cost set back to instrument book marks or validate valuations; those supplied bases differ in case 10. Concentration checking reconciles total marks but does not validate real issuer holdings. Conditional classification is a human mapping, not proof the hypothesis is economically sound. This is a small set of typed gates/calculations, not a production semantic verifier.

### Cost, latency and failures

All twenty attempts returned usage metadata, including the six truncations. There is no missing timeout usage in this run. Completion tokens include provider reasoning counters; those must not be added again. No private reasoning trace was requested or inspected.

| Condition | Attempts / valid / truncated | Prompt tokens | Completion tokens | Total reported tokens | Summed request seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| A | 10 / 8 / 2 | 52,488 | 64,787 | 117,275 | 230.682 |
| B | 10 / 6 / 4 | 53,788 | 69,542 | 123,330 | 240.562 |
| Total | 20 / 14 / 6 | 106,276 | 134,329 | 240,605 | 471.244 |

Wall time: **471.333s**. B adds exactly 130 prompt tokens per case and uses 6,055 more reported total tokens overall (about 5.2%), with 9.880s more summed request time. The six failed requests consume **80,106 reported tokens** (A 26,543; B 53,563); they are included, not dropped from costs. For only the same five complete pairs, A uses 55,028 tokens / 99.465s, B 58,181 / 105.245s. This subset excludes missing financial outputs for quality comparison, not from overall attempt costs.

| Case | A status / total tokens / seconds | B status / total tokens / seconds |
| --- | --- | --- |
| 01 | Valid / 10,194 / 17.393 | Valid / 12,809 / 25.698 |
| 02 | Valid / 10,172 / 16.231 | Valid / 9,633 / 13.864 |
| 03 | Valid / 10,556 / 18.024 | Valid / 11,719 / 20.595 |
| 04 | Valid / 13,132 / 28.156 | Valid / 11,083 / 19.837 |
| 05 | Truncated / 13,210 / 28.017 | Truncated / 13,340 / 26.703 |
| 06 | Valid / 12,333 / 21.863 | Truncated / 13,344 / 26.382 |
| 07 | Valid / 11,297 / 25.633 | Truncated / 13,414 / 31.945 |
| 08 | Truncated / 13,333 / 30.242 | Valid / 11,586 / 21.970 |
| 09 | Valid / 10,974 / 19.661 | Valid / 12,937 / 25.251 |
| 10 | Valid / 12,074 / 25.462 | Truncated / 13,465 / 28.317 |

These are sequential timings under uncontrolled hosted-provider conditions, not throughput or monetary-cost estimates. More observed B truncations cannot be attributed causally to the suffix from this fixed-order, single-sample design. The unchanged budget is an operational constraint, and the prompt also asks for compact output; no budget rescue or post-result prompt optimization was attempted.

### Recommendation: Keep baseline

B does **not demonstrate sufficient net benefit** for production integration. Its one clear paired flow qualification coexists with a missing hedge-objective qualification, unsupported default language, an unpaired FX sign error and more unavailable outputs. Supported-data questions are often handled usefully by A already. The bounded research checks expose a useful distinction between absent evidence and supported supplemental calculations, but do not solve selection/mapping omissions or arbitrary financial prose.

Keep the production prompt, verifier, analytics and workstation unchanged. There is no proposed production diff for this experiment. Neither observer/self-review orchestration nor another model/training run follows from these findings. Any later attempt to reduce output pressure or make targeted evidence checks operational needs a separately authorized, predeclared design and evaluation; it is not part of this run.

### Limitations, validation and stopping

Only ten invented fixtures and five complete pairs, fixed A-before-B order, non-blinded manual financial judgments, an unpinned hosted model, and selective failure availability. The fixtures explicitly supply some missing contracts/look-through inputs; they do not establish that actual portfolio data would be complete or legally reliable. Generic schema fields and existing production risk instructions remain cues. Supplemental calculations are deliberately separate from linear P&L; the baseline instruction against calculating new results can conflict with questions asking arithmetic from supplemental inputs, equally in both arms. Book marks and replacement-cost inputs in 10 are not reconciled, limiting any portfolio-wide exposure inference beyond the supplied formula. No result measures statistical reliability, real-market causation or an internal reasoning process.

Validation: **135 backend tests**, **12 frontend tests** and the **production build pass**, with existing Starlette/httpx deprecation and large-bundle warnings. New tests cover fresh fixtures/engine arithmetic, scoped positive/negative checks, conditional versus definitive mappings, pair identity, expectations excluded, protocol written before inference, twenty-call/no-retry bounds and existing-directory refusal. An initial fixture-test filename/setup error was corrected before inference. An interactive dotenv preflight without an explicit path failed before any requests; explicit `.env` loading passed. Automatic approval initially denied external inference because it could not establish authorization; inspection of the user's exact request and synthetic-only payload resolved that rejection before execution. These preflight issues made no live requests and are distinct from the six API truncations.

All frozen implementation/input source hashes and paired identities passed after the run. No production file or prior report was changed; credentials, private outputs and generated artifacts remain excluded. **Stopped after the one twenty-attempt evaluation and manual decision.** No retries, new cases, LLM judge, follow-up inference, production integration or expanded infrastructure.
