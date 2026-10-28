"""One frozen A/B run on ten fresh fixtures; at most twenty requests, no retries."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import monotonic

import pandas as pd
from dotenv import load_dotenv

from metis.analytics.engine import Shocks, calculate, exposures
from metis.reasoning.harness import HTTPProvider, Interpretation, META_INFERENCE_PARAMETERS, ProviderError, ReasoningRequest, SYSTEM
from metis.verification.claims import verify_claims
from observer_experiment import digest, write_private

HERE = Path(__file__).resolve().parent
CASES = HERE/'evidence-grounded-cases.json'
GROUNDING_RULES = '''Before concluding, check signed exposures. Distinguish asset marks, risk sensitivities, realized cash flows and contractual collateral needs. CS01 measures spread sensitivity, not default or liquidity loss. Judge hedge success/failure only against a stated objective; a positive hedge contribution need not offset total losses. Do not infer issuer concentration or net counterparty exposure without the relevant position-level, netting and collateral evidence. Separate market movements from proposed causes. When a material conclusion is not established, name the missing evidence and give the strongest useful scoped conclusion the evidence supports. Preserve supported conclusions; avoid blanket caution, repetitive disclaimers and case-specific assumptions.'''
BASELINE_SYSTEM = SYSTEM
GROUNDED_SYSTEM = SYSTEM+'\n\nEvidence-grounding discipline: '+GROUNDING_RULES


def fixture_context(case):
    frame = pd.DataFrame(deepcopy(case['positions']))
    scenario = calculate(frame, Shocks(**case['shocks']))
    return {'portfolio': {'portfolio_name': 'Isolated v1.0 research fixture', 'nav_usd': float(frame.market_value_usd.sum()),
                          'positions': frame.to_dict(orient='records'), 'exposures': exposures(frame)},
            'scenario': scenario,
            'market': {'as_of': '2026-10-20', 'label': 'Synthetic research observations, not live data', 'moves': case['shocks'],
                       'observation_status': case['observation_status']},
            'supplemental_evidence': deepcopy(case['supplemental_evidence']),
            'historical_context': [], 'alternative_scenarios': [],
            'conventions': 'USD. Positive DV01/CS01 gains when rates/spreads fall 1bp. Rates=-DV01*rates_bp; spreads=-CS01*bucket_bp; equity/FX=delta*percent/100. Sum all position/factor contributions. First-order only; no funding, liquidity, default, carry or convexity costs. No historical evidence supplied.',
            'evidence': [{'id': 'portfolio', 'description': 'Synthetic fixture positions, marks and signed sensitivities'},
                         {'id': 'scenario', 'description': 'Engine results for the supplied hypothetical factor moves'},
                         {'id': 'market', 'description': 'Synthetic changes with explicit observation status'},
                         {'id': 'supplemental', 'description': 'Additional synthetic contractual or look-through inputs, if supplied; no real measurements'}]}


def prepare():
    cases = json.loads(CASES.read_text())
    assert len(cases) == 10 and len({c['id'] for c in cases}) == 10
    old_questions = {c['question'] for c in json.loads((HERE/'observer-cases.json').read_text())}
    assert not old_questions & {c['question'] for c in cases}
    rows = []
    for case in cases:
        context = fixture_context(case)
        calc = context['scenario']
        truth = {'total_pnl_usd': calc['total_pnl_usd'], 'by_factor': calc['by_factor'],
                 'exposures': context['portfolio']['exposures'],
                 'position_pnl': {p['id']: {k: p[k] for k in ['rates_pnl','credit_pnl','equity_pnl','fx_pnl','pnl_usd']} for p in calc['positions']}}
        rows.append({'case': case, 'context': context, 'ground_truth': truth})
    return rows


def run(output_dir, provider=None):
    rows = prepare()
    if provider is None:
        if os.getenv('METIS_PROVIDER') != 'meta' or os.getenv('METIS_MODEL') != 'muse-spark-1.3':
            raise ProviderError('Requires live meta / muse-spark-1.3. No demonstration fallback.')
        provider = HTTPProvider('meta')
    if provider.model != 'muse-spark-1.3': raise ValueError('Required Muse Spark model differs')
    output_dir = Path(output_dir).resolve()
    if HERE/'runs' not in output_dir.parents: raise ValueError('Use a fresh ignored research/runs/ directory')
    output_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    paths = [Path(__file__), CASES, HERE/'evidence_grounding.py', HERE.parent/'backend/metis/reasoning/harness.py',
             HERE.parent/'backend/metis/analytics/engine.py', HERE.parent/'backend/metis/verification/claims.py']
    frozen = {'started_utc': datetime.now(timezone.utc).isoformat(), 'git_revision': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              'model': provider.model, 'endpoint': provider.base+'/chat/completions', 'settings': dict(META_INFERENCE_PARAMETERS),
              'timeout_seconds': 60, 'max_calls': 20, 'order': '01A,01B,...,10A,10B',
              'systems': {'A': BASELINE_SYSTEM, 'B': GROUNDED_SYSTEM}, 'schema': Interpretation.model_json_schema(),
              'source_sha256': {str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'cases_and_ground_truth': rows,
              'criteria': ['material financial errors','unsupported definitive conclusions','required economic distinctions omitted',
                           'main question answered','supported conclusions unnecessarily weakened','numerical consistency',
                           'calls/tokens/latency and failures; manual review, no LLM judge'],
              'input_hashes': {r['case']['id']: digest({'question': r['case']['question'], 'context': r['context']}) for r in rows}}
    write_private(output_dir/'protocol.json', frozen)  # before first call, including expectations outside inputs
    records = []
    start = monotonic()
    for row in rows:
        for condition, system in [('A', BASELINE_SYSTEM), ('B', GROUNDED_SYSTEM)]:
            context = deepcopy(row['context'])
            request = ReasoningRequest(question=row['case']['question'])
            record = {'case': row['case']['id'], 'condition': condition, 'question': request.question, 'context': context,
                      'context_sha256': digest(context), 'started_utc': datetime.now(timezone.utc).isoformat(),
                      'response': None, 'error': None, 'usage': None}
            t = monotonic()
            try:
                result = provider.structured(request, context, Interpretation, system, 'financial_interpretation')
                record['response'] = result.model_dump()
            except ProviderError as exc:
                record['error'] = str(exc)
            record['seconds'] = round(monotonic()-t, 3)
            record['usage'] = deepcopy(provider.last_usage)
            write_private(output_dir/f"{row['case']['id']}-{condition}.json", record)
            if record['response'] is not None:
                write_private(output_dir/f"{row['case']['id']}-{condition}-checks.json", {
                    'production_numeric_checks': verify_claims(result.financial_claims, context),
                    'note': 'Unchanged production verifier. Experimental evidence mappings require separate manual audit; no feedback enters inference.'})
            compact = {k: record[k] for k in ['case','condition','error','seconds','usage']}
            compact['success'] = record['response'] is not None
            records.append(compact)
            print(json.dumps(compact), flush=True)
    manifest = {'records': records, 'attempts': len(records), 'successes': sum(r['success'] for r in records),
                'finished_utc': datetime.now(timezone.utc).isoformat(), 'wall_seconds': round(monotonic()-start, 3),
                'source_unchanged': all(hashlib.sha256((HERE.parent/p).read_bytes()).hexdigest() == h for p,h in frozen['source_sha256'].items())}
    write_private(output_dir/'manifest.json', manifest)
    if not manifest['source_unchanged']: raise RuntimeError('Frozen source changed during inference')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    load_dotenv()
    run(args.output_dir)
