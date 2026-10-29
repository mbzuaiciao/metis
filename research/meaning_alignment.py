"""Offline, deliberately narrow sentence rules. No model or semantic labels as input."""
import re

AMOUNT = r'([+-]?\$[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)'


def money(value):
    return float(value.replace('$', '').replace(',', ''))


def check(statement, citation, evidence):
    """Check a whole recognized sentence against one trusted, source-derived citation.

    The evidence catalog is an offline adapter, not caller-asserted production truth.
    No verdict certifies arbitrary prose, other sentences or omitted assertions.
    """
    result = {'verdict': 'Uncheckable', 'reason': 'Entire sentence is outside the fixed grammar.',
              'coverage': 'This sentence pattern and cited synthetic scope only; no whole-answer verification.',
              'evidence': evidence.get(citation)}
    if citation not in evidence:
        return result | {'reason': 'Unknown citation.'}
    e = evidence[citation]

    def finish(verdict, reason):
        return result | {'verdict': verdict, 'reason': reason}

    def equals(value, actual):
        return abs(value - actual) <= .01

    def verdict(matches, reason):
        return finish('Scoped match' if matches else 'Mismatch', reason)

    m = re.fullmatch(r'In the scenario, (HY net|HY spread-only|portfolio rates|portfolio total) P&L is '+AMOUNT+r'\.', statement)
    if m:
        label, amount = m.groups()
        required = {'HY net': 'hy_net', 'HY spread-only': 'hy_spread',
                    'portfolio rates': 'scenario_rates', 'portfolio total': 'scenario_total'}[label]
        if required not in evidence:
            return finish('Uncheckable', 'Required calculation unavailable.')
        actual = evidence[required]['value']
        return verdict(citation == required and equals(money(amount), actual),
                       f'Sentence names {required}; cited {citation}. Authoritative named value: {actual}.')

    m = re.fullmatch(r'In the daily snapshot, (EUR|USD) appreciation causes the short-EUR position\x27s FX P&L of '+AMOUNT+r' in the linear model\.', statement)
    if m:
        currency, amount = m.groups()
        if citation != 'daily_fx':
            return finish('Uncheckable', 'Requires position-level FX citation.')
        if not (e['fx_delta_usd'] < 0 and e['eurusd_pct'] > 0):
            return finish('Uncheckable', 'This rule supports short EUR with rising EUR/USD only.')
        return verdict(currency == 'EUR' and equals(money(amount), e['value']),
                       'Rising EUR/USD is EUR appreciation; negative EUR delta loses in the linear model.')

    m = re.fullmatch(r'Available funding of '+AMOUNT+r' covers the specified '+AMOUNT+r' outflows for (the next day|all future horizons)\.', statement)
    if m:
        if citation != 'funding':
            return finish('Uncheckable', 'Requires scoped funding citation.')
        available, required, scope = m.groups()
        if not equals(money(available), e['available']) or not equals(money(required), e['required']):
            return finish('Mismatch', 'Funding amounts disagree with inputs.')
        if scope != 'the next day' or e['horizon'] != 'Next business day; resources unencumbered and drawable; obligations exhaustive for this horizon':
            return finish('Not established', 'Evidence covers next day only, not other horizons.')
        return verdict(e['available'] >= e['required'], 'Coverage of the specified next-day outflows only.')

    m = re.fullmatch(r'The (specified issuer default scenario|expected issuer default) loss is '+AMOUNT+r'\.', statement)
    if m:
        if citation != 'default':
            return finish('Uncheckable', 'Requires specified issuer scenario citation.')
        scope, amount = m.groups()
        if not equals(money(amount), e['value']):
            return finish('Mismatch', 'Amount differs from specified scenario loss.')
        if scope == 'expected issuer default':
            return finish('Not established', 'Scenario loss supplies no probability-weighted expected loss.')
        return finish('Scoped match', 'Specified issuer default scenario only; no forecast.')

    m = re.fullmatch(r'Portfolio CS01 of '+AMOUNT+r' per bp proves issuer concentration exceeds policy limits\.', statement)
    if m and citation == 'cs01':
        if not equals(money(m[1]), e['value']):
            return finish('Mismatch', 'CS01 amount differs.')
        return finish('Not established', 'A CS01 scalar supplies neither issuer look-through nor policy limits.')

    m = re.fullmatch(r'If issuer look-through reveals a policy breach, portfolio CS01 of '+AMOUNT+r' per bp could coexist with excessive issuer concentration\.', statement)
    if m and citation == 'cs01':
        if not equals(money(m[1]), e['value']):
            return finish('Mismatch', 'Conditional wording does not excuse a wrong factual amount.')
        return finish('Conditional hypothesis', 'Explicit possibility; issuer breach and economic validity unchecked.')

    m = re.fullmatch(r'The daily portfolio P&L of '+AMOUNT+r' proves forced liquidation caused the market moves\.', statement)
    if m and citation == 'daily_total':
        if not equals(money(m[1]), e['value']):
            return finish('Mismatch', 'Daily amount differs.')
        return finish('Not established', 'A P&L calculation does not identify the cause of its input moves.')

    m = re.fullmatch(r'If funding pressure drove sales, the daily portfolio P&L of '+AMOUNT+r' could be consistent with forced liquidation\.', statement)
    if m and citation == 'daily_total':
        if not equals(money(m[1]), e['value']):
            return finish('Mismatch', 'Conditional wording does not excuse a wrong factual amount.')
        return finish('Conditional hypothesis', 'Conditional mechanism only; causal plausibility and identification unchecked.')
    return result
