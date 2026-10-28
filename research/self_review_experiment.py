"""Ten self-review attempts over immutable v0.8 originals; no regeneration or retries."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import monotonic

from dotenv import load_dotenv
from pydantic import Field

from observer_experiment import INITIAL_SYSTEM, Revision, digest, model_context, write_private
from metis.reasoning.harness import HTTPProvider, Interpretation, META_INFERENCE_PARAMETERS, ProviderError, ReasoningRequest
from metis.verification.claims import FinancialClaim, verify_claims

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'runs/observer-v08-20261028'
REVIEW_INSTRUCTION='''Review your previous financial explanation carefully. Check its numerical interpretations, signed exposures, economic logic, unsupported conclusions, and important omissions.

Correct material mistakes and qualify conclusions that the evidence cannot establish. Preserve valid conclusions. Do not invent missing information.

Return the revised explanation and a short account of substantive changes. If no correction is justified, preserve the original conclusions.'''
SELF_REVIEW_SYSTEM=INITIAL_SYSTEM+'\n\n'+REVIEW_INSTRUCTION+'\nReturn substantive_changes as at most five short statements of changes; an empty list is allowed if no substantive change is justified. No private chain-of-thought is requested.'


class SelfReview(Interpretation):
    substantive_changes: list[str] = Field(max_length=5)


def source_hashes(source):
    if not source.is_dir():
        raise RuntimeError('Original v0.8 private record directory is unavailable; no reconstruction or inference permitted.')
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.iterdir()) if p.is_file()}


def load_sources(source):
    """Load exact originals/C comparisons; never recalculate their contexts."""
    try:
        protocol=json.loads((source/'protocol.json').read_text())
        manifest=json.loads((source/'manifest.json').read_text())
        cases=protocol['case_expectations_fixed_before_inference']
        if len(cases)!=10 or not manifest['all_ten_complete']:
            raise ValueError('Expected ten complete original cases')
        if protocol['model']!='muse-spark-1.3' or protocol['settings']!=META_INFERENCE_PARAMETERS:
            raise ValueError('Model/settings differ from required source experiment')
        rows=[]
        for case in cases:
            key=case['id']
            initial=json.loads((source/f'{key}-initial.json').read_text())
            observed=json.loads((source/f'{key}-observer.json').read_text())
            assisted=json.loads((source/f'{key}-C.json').read_text())
            Interpretation.model_validate(initial['response'],strict=True)
            Revision.model_validate(assisted['response'],strict=True)
            if initial['error'] or observed['error'] or assisted['error'] or initial['question']!=case['question']:
                raise ValueError('Incomplete or mismatched original records')
            if assisted['context']['original_explanation']!=initial['response']:
                raise ValueError('Observer-assisted response does not use the same original')
            rows.append({'id':key,'initial':initial,'observer':observed,'assisted':assisted})
        return protocol,manifest,cases,rows
    except (OSError,ValueError,KeyError,TypeError) as exc:
        raise RuntimeError('Required original v0.8 records are missing, invalid or incompatible; no originals were regenerated.') from exc


def self_review_context(initial):
    # Whitelist these two sources; C, observer, verifier and grading records are not used.
    return model_context(initial['context'],original=initial['response'])


def run(output_dir, *, source=SOURCE, provider=None):
    source=source.resolve()
    output_dir=output_dir.resolve()
    if output_dir==source or source in output_dir.parents:
        raise ValueError('New records must not be written inside the v0.8 source directory.')
    before=source_hashes(source)
    protocol,old_manifest,cases,rows=load_sources(source)
    if provider is None:
        if os.getenv('METIS_PROVIDER')!='meta' or os.getenv('METIS_MODEL')!='muse-spark-1.3':
            raise ProviderError('Self-review requires live meta / muse-spark-1.3; no demonstration fallback.')
        provider=HTTPProvider('meta')
    if provider.model!=protocol['model'] or provider.base+'/chat/completions'!=protocol['endpoint']:
        raise ValueError('Provider model/endpoint must match the original experiment.')
    output_dir.mkdir(parents=True,mode=0o700,exist_ok=False)
    frozen={'started_utc':datetime.now(timezone.utc).isoformat(),'model':provider.model,
            'endpoint':protocol['endpoint'],'settings':dict(META_INFERENCE_PARAMETERS),'max_new_calls':10,
            'source_directory':str(source),'source_record_sha256':before,
            'source_protocol_sha256':digest(protocol),'original_case_expectations':cases,
            'system':SELF_REVIEW_SYSTEM,'review_instruction':REVIEW_INSTRUCTION,'schema':SelfReview.model_json_schema(),
            'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'source_sha256':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'observer_experiment.py',HERE/'observer-cases.json',HERE.parent/'backend/metis/reasoning/harness.py',HERE.parent/'backend/metis/verification/claims.py']},
            'input_hashes':{row['id']:digest({'question':row['initial']['question'],'context':self_review_context(row['initial'])}) for row in rows},
            'execution_order':[row['id'] for row in rows]}
    # This preflight is immutable and written before any new inference.
    write_private(output_dir/'protocol.json',frozen)
    records=[]
    started=monotonic()
    for row in rows:
        context=self_review_context(row['initial'])
        assert not any(k in context for k in ['observer_feedback','deterministic_findings','expected_quantitative','economic_distinctions'])
        record={'case':row['id'],'question':row['initial']['question'],'context':context,
                'original_response_sha256':digest(row['initial']['response']),
                'context_sha256':digest(context),'system_sha256':digest(SELF_REVIEW_SYSTEM),
                'schema_sha256':digest(SelfReview.model_json_schema()),'response':None,'error':None,
                'started_utc':datetime.now(timezone.utc).isoformat()}
        t=monotonic()
        try:
            record['response']=provider.structured(ReasoningRequest(question=record['question']),context,SelfReview,SELF_REVIEW_SYSTEM,'financial_interpretation').model_dump()
        except ProviderError as exc:
            record['error']=str(exc)
        record['seconds']=round(monotonic()-t,3)
        record['usage']=deepcopy(provider.last_usage)
        write_private(output_dir/f"{row['id']}-self-review.json",record)
        if record['response'] is not None:
            # Posthoc numerical coverage only, never supplied to this or another call.
            checks=verify_claims([FinancialClaim.model_validate(c,strict=True) for c in record['response']['financial_claims']],row['initial']['context'])
            write_private(output_dir/f"{row['id']}-checks.json",{'results':checks,'posthoc_only':True})
        records.append({'case':row['id'],'success':record['response'] is not None,'error':record['error'],'seconds':record['seconds'],'usage':record['usage']})
        print(json.dumps(records[-1]),flush=True)
    unchanged=source_hashes(source)==before
    manifest={'started_utc':frozen['started_utc'],'finished_utc':datetime.now(timezone.utc).isoformat(),
              'completed_calls':len(records),'successful_calls':sum(r['success'] for r in records),
              'records':records,'wall_seconds':round(monotonic()-started,3),'source_records_unchanged':unchanged,
              'total_tokens_reported':sum((r['usage'] or {}).get('total_tokens',0) for r in records)}
    write_private(output_dir/'manifest.json',manifest)
    if not unchanged: raise RuntimeError('Source-record immutability check failed.')
    print(json.dumps({k:v for k,v in manifest.items() if k!='records'}),flush=True)
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,default=SOURCE)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    load_dotenv()
    run(args.output_dir,source=args.source_dir)
