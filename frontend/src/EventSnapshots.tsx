import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import type { EventSnapshot } from './types';

export const money = (v: number | null) =>
  v === null
    ? 'Unavailable'
    : new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
      }).format(Math.round(v / 1000) * 1000);

export const pnlTone = (v: number | null) =>
  v === null || v === 0 ? '' : v < 0 ? 'negative' : 'positive';

export function EventTable({ snapshot, market = false }: { snapshot: EventSnapshot; market?: boolean }) {
  return (
    <div className="etf-table-wrap">
      <table className="etf-table event-table">
        <thead>
          <tr>
            <th>{market ? "Instrument" : "Holding"}</th>
            <th>
              Starting USD value
              <br />
              {snapshot.start}
            </th>
            <th>
              Ending USD value
              <br />
              {snapshot.end}
            </th>
            <th>{market ? "Change · Estimated USD P&L" : "Estimated P&L"}</th>
          </tr>
        </thead>
        <tbody>
          {snapshot.positions.map((p) => (
            <tr key={p.id} data-event-position={p.id}>
              <td>
                <details className="holding-details">
                  <summary className="holding-summary">
                    <span className="holding-chevron" aria-hidden="true">
                      <ChevronRight size={14} />
                    </span>
                    <span className="holding-title">
                      <b>{p.id}</b>
                      <span className="holding-label">{p.label}{market && (
                        p.id === 'CASH' ? ' · assumed balance'
                        : ['IRS-R', 'IRS-P', 'FX-EUR'].includes(p.id) ? ' · modeled NPV'
                        : p.method.startsWith('Hypothetical current-mandate') ? ' · hypothetical exposure'
                        : ''
                      )}</span>
                    </span>
                  </summary>
                  <div className="holding-basis">
                    {market && <p><b>{p.id === 'CASH' ? 'Assumed USD cash balance'
                      : ['IRS-R', 'IRS-P', 'FX-EUR'].includes(p.id) ? 'Hypothetical modeled USD NPV'
                      : p.method.startsWith('Hypothetical current-mandate') ? 'Hypothetical euro-credit exposure · estimated USD value'
                      : p.method.startsWith('Starting allocation') ? 'Estimated USD position value · observed ETF close inputs (USD/share)'
                      : 'Hypothetical Treasury exposure · estimated USD value'}</b></p>}
                    <p>{p.method}</p>
                    {p.inputs.map((i, n) => (
                      <p key={n}>
                        <b>{i.status}</b> · {i.label}: {i.value} {i.unit}{' '}
                        {i.source_url && (
                          <a href={i.source_url} target="_blank" rel="noreferrer">
                            Source
                          </a>
                        )}
                      </p>
                    ))}
                    {Object.entries(p.terms).map(([key, value]) => (
                      <p key={key}>
                        {key.replaceAll('_', ' ')}: {String(value)}
                      </p>
                    ))}
                    {p.assumptions.map((a, i) => (
                      <p key={i}>{a}</p>
                    ))}
                  </div>
                </details>
              </td>
              <td>{money(p.start_value_usd)}</td>
              <td>{money(p.end_value_usd)}</td>
              <td className={pnlTone(p.pnl_usd) || undefined}>{money(p.pnl_usd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EventSnapshots({
  snapshots,
  onExplore,
  selectedId,
  onSelect,
}: {
  snapshots: EventSnapshot[];
  onExplore?: (id: string) => void;
  selectedId?: string;
  onSelect?: (id: string) => void;
}) {
  const [localSelected, setLocalSelected] = useState(0);
  const selectedIndex = selectedId
    ? Math.max(0, snapshots.findIndex((s) => s.id === selectedId))
    : localSelected;
  const snapshot = snapshots[selectedIndex] ?? snapshots[0];

  const handleSelect = (idx: number) => {
    setLocalSelected(idx);
    if (snapshots[idx]) {
      onSelect?.(snapshots[idx].id);
    }
  };

  return (
    <section className="etf-portfolio" aria-label="Historical event replay">
      <h2>Historical event replay</h2>
      <label>
        Event window{' '}
        <select value={selectedIndex} onChange={(e) => handleSelect(Number(e.target.value))}>
          {snapshots.map((s, i) => (
            <option value={i} key={s.id}>
              {s.start} → {s.end} · {s.title}
            </option>
          ))}
        </select>
      </label>
      <p>
        <b>
          Estimated portfolio P&amp;L:{' '}
          {snapshot.estimated_pnl_usd === null ? (
            'Unavailable'
          ) : (
            <span className={pnlTone(snapshot.estimated_pnl_usd)}>
              {money(snapshot.estimated_pnl_usd)}
            </span>
          )}
        </b>
        <br />
        Starting illustrative value {money(snapshot.start_nav_usd)} → ending illustrative value{' '}
        {money(snapshot.end_nav_usd)} · {snapshot.coverage_count}/12 rows.
        <br />
        <small className="context-note">Illustrative estimate — not actual portfolio returns.</small>
      </p>
      {snapshot.estimated_pnl_usd === null && (
        <p>
          Covered subtotal only:{' '}
          {snapshot.covered_pnl_usd === null ? (
            'Unavailable'
          ) : (
            <span className={pnlTone(snapshot.covered_pnl_usd)}>
              {money(snapshot.covered_pnl_usd)}
            </span>
          )}
          . Missing rows are excluded, never assumed zero.
        </p>
      )}
      <EventTable snapshot={snapshot} />
      {onExplore && (
        <button
          onClick={() => {
            onSelect?.(snapshot.id);
            onExplore(snapshot.id);
          }}
        >
          Use this snapshot as a causal reference
        </button>
      )}
      <details>
        <summary>Methodology &amp; Assumptions</summary>
        <p>{snapshot.disclosure}</p>
        <p>
          <span className="badge">Observed input</span> Dated sourced market input ·{' '}
          <span className="badge amber">Estimated</span> Derived value with approximate inputs or
          hypothetical assumptions · <span className="badge">Unavailable</span> Missing required
          evidence.
        </p>
        <p>
          Dollar display rounded to the nearest $1,000; expandable inputs retain calculation
          precision. Rounded rows may not sum exactly. Zero cash P&amp;L is an explicit assumption.
          These reconstructions do not replace archived results.
        </p>
        <p>
          Market inputs: {snapshot.market_provenance.provider}, downloaded{' '}
          {snapshot.market_provenance.retrieved_at}. {snapshot.market_provenance.timing}
        </p>
        <p>
          March ETF observations retrieved {snapshot.march_etf_retrieved_at}; September/October
          use the unchanged cached source records in the coverage audit.
        </p>
        <p>{snapshot.causal_use}</p>
      </details>
    </section>
  );
}
