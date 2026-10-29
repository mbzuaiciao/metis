"""Bounded research runner and existing workstation contracts, no live model."""
import importlib
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
s=importlib.import_module('inference_reliability')


def test_representative_inputs_use_production_context_and_baseline():
    rows=s.cases()
    assert len(rows)==4
    assert rows[0]['context']['scenario']['total_pnl_usd']==-560770
    assert rows[1]['context']['scenario']['total_pnl_usd']==-3347000
    assert rows[2]['context']==rows[0]['context']
    assert rows[3]['context']==rows[1]['context']
    assert 'expected' not in rows[0]['context']
    assert s.COMPACT_SYSTEM==s.SYSTEM+'\n\n'+s.COMPACT_OUTPUT
    assert s.META_INFERENCE_PARAMETERS=={'max_completion_tokens':8000,'temperature':.2,'reasoning_effort':'low'}


def test_eight_attempts_frozen_before_calls_no_retry(tmp_path,monkeypatch):
    real=s.HERE;rows=s.cases();monkeypatch.setattr(s,'cases',lambda:rows)
    mirror=tmp_path/'research';mirror.mkdir()
    for relative in ['research/inference_reliability.py','backend/metis/reasoning/harness.py','backend/metis/analytics/engine.py','backend/metis/verification/claims.py','frontend/src/investigation.ts']:
        p=tmp_path/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((real.parent/relative).read_bytes())
    monkeypatch.setattr(s,'HERE',mirror);monkeypatch.setattr(s,'__file__',str(mirror/'inference_reliability.py'))
    out=mirror/'runs/fake'
    class Fake:
        model='muse-spark-1.3';base='https://example.com/v1';last_usage=None
        def __init__(self):self.calls=[]
        def structured(self,request,context,schema,system,name):
            assert (out/'protocol.json').exists();self.calls.append((request.question,context,system))
            self.last_usage={'completion_tokens':8000}
            if len(self.calls)==2:raise s.ProviderError('Synthetic truncated failure')
            return schema(summary='Fixture',principal_risk_observations=['Fixture'],economic_interpretation='Fixture',historical_analogies=[],potential_vulnerabilities=[],assumptions_and_uncertainties=['Fixture'],evidence_references=['portfolio'],financial_claims=[])
    fake=Fake();m=s.run(out,fake)
    assert m['attempts']==8 and m['successes']==7 and len(fake.calls)==8
    for a,b in zip(fake.calls[::2],fake.calls[1::2]):assert a[:2]==b[:2]
    with pytest.raises(FileExistsError):s.run(out,Fake())


def test_demo_host_three_attempt_guard_and_simulated_failure(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    host=importlib.import_module('demo_readiness_host')
    monkeypatch.setenv('METIS_PROVIDER','demo')
    static=tmp_path/'frontend/dist';static.mkdir(parents=True)
    (static/'index.html').write_text('<html>Unit-test fixture</html>')
    monkeypatch.setattr(host,'ROOT',tmp_path)
    (tmp_path/'manifest.json').write_text(json.dumps({'attempts':8}))
    app=host.create_host(tmp_path)
    with TestClient(app) as client:
        assert client.get('/').status_code==200
        for _ in range(2):
            r=client.post('/api/reasoning',json={'question':'Explain the illustrative daily portfolio loss.'})
            assert r.status_code==200 and r.json()['mode']=='demo'
        r=client.post('/api/causal-exploration',json={'hypothesis':'Recession fears','alternative':'Inflation relief','common_rates_bp':-50})
        assert r.status_code==200
        r=client.post('/api/reasoning',json={'question':'This is simulated only.'})
        assert r.status_code==502 and 'no Meta request' in r.json()['detail']
        assert client.get('/missing-static-file').status_code==404
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses=list(pool.map(lambda bp:client.post('/api/scenario',json={'rates_bp':bp}),[-50,50]))
        assert [r.status_code for r in responses]==[200,200]
    assert len(list(tmp_path.glob('integration-*-start.json')))==3
    assert len(list(tmp_path.glob('ui-*-response.json')))==5
