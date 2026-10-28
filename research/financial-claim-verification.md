# v0.7 bounded financial claim verification

## Contract and ground truth

The existing Meta interpretation now includes up to three explicit `financial_claims`. Each contains the unchanged original `statement` plus `kind`, `period`, `target`, `metric`, `assertion`, `value`, `rounding` and `components`. The backend returns annotations beside the original interpretation; it does not repair its prose or silently substitute demonstration text. Empty claim lists explicitly mean no claims were checked.

The verifier accepts application-owned calculation snapshots only. `/api/verify-claims` accepts assertions and `Shocks`, rejects extra caller-supplied context/truth, and assembles ground truth through the existing analytics. Normal reasoning uses its captured backend context, not current frontend controls or model-returned calculations. Confidence and valid evidence IDs are not verification. No additional LLM, extraction regex, judge, agent or benchmark is involved.

**Important boundary:** a verdict applies to the **structured assertion**, not semantic equivalence between the mapping and the original sentence. The UI shows original wording as **Not checked**, a separate human-readable mapping/verdict, original structured fields, backend paths/values and limitations. It never labels the whole interpretation verified. A model can omit a statement or map it incorrectly; this implementation does not detect arbitrary prose mistakes. Causal narratives remain Not checked.

## Supported mappings

| Kind | Checks | Limits |
| --- | --- | --- |
| `number` | Equals for total/net P&L, rates, spread-only credit, equity and FX P&L; signed DV01/CS01; portfolio IG/HY CS01. | Daily or selected scenario. Targets: portfolio, explicit position, asset class or IG/HY spread bucket. Group values aggregate existing engine contributions; unavailable target/metric combinations are Not checked. |
| `sign` | Positive, negative or zero for the same quantities. | Direct backend sign; positive DV01/CS01 gains for a 1bp decline. Sign checks do not infer profitability from sensitivity alone. |
| `hedge_vs_total` | Three explicit falling-yield premise combinations: rates loss/total loss, rates gain/total loss, rates gain/total gain. | Checks yield direction, rate contribution and portfolio result. Does not prove the sentence's causal attribution. Evidence also shows other factors and Treasury cash holdings separately. |
| `dv01_decomposition` | Exact portfolio DV01 total from an exhaustive, disjoint list of position/asset-class/bucket components. | Rejects overlapping memberships before summing and rejects missing rate-sensitive positions. No general weighted decomposition, gross exposure or arbitrary risk allocation. |
| `unmeasured_risk` | Funding, margin, liquidity or default losses: verifies only that the linear model does not quantify the channel. | Assertions of loss amount/existence/absence or adequate/inadequate buffers are Not established. Missing data and available cash facts are shown; unmodeled does not mean zero. |
| Unsupported | Unknown kind, period, metric, target, comparison, precision or malformed mapping is Not checked. | No probabilities, causal correctness, historical accuracy, hedge optimality, nonlinear risk, or arbitrary financial prose verification. |

All fields are bounded/typed; numeric values must be finite and within ±1e15. The provider JSON schema restricts kind labels to the supported kinds plus `other`. Unknown string kinds received on other paths deliberately remain Not checked, never normalized into a supported kind.

### Numerical tolerances

No model-defined tolerance or relative-error band is accepted. Decimal comparisons use inclusive absolute tolerances:

| Declared precision | Allowed difference | Additional rule |
| --- | ---: | --- |
| `exact` | 0.01 USD for P&L or 0.01 USD/bp for sensitivity | Cent-sized interoperability tolerance, not mathematical identity. |
| `whole` | 0.5 USD or USD/bp | Claimed value must be an integer. |
| `million_2dp` | 5,000 USD | P&L only; claimed value must be a multiple of 10,000 USD (0.01 million). |

Signs use the actual backend sign without rounding-to-zero tolerance. DV01 decompositions require disjoint/exhaustive coverage and portfolio sum equality, with 0.01 USD/bp tolerance on the asserted value. Unsupported precision is Not checked. A valid rounded result says nothing about economic causation or omitted loss channels.

## Three reproducible demonstrations

Open **Metis AI Reasoning → Financial claim verification · three reproducible examples**. This calls `GET /api/verification-demo` and does not invoke a model.

| Fixed original statement / mapped premises | Verdict | Backend evidence and qualification |
| --- | --- | --- |
| “The portfolio lost money because its Treasury hedge generated losses as yields fell.” Mapped to falling yields, negative rates contribution and total loss. | **Contradicted** | Yields −8bp; government-rate P&L **+$412,480**; daily total **−$560,770**. Treasury cash holdings themselves gained $128,000 and $17,280. The claimed hedge-loss premise fails; no general causal inference is attempted. |
| Rates contributed positively as yields fell, but other losses left a portfolio loss. | **Verified** (mapped premises) | Rates +$412,480; spreads −$407,250; equities −$506,000; FX −$60,000; total −$560,770. Government-rate P&L includes swaps/credit rate legs, not just Treasury holdings. |
| The $6m cash balance is insufficient for funding needs. | **Not established** | Cash is factual; adequacy requires unencumbered balances, funding access, timing and contractual terms. Linear P&L does not establish a shortfall or its absence. |

