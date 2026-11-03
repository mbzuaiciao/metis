# Issue #10 — Treasury, OTC and cash valuation coverage · 2026-11-03

Engineering/source audit from merged PR #9, `main` at `bc783ab`, on `codex/issue-10-valuation-coverage`. Read AGENTS.md, the research log, Issue #10 and the prior ETF instrument audit before editing. Resume preserves the existing implementation and evidence; no experiment, inference or ETF quote retrieval repeated.

## Completed behavior

All 12 Portfolio rows have an explicit valuation type, status, unit, comparison dates and inspectable basis/source or missing-input explanation. “Starting/Ending valuation” replaces the misleading common close headings. ETF contributions retain a price-return/price-P&L label; the six other rows show unavailable P&L, not zero.

| Rows | Type / unit | Available versus unavailable |
| --- | --- | --- |
| LQD, EUIG, HYG, EUHY, SPY, HEFA | Observed security close / USD per ETF share | Existing cached observations and price P&L unchanged. EUIG/EUHY remain unavailable/ineligible in September 2022. |
| UST10, UST2 | Treasury issue price / USD per $100 face | Verified research identities and dated special-security reference rows available; accepted marketable-bond prices, face amounts, dirty valuations and historical P&L unavailable. |
| IRS-R, IRS-P, FX-EUR | Modeled OTC mark / contractual USD NPV | Complete contracts and consistent dated inputs unavailable; no modeled marks calculated. |
| CASH | Cash balance / USD | $4m illustrative reference balance dated 2026-10-30 is shown separately; actual balances at either comparison date, interest, cash flows and P&L unavailable. |

**Cash decision:** no share/stock quote or $1 numeraire is needed. The $4m remains part of the signed $100m illustrative allocation, without being backfilled into 2022 or treated as evidence of actual balances in October. The dates atop the value columns are requested valuation dates, not claims that a missing value was observed then.

## TreasuryDirect investigation: observations and negative valuation result

Primary evidence checked November 3, 2026:

