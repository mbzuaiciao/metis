# Issue #8: ETF identity, observations and instrument audit · 2026-11-03

Engineering implementation from `main`, branch `codex/issue-8-etf-portfolio`. No inference experiment or repeat of prior investigations. Original market/positions/historical fixtures, completed reports, research inputs and ignored private runs remain unchanged.

## Stage 1: verified identities and comparability

Primary issuer pages were inspected on November 3, 2026. Each page identifies mandate and listing exchange; these are product-identity evidence, not historical quote evidence. The full current fund names and links are stored in `etf-portfolio.json` and exposed in Portfolio.

| Old ID | Ticker / full fund name | Listing / economic scope | Initial USD allocation |
| --- | --- | --- | ---: |
| IG-US | [LQD — iShares iBoxx $ Investment Grade Corporate Bond ETF](https://www.ishares.com/us/products/239566/) | NYSE Arca; USD-denominated IG corporate debt, not restricted by issuer domicile | $15,000,000 |
| IG-EU | [EUIG — iShares Euro Investment Grade Corporate Bond USD Hedged ETF](https://www.ishares.com/us/products/346691/) | Cboe BZX; euro-denominated IG corporate debt, hedged to USD | $9,000,000 |
| HY-US | [HYG — iShares iBoxx $ High Yield Corporate Bond ETF](https://www.ishares.com/us/products/239565/) | NYSE Arca; USD-denominated HY corporate debt | $8,000,000 |
| HY-EU | [EUHY — iShares Euro High Yield Corporate Bond USD Hedged ETF](https://www.ishares.com/us/products/239550/) | Cboe BZX; euro-denominated HY, hedged to USD | $6,000,000 |
| EQ-US | [SPY — State Street SPDR S&P 500 ETF Trust](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy) | NYSE Arca, USD; S&P 500 large-cap US equities | $17,000,000 |
| EQ-DM | [HEFA — iShares Currency Hedged MSCI EAFE ETF](https://www.ishares.com/us/products/259622/) | Cboe BZX; USD-hedged EAFE developed equities (excludes US/Canada) | $9,000,000 |

**Special eligibility:** [Cboe's EUIG listing](https://www.cboe.com/us/equities/listings/listed_products/symbols/EUIG/) states November 6, 2025, distinct from issuer inception November 4. No 2022 EUIG quote exists. [Issuer annual report filed with the SEC](https://www.sec.gov/Archives/edgar/data/930667/000119312526003756/d78463dncsr.htm), “Material Fund changes”, confirms EUHY's November 3, 2025 name/ticker, benchmark and objective changes: previously HYXU / Markit iBoxx Global Developed Markets ex-US High Yield; now Bloomberg Pan-European High Yield (Euro) TR Index Hedged USD. Pre-change prices are ineligible for today's mandate. Older funds' eligibility floors use issuer inception dates, not assertions of first exchange trades; actual exact-date observations are also required. No benchmark returns substituted for ETF observations.

**Engineering decision:** choose illustrative starting market-value allocations rather than units. The six ETF allocations total $64m; remaining signed allocations total $36m: UST10 $18m, UST2 $10m, IRS-R $3m, IRS-P −$0.5m, FX-EUR $1.5m, cash $4m. NAV $100m, allocation weights sum to 100%; ETF weights 15/9/8/6/17/9%. The reference dollars come from the October fixture; for each comparison assume those dollars invested at its starting close. They are neither actual past holdings nor observed October ETF marks. No shares, ETF notionals, actual fund holdings or measured sensitivities invented. Market-value allocation preserves broad dollar structure, not old duration/spread risk: the latter remains unknown for ETFs. No OAS/parallel rate/equity/FX leg is added on top of their observed full price move.

## Retrieved market observations and attribution

Yahoo Finance chart API was reachable with explicit network access after sandbox DNS failed. A one-time local retrieval requested daily bars and dividend/split events for the two exact pairs (10 successful symbol/period requests, 20 closing observations; no failed endpoint requests in that retrieval). URL parameters and original double-precision close fields are stored per observation; no permanent ingestion service or network use at runtime. Stooq returned a browser-verification page and was not used. Browser search access to these CSV/JSON endpoints failed; that did not establish market-data absence. A preliminary Yahoo access check succeeded before the bounded ten-request retrieval (one extra successful check, not a separate observation dataset).

`etf-observations.json` records retrieval at **2026-11-03T18:54:45.089230+00:00**, provider, USD denomination, **unadjusted closing price** basis, source URLs, session-bar timestamps and reported distribution/split events. Yahoo timestamps identify daily session bars at the open (13:30 UTC on these dates), not certified close/publication clocks. Original publication times, trade-level provenance and original-vintage revisions are unavailable. Price differences use full source precision, display prices round to cents and returns to three decimals; per-position P&L rounds to cents before summation. No cross-source certification or inference that vendor precision equals exchange accuracy. EUHY's October 30 close 51.71 also agrees at cents with its issuer page; no claim of independent validation of the other historical pairs.

The requested intervals report no splits or distributions. Regardless, **distributions are excluded** from price returns, and total return is unavailable; adjusted-close fields are deliberately unused. This is not a total-return backtest. A split event, wrong currency/basis, invalid/ambiguous/missing quote or missing provenance makes a contribution unavailable. Only the retrieved pairs are supported, avoiding unverified corporate actions across long gaps.

`price_return = end_close / start_close − 1`; `hypothetical_price_P&L = starting_allocation × price_return`. Units are unnecessary for this market-value-weighted comparison. No rate/spread decomposition, carry, distribution reinvestment, funding, taxes, trading costs, slippage, transactions or currency conversion is included. Currency hedging and its costs affect ETF prices internally, not an invented extra FX leg.

| Ticker | Sep 12 close | Sep 13 close | Sep hypothetical price P&L | Oct 29 close | Oct 30 close | Oct hypothetical price P&L |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LQD | 108.14 | 107.36 | −$108,192.91 | 104.22 | 104.27 | +$7,195.66 |
| EUIG | Unavailable | Unavailable | Unavailable | 49.15 | 49.205 | +$10,071.27 |
| HYG | 76.04 | 74.31 | −$182,009.82 | 77.58 | 77.43 | −$15,468.06 |
| EUHY | Ineligible | Ineligible | Unavailable | 51.83 | 51.71 | −$13,891.89 |
| SPY | 410.97 | 393.10 | −$739,202.17 | 769.36 | 755.72 | −$301,393.70 |
| HEFA | 32.56 | 31.86 | −$193,489.15 | 46.84 | 46.30 | −$103,757.65 |
| Covered subtotal | | | **−$1,222,894.05** | | | **−$417,244.37** |

September covers $49m of allocations; October covers $64m. The other six rows remain unavailable, so neither subtotal is complete portfolio P&L. EUIG/EUHY missing contributions are null, never zero. No SPY substitution for HEFA, no US OAS substitution for euro ETFs. SPY's retrieved −4.348248% differs from the archived S&P index report's −4.32%; different instruments/sources, not a reason to rewrite the archived event. ETF price moves cannot identify macro causes or separate rates from spreads.

## Stage 2: retained instrument types and minimum valuation inputs

These six are valid instrument categories, not uniquely identified priced holdings. Their illustrative allocations remain; no forced conversion to ETFs. All historical instrument P&L is unavailable.

| Row | Minimum missing data | Recommendation |
| --- | --- | --- |
| UST10 | CUSIP/ISIN, coupon, maturity, face amount, settlement date, clean quote provenance, accrued interest/day-count and coupon flows | Identify actual Treasury, then compare dirty prices plus coupon cash flows; “10Y” curve yield is not its price. |
| UST2 | Same bond identifiers, terms, dated prices/accruals and cash flows | Identify actual Treasury; do not infer a particular on-the-run issue. |
| IRS-R | Trade confirmation, notional, fixed rate, effective/maturity dates, schedules/day-count, floating index/reset history, collateral and dated discount/forward curves | Retain receive-fixed OTC swap; revalue both contractual legs and intervening cash flows. |
| IRS-P | Same contract and curve requirements, paying/receiving directions | Retain pay-fixed OTC swap; signed generic DV01 alone cannot establish instrument-level P&L. |
| FX-EUR | Currency amounts/directions, strike, trade/settlement/maturity dates, dated spot/forward points and collateral/discount curves | Retain OTC FX forward; use maturity-matched forward valuation rather than spot return × mark. |
| CASH | Dated account/collateral statements, currency, restricted/available balances, interest accruals and flows | Reconcile balance and income; do not infer funding/liquidity adequacy from illustrative cash. |

## Isolation, incomplete requirements and validation

Portfolio is the primary identified allocation view. Original fixtures remain byte-unchanged. Its expander preserves the October basket demo, daily −$282,200; other calculation/reasoning pages retain explicitly labeled archived baskets. September's existing proxy investigation remains −$1,496,577.20 on March holdings; March daily remains −$560,770. Captured evidence/follow-ups and research records are unchanged. The workstation response adds `etf_portfolio`/`etf_history`; no existing calculation contract or model context is relabeled as observed ETF attribution.

**Limitations/incomplete:** no actual portfolio NAV/units, ETF measured DV01/CS01, total returns, general price history or six remaining valuations. Live AI/scenario risk remains archived synthetic-basket risk; it does not price the new allocation. Two daily comparisons from one secondary vendor establish data availability/arithmetic, not broad reliability, market causality or a complete historical replay. No new provider credentials, dependencies, inference calls, model/settings or paid data access. No production deployment or merge.

Validation: **199 backend/research tests passed (3.67s)**; **34 frontend tests passed (0.779s runner)**; TypeScript/Vite production build passed (**3.19s Vite**). Checks cover exact retrieved dates/known numerical oracles, partial/missing/ineligible observations, incompatible currency/basis, split events, invalid/duplicate quotes, no interpolation, signed allocations/NAV/weights, unavailable measured risk, API separation, real React rendering of sources/audit/coverage, and all previous archival/reasoning tests. `git diff --check` passes. Initial `npm test` from repository root failed because package.json is under frontend; corrected invocation passes. Existing Starlette/httpx deprecation and Vite bundle-size warnings remain. No live model quality claim; **0 live inference calls / 0 tokens**, inference latency not applicable, monetary cost unavailable. Deterministic/mocked request census and overall validation wall time not tabulated.
