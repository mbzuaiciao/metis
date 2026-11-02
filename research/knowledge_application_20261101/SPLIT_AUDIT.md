# Split provenance and structural separation

Both files were newly authored during preparation using financial identities/contracts, without model inference, copied response text or imported prior cases. They are synthetic teaching/evaluation material, not observed investment evidence. Dataset authorship is by the coding assistant, not an independent human financial expert. Human acceptance before later execution remains outstanding.

Training: 60 distinct structures, 15 per domain, 30 sufficient / 30 insufficient. Evaluation: 20 structures, 5 per domain, 10 sufficient / 10 insufficient. Counts are fixed, not random splits of numerical variants. No prior Metis evaluation expectations are used as targets. Held-outs deliberately transfer shared principles into different payoff structures, entity boundaries, time ordering or attribution formulas. Knowledge overlap is necessary for the application hypothesis; structural disjointness is not proof of zero conceptual leakage.

| Held-out IDs | New structure/reasoning | Separation from training |
|---|---|---|
| 01 | Callable liability + nonterminating swap across exercise paths | Training covers mortgage prepayment but not issuer call decisions and surviving swap obligations. |
| 02 | Long call + short put purchase collar, piecewise floor/ceiling | Training uses one-sided fuel cap and FX put; no two-option collar or short-put branch. |
| 03 | CHF→EUR→USD hedge chain, intermediate residual currency | Training has one currency pair per hedge; no triangular contractual flow matching. |
| 04 | Componentwise two-factor residual mandate | Training tests individual delta/vega/beta, not a signed vector with independent limits; correlation is deliberately irrelevant. |
| 05 | Barrier survival and contingent removal of protection | No training barrier/knock-out payoff. |
| 06 | Intraday peak deficit despite positive end-day balance | Training has daily ladders and next-day settlement gaps; no midday inflow masking an earlier same-day deficit. |
| 07 | Accepted collateral substitution before a cutoff releases cash | Training tests collateral borrowing value; no substitution/acceptance workflow. |
| 08 | FX payment-versus-payment gross prefunding | No training settlement-protection versus funding distinction. |
| 09 | Currency-specific collateral eligibility and conversion cutoff | Training concerns capital-controlled offshore cash, not collateral-eligibility rules. |
| 10 | Securitization reserve top-up distribution waterfall | Training has a corporate cash reserve constraint, not existing reserve versus required top-up and residual-holder distribution priority. |
| 11 | Tranche attachment/detachment loss allocation | Training has whole-claim loss and senior/junior estate recovery, not tranche thresholds on a pool-loss axis. |
| 12 | Cross-default threshold/grace/waiver and acceleration | Training tests a borrower financial covenant, not propagation of another entity's event through contract triggers. |
| 13 | Effective novation releases named original debtor | No training novation/assignment distinction; not a group-wide safety conclusion. |
| 14 | Equal-face restructuring versus discounted economic loss | Training has final principal recovery, not exchanged cash-flow timing/coupon valuation. |
| 15 | Sovereign domestic funds versus external-currency debt service | Training concerns credit PD/LGD/collateral, not sovereign external transfer capacity; currency transfer principles appear only in liquidity training. |
| 16 | Formula-specific Brinson allocation | Training has scalar active return, not sector benchmark-relative weighting with a selection-information distractor. |
| 17 | Multi-period attribution linking | Training has scalar compounding but no reconciliation of monthly active effects to annual compounded active return. |
| 18 | Short-sale dividend liability and borrow fees | Training has long-share dividends; held-out reverses cash-flow ownership and adds stock borrowing. |
| 19 | Private-capital multiple versus dated IRR | Training has flow-distorted NAV growth, not a fully liquidated multiple and an underdetermined annualized IRR. |
| 20 | Buy execution cost versus arrival midpoint, stated limit | Training has realized profit/fee return bridges, not execution-quality benchmarking against an untraded arrival price. |

Prior-case exclusion review: inspected the frozen investigation cases and reports, observer cases, evidence-grounded cases and meaning-alignment cases. Their portfolio snapshot, daily/stress totals, position IDs, CSA/current-mark examples, duration-mandate question, CS01/default question, macro-mechanism explanation and verifier statement matching are not held-out scenarios here. Shared themes such as cash timing, contractual coverage and unjustified magnitude are intentional, not new benchmark independence. No prior text or numeric perturbation of a prior scenario was used. Automated checks additionally compare normalized complete question/evidence strings against prior tracked JSON strings; this catches direct reuse only. This authored structural review does not authenticate unknown pretraining exposure, independently certify semantic novelty, or replace external human review.
