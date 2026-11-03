"""Bounded local comparison; never calls an inference provider or loads credentials."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter

import pandas as pd

from metis.analytics.engine import Shocks, calculate
from metis.reasoning.harness import assemble_context
from metis.verification.claims import claim, verify_claim
from evidence_grounding import EvidenceClaim, check as ground_check
from meaning_alignment import check

HERE = Path(__file__).resolve().parent


def inputs():
    context = assemble_context(Shocks(rates_bp=-50, ig_bp=75, hy_bp=250, equity_pct=-15, fx_pct=-5), investigation_date='2025-03-10')
    fixtures = json.loads((HERE/'evidence-grounded-cases.json').read_text())
    funding = fixtures[6]['supplemental_evidence']['funding']
    default = fixtures[7]['supplemental_evidence']['default']
    # Reuse input arithmetic, not previous inference outputs or evaluation verdicts.
    context['supplemental_evidence'] = {'funding': funding, 'default': default}
    hy = [p for p in context['scenario']['positions'] if p['spread_bucket'] == 'hy']
    context['fx_snapshot'] = calculate(pd.DataFrame(fixtures[7]['positions']), Shocks(**fixtures[7]['shocks']))
    fx = next(p for p in context['fx_snapshot']['positions'] if p['fx_delta_usd'] != 0)
    catalog = {
        'hy_net': {'value': sum(p['pnl_usd'] for p in hy), 'path': ['scenario', 'positions[spread_bucket=hy]', 'pnl_usd']},
        'hy_spread': {'value': sum(p['credit_pnl'] for p in hy), 'path': ['scenario', 'positions[spread_bucket=hy]', 'credit_pnl']},
        'scenario_rates': {'value': context['scenario']['by_factor']['rates_pnl'], 'path': ['scenario','by_factor','rates_pnl']},
        'scenario_total': {'value': context['scenario']['total_pnl_usd'], 'path': ['scenario','total_pnl_usd']},
        'daily_fx': {'value': fx['fx_pnl'], 'fx_delta_usd': fx['fx_delta_usd'], 'eurusd_pct': context['fx_snapshot']['shocks']['fx_pct'],
                     'path': ['fx_snapshot',f"positions[{fx['id']}]",'fx_pnl']},
        'daily_total': {'value': context['daily']['total_pnl_usd'], 'path': ['daily','total_pnl_usd']},
        'cs01': {'value': context['portfolio']['exposures']['cs01_usd_per_bp'], 'path': ['portfolio','exposures','cs01_usd_per_bp']},
        'funding': {'available': funding['available_cash_usd']+funding['committed_facility_usd'],
                    'required': funding['margin_due_usd']+funding['other_outflows_usd'], 'horizon': funding['horizon'],
                    'path': ['supplemental_evidence','funding']},
        'default': {'value': default['issuer_face_usd']*default['default_fraction']*(1-default['recovery_fraction']),
                    'path': ['supplemental_evidence','default']},
    }
    return context, catalog


def existing_checks(case, context, catalog):
    """Explicit analyst mappings: these are comparator inputs, never candidate inputs."""
    text, citation = case['statement'], case['citation']
    if citation == 'daily_fx':
        context = context | {'daily': context['fx_snapshot']}
    fx_id = next(p['id'] for p in context['fx_snapshot']['positions'] if p['fx_delta_usd'] != 0)
    specs = {
        'hy_net': ('scenario','spread_bucket:hy','pnl_usd'),
        'scenario_rates': ('scenario','portfolio','rates_pnl'),
        'daily_fx': ('daily',f'position:{fx_id}','fx_pnl'),
        'daily_total': ('daily','portfolio','total_pnl_usd'),
        'cs01': ('daily','portfolio','cs01_usd_per_bp'),
    }
    if citation in specs:
        period, target, metric = specs[citation]
        numeric = verify_claim(claim(text, 'number', metric, 'equals', float(catalog[citation]['value']), period=period, target=target), context)
    else:
        numeric = {'verdict': 'Uncheckable', 'reason': 'Supplemental calculation outside production numerical vocabulary.'}
    paths = {
        'scenario_rates': ['scenario','by_factor','rates_pnl'], 'daily_fx': ['fx_snapshot','by_factor','fx_pnl'],
        'daily_total': ['daily','total_pnl_usd'], 'cs01': ['portfolio','exposures','cs01_usd_per_bp'],
        'funding': ['supplemental_evidence','funding','available_cash_usd'],
        'default': ['supplemental_evidence','default','issuer_face_usd'],
    }
    # Fact lane compares the cited basis only. Supplemental bases are labeled explicitly.
    if citation in paths:
        path = paths[citation]
        value = context
        for key in path:
            value = value[key]
        fact = ground_check(EvidenceClaim(statement=text,category='funding',stance='fact',assertion='equals',value=float(value),fact_path=path),context)
    else:
        fact = {'verdict': 'Uncheckable', 'reason': 'Fact interface has no aggregate/list-selector path.'}
    conclusions = {
        '07': ('funding','definitive','adequate',None), '08': ('funding','definitive','adequate',None),
        '09': ('default','definitive','equals',4160000.), '10': ('default','definitive','equals',4160000.),
        '11': ('issuer_concentration','definitive','concentrated',None), '12': ('issuer_concentration','conditional','concentrated',None),
        '13': ('causation','definitive','established',None), '14': ('causation','conditional','established',None),
    }
    if case['id'] in conclusions:
        category, stance, assertion, value = conclusions[case['id']]
        conclusion = ground_check(EvidenceClaim(statement=text,category=category,stance=stance,assertion=assertion,value=value),context)
    else:
        conclusion = {'verdict': 'Uncheckable', 'reason': 'No supported conclusion vocabulary.'}
    # A faithful HUMAN remapping detects numeric attribution errors without the new checker.
    literal = {'verdict': 'Uncheckable', 'reason': 'No additional literal diagnostic specified.'}
    if case['id'] in {'02','04'}:
        metric, target, value = ('credit_pnl','spread_bucket:hy',-872500.) if case['id']=='02' else ('total_pnl_usd','portfolio',2578000.)
        literal = verify_claim(claim(text,'number',metric,'equals',value,period='scenario',target=target),context)
    return {'production_cited_fact': numeric, 'prototype_cited_fact': fact,
            'prototype_human_conclusion': conclusion, 'production_human_literal_diagnostic': literal}


def run():
    cases = json.loads((HERE/'meaning-alignment-cases.json').read_text())
    assert len(cases) == 16 and len({c['id'] for c in cases}) == 16
    context, catalog = inputs()
    sources = ['research/meaning-alignment-cases.json','research/meaning-alignment-protocol.md',
               'research/meaning_alignment.py','research/meaning_alignment_evaluation.py',
               'research/evidence_grounding.py','research/evidence-grounded-cases.json',
               'backend/metis/verification/claims.py','backend/metis/analytics/engine.py',
               'backend/metis/reasoning/harness.py','backend/metis/data/positions.csv',
               'backend/metis/data/market.json']
    hashes = {p: hashlib.sha256((HERE.parent/p).read_bytes()).hexdigest() for p in sources}
    start = perf_counter()
    records = []
    for c in cases:
        t = perf_counter()
        existing = existing_checks(c, context, catalog)
        existing_seconds = perf_counter()-t
        t = perf_counter()
        candidate = check(c['statement'], c['citation'], catalog)
        candidate_seconds = perf_counter()-t
        records.append(c | existing | {'candidate':candidate,'existing_seconds':existing_seconds,'candidate_seconds':candidate_seconds})
    flags = {'Mismatch','Not established'}
    summary = {
        'expected_counts': dict(Counter(c['expected'] for c in cases)),
        'candidate_counts': dict(Counter(r['candidate']['verdict'] for r in records)),
        'detected_errors': [r['id'] for r in records if r['expected']=='error' and r['candidate']['verdict'] in flags],
        'missed_errors': [r['id'] for r in records if r['expected']=='error' and r['candidate']['verdict'] not in flags],
        'incorrect_verdicts': [r['id'] for r in records if (r['expected']!='error' and r['candidate']['verdict'] in flags) or (r['expected']=='error' and r['candidate']['verdict']=='Scoped match')],
        'abstentions': [r['id'] for r in records if r['candidate']['verdict']=='Uncheckable'],
    }
    return {'date_utc': datetime.now(timezone.utc).isoformat(), 'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'model':None,'model_calls':0,'inference_tokens':0,'inference_latency':None,
            'source_sha256':hashes,'context_sha256':hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest(),
            'catalog':catalog,'summary':summary,'records':records,'evaluation_seconds':perf_counter()-start}


if __name__ == '__main__':
    # Refuse overwrite so a later run cannot silently replace this bounded record.
    result = run()
    output = HERE/'meaning-alignment-results.json'
    with output.open('x') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result['summary'],indent=2))
    print(f"Evaluation seconds: {result['evaluation_seconds']:.6f}")
