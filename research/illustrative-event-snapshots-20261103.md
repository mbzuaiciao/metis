# Issue #12 — three fixed illustrative event valuations · 2026-11-03

Base: latest merged `main`, `cf659bf` (PR #11). Read AGENTS.md, research memory, Issues #10/#12 and the #8/#10 source/valuation reports. Issue #12 explicitly supersedes the strict unavailable-unless-observable threshold **for illustrative estimates only**. Prior negative findings and actual-data gaps remain valid; their reports and calculation paths are preserved.

## Observations and provenance

Only the requested three windows are supported. New static files hold 24 published market-input values (four series × six dates), eight March ETF closes (four symbols × two dates), and the explicit assumptions/configuration. Runtime calculations perform no retrieval.

| Date | DGS2 % | DGS5 % | DGS10 % | DEXUSEU USD/EUR |
| --- | ---: | ---: | ---: | ---: |
| 2022-09-12 | 3.58 | 3.47 | 3.37 | 1.0129 |
| 2022-09-13 | 3.75 | 3.58 | 3.42 | 0.9997 |
| 2025-03-07 | 3.99 | 4.09 | 4.32 | 1.0859 |
| 2025-03-10 | 3.89 | 3.98 | 4.22 | 1.0837 |
| 2026-10-29 | 4.61 | 4.78 | 4.98 | 1.1165 |
| 2026-10-30 | 4.56 | 4.71 | 4.94 | 1.1163 |

Sources: Federal Reserve Board H.15/H.10 via FRED — [DGS2](https://fred.stlouisfed.org/series/DGS2), [DGS5](https://fred.stlouisfed.org/series/DGS5), [DGS10](https://fred.stlouisfed.org/series/DGS10), [DEXUSEU](https://fred.stlouisfed.org/series/DEXUSEU). Exact [CSV request](https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2,DGS5,DGS10,DEXUSEU&cosd=2022-09-12&coed=2026-10-30) and per-series source URLs are recorded in `event-market-observations.json`; download completion **2026-11-03T19:50:31.901003Z**. The response included broader series history despite the date parameters; only these six dates/24 values were retained. DGS figures are published daily constant-maturity curve yields, not bond or swap quotes. EUR/USD is the New York noon buying rate, asynchronous with ETF closes. Retrieved vintage; original publication clocks and vintage revisions are unavailable. A direct Treasury XML request timed out after 20 seconds; FRED succeeded. This does not establish unavailability of official Treasury data.

March ETF unadjusted USD closes: LQD **108.31999969482422 → 108.69000244140625**, HYG **79.44999694824219 → 79.1500015258789**, SPY **575.9199829101562 → 560.5800170898438**, HEFA **37.27000045776367 → 36.41999816894531**. Four Yahoo chart requests, eight bars, retrieved **2026-11-03T19:50:44.442086Z**, stored separately in `event-etf-observations.json`. Example [exact SPY request](https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1=1741305600&period2=1741651200&interval=1d&events=div%2Csplits); the file records all URLs/session-bar timestamps and reported corporate actions. No splits/distributions reported for the pair. September/October reuse the unchanged prior cache; no re-retrieval or relabeling. Unadjusted price returns exclude distributions, even where no event is reported: not a total-return backtest. Vendor bar clocks are not certified close/publication times; no independent exchange/original-vintage certification.

## Hypothetical assumptions and derived valuations

All start values are the unchanged October **illustrative signed market-value allocations**, reapplied at each event's starting date: UST10 $18m, UST2 $10m, IRS-R $3m, IRS-P −$0.5m, LQD $15m, EUIG $9m, HYG $8m, EUHY $6m, SPY $17m, HEFA $9m, FX-EUR $1.5m, CASH $4m. Sum **$100m**. They are not evidence of historic ownership or observed NAV. Each ending value = starting value + cents-rounded contribution; portfolio estimate sums those contributions once. Main UI rounds dollar displays to the nearest $1,000 to avoid implying market accuracy (rounded rows may not sum exactly); exact arithmetic in fixtures/tests is reproducible, not a precision claim.

**Eligible ETFs:** `P&L = initial market-value allocation × (end unadjusted close / start unadjusted close − 1)`. All dollar marks are Estimated even when price inputs are Observed. No actual shares are claimed and no extra rate/spread/equity/FX leg is added to an ETF's complete price move. Missing/duplicate/invalid eligible quotes or split events leave that row and the complete portfolio result unavailable, with a covered subtotal only.

**EUIG/EUHY in September 2022 and March 2025:** keep the real identities, but represent explicitly hypothetical exposures to their **current** mandates; these are not historical ETF holdings/prices. EUIG listed November 6, 2025, and EUHY's mandate changed November 3, 2025; predecessor returns cannot fill these gaps. Assumed IG rate/spread durations **6/6 years**, HY **3.5/3.5 years**. Assume **0bp euro rate change** in both windows; euro spread shocks IG/HY **+15/+30bp** in September and **+10/+25bp** in March. Formula `−allocation × (rate duration × rate bp + spread duration × spread bp) / 10,000`. These shocks are invented, uncalibrated demo assumptions, not observed euro spreads or US OAS substitutions. In October use the actual cached eligible ETF price moves instead. Conclusions about these earlier euro contributions are assumption-driven.

**UST10/UST2:** hypothetical constant-maturity exposures, no CUSIP or bond price. Assume modified durations **8.0/1.9 years**; `P&L = −initial USD value × duration × Δyield_decimal`, using DGS10/DGS2. One percentage point = 100bp. No coupon/accrual/carry, convexity or roll-down; duration frozen. No TreasuryDirect special-security data enters these estimates.

**IRS-R/IRS-P:** event-specific fictional USD receive-/pay-fixed contracts transferred at the assumed starting marks. Notionals **$35m/$25m**, tenors **10Y/5Y**, assumed annuities **7.0/4.5 years**, annual fixed ACT/360 versus fictional quarterly compounded-SOFR ACT/360. Maturities are event-start anniversaries adjusted to the following weekday; holidays ignored. Assume no coupon/reset settlement in these short windows. Use DGS10/DGS5 as **approximate par-swap-rate proxies**, not observed swap quotes. No actual forward/discount curve claimed.

Signed `PV01 = direction × notional × annuity / 10,000` = **+$24,500/bp / −$11,250/bp**. These are assumed demo sensitivities, separate from the old archived −$10,000/bp payer sensitivity. Linear mark `V = signed PV01 × (fixed strike bp − proxy par rate bp)`. Set off-market fixed strike `K_bp = starting proxy rate bp + initial signed mark / signed PV01`; this makes $3m/−$0.5m internally coherent **opening NPVs**, not notionals/collateral or par-new-swap values. No transfer/upfront flow occurs within the comparison window. Receive/pay strikes by event are approximately **4.594490%/3.914444%**, **5.544490%/4.534444%**, **6.204490%/5.224444%**. Then `ΔV = −signed PV01 × Δproxy_rate_bp`. Annuities, projection/discount basis and time aging are frozen; no carry/funding/collateral/default/convexity valuation. Contract terms are assumptions, not reconstructed actual confirmations.

**FX-EUR:** fictional long-EUR/short-USD one-year forward transferred at a **$1.5m starting NPV**. Set EUR bought = **$12m reference exposure / starting spot**; actual contractual USD sold = EUR bought × strike, distinct from that reference exposure. Assume equal, frozen EUR/USD discount factors **0.96**, hence **zero forward points** at both dates. Set `K = starting spot − $1.5m / (EUR bought × 0.96)`. Model `NPV = EUR bought × 0.96 × (spot + assumed points − K)`; `ΔNPV = EUR bought × 0.96 × Δspot`. USD sold is $10,437,500 under this calibration. Strikes are about **0.881012 / 0.944507 / 0.971122 USD/EUR**. Forward maturity is one year from window start, following weekday (holidays ignored); calendar aging, changes in discount factors, basis, carry and flows excluded. This is an assumed forward surface, not observed maturity-matched forward pricing.

**CASH:** $4m constant on both dates; explicit **zero net flows / zero interest**. Zero P&L is permitted by this assumption, not a claim to actual account data.

## Reproducible contributions (USD)

| Position | September 2022 | March 2025 | October 2026 |
| --- | ---: | ---: | ---: |
| UST10 | −72,000.00 | +144,000.00 | +57,600.00 |
| UST2 | −32,300.00 | +19,000.00 | +9,500.00 |
| IRS-R | −122,500.00 | +245,000.00 | +98,000.00 |
| IRS-P | +123,750.00 | −123,750.00 | −78,750.00 |
| LQD | −108,192.91 | +51,237.46 | +7,195.66 |
| EUIG | −81,000.00 | −54,000.00 | +10,071.27 |
| HYG | −182,009.82 | −30,207.22 | −15,468.06 |
| EUHY | −63,000.00 | −52,500.00 | −13,891.89 |
| SPY | −739,202.17 | −452,804.95 | −301,393.70 |
| HEFA | −193,489.15 | −205,259.47 | −103,757.65 |
| FX-EUR | −150,127.36 | −23,339.17 | −2,063.59 |
| CASH | 0.00 | 0.00 | 0.00 |
| **Estimated portfolio P&L** | **−1,620,071.41** | **−482,623.35** | **−332,957.96** |
| Estimated ending USD value | 98,379,928.59 | 99,517,376.65 | 99,667,042.04 |

## Interpretation, workflow and stopping decision

These are **hypothetical reconstructed/stressed P&L**, not actual historical holdings, observed NAV or complete historical economic returns. Sources/timing differ from archived investigations: e.g. September daily DGS10 +5bp differs from the old intraday/rounded +5.37bp proxy; March's archived scenario is synthetic; October's sourced rates/spot differ from its fictional demonstration. Those prior figures/findings are not corrections to these new estimates and are not overwritten.

Portfolio provides three selectable compact tables with Observed-input/Estimated/Unavailable legend, plus approximate/hypothetical distinctions and row-level methods, units, dates, terms and assumptions. The previous strict observed-price audit and October synthetic demonstration remain expandable. All original ETF identities/caches and financial fixtures are byte-unchanged. Prior research/captured follow-ups remain intact; no old result is relabeled.

Causal Exploration can capture a selected snapshot as an **optional reference**, including its input provenance/assumptions. The contextual Meta prompt distinguishes this from its archived synthetic portfolio; deterministic templates remain templates. No inference happens merely by selecting/navigating. Accepted scenario calculations still use the archived basket engine, explicitly disclosed in UI and prompt. Captured references remain attached to the original response when selection changes. **Appropriate for conditional competing-hypothesis exploration**, not identification of true causes, validation of macro mechanisms, calibration of shock probabilities, or estimation of causal effects: imposed euro shocks and starting-mark calibration cannot be causal evidence.

**Stop after these fixed snapshots.** Actual Treasury closes, real derivative confirmations/curves, real account data, total returns and complete funding/liquidity/default/convexity valuation remain unavailable. Do not expand retrieval dates, add a provider/pricer/service or run live inference. No paid data, new dependencies or generalized ingestion. Future production-quality valuation requires separately scoped data/contracts; these deliberately simple approximations do not establish reliability.

Validation results/timing and execution limitations are appended in RESEARCH_LOG.md. New deterministic financial tests independently reproduce position totals, signed PV01/strike/forward formulas, input eligibility and failure behavior; mocked Meta tests inspect reference/provenance wire content without network inference. Frontend tests render all three windows and preserved causal separation. No manual browser validation claimed.
