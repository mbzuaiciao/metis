import { useState } from 'react';
import type { EtfPortfolio as Portfolio, EtfHistory } from './types';

const usd = (v: number | null) => v === null ? 'Unavailable' : new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 2,
}).format(v);
const pnlTone = (v: number | null) => (v === null || v === 0 ? '' : v < 0 ? 'negative' : 'positive');
const valuationName = {
  observed_security_close: 'Observed security close',
  treasury_issue_price: 'Treasury issue price',
  modeled_otc_mark: 'Modeled OTC mark',
  cash_balance: 'Cash balance',
};

export function EtfPortfolio({ portfolio, history, showSelector = false, title }: {
  portfolio: Portfolio;
  history: EtfHistory[];
  showSelector?: boolean;
  title?: string;
}) {
  const [period, setPeriod] = useState(0);
  const comparison = history[period] ?? history[0];
  return <section className="etf-portfolio">
    <h2>{title ?? `Portfolio snapshot · As of ${comparison.end}`}</h2>
    <p className="context-note">Dated illustrative allocation snapshot · Daily price comparison: {comparison.start} → {comparison.end}. Not a live account or today's prices.</p>
    <p>{portfolio.basis}</p>
    <p><b>Illustrative allocation: {usd(portfolio.allocation_nav_usd)}.</b> Observed NAV: Unavailable. Units: Unavailable.</p>
    <p>{portfolio.risk_basis}</p>
    {showSelector && history.length > 1 && (
      <label>Observed ETF comparison: <select value={period} onChange={e => setPeriod(Number(e.target.value))}>
        {history.map((h, i) => <option value={i} key={h.end}>{h.start} → {h.end}</option>)}
      </select></label>
    )}
    <p>{comparison.method}</p>
    <p><b>Covered price P&amp;L: <span className={pnlTone(comparison.covered_price_pnl_usd)}>{usd(comparison.covered_price_pnl_usd)}</span></b> on {usd(comparison.covered_allocation_usd)} of starting allocations.
      {' '}Complete portfolio P&amp;L: Unavailable (observed-price basis). Total return: Unavailable. MTD P&amp;L: Unavailable.</p>
    <p className="context-note">MTD P&amp;L is unavailable: source price data do not cover the beginning of the month through the as-of date (intervening daily bars are not retrieved; extrapolation from two daily closes is not defensible). Valuation coverage: {comparison.positions.filter(p => p.valuation.status === 'available').length} of {comparison.positions.length} holdings covered by observed security closes.</p>
    <div className="etf-table-wrap"><table className="etf-table">
      <thead><tr><th>Holding</th><th>Initial allocation / NAV weight</th><th>Valuation type / status</th><th>Starting valuation<br />{comparison.start}</th><th>Ending valuation<br />{comparison.end}</th><th>Historical contribution</th></tr></thead>
      <tbody>{comparison.positions.map(p => <tr key={p.id} data-position-id={p.id}>
        <td><b>{p.id}</b> · {p.label}<br />{p.source_url ? <a href={p.source_url} target="_blank" rel="noreferrer">{p.name}</a> : p.name}</td>
        <td>{usd(p.allocation_usd)} / {p.weight_pct.toFixed(1)}%</td>
        <td><b>{valuationName[p.valuation.type]}</b><br />
          {p.valuation.status === 'available' ? 'Available' : p.valuation.status === 'illustrative_only' ? 'Illustrative only' : 'Unavailable'}
          <br />{p.valuation.unit}
          {p.valuation.type === 'cash_balance' && <p>Reference balance: {usd(p.valuation.reference_balance_usd ?? null)} · {p.valuation.reference_date} · illustrative, not a historical account observation.</p>}
          <details><summary>Basis{p.audit ? ' / missing inputs' : ''}</summary><p>{p.valuation.basis}</p>
            {p.audit && <><p>{p.audit.minimum_data}</p><p>Next step: {p.audit.next_step}</p></>}
            {p.valuation.source_urls.map(url => <p key={url}><a href={url} target="_blank" rel="noreferrer">Valuation basis source</a></p>)}
          </details>
        </td>
        <td>{usd(p.valuation.start_value)}{p.valuation.type === 'cash_balance' && <><br />Historical balance</>}</td>
        <td>{usd(p.valuation.end_value)}{p.valuation.type === 'cash_balance' && <><br />Historical balance</>}</td>
        <td>{p.instrument === 'ETF' ? <>{p.price_return_pct === null ? 'Price return: Unavailable' : `${p.price_return_pct.toFixed(3)}% price return`}<br />Price P&amp;L: <span className={pnlTone(p.price_pnl_usd)}>{usd(p.price_pnl_usd)}</span></> : 'P&L: Unavailable'}</td>
      </tr>)}</tbody>
    </table></div>
    <p>{comparison.provider} · retrieved {comparison.retrieved_at}. {comparison.distribution_treatment} {comparison.split_treatment}</p>
    <p>Daily bar timestamps below identify the provider’s session bar, not a certified closing-auction or original publication timestamp. Only the displayed pairs were retrieved; other periods are unavailable.</p>
    <details><summary>Fund identity, coverage and quote provenance</summary>
      <p>Primary product evidence checked {portfolio.verified_on}. USD listing alone does not imply a currency hedge.</p>
      {comparison.positions.filter(p => p.instrument === 'ETF').map(p => <article key={p.id}>
        <h3>{p.id} · {p.name}</h3><p>{p.exchange} · {p.currency}. {p.note}</p>
        {p.event_source_url && <a href={p.event_source_url} target="_blank" rel="noreferrer">Listing / mandate change evidence</a>}
        <p>{p.reason}</p>
        {[p.start_observation, p.end_observation].filter(o => o !== null).map(o => <p key={o.date}>
          <a href={o.source_url} target="_blank" rel="noreferrer">{o.date} · {o.close} {o.currency}</a>
          {' '}· {o.price_basis} · bar {o.bar_timestamp_utc} · {o.distribution_events.length} distribution events / {o.split_events.length} split events reported.
        </p>)}
      </article>)}
    </details>
    <details><summary>Remaining six instruments: valuation gaps and minimum data</summary>
      {comparison.positions.filter(p => p.audit).map(p => <article key={p.id}>
        <h3>{p.id} · {p.name}</h3><p>Historical valuation: Unavailable. {p.audit!.minimum_data}</p>
        <p>{p.audit!.recommendation} Next step: {p.audit!.next_step}</p>
        {p.valuation.treasury_review && <>
          <p>Treasury coverage checked {p.valuation.treasury_review.checked_on}: {p.valuation.treasury_review.decision}</p>
          <p><a href={p.valuation.treasury_review.reference_source_url} target="_blank" rel="noreferrer">TreasuryDirect historical reference source</a>: {p.valuation.treasury_review.source_qualification}</p>
          {p.valuation.treasury_review.candidates.map(c => <div key={c.cusip}>
            <p><a href={c.terms_source_url} target="_blank" rel="noreferrer">Research candidate {c.cusip}</a> · {c.original_term} · coupon {c.coupon_pct}% · issued {c.issue_date} · matures {c.maturity_date} · {c.eligibility === 'live_on_dates' ? 'Live on comparison dates' : 'Ineligible on comparison dates'}.</p>
            <p>Published special-security reference rows only (not marketable-bond quotes or portfolio valuations): {c.reference_rows.map(r => `${r.date}: ${r.end_of_day_reference}`).join('; ')}. Price/accrual basis unverified; unused in P&amp;L.</p>
          </div>)}
        </>}
      </article>)}
    </details>
    <p>The Overview, market, risk, scenario and AI investigation pages retain the archived synthetic demonstrations and their original baskets. Their sensitivities and P&amp;L do not describe this ETF allocation.</p>
  </section>;
}
