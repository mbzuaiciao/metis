import type { EtfPortfolio, EventSnapshot } from './types';

type Position = EventSnapshot['positions'][number];
export type MarketRow = {
  id: string; label: string; measure: string; unit: '%' | 'USD/share' | 'USD/EUR' | 'USD/USD';
  start: number | null; end: number | null; change: number | null;
  startFormatted: string; endFormatted: string; changeFormatted: string;
  tone: string; note: string; sources: string[];
};

// Select exact dated observed inputs by meaning, never by array order or USD position mark.
function observedPair(position: Position, snapshot: EventSnapshot, series: string, unit: string) {
  return [snapshot.start, snapshot.end].map(day => {
    const inputs = position.inputs.filter(i => i.label === `${series} · ${day}`);
    const input = inputs[0];
    return inputs.length === 1 && input.status === 'Observed' && input.unit === unit
      && Number.isFinite(input.value) && !!input.source_url ? input : null;
  });
}

export function getMarketSnapshotRows(snapshot?: EventSnapshot, portfolio?: EtfPortfolio): MarketRow[] {
  if (!snapshot) return [];
  return snapshot.positions.map(position => {
    const { id, label } = position;
    const fund = portfolio?.positions.find(p => p.id === id && p.instrument === 'ETF');
    let measure = fund ? 'ETF close' : 'Unsupported market measure';
    let unit: MarketRow['unit'] = 'USD/share';
    let note = fund?.note ?? 'Exact eligible ETF closes are unavailable in the cached inputs.';
    let inputs: ReturnType<typeof observedPair> = [];
    let start: number | null = null;
    let end: number | null = null;
    let rate = false;
    if (['UST2', 'UST10', 'IRS-P', 'IRS-R'].includes(id)) {
      const series = id === 'UST2' ? 'DGS2' : id === 'IRS-P' ? 'DGS5' : 'DGS10';
      const swap = id.startsWith('IRS-');
      measure = `${series} · ${swap ? 'Indicative swap-rate proxy' : 'Treasury yield proxy'}`;
      unit = '%';
      rate = true;
      note = swap ? 'Treasury yield proxy, not an observed par swap quote.'
        : 'Constant-maturity Treasury yield, not a bond price. No particular CUSIP price is available.';
      inputs = observedPair(position, snapshot, series, 'percent per annum');
    } else if (id === 'FX-EUR') {
      measure = 'EUR/USD spot proxy';
      unit = 'USD/EUR';
      note = 'FRED DEXUSEU noon buying rate in USD per EUR; a proxy for the forward, not its strike or NPV.';
      inputs = observedPair(position, snapshot, 'DEXUSEU', 'USD per EUR');
    } else if (id === 'CASH') {
      measure = 'Constant USD denomination';
      unit = 'USD/USD';
      note = 'Assumed stable USD denomination, not a traded quote or account balance.';
      start = end = 1;
    } else if (fund?.currency === 'USD' && fund.eligible_from && snapshot.start >= fund.eligible_from) {
      inputs = observedPair(position, snapshot, `${id} unadjusted close`, 'USD/share');
      note = `Observed unadjusted ETF close; price return excludes distributions. ${fund.note ?? ''}`;
    } else if (fund?.eligible_from && snapshot.start < fund.eligible_from) {
      note = `ETF quote unavailable: current listing/mandate eligible from ${fund.eligible_from}. ${fund.note ?? ''}`;
    }
    if (inputs.length === 2 && inputs.every(i => i && (rate || i.value > 0))) {
      start = inputs[0]!.value;
      end = inputs[1]!.value;
    }
    if (start === null || end === null) note += ' No compatible dated observation pair; no substitute quote.';
    const change = start === null || end === null ? null
      : rate ? (end - start) * 100 : (end / start - 1) * 100;
    const format = (value: number | null) => value === null ? 'Unavailable'
      : unit === '%' ? `${value.toFixed(2)}%`
      : unit === 'USD/EUR' ? value.toFixed(4) : value.toFixed(2);
    return {
      id, label, measure, unit, start, end, change,
      startFormatted: format(start), endFormatted: format(end),
      changeFormatted: change === null ? '—' : `${change > 0 ? '+' : ''}${rate ? Math.round(change) : change.toFixed(2)}${rate ? 'bp' : '%'}`,
      tone: rate || change === null || change === 0 ? '' : change < 0 ? 'negative' : 'positive',
      note, sources: [...new Set(inputs.flatMap(i => i?.source_url ? [i.source_url] : []))],
    };
  });
}

export function treasuryCurve(rows: MarketRow[]) {
  return ['UST2', 'IRS-P', 'UST10'].map((id, i) => ({
    tenor: ['2Y', '5Y', '10Y'][i],
    start: rows.find(r => r.id === id)?.start ?? null,
    end: rows.find(r => r.id === id)?.end ?? null,
  }));
}
