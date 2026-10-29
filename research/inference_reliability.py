"""Eight-call compact-output comparison; no production changes or retries."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from time import monotonic

from dotenv import load_dotenv
from metis.analytics.engine import Shocks, workstation
from metis.reasoning.harness import HTTPProvider, Interpretation, META_INFERENCE_PARAMETERS, ProviderError, ReasoningRequest, SYSTEM, assemble_context
from metis.verification.claims import verify_claims
from observer_experiment import digest, write_private

HERE = Path(__file__).resolve().parent
COMPACT_OUTPUT = '''Presentation limits: keep the executive summary to two sentences and 55 words; at most three observations of 35 words each; economic interpretation at most 110 words; up to two historical analogies of 35 words each; at most two vulnerabilities of 60 words each, retaining Concern, Why it matters, Available evidence and Next investigation; at most three uncertainty items of 25 words each. State shared synthetic-date and model limitations once, not in every section. Keep up to three existing financial claims with one-sentence statements. Preserve the answer, signed exposures, essential interacting risks and material missing evidence; combine related risks rather than omit them. Do not repeat totals or caveats across fields unnecessarily.'''
COMPACT_SYSTEM = SYSTEM+'\n\n'+COMPACT_OUTPUT


def cases():
    data = workstation()
    text = (HERE.parent/'frontend/src/investigation.ts').read_text()
    daily = re.search(r'export const dailyQuestion =\s*"([^"]+)"',text).group(1)
    scenario = re.search(r'export const scenarioQuestion =\s*"([^"]+)"',text).group(1)
    broad = next(s['shocks'] for s in data['scenarios'] if s['id']=='risk-off')
    definitions = [
        ('01',daily,data['market']['daily_shocks'],['Daily -560770; rates+412480, spreads-407250, equities-506000, FX-60000. Important loss drivers and conditional economics; no established cause.']),
        ('02',scenario,broad,['Stress -3347000 versus daily -560770. Rates+2578000, spreads-1975000, equity-3450000, FX-500000. HY spread-1112500 versus net-872500.']),
        ('03','How did the receive-fixed and pay-fixed swaps behave in the daily yield decline, and what can we conclude about hedge effectiveness from the portfolio loss? Distinguish signed sensitivities, directional contributions and an unstated hedge objective.',data['market']['daily_shocks'],['Receive-fixed+224000, pay-fixed-96000, net swaps+128000. Negative payer DV01 -12000. Positive aggregate rates do not establish mandate success/failure or optimum.']),
        ('04','Can the cash balance, derivative marks and credit baskets establish funding adequacy, net counterparty exposure or issuer default losses under this stress? Give a useful scoped conclusion and the missing evidence, distinguishing marks and sensitivities from cash flows and losses.',broad,['Cash6m; no CSA/netting, collateral availability, actual calls/timing, issuer/recovery/default facts. Neither adequacy nor shortfall, net counterparty amount, concentrated issuers or default loss is established. CS01 spread only.'])]
    return [{'id':key,'question':q,'context':assemble_context(Shocks(**shocks)), 'expected':expected} for key,q,shocks,expected in definitions]


def run(output_dir, provider=None):
    rows=cases()
    if provider is None:
        if os.getenv('METIS_PROVIDER')!='meta' or os.getenv('METIS_MODEL')!='muse-spark-1.3':
            raise ProviderError('Requires live meta/muse-spark-1.3, no demonstration fallback.')
        provider=HTTPProvider('meta')
    if provider.model!='muse-spark-1.3':raise ValueError('Model differs from protocol')
    directory=Path(output_dir).resolve()
    if HERE/'runs' not in directory.parents:raise ValueError('Use ignored research/runs')
    directory.mkdir(parents=True,mode=0o700,exist_ok=False)
    paths=[Path(__file__),HERE.parent/'backend/metis/reasoning/harness.py',HERE.parent/'backend/metis/analytics/engine.py',HERE.parent/'backend/metis/verification/claims.py',HERE.parent/'frontend/src/investigation.ts',*sorted((HERE.parent/'backend/metis/data').glob('*'))]
    protocol={'started_utc':datetime.now(timezone.utc).isoformat(),'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              'model':provider.model,'endpoint':provider.base+'/chat/completions','settings':dict(META_INFERENCE_PARAMETERS),'timeout_seconds':60,
              'max_paired_calls':8,'max_integration_calls':3,'total_planned_cap':11,'user_absolute_cap':12,
              'systems':{'A':SYSTEM,'B':COMPACT_SYSTEM},'schema':Interpretation.model_json_schema(),'cases_and_expectations':rows,
              'source_sha256':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'input_hashes':{r['id']:digest({'question':r['question'],'context':r['context']}) for r in rows},
              'manual_criteria':['complete/validated; errors separate from financial quality','correct signed attribution and totals','no unsupported conclusion','adequate answer with essential risks and missing evidence','not better merely because shorter'],
              'integration_rule':'Integrate compact guidance only if B returns more complete adequate responses than A, with no material financial/usefulness regression on available pairs and acceptable token/latency costs. Equal completeness or fewer words alone is inconclusive: preserve baseline.'}
    write_private(directory/'protocol.json',protocol)
    records=[];start=monotonic()
    for row in rows:
        for condition,system in [('A',SYSTEM),('B',COMPACT_SYSTEM)]:
            record={'case':row['id'],'condition':condition,'question':row['question'],'context':deepcopy(row['context']),
                    'started_utc':datetime.now(timezone.utc).isoformat(),'response':None,'error':None,'usage':None}
            t=monotonic()
            try:
                result=provider.structured(ReasoningRequest(question=row['question']),record['context'],Interpretation,system,'financial_interpretation')
                record['response']=result.model_dump()
                record['verification']=verify_claims(result.financial_claims,record['context'])
            except ProviderError as exc:record['error']=str(exc)
            record['seconds']=round(monotonic()-t,3);record['usage']=deepcopy(provider.last_usage)
            record['serialized_response_chars']=len(json.dumps(record['response'])) if record['response'] else None
            write_private(directory/f"{row['id']}-{condition}.json",record)
            compact={k:record[k] for k in ['case','condition','error','usage','seconds','serialized_response_chars']}
            compact['success']=record['response'] is not None;records.append(compact)
            print(json.dumps(compact),flush=True)
    manifest={'records':records,'attempts':len(records),'successes':sum(r['success'] for r in records),
              'finished_utc':datetime.now(timezone.utc).isoformat(),'wall_seconds':round(monotonic()-start,3),
              'source_unchanged':all(hashlib.sha256((HERE.parent/p).read_bytes()).hexdigest()==h for p,h in protocol['source_sha256'].items())}
    write_private(directory/'manifest.json',manifest)
    if not manifest['source_unchanged']:raise RuntimeError('Frozen source changed')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args();load_dotenv('.env');run(args.output_dir)
