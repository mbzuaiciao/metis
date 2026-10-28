"""Research contracts and bounded checks; never grades live financial prose."""
import importlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'research'))
study = importlib.import_module('evidence_grounded_experiment')
ground = importlib.import_module('evidence_grounding')


def mapped(category, assertion='equals', value=None, stance='definitive', **kwargs):
    return ground.EvidenceClaim(statement='Explicit synthetic test mapping', category=category, stance=stance,
                               assertion=assertion, value=value, **kwargs)


@pytest.mark.parametrize('category', list(ground.REQUIRED))
def test_missing_evidence_and_conditional_mentions_are_distinct(category):
    assert ground.check(mapped(category), {})['verdict'] == 'Not established'
    assert ground.check(mapped(category, stance='conditional'), {})['verdict'] == 'Conditional hypothesis'
    assert ground.check(mapped(category, assertion='unavailable', stance='unknown'), {})['verdict'] == 'Not established'


def test_fresh_fixtures_engine_truth_and_supported_scopes():
    rows = study.prepare()
    assert study.BASELINE_SYSTEM == study.SYSTEM
    assert study.GROUNDED_SYSTEM == study.SYSTEM+'\n\nEvidence-grounding discipline: '+study.GROUNDING_RULES
    assert rows[0]['ground_truth']['exposures']['dv01_usd_per_bp'] == -4600
    assert rows[0]['ground_truth']['by_factor']['rates_pnl'] == 161000
    assert rows[1]['ground_truth']['by_factor']['rates_pnl'] > 0 > rows[1]['ground_truth']['total_pnl_usd']
    assert ground.check(mapped('funding', 'adequate'), rows[6]['context'])['verdict'] == 'Supported scoped conclusion'
    assert ground.check(mapped('funding', 'inadequate'), rows[6]['context'])['verdict'] == 'Contradicted'
    assert ground.check(mapped('issuer_concentration', 'concentrated'), rows[7]['context'])['verdict'] == 'Supported scoped conclusion'
    assert ground.check(mapped('issuer_concentration', value=.4), rows[7]['context'])['verdict'] == 'Supported scoped conclusion'
    assert ground.check(mapped('issuer_concentration', value=.409), rows[7]['context'])['verdict'] == 'Contradicted'
    assert ground.check(mapped('default', value=4160000.), rows[7]['context'])['verdict'] == 'Supported scoped conclusion'
    h = ground.check(mapped('hedge', 'misses_objective'), rows[8]['context'])
    assert h['verdict'] == 'Supported scoped conclusion'
    assert h['evidence']['hedge_pnl_usd'] == 80000 and h['evidence']['nonhedge_pnl_usd'] == -404000
    assert ground.check(mapped('counterparty', value=300000.), rows[9]['context'])['verdict'] == 'Supported scoped conclusion'
    for row in rows:
        assert row['ground_truth']['total_pnl_usd'] == sum(p['pnl_usd'] for p in row['context']['scenario']['positions'])
        assert 'expected_distinctions' not in row['context']


def test_invalid_evidence_does_not_become_supported():
    context = study.prepare()[7]['context']
    context['supplemental_evidence']['issuer_concentration']['issuer_amounts_usd'].pop('Issuer-C')
    assert ground.check(mapped('issuer_concentration','concentrated'), context)['verdict'] == 'Not established'
    context = study.prepare()[9]['context']
    context['supplemental_evidence']['counterparty']['netting_sets'][0]['enforceable'] = False
    assert ground.check(mapped('counterparty',value=300000.),context)['verdict'] == 'Not established'
    context = {'supplemental_evidence': {'causation': dict.fromkeys(ground.REQUIRED['causation'],'supplied')}}
    assert ground.check(mapped('causation','established'),context)['verdict'] == 'Not checked'


def test_fact_is_not_adequacy_and_mappings_do_not_check_prose():
    context = study.prepare()[2]['context']
    c = mapped('funding',value=context['portfolio']['nav_usd'],stance='fact',fact_path=['portfolio','nav_usd'])
    result = ground.check(c,context)
    assert result['verdict'] == 'Supported fact' and result['original_wording_status'] == 'Not checked'
    assert ground.check(mapped('funding','adequate'),context)['verdict'] == 'Not established'


def test_twenty_calls_pair_identity_frozen_protocol_and_failure(tmp_path, monkeypatch):
    # Keep synthetic test output isolated; do not write into the actual private archive.
    original_here = Path(__file__).resolve().parents[1]/'research'
    rows = study.prepare()
    monkeypatch.setattr(study,'prepare',lambda: rows)
    # Use a temporary mirror of just the frozen source files.
    mirror = tmp_path/'research'; mirror.mkdir()
    for p in [original_here/'evidence_grounded_experiment.py',original_here/'evidence-grounded-cases.json',original_here/'evidence_grounding.py']:
        (mirror/p.name).write_bytes(p.read_bytes())
    for name in ['reasoning/harness.py','analytics/engine.py','verification/claims.py']:
        target=tmp_path/'backend/metis'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((original_here.parent/'backend/metis'/name).read_bytes())
    monkeypatch.setattr(study,'HERE',mirror)
    monkeypatch.setattr(study,'CASES',mirror/'evidence-grounded-cases.json')
    # __file__ participates in hashes, so point to the mirrored source.
    monkeypatch.setattr(study,'__file__',str(mirror/'evidence_grounded_experiment.py'))
    output=mirror/'runs'/'fake'
    class Fake:
        model='muse-spark-1.3';base='https://example.com/v1';last_usage=None
        calls=[]
        def structured(self,request,context,schema,system,name):
            assert (output/'protocol.json').exists()
            self.calls.append((request.question,context,system,schema))
            self.last_usage=None
            if len(self.calls)==2: raise study.ProviderError('Synthetic timeout; no retry')
            return schema(summary='Test',principal_risk_observations=['Test'],economic_interpretation='Test',historical_analogies=[],potential_vulnerabilities=[],assumptions_and_uncertainties=['Test'],evidence_references=['portfolio'],financial_claims=[])
    provider=Fake()
    manifest=study.run(output,provider)
    assert manifest['attempts']==20 and manifest['successes']==19
    for a,b in zip(provider.calls[::2],provider.calls[1::2]):
        assert a[:2]==b[:2] and a[3] is b[3] is study.Interpretation
        assert 'expected_distinctions' not in json.dumps(a[1])
        assert a[2]==study.SYSTEM and b[2]==study.GROUNDED_SYSTEM
    with pytest.raises(FileExistsError):study.run(output,Fake())