- [TreasuryDirect historical price form](https://www.treasurydirect.gov/GA-FI/FedInvest/selectSecurityPriceDate): four successful date requests, with returned headings explicitly matching September 12/13, 2022 and October 29/30, 2026. POST `priceDate=YYYY-MM-DD`, `submit=Show Prices`, with a session CSRF token; no tokens/cookies committed. Snapshot date parameters and eight selected reference rows/response SHA-256 hashes are in `backend/metis/data/treasury-coverage.json`. These are public financial source records, not private inference records.
- That service's returned table qualifies its prices: “These prices apply only to market-based Treasury special securities.” Its columns distinguish BUY, SELL and END OF DAY; only the source's literal END OF DAY field is recorded in the research evidence, without using it in calculations. [Today's price page](https://www.treasurydirect.gov/GA-FI/FedInvest/todaySecurityPriceDetail) exposes the same qualification. No assertion that these are tradeable marketable-bond closes or certified clean/dirty prices.
- [Treasury Financial Experience government-investment guidance](https://tfx.treasury.gov/government-investments) describes GAS securities as nonmarketable government-account investments and their FedInvest pricing/transactions. **Interpretation:** the special-security scope cannot silently become evidence of a marketable Treasury close. The retrieved tables did not establish an adequate clean/dirty price, settlement and accrual basis for this portfolio use.
- Official Treasury auction API records verify coupon, original term, original issue date, maturity and semiannual interest frequency for the candidates below. For reopened issues choose the earliest issue record; a later reopening is not a new original issue. Auction prices/accrued interest are tied to auction settlement, not observations for the requested historical dates, and are unused.

| Period / role | Candidate CUSIP and official terms evidence | Coupon | Original term | Issued | Matures | Source EOD references for the two requested dates — unused |
| --- | --- | ---: | --- | --- | --- | --- |
| Sep 2022 / UST10 | [91282CFF3](https://www.treasurydirect.gov/TA_WS/securities/search?cusip=91282CFF3&format=json) | 2.750% | 10-Year | 2022-08-15 | 2032-08-15 | 94.781250 / 94.406250 |
| Sep 2022 / UST2 | [91282CFA4](https://www.treasurydirect.gov/TA_WS/securities/search?cusip=91282CFA4&format=json) | 3.000% | 2-Year | 2022-08-01 | 2024-07-31 | 98.906250 / 98.593750 |
| Oct 2026 / UST10 | [91282CRF0](https://www.treasurydirect.gov/TA_WS/securities/search?cusip=91282CRF0&format=json) | 4.625% | 10-Year | 2026-08-17 | 2036-08-15 | 97.281250 / 97.656250 |
| Oct 2026 / UST2 | [91282CRH6](https://www.treasurydirect.gov/TA_WS/securities/search?cusip=91282CRH6&format=json) | 4.125% | 2-Year | 2026-08-31 | 2028-08-31 | 99.093750 / 99.218750 |

These are **research candidates, not assigned holdings**. All are live with appropriate original terms and roughly corresponding remaining maturity on their respective comparison dates. The 2022 2Y has matured by October 2026; 2026 candidates did not exist in September 2022. The still-live 2022 10Y would have substantially shorter remaining maturity in October 2026. Lifecycle status is necessary but does not establish price coverage or ownership; tests check pre-issue and maturity boundaries. No generic constant-maturity yield is used as a bond price.

**Stopping decision:** no marketable Treasury close or bond P&L is accepted. Evidence is insufficient to map these special-security references to marketable holdings and a defensible accrued-interest/coupon-inclusive change in value. Do not infer face from the old synthetic mark/notional or calculate a duration/yield proxy under an observed-price label. Next step: obtain an actual CUSIP/face amount (or explicitly authorize a representative holding assumption) and documented date-matched marketable clean quotes with settlement/day-count, accrued interest and coupon cash-flow treatment. The UI exposes both the source evidence and this gap.

**Retrieval limitations:** initial sandbox DNS failed; an explicit-network Python request failed certificate verification. System curl then retrieved the form/tables successfully, without disabling TLS verification. The bounded investigation made four successful historical POSTs, five successful form GETs (including initial inspection), and five successful auction queries covering four CUSIPs (including one preliminary CFF3 query). Browser/search requests are additional context, not a complete network-call census. Check date recorded; exact original publication times, vendor methodology, archival vintage revisions and a timed retrieval-latency census are unavailable. Full HTML and session files remain transient under `/tmp`; the tracked evidence is a normalized selected subset with original-response hashes.

## OTC minimum data and smallest next steps

IRS-R/IRS-P retain their receive-/pay-fixed swap identities. Their names, synthetic reference notionals and old DV01 do not specify actual fixed rates, effective/maturity dates, payment schedules/day-count, floating index/reset history, collateral terms, or consistent dated forward and discount curves. [CME's SOFR discounting/price-alignment methodology](https://www.cmegroup.com/trading/interest-rates/files/cme-sofr-discounting-and-pa-transition-whitepaper.pdf) distinguishes forecasting from discounting inputs; a single daily short rate or generic 10Y Treasury yield cannot supply the missing term structures. **Next step:** obtain one actual confirmation and collateral terms, then source matching schedules/resets and forward/discount curves for both dates. No curves were built or claimed to be retrieved.

FX-EUR retains the OTC forward identity. Missing currency-leg amounts/directions, strike, trade/settlement/maturity dates and maturity-matched forwards/discount inputs prevent revaluation. [IMF valuation guidance](https://www.elibrary.imf.org/display/book/9781513579191/ch05.xml) treats a currency forward through its discounted contractual amounts; spot movement times the synthetic mark is not an instrument valuation. **Next step:** obtain the actual confirmation/legs, strike and maturity, then matched forward/discount inputs for both dates. No public ETF close, spot quote or synthetic daily sensitivity is substituted for an observed OTC mark. No hypothetical contracts or generic derivatives pricer added.

Cash next step: retrieve statements for both dates plus flows and interest accruals, and reconcile balances before calculating income or P&L. No actual account data was available in the repository or obtained externally.

## Preservation and validation

The six ETF identity records are structurally identical to merged main; ETF observations and both position/market fixtures plus the September historical dataset are byte-identical. $100m illustrative allocation and every signed row are unchanged. October demo stays −$282,200, March daily −$560,770, and the previous September proxy investigation −$1,496,577.20. Existing research reports and captured follow-up/archival pathways remain unchanged. New valuation metadata enriches the existing Portfolio comparison only; original calculations and provider contexts are not relabeled.

- Backend/research: `.venv/bin/python -m pytest tests research/test_historical_macro_context.py research/test_meaning_alignment.py -q --tb=short` — **203 passed, 3.62s**.
- Frontend: `cd frontend && npm test` — **35 passed, 1.378s runner**. Actual component rendering checks both date pairs, all row types/statuses/units, qualified research references, cash semantics, missing inputs and unavailable P&L.
- Production: `cd frontend && npm run build` — **TypeScript/Vite passed, 3.13s Vite**.
- Preservation byte/structure comparisons against `bc783ab` and `git diff --check` pass. Existing Starlette/httpx deprecation and Vite bundle-size warnings remain. No manual browser check claimed.

**Completion:** valuation meanings, identity/coverage evidence and actionable next steps are now available. Accepted historical numeric coverage remains the existing ETF sleeve only; complete portfolio P&L/total return, Treasury dirty valuations, OTC marks and actual cash histories remain unavailable. This is a documented negative valuation result within Issue #10's stopping rule, not evidence that no free data could ever be obtained. **0 live inference calls / 0 inference tokens**; model/settings unchanged and unexercised; inference latency not applicable, monetary cost unavailable. Offline request census/total validation wall time not tabulated. Commit/push/new PR requested; do not merge.
