"""Record reuse and isolation tests; no model calls or economic grading."""
import importlib
import json
from pathlib import Path
import sys

import pytest

RESEARCH=Path(__file__).resolve().parents[1]/'research'
sys.path.insert(0,str(RESEARCH))
study=importlib.import_module('self_review_experiment')


class FakeProvider:
    model='muse-spark-1.3'
    base='https://example.com/v1'
    last_usage=None
    def __init__(self,fail_first=False):
        self.calls=[]
        self.fail_first=fail_first
    def structured(self,request,context,schema,system,name):
        self.calls.append((request.question,context))
        self.last_usage={'prompt_tokens':10,'completion_tokens':10,'total_tokens':20}
        if self.fail_first:
            self.fail_first=False
            raise study.ProviderError('Test failure, no retry.')
        return schema(**context['original_explanation'],substantive_changes=[])


def make_archive(path):
    path.mkdir()
    cases=json.loads((RESEARCH/'observer-cases.json').read_text())
    protocol={'case_expectations_fixed_before_inference':cases,'model':'muse-spark-1.3',
              'settings':study.META_INFERENCE_PARAMETERS,'endpoint':'https://example.com/v1/chat/completions'}
    (path/'protocol.json').write_text(json.dumps(protocol))
    (path/'manifest.json').write_text(json.dumps({'all_ten_complete':True}))
    for case in cases:
        initial={'question':case['question'],'error':None,'context':{'evidence':[{'id':'portfolio'}]},'response':{
            'summary':'Original fixture','principal_risk_observations':['Fixture'], 'economic_interpretation':'Original fixture',
            'historical_analogies':[],'potential_vulnerabilities':[],'assumptions_and_uncertainties':['Unknown'],
            'evidence_references':['portfolio'],'financial_claims':[]}}
        observer={'error':None,'response':{'objections':[{'statement':'OBSERVER_PRIVATE_SENTINEL'}]}}
        assisted={'error':None,'context':{'original_explanation':initial['response']},
                  'response':initial['response']|{'summary':'ASSISTED_PRIVATE_SENTINEL','feedback_resolutions':[]}}
        for suffix,value in [('initial',initial),('observer',observer),('C',assisted)]:
            (path/f"{case['id']}-{suffix}.json").write_text(json.dumps(value))


def test_ten_calls_reuse_originals_and_exclude_other_conditions(tmp_path):
    source=tmp_path/'old';make_archive(source)
    before=study.source_hashes(source)
    provider=FakeProvider()
    result=study.run(tmp_path/'new',source=source,provider=provider)
    assert result['completed_calls']==result['successful_calls']==10
    assert len(provider.calls)==10
    assert before==study.source_hashes(source)
    for question,context in provider.calls:
        text=json.dumps(context)
        assert 'OBSERVER_PRIVATE_SENTINEL' not in text and 'ASSISTED_PRIVATE_SENTINEL' not in text
        assert 'expected_quantitative' not in context and 'deterministic_findings' not in context
        assert context['original_explanation']['summary']=='Original fixture'
    assert (tmp_path/'new/protocol.json').stat().st_mode & 0o777 == 0o600


def test_missing_records_fail_before_any_inference(tmp_path):
    provider=FakeProvider()
    with pytest.raises(RuntimeError,match='unavailable'):
        study.run(tmp_path/'new',source=tmp_path/'missing',provider=provider)
    assert provider.calls==[]
    source=tmp_path/'old';make_archive(source);(source/'05-C.json').unlink()
    with pytest.raises(RuntimeError,match='missing, invalid'):
        study.run(tmp_path/'new',source=source,provider=provider)
    assert provider.calls==[]


def test_failure_is_recorded_once_and_source_never_overwritten(tmp_path):
    source=tmp_path/'old';make_archive(source)
    provider=FakeProvider(fail_first=True)
    result=study.run(tmp_path/'new',source=source,provider=provider)
    assert result['completed_calls']==10 and result['successful_calls']==9
    assert len(provider.calls)==10 and result['records'][0]['error']
    assert not (tmp_path/'new/01-checks.json').exists()
    with pytest.raises(ValueError,match='must not be written'):
        study.run(source/'nested',source=source,provider=FakeProvider())


def test_context_is_exact_deep_copy_of_original():
    initial={'context':{'portfolio':{'value':1}},'response':{'summary':'Original'}}
    context=study.self_review_context(initial)
    context['portfolio']['value']=2;context['original_explanation']['summary']='changed'
    assert initial['context']['portfolio']['value']==1 and initial['response']['summary']=='Original'
