import { useState } from 'react';
import type { EtfPortfolio as Portfolio, EtfHistory } from './types';

const usd = (v: number | null) => v === null ? 'Unavailable' : new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 2,
}).format(v);

export function EtfPortfolio({ portfolio, history }: { portfolio: Portfolio; history: EtfHistory[] }) {
  const [period, setPeriod] = useState(0);
  const comparison = history[period];
  return <section className="etf-portfolio">
    <h2>Identified ETF allocation &amp; instrument audit</h2>
    <p>{portfolio.basis}</p>
    <p><b>Illustrative allocation: {usd(portfolio.allocation_nav_usd)}.</b> Observed NAV: Unavailable. Units: Unavailable.</p>
    <p>{portfolio.risk_basis}</p>
    <label>Observed ETF comparison: <select value={period} onChange={e => setPeriod(Number(e.target.value))}>
      {history.map((h, i) => <option value={i} key={h.end}>{h.start} → {h.end}</option>)}
    </select></label>
    <p>{comparison.method}</p>
    <p><b>Covered price P&amp;L: {usd(comparison.covered_price_pnl_usd)}</b> on {usd(comparison.covered_allocation_usd)} of starting allocations.
      {' '}Complete portfolio P&amp;L: Unavailable. Total return: Unavailable.</p>
    <div className="etf-table-wrap"><table className="etf-table">
      <thead><tr><th>Holding</th><th>Initial allocation / NAV weight</th><th>Starting close</th><th>Ending close</th><th>Price return</th><th>Price P&amp;L</th></tr></thead>
      <tbody>{comparison.positions.map(p => <tr key={p.id}>
        <td><b>{p.id}</b> · {p.label}<br />{p.source_url ? <a href={p.source_url} target="_blank" rel="noreferrer">{p.name}</a> : p.name}</td>
        <td>{usd(p.allocation_usd)} / {p.weight_pct.toFixed(1)}%</td>
        <td>{usd(p.start_observation?.close ?? null)}</td><td>{usd(p.end_observation?.close ?? null)}</td>
        <td>{p.price_return_pct === null ? 'Unavailable' : `${p.price_return_pct.toFixed(3)}%`}</td>
        <td>{usd(p.price_pnl_usd)}</td>
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
      {portfolio.positions.filter(p => p.audit).map(p => <article key={p.id}>
        <h3>{p.id} · {p.name}</h3><p>Historical valuation: Unavailable. {p.audit!.minimum_data}</p>
        <p>{p.audit!.recommendation}</p>
      </article>)}
    </details>
    <p>The Overview, market, risk, scenario and AI investigation pages retain the archived synthetic demonstrations and their original baskets. Their sensitivities and P&amp;L do not describe this ETF allocation.</p>
  </section>;
}
