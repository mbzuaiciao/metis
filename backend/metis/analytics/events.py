"""Three fixed hypothetical reconstructions; no runtime retrieval or general pricer."""
from datetime import date, timedelta
import math

from metis.analytics.engine import load_json
from metis.analytics.etf import portfolio


def _one(records, **keys):
    found = [r for r in records if all(r.get(k) == v for k, v in keys.items())]
    return found[0] if len(found) == 1 else None


def _input(label, value, unit, status, source_url=None):
    return dict(label=label, value=value, unit=unit, status=status, source_url=source_url)


def _maturity(effective, years):
    maturity = effective.replace(year=effective.year + years)
    while maturity.weekday() >= 5:
        maturity += timedelta(days=1)
    return maturity.isoformat()


def event_snapshot(event_id: str) -> dict:
    config = load_json('event-snapshots')
    event = _one(config['events'], id=event_id)
    if event is None:
        raise ValueError('Only the three configured event snapshots are supported.')
    start, end = event['start'], event['end']
    effective = date.fromisoformat(start)
    assumptions = config['assumptions']
    market = load_json('event-market-observations')
    extra_quotes = load_json('event-etf-observations')
    quotes = load_json('etf-observations')['observations'] + extra_quotes['observations']

    def observed(series, day):
        record = _one(market['observations'], series=series, date=day)
        if (not record or not isinstance(record.get('value'), (int, float))
                or not math.isfinite(record['value']) or not record.get('source_url')):
            raise ValueError(f'Missing or invalid {series} observation for {day}.')
        return _input(f'{series} · {day}', record['value'], record['unit'], 'Observed', record['source_url'])

    rows = []
    for position in portfolio()['positions']:
        id = position['id']
        initial = position['allocation_usd']
        row = dict(id=id, label=position['label'], start_value_usd=initial, end_value_usd=None,
                   pnl_usd=None, status='Unavailable', inputs=[], terms={}, method='', assumptions=[])
        try:
            if position['instrument'] == 'ETF' and start >= position['eligible_from']:
                pair = [_one(quotes, ticker=id, date=day) for day in [start, end]]
                if any(not q or q['currency'] != 'USD' or q['price_basis'] != 'unadjusted_close'
                       or not q.get('source_url') or not q.get('bar_timestamp_utc')
                       or not isinstance(q['close'], (int, float)) or not math.isfinite(q['close']) or q['close'] <= 0
                       for q in pair) or pair[1]['split_events']:
                    raise ValueError('Exact eligible ETF closes unavailable or incompatible; no assumed replacement.')
                a, b = pair
                pnl = initial * (b['close'] / a['close'] - 1)
                row['inputs'] = [_input(f'{id} unadjusted close · {q["date"]}', q['close'], 'USD/share', 'Observed', q['source_url']) for q in pair]
                row['method'] = 'Starting allocation × (end close / start close − 1).'
                row['assumptions'] = ['Hypothetical starting market-value allocation; no actual share holding inferred.', 'Price return only; distributions excluded, not total return. No extra rates/spread/equity/FX legs.']
            elif id in assumptions['ineligible_euro_exposures']:
                risk = assumptions['ineligible_euro_exposures'][id]
                spread = event['euro_ig_spread_change_bp' if id == 'EUIG' else 'euro_hy_spread_change_bp']
                rate = event['euro_rate_change_bp']
                pnl = -initial * (risk['rate_duration_years'] * rate + risk['spread_duration_years'] * spread) / 10000
                row['method'] = 'Hypothetical current-mandate euro credit exposure: −allocation × (rate duration × assumed rate bp + spread duration × assumed spread bp) / 10,000.'
                row['inputs'] = [_input('Euro rates change', rate, 'bp', 'Hypothetical assumption'), _input('Euro credit spread change', spread, 'bp', 'Hypothetical assumption')]
                row['terms'] = risk
                row['assumptions'] = [position['note'], 'Not an ETF price or actual pre-inception holding. No US OAS/other ETF return used.', 'Zero assumed euro rate move; spread shock and durations are uncalibrated demo assumptions. No carry/distributions.']
            elif id in {'UST10', 'UST2'}:
                series = 'DGS10' if id == 'UST10' else 'DGS2'
                a, b = observed(series, start), observed(series, end)
                duration = assumptions['treasury_duration_years'][id]
                pnl = -initial * duration * (b['value'] - a['value']) / 100
                row['method'] = '−starting allocation × assumed modified duration × yield change in decimal units.'
                row['inputs'] = [a, b, _input('Modified duration', duration, 'years', 'Hypothetical assumption')]
                row['terms'] = {'exposure': 'Hypothetical constant-maturity Treasury exposure', 'tenor_years': 10 if id == 'UST10' else 2}
                row['assumptions'] = ['No CUSIP, observed bond price or face amount; CMT yields are observed inputs only.', 'Duration frozen; exclude coupon/accrual/carry/convexity and roll-down. No TreasuryDirect special-security prices used.']
            elif id in assumptions['swaps']:
                terms = assumptions['swaps'][id]
                a, b = observed(terms['rate_series'], start), observed(terms['rate_series'], end)
                pv01 = terms['direction'] * terms['notional_usd'] * terms['annuity_years'] / 10000
                # Frozen annuity linear mark V = signed PV01 × (fixed strike bp − proxy par rate bp).
                # Calibrate an off-market fixed strike to the supplied initial signed dollar allocation.
                fixed_bp = a['value'] * 100 + initial / pv01
                pnl = -pv01 * (b['value'] - a['value']) * 100
                row['inputs'] = [a, b, _input('Treasury rate used as swap-par proxy', a['value'], '% p.a.', 'Approximate input'), _input('Frozen annuity', terms['annuity_years'], 'years', 'Hypothetical assumption')]
                row['terms'] = {**terms, 'effective_date': start, 'maturity_date': _maturity(effective, terms['tenor_years']), 'fixed_rate_pct': fixed_bp / 100, 'signed_pv01_usd_per_bp': pv01, 'floating_leg': 'Fictional compounded SOFR, quarterly ACT/360', 'fixed_leg': 'Annual ACT/360', 'calendar': 'Following weekday; holidays ignored in this approximation', 'initial_mark_relation': 'Off-market fixed strike calibrated to initial signed allocation; not notional or collateral.'}
                row['method'] = 'V = signed PV01 × (fixed strike bp − Treasury par-rate proxy bp); event P&L = −signed PV01 × proxy rate change bp.'
                row['assumptions'] = ['Fictional event-specific transferred contract at assumed opening mark, not a par new swap or an actual holding.', 'Treasury CMT is an approximate swap-rate input, not an observed swap quote. Frozen annuity, no reset/coupon settlement within window, carry, curve-basis, collateral/funding or discount-factor change.']
            elif id == 'FX-EUR':
                a, b = observed('DEXUSEU', start), observed('DEXUSEU', end)
                fx = assumptions['fx']
                eur = fx['usd_reference_notional'] / a['value']
                f0, f1 = a['value'] + fx['forward_points_start'], b['value'] + fx['forward_points_end']
                strike = f0 - initial / (eur * fx['discount_factor'])
                pnl = eur * fx['discount_factor'] * (f1 - f0)
                row['inputs'] = [a, b, _input('Starting forward points', fx['forward_points_start'], 'USD/EUR', 'Hypothetical assumption'), _input('Ending forward points', fx['forward_points_end'], 'USD/EUR', 'Hypothetical assumption'), _input('Frozen USD discount factor', fx['discount_factor'], 'ratio', 'Hypothetical assumption')]
                row['terms'] = {'eur_bought': eur, 'usd_sold': eur * strike, 'strike_usd_per_eur': strike, 'usd_reference_notional': fx['usd_reference_notional'], 'effective_date': start, 'maturity_date': _maturity(effective, fx['tenor_years']), 'calendar': 'Following weekday; holidays ignored in this approximation', 'initial_mark_relation': 'EUR amount set by $12m reference exposure / start spot; strike calibrated so opening NPV = $1.5m.'}
                row['method'] = 'Long EUR forward: NPV = EUR bought × assumed USD discount factor × (spot + assumed points − strike).'
                row['assumptions'] = ['Fictional event-specific off-market forward; initial allocation is NPV, not its $12m reference exposure.', 'Equal frozen EUR/USD discount factors of 0.96 imply zero forward points at both dates; no cash flows/funding or aging. Spot noon clock differs from ETF closes. No observed forward quote or curve claimed.']
            elif id == 'CASH':
                pnl = 0
                row['method'] = 'Constant illustrative USD balance under explicit zero-interest/zero-flow assumptions.'
                row['inputs'] = [_input('Interest', assumptions['cash_interest_usd'], 'USD', 'Hypothetical assumption'), _input('Net cash flows', assumptions['cash_flows_usd'], 'USD', 'Hypothetical assumption')]
                row['assumptions'] = ['Illustrative $4m at both dates, not actual account balances or a market quote.']
            else:
                raise ValueError('No reviewed valuation method.')
            row.update(status='Estimated', pnl_usd=round(pnl, 2), end_value_usd=round(initial + round(pnl, 2), 2))
        except ValueError as exc:
            row['method'] = str(exc)
        rows.append(row)
    covered = [r for r in rows if r['pnl_usd'] is not None]
    subtotal = round(sum(r['pnl_usd'] for r in covered), 2)
    total = subtotal if len(covered) == 12 else None
    opening = sum(r['start_value_usd'] for r in rows)
    return {**event, 'positions': rows, 'start_nav_usd': opening, 'end_nav_usd': round(opening + total, 2) if total is not None else None,
            'estimated_pnl_usd': total, 'covered_pnl_usd': subtotal, 'coverage_count': len(covered),
            'market_provenance': {k: v for k, v in market.items() if k != 'observations'},
            'march_etf_retrieved_at': extra_quotes['retrieved_at'],
            'disclosure': 'Hypothetical reconstructed/stressed P&L, not actual historical holdings, observed NAV or total return. Starting signed allocations sum to $100m. All dollar valuations are estimates even when inputs are observed. Durations, euro-credit shocks and OTC terms are assumptions; approximate sensitivity calculations omit carry and nonlinear risks. Suitable for conditional hypothesis exploration, not historical causal identification.',
            'causal_use': 'Observed co-moves and these assumed exposures may motivate competing hypotheses; assumed shocks and calibrated opening marks cannot identify or validate event causes.'}


def event_snapshots() -> list[dict]:
    return [event_snapshot(e['id']) for e in load_json('event-snapshots')['events']]
