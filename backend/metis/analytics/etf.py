"""Identified ETF allocation; deliberately separate from frozen synthetic risk demos."""
from datetime import date
import math

from metis.analytics.engine import load_json, load_positions


REFERENCE_DATE = '2026-10-30'
SUPPORTED_PAIRS = {('2026-10-29', '2026-10-30'), ('2022-09-12', '2022-09-13')}


def portfolio() -> dict:
    catalog = load_json('etf-portfolio')
    mapping = {fund['legacy_id']: fund for fund in catalog['funds']}
    rows = []
    frame = load_positions(REFERENCE_DATE)
    nav = float(frame.market_value_usd.sum())
    for row in frame.to_dict(orient='records'):
        fund = mapping.get(row['id'])
        # Neither a synthetic mark nor a basket sensitivity is a measured ETF value/risk.
        item = {'id': fund['ticker'] if fund else row['id'],
                'name': fund['name'] if fund else row['name'],
                'label': fund['label'] if fund else row['name'],
                'asset_class': row['asset_class'], 'allocation_usd': row['market_value_usd'],
                'weight_pct': row['market_value_usd'] / nav * 100,
                'units': None, 'observed_market_value_usd': None,
                'dv01_usd_per_bp': None, 'cs01_usd_per_bp': None,
                'valuation_status': 'unavailable', 'instrument': 'ETF' if fund else row['instrument']}
        if fund:
            item.update(fund)
        else:
            item['audit'] = next(a for a in catalog['audit'] if a['id'] == row['id'])
        rows.append(item)
    return {'reference_date': REFERENCE_DATE, 'allocation_nav_usd': nav,
            'observed_nav_usd': None, 'positions': rows, 'verified_on': catalog['verified_on'],
            'basis': 'Initial market-value-weighted illustrative allocation using October 30 synthetic dollar exposures. '
                     'Not actual holdings or an observed NAV. No unit/share counts inferred. '
                     'For each historical comparison these dollars are assumed invested at the starting close.',
            'risk_basis': 'ETF DV01/CS01 unavailable; old generic-basket sensitivities are retained only in archived demonstrations. '
                          'Observed ETF price P&L is a single price leg, with no additional rates/spread/equity/FX legs.'}


def historical_prices(start: str, end: str) -> dict:
    """Use exact cached dates only. Missing/ineligible legs never become zero or proxies."""
    start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    if start_date >= end_date:
        raise ValueError('Start date must precede end date.')
    data = portfolio()
    quotes = load_json('etf-observations')
    observations = quotes['observations']
    rows = []
    for position in data['positions']:
        row = {**position, 'status': 'unavailable', 'reason': 'Instrument-level historical valuation unavailable; see audit.',
               'start_observation': None, 'end_observation': None,
               'price_return_pct': None, 'price_pnl_usd': None, 'total_return_pct': None}
        if position['instrument'] == 'ETF':
            row['reason'] = 'Exact dated closes unavailable; no proxy substituted.'
            if start < position['eligible_from']:
                row['reason'] = position['note'] if position['id'] in {'EUIG', 'EUHY'} else 'Before fund inception.'
            elif (start, end) in SUPPORTED_PAIRS:
                pair = [[q for q in observations if q['ticker'] == position['id'] and q['date'] == day]
                        for day in [start, end]]
                # Fail closed on ambiguous quotes, incompatible currency/basis, invalid prices or split events.
                if all(len(q) == 1 for q in pair):
                    a, b = pair[0][0], pair[1][0]
                    interval = [q for q in observations if q['ticker'] == position['id'] and start < q['date'] <= end]
                    if all(q['currency'] == 'USD' and q['price_basis'] == 'unadjusted_close'
                           and q.get('source_url') and q.get('bar_timestamp_utc')
                           and isinstance(q['close'], (int, float)) and math.isfinite(q['close']) and q['close'] > 0
                           for q in [a, b]) and not any(q['split_events'] for q in interval):
                        change = b['close'] / a['close'] - 1
                        row.update(status='available', reason='Observed ETF price return; hypothetical P&L on starting allocation, distributions excluded.',
                                   start_observation=a, end_observation=b, price_return_pct=change * 100,
                                   price_pnl_usd=round(position['allocation_usd'] * change, 2))
                    else:
                        row['reason'] = 'Invalid/incompatible close metadata or split event; valuation unavailable.'
        rows.append(row)
    covered = [row for row in rows if row['status'] == 'available']
    return {'start': start, 'end': end, 'positions': rows,
            'covered_allocation_usd': sum(row['allocation_usd'] for row in covered),
            'covered_price_pnl_usd': round(sum(row['price_pnl_usd'] for row in covered), 2) if covered else None,
            'portfolio_pnl_usd': None, 'total_return_pct': None,
            'provider': quotes['provider'], 'retrieved_at': quotes['retrieved_at'],
            'method': 'Starting illustrative dollar allocation × (ending unadjusted close / starting unadjusted close − 1). '
                      'USD price return only, not total return or actual historical portfolio P&L. '
                      'Missing positions excluded from covered subtotal; complete portfolio P&L unavailable. '
                      'Only the two cached comparison pairs are supported; no interpolation.',
            'distribution_treatment': quotes['distribution_treatment'], 'split_treatment': quotes['split_treatment']}
