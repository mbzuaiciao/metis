"""Research-only typed evidence checks. Never verifies arbitrary model prose."""
from typing import Literal
import math
from pydantic import BaseModel, ConfigDict, Field

Category = Literal['funding', 'issuer_concentration', 'counterparty', 'default', 'hedge', 'causation']
REQUIRED = {
    'funding': ['available_cash_usd', 'committed_facility_usd', 'margin_due_usd', 'other_outflows_usd', 'horizon'],
    'issuer_concentration': ['issuer_amounts_usd', 'covered_credit_mark_usd', 'threshold_share'],
    'counterparty': ['netting_sets', 'scope', 'coverage'],
    'default': ['issuer_face_usd', 'default_fraction', 'recovery_fraction', 'scope'],
    'hedge': ['hedge_position_ids', 'minimum_offset_fraction', 'scope'],
    'causation': ['identification_design', 'exogenous_variation', 'outcomes', 'confounder_controls', 'uncertainty'],
}


class EvidenceClaim(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    statement: str = Field(min_length=1, max_length=1500)
    category: Category
    stance: Literal['fact', 'conditional', 'definitive', 'unknown']
    assertion: Literal['equals', 'adequate', 'inadequate', 'concentrated', 'not_concentrated', 'meets_objective', 'misses_objective', 'established', 'unavailable']
    value: float | None = Field(default=None, ge=-1e15, le=1e15)
    # Fact mappings must name one numeric scalar; conclusions use the category calculation.
    fact_path: list[str] = Field(default_factory=list, max_length=6)


def check(c: EvidenceClaim, context: dict) -> dict:
    data = context.get('supplemental_evidence', {}).get(c.category, {})
    missing = [k for k in REQUIRED[c.category] if k not in data]
    result = {'claim': c.model_dump(), 'missing': missing, 'evidence': {},
              'original_wording_status': 'Not checked',
              'limitation': 'Only this human-specified typed mapping and scoped synthetic inputs are checked; prose equivalence, omitted claims and real-world truth are not checked.'}
    def finish(verdict, reason):
        return result | {'verdict': verdict, 'reason': reason}
    if c.stance == 'conditional':
        return finish('Conditional hypothesis', 'Possibility is not a definitive assertion; its economic validity is not verified.')
    if c.stance == 'unknown':
        return finish('Not established' if missing else 'Not checked', 'Missing evidence recorded; not a violation. Complete fields alone do not verify an uncertainty statement.')
    if c.stance == 'fact':
        if c.assertion != 'equals' or c.value is None or not c.fact_path:
            return finish('Not checked', 'A fact mapping needs an explicit scalar path and value.')
        value = context
        try:
            for key in c.fact_path: value = value[key]
        except (KeyError, TypeError):
            return finish('Not checked', 'Fact path is unavailable.')
        if type(value) not in (float, int) or not math.isfinite(value):
            return finish('Not checked', 'Only finite numerical facts are supported.')
        result['evidence'] = {'path': c.fact_path, 'value': value}
        return finish('Supported fact' if abs(value-c.value) <= .01 else 'Contradicted', 'Numeric equality only; a mark does not establish adequacy or exposure.')
    if missing:
        return finish('Not established', 'Required category evidence is unavailable.')
    if c.category == 'causation':
        return finish('Not checked', 'Presence of identification fields does not validate causal identification; expert study review is required.')
    def nonnegative(value):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('Expected nonnegative finite input')
        return value
    try:
        if c.category == 'funding':
            available = nonnegative(data['available_cash_usd']) + nonnegative(data['committed_facility_usd'])
            required = nonnegative(data['margin_due_usd']) + nonnegative(data['other_outflows_usd'])
            if not data['horizon']: raise ValueError('Missing horizon')
            value = available >= required
            assertions = {'adequate': value, 'inadequate': not value}
            result['evidence'] = {'available_usd': available, 'required_usd': required, 'scope': data['horizon']}
        elif c.category == 'issuer_concentration':
            amounts = [nonnegative(x) for x in data['issuer_amounts_usd'].values()]
            total = nonnegative(data['covered_credit_mark_usd'])
            credit_total = sum(p['market_value_usd'] for p in context['portfolio']['positions'] if p['spread_bucket'] != 'none')
            if not amounts or total <= 0 or abs(sum(amounts)-total) > .01 or abs(credit_total-total) > .01 or not 0 < data['threshold_share'] <= 1:
                raise ValueError('Incomplete issuer coverage or threshold')
            value = max(amounts)/total
            assertions = {'concentrated': value >= data['threshold_share'], 'not_concentrated': value < data['threshold_share'], 'equals': value}
            result['evidence'] = {'largest_share': value, 'threshold': data['threshold_share'], 'covered_mark_usd': total}
        elif c.category == 'counterparty':
            if data['scope'] != 'current_replacement_exposure' or not data['netting_sets'] or not data['coverage']:
                raise ValueError('Unsupported exposure scope')
            value = 0
            ids = set()
            for row in data['netting_sets']:
                if row['id'] in ids or row['enforceable'] is not True: raise ValueError('Unestablished netting')
                ids.add(row['id'])
                cost = row['net_replacement_cost_usd']
                if type(cost) not in (int, float) or not math.isfinite(cost): raise ValueError('Invalid replacement cost')
                value += max(cost-nonnegative(row['eligible_collateral_usd']), 0)
            assertions = {'equals': value}
            result['evidence'] = {'current_exposure_usd': value, 'scope': data['scope']}
        elif c.category == 'default':
            face = nonnegative(data['issuer_face_usd'])
            if not 0 <= data['default_fraction'] <= 1 or not 0 <= data['recovery_fraction'] <= 1 or data['scope'] != 'specified_issuer_default_scenario':
                raise ValueError('Invalid default scenario')
            value = face*data['default_fraction']*(1-data['recovery_fraction'])
            assertions = {'equals': value}
            result['evidence'] = {'scenario_loss_usd': value, 'scope': data['scope']}
        else:
            ids = data['hedge_position_ids']
            rows = context['scenario']['positions']
            if not ids or len(set(ids)) != len(ids) or not set(ids) <= {p['id'] for p in rows} or data['scope'] != 'fraction_of_nonhedge_scenario_loss' or not 0 < data['minimum_offset_fraction'] <= 1:
                raise ValueError('Unsupported objective')
            hedge = sum(p['pnl_usd'] for p in rows if p['id'] in ids)
            rest = sum(p['pnl_usd'] for p in rows if p['id'] not in ids)
            if rest >= 0: raise ValueError('Objective requires nonhedge loss')
            fraction = hedge/abs(rest)
            value = fraction >= data['minimum_offset_fraction']
            assertions = {'meets_objective': value, 'misses_objective': not value}
            result['evidence'] = {'hedge_pnl_usd': hedge, 'nonhedge_pnl_usd': rest, 'offset_fraction': fraction, 'required_fraction': data['minimum_offset_fraction']}
    except (KeyError, TypeError, ValueError, AttributeError):
        return finish('Not established', 'Required inputs are invalid, incomplete or outside the bounded scope.')
    if c.assertion not in assertions:
        return finish('Not checked', 'Assertion is outside this category calculation.')
    expected = assertions[c.assertion]
    if c.assertion == 'equals':
        tolerance = 1e-9 if c.category == 'issuer_concentration' else .01
        matches = c.value is not None and abs(expected-c.value) <= tolerance
    else:
        if c.value is not None: return finish('Not checked', 'Unexpected numeric value for a categorical assertion.')
        matches = expected
    return finish('Supported scoped conclusion' if matches else 'Contradicted', 'Within the exact supplied scenario/definition only; not general adequacy, future exposure, optimality or causation.')
