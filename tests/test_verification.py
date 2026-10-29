"""Deterministic bounded-assertion checks, not tests of prose or model quality."""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from metis.api.app import app
from metis.analytics.engine import Shocks
from metis.reasoning.harness import assemble_context, reason, ReasoningRequest
from metis.verification.claims import FinancialClaim, claim, demonstration_claims, verify_claim


@pytest.fixture
def context():
    return assemble_context(Shocks(rates_bp=-50,ig_bp=75,hy_bp=250,equity_pct=-15,fx_pct=-5))


def test_three_reproducible_examples_and_attached_evidence(context):
    results=[verify_claim(c,context) for c in demonstration_claims()]
    assert [r['verdict'] for r in results]==['Contradicted','Verified','Not established']
    evidence={e['path']:e['value'] for e in results[0]['evidence']}
    assert evidence['daily.shocks.rates_bp']==-8
    assert evidence['daily.by_factor.rates_pnl']==412480
    assert evidence['daily.total_pnl_usd']==-560770
    assert evidence['daily.positions[UST10].rates_pnl']==128000
    assert 'missing_inputs' in {e['path'] for e in results[2]['evidence']}


@pytest.mark.parametrize('metric,value,verdict',[
    ('total_pnl_usd',-560770,'Verified'),('total_pnl_usd',560770,'Contradicted'),
    ('rates_pnl',412480,'Verified'),('credit_pnl',-407250,'Verified'),
    ('equity_pnl',-506000,'Verified'),('fx_pnl',-60000,'Verified'),
    ('dv01_usd_per_bp',51560,'Verified'),('cs01_usd_per_bp',15950,'Verified'),
])
def test_values_against_authoritative_snapshot(context,metric,value,verdict):
    assert verify_claim(claim('Mapped amount','number',metric,'equals',value),context)['verdict']==verdict


@pytest.mark.parametrize('target,metric,assertion,verdict',[
    ('portfolio','dv01_usd_per_bp','positive','Verified'),
    ('position:IRS-P','dv01_usd_per_bp','negative','Verified'),
    ('position:IRS-P','dv01_usd_per_bp','positive','Contradicted'),
    ('position:IRS-R','rates_pnl','positive','Verified'),
    ('position:IRS-P','rates_pnl','negative','Verified'),
    ('portfolio','cs01_usd_per_bp','negative','Contradicted'),
])
def test_sensitivity_sign_and_pnl_conventions(context,target,metric,assertion,verdict):
    c=claim('Mapped sign','sign',metric,assertion,target=target)
    assert verify_claim(c,context)['verdict']==verdict


def test_credit_net_is_not_spread_only(context):
    correct=claim('HY spread-only loss is 1,112,500','number','credit_pnl','equals',-1112500,period='scenario',target='spread_bucket:hy')
    wrong=correct.model_copy(update={'value':-872500})
    net=correct.model_copy(update={'metric':'pnl_usd','value':-872500})
    assert verify_claim(correct,context)['verdict']=='Verified'
    assert verify_claim(wrong,context)['verdict']=='Contradicted'
    assert verify_claim(net,context)['verdict']=='Verified'
    evidence=verify_claim(correct,context)['evidence']
    assert {e['path'] for e in evidence} >= {'scenario.positions[HY-US].credit_pnl','scenario.positions[HY-EU].credit_pnl'}
    assert not any('.pnl_usd' in e['path'] for e in evidence)


def test_disjoint_vs_overlapping_dv01(context):
    c=claim('Exhaustive DV01 breakdown','dv01_decomposition','dv01_usd_per_bp','equals',51560,components=['asset_class:Government bonds','asset_class:Rate derivatives','spread_bucket:ig','spread_bucket:hy'])
    assert verify_claim(c,context)['verdict']=='Verified'
    overlap=c.model_copy(update={'components':['portfolio','position:IRS-R'],'value':79560})
    result=verify_claim(overlap,context)
    assert result['verdict']=='Contradicted'
    assert next(e['value'] for e in result['evidence'] if e['path']=='overlapping_position_ids')=='IRS-R'
    incomplete=c.model_copy(update={'components':['asset_class:Government bonds'],'value':18160})
    assert verify_claim(incomplete,context)['verdict']=='Contradicted'


@pytest.mark.parametrize('risk',['funding','margin','liquidity','default'])
def test_unmodeled_is_not_zero_or_inadequate(context,risk):
    for assertion in ['loss_exists','loss_absent','buffer_adequate','buffer_inadequate','loss_equals']:
        c=claim('Unmeasured assertion','unmeasured_risk','loss_usd',assertion,0 if assertion=='loss_equals' else None,target=risk)
        assert verify_claim(c,context)['verdict']=='Not established'
    c=claim('This model does not quantify this loss','unmeasured_risk','loss_usd','not_quantified',target=risk)
    assert verify_claim(c,context)['verdict']=='Verified'


@pytest.mark.parametrize('amount,rounding,verdict',[
    (-560770.01,'exact','Verified'),(-560770.02,'exact','Contradicted'),
    (-560770,'whole','Verified'),(-560771,'whole','Contradicted'),
    (-560770.5,'whole','Not checked'),(-560000,'million_2dp','Verified'),
    (-550000,'million_2dp','Contradicted'),(-560000,'unbounded','Not checked'),
])
def test_documented_absolute_rounding_tolerances(context,amount,rounding,verdict):
    c=claim('Reported rounded P&L','number','total_pnl_usd','equals',amount,rounding=rounding)
    assert verify_claim(c,context)['verdict']==verdict