## Small manual review and observed coverage gaps

Fourteen fixed mappings were reviewed against existing calculations, not a model's opinion. The three above were supplemented with: correct/incorrect total P&L; HY spread versus net attribution; pay-fixed DV01 sign; overlapping/disjoint DV01; an unsupported probability; unquantified funding; a rounded P&L value; and an intentionally mismapped original sentence.

| Additional case | Observed outcome |
| --- | --- |
| Daily −$560,770 versus incorrectly claimed +$560,770 | Verified versus Contradicted. |
| Broad Risk-Off HY spread-only −$872,500 | Contradicted: spread-only is **−$1,112,500**. |
| Broad Risk-Off HY net −$872,500 | Verified: it includes **+$240,000** rates and −$1,112,500 spreads. |
| Pay-fixed swap DV01 is negative | Verified against −$12,000/bp. |
| Portfolio DV01 plus receive-fixed swap as an additive total | Contradicted: IRS-R is counted twice, even if the claimed arithmetic sum is 79,560. |
| Government bonds + rate derivatives + IG + HY DV01 | Verified disjoint total **$51,560/bp**. |
| Unsupported causal probability | Not checked, not treated as a financial calculation. |
| Funding loss is not quantified by this model | Verified; actual funding loss is still unknown. |
| Daily P&L −$0.56m with declared two-decimal-million precision | Verified: $770 difference is within $5,000; broader unsupported tolerances are rejected. |
| Original sentence says portfolio profitable but mapping asserts −$560,770 | Mapping Verified; **original sentence Not checked**. This is an explicit semantic coverage miss, not proof the sentence is correct. |

No unexpected verdict was observed within these typed mappings, but this is not a measured false-positive rate. The deliberate mismapping demonstrates why mapping correctness and omission coverage remain material limitations. A small fixed set cannot establish general reliability.

### Live integration observations

Live validation used the configured `muse-spark-1.3` endpoint `https://api.meta.ai/v1/chat/completions`, temperature 0.2 and completion budget 8,000. This was application validation, not another research ablation.

1. Initial live daily-loss response succeeded but used `kind=value` for five numerical assertions. They were correctly **Not checked** as unknown kinds; one valid hedge mapping was Verified. This was a real coverage miss. The provider schema now restricts supported labels, with a regression test preserving conservative handling of unknown labels.
2. A subsequent six-claim response reached `finish_reason=length`. The interface visibly reported **truncated**, without a demo fallback or partial interpretation. To reduce output pressure, claim count was bounded to three and supporting sections requested compactly; the model/endpoint/token budget were unchanged.
3. The final live daily-loss response succeeded with three supported mappings: total P&L −$560,770, rates gain with total loss as yields declined, and equity P&L −$506,000. All three were Verified with the proper daily evidence. Other prose remained Not checked. In particular, the model's description of the hedge as “undersized” is an unchecked economic judgment about objectives, not a verified hedge-optimality finding.

These are live integration outcomes, separate from deterministic verifier correctness and from financial reasoning quality. Raw private responses and credentials are not committed. The existing Causal Exploration schema remains unchanged and its narratives are explicitly labeled Not checked by this verifier. A separate live causal request also succeeded; after explicit acceptance its A/B assumptions produced −$29,500 / +$3,948,500 through the unchanged engine. This checks preservation of the workflow, not causal correctness.

## Validation and remaining limits

Validation: **115 backend tests, 12 frontend tests and production build pass**. Existing test-client deprecation and large-bundle warnings remain. Deterministic tests cover the correct, contradicted and unsupported cases; sign conventions; spread/net distinctions; additive coverage and overlaps; tolerance boundaries; invalid inputs; source evidence attachment; known evidence IDs not proving truth; context immutability; and original text preservation. Analytics/data and prior research are unchanged. Historical response schemas remain reproducible at their recorded source commits; the current interpretation schema adds `financial_claims`.

The main limitations are model-selected coverage, possible statement/mapping disagreement, only two calculation periods, and a fixed linear model with no quantified funding/liquidity/default losses. Verification is against this synthetic snapshot and its model, not actual market truth. No general prose extraction, natural-language causal verification or quality score is provided. Stop at the three requested reproducible verdicts; broader semantic checking would require a separate design decision.
