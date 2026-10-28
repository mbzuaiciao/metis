"""Research plumbing tests, never an economic model judge."""
import json
from pathlib import Path

import pytest

import importlib.util
import sys
spec=importlib.util.spec_from_file_location("observer_experiment",Path(__file__).resolve().parents[1]/"research/observer_experiment.py")
study=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=study
spec.loader.exec_module(study)
from metis.reasoning.harness import ProviderError, validate_interpretation


class FakeProvider:
    model='test-only'
    base='https://example.com/v1'
    last_usage=None
    def __init__(self,fail_observer=False):
        self.calls=[]
        self.fail_observer=fail_observer
    def structured(self,request,context,schema,system,name):
        self.calls.append((request.question,context,schema))
        self.last_usage={'prompt_tokens':10,'completion_tokens':10,'total_tokens':20}
        if schema is study.ObserverFeedback:
            if self.fail_observer:
                self.fail_observer=False
                raise ProviderError('Test-only provider failure; no fallback.')
            return schema(objections=[],evidence_references=['portfolio'])
        values={'summary':'Test fixture','principal_risk_observations':['Test observation'],
                'economic_interpretation':'Test-only explanation','historical_analogies':[],
                'potential_vulnerabilities':[],'assumptions_and_uncertainties':['Test uncertainty'],
                'evidence_references':['portfolio'],'financial_claims':[]}
        if schema is study.Revision: values['feedback_resolutions']=[]
        return schema(**values)


def test_case_keys_and_expectations_never_leak():
    cases=json.loads(study.CASES_PATH.read_text())
    assert len(cases)==10
    for case in cases:
        changed=case|{'economic_distinctions':['PRIVATE_ANSWER_KEY_SENTINEL'],'expected_quantitative':{'PRIVATE_ANSWER_KEY_SENTINEL':1}}
        facts=study.case_context(changed)
        for payload in [facts,study.model_context(facts,{'summary':'original'}),study.model_context(facts,{'summary':'original'},{'objections':[]},[])]:
            assert 'PRIVATE_ANSWER_KEY_SENTINEL' not in json.dumps(payload)
            assert 'expected_quantitative' not in payload
        assert 'commentary' not in facts['market']
        assert 'historical_context' not in facts
    assert 'daily' not in study.case_context(cases[5])


def test_all_conditions_share_initial_and_observer_and_do_not_recurse(tmp_path):
    provider=FakeProvider()
    path=tmp_path/'run'
    result=study.run(path,provider=provider)
    assert result['unique_calls']==40 and len(provider.calls)==40
    assert result['all_ten_complete']
    assert (path/'protocol.json').stat().st_mode & 0o777 == 0o600
    for i in range(0,40,4):
        initial,observer,c,d=provider.calls[i:i+4]
        assert observer[1]['original_explanation']==c[1]['original_explanation']==d[1]['original_explanation']
        assert c[1]['observer_feedback']==d[1]['observer_feedback']
        assert 'deterministic_findings' not in c[1]
        assert 'deterministic_findings' not in observer[1]
        assert d[1]['deterministic_findings']==[]
    assert all(not json.loads(p.read_text())['B_changes_explanation'] for p in path.glob('*-verification.json'))


def test_observer_failure_is_not_retried_or_fabricated(tmp_path):
    provider=FakeProvider(fail_observer=True)
    result=study.run(tmp_path/'failed',provider=provider)
    assert result['unique_calls']==38
    assert result['cases'][0]['C'] is None and result['cases'][0]['D'] is None
    assert not result['all_ten_complete']
    assert result['cases'][0]['observer']['success'] is False


def test_custom_feedback_schema_uses_existing_reference_validation():
    context={'evidence':[{'id':'portfolio'}]}
    feedback=study.ObserverFeedback(objections=[],evidence_references=['portfolio'])
    assert validate_interpretation(feedback.model_dump_json(),context,'meta',study.ObserverFeedback)==feedback
    bad=feedback.model_copy(update={'evidence_references':['private-invented']})
    with pytest.raises(ProviderError,match='unknown_evidence') as caught:
        validate_interpretation(bad.model_dump_json(),context,'meta',study.ObserverFeedback)
    assert 'private-invented' not in str(caught.value)


def test_resolution_ids_are_checked_without_scoring_content():
    feedback={'objections':[{'id':'O1'}]}
    assert study.check_resolutions({'feedback_resolutions':[{'objection_id':'O1','decision':'reject'}]},feedback)
    assert not study.check_resolutions({'feedback_resolutions':[]},feedback)
    assert not study.check_resolutions({'feedback_resolutions':[{'objection_id':'O2'}]},feedback)


def test_predefined_numeric_expectations_match_engine():
    cases=json.loads(study.CASES_PATH.read_text())
    daily=study.case_context(cases[0])['daily']
    assert daily['total_pnl_usd']==cases[0]['expected_quantitative']['daily_total']
    for index in [2,6]:
        scenario=study.case_context(cases[index])['scenario']
        key='portfolio_total' if index==2 else 'total'
        assert scenario['total_pnl_usd']==cases[index]['expected_quantitative'][key]
    comparisons=study.case_context(cases[7])['rate_comparisons']
    assert [c['total_pnl_usd'] for c in comparisons]==[2578000,-2578000]