@pytest.mark.parametrize('changes',[
    {'kind':'causal_probability'}, {'kind':'value'}, {'period':'future'}, {'target':'position:UNKNOWN'},
    {'metric':'value_at_risk'}, {'components':['position:UST10']},
    {'metric':'dv01_usd_per_bp','rounding':'million_2dp'},
])
def test_unsupported_mappings_are_never_verified(context,changes):
    c=claim('Outside supported mapping','number','total_pnl_usd','equals',-560770).model_copy(update=changes)
    assert verify_claim(c,context)['verdict']=='Not checked'


def test_original_text_is_never_claimed_verified_or_mutated(context):
    c=claim('A deliberately mismapped sentence says the portfolio made money.','number','total_pnl_usd','equals',-560770)
    original=deepcopy(c.model_dump())
    result=verify_claim(c,context)
    assert result['verdict']=='Verified'  # Mapped numeric assertion only.
    assert result['original_wording_status']=='Not checked'
    assert 'wording' in result['limitations'][0]
    assert c.model_dump()==original==result['claim']


def test_no_untrusted_truth_and_claims_are_optional_coverage(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER','demo')
    with TestClient(app) as client:
        demo=client.get('/api/verification-demo').json()
        assert [r['verdict'] for r in demo['results']]==['Contradicted','Verified','Not established']
        assert client.post('/api/verify-claims',json={'claims':[],'context':{'truth':1}}).status_code==422
        c=claim('Selected scenario P&L','number','total_pnl_usd','equals',-2300000,period='scenario')
        result=client.post('/api/verify-claims',json={'claims':[c.model_dump()],'shocks':{'equity_pct':-10}})
        assert result.json()['results'][0]['verdict']=='Verified'
    result=reason(ReasoningRequest(question='Explain the loss'))
    assert len(result['verification'])==len(result['interpretation']['financial_claims'])
    assert result['verification'][0]['claim']==result['interpretation']['financial_claims'][0]


def test_nonfinite_or_non_numeric_values_rejected():
    c=demonstration_claims()[0].model_dump()
    for value in [float('nan'),float('inf'),True,'private-invalid-value']:
        with pytest.raises(ValidationError):
            FinancialClaim.model_validate(c|{'value':value},strict=True)


def test_hedge_gain_does_not_establish_portfolio_profit(context):
    c=claim('A hedge gain means the portfolio is profitable','hedge_vs_total','rates_pnl','rates_gain_total_gain_yields_down')
    assert verify_claim(c,context)['verdict']=='Contradicted'


def test_provider_schema_constrains_kind_but_unknown_api_labels_remain_not_checked(context):
    schema=FinancialClaim.model_json_schema()
    assert 'number' in schema['properties']['kind']['enum']
    assert 'value' not in schema['properties']['kind']['enum']
    c=claim('A wrongly labeled numerical assertion','value','total_pnl_usd','equals',-560770)
    parsed=FinancialClaim.model_validate_json(c.model_dump_json(),strict=True)
    assert verify_claim(parsed,context)['verdict']=='Not checked'


def test_valid_evidence_ids_do_not_prove_an_incorrect_amount(context):
    context['evidence']=[{'id':'daily','description':'valid evidence ID'}]
    before=deepcopy(context)
    c=claim('Incorrect amount despite a known evidence ID','number','total_pnl_usd','equals',560770)
    assert verify_claim(c,context)['verdict']=='Contradicted'
    assert context==before


@pytest.mark.parametrize("shocks,rates,total", [
    (Shocks(rates_bp=50), -2578000, -2578000),
    (Shocks(rates_bp=50, equity_pct=20), -2578000, 2022000),
    (Shocks(), 0, 0),
])
def test_rising_and_zero_yields_preserve_documented_verification_scope(shocks, rates, total):
    context = assemble_context(shocks)
    for metric, value in [("rates_pnl", rates), ("total_pnl_usd", total)]:
        c = claim("Mapped scenario amount", "number", metric, "equals", value, period="scenario")
        assert verify_claim(c, context)["verdict"] == "Verified"
        sign = "negative" if value < 0 else "positive" if value > 0 else "zero"
        c = claim("Mapped scenario sign", "sign", metric, sign, period="scenario")
        assert verify_claim(c, context)["verdict"] == "Verified"
    # These supported composite assertions explicitly require declining yields.
    for assertion in ["rates_loss_total_loss_yields_down", "rates_gain_total_loss_yields_down", "rates_gain_total_gain_yields_down"]:
        c = claim("Falling-yield premises", "hedge_vs_total", "rates_pnl", assertion, period="scenario")
        result = verify_claim(c, context)
        assert result["verdict"] == "Contradicted"
        assert next(e["value"] for e in result["evidence"] if e["path"] == "scenario.shocks.rates_bp") == shocks.rates_bp
    c = claim("Unsupported rising-yield composite", "hedge_vs_total", "rates_pnl", "rates_loss_total_loss_yields_up", period="scenario")
    assert verify_claim(c, context)["verdict"] == "Not checked"
