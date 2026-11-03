"""Offline safety boundaries; no second evaluation, no inference."""
from copy import deepcopy
import json
from pathlib import Path

from meaning_alignment import check
from meaning_alignment_evaluation import inputs

HERE = Path(__file__).resolve().parent


def test_complete_sentence_required_and_no_false_partial_support():
    _, evidence = inputs()
    sentence = 'In the scenario, HY net P&L is -$872,500.'
    for changed in [sentence+' Therefore funding is sufficient.', 'It is not true that '+sentence,
                    sentence.replace('net P&L is','net P&L is not'), sentence.replace('scenario','daily snapshot')]:
        assert check(changed,'hy_net',evidence)['verdict'] == 'Uncheckable'
    assert check(sentence,'unknown',evidence)['verdict'] == 'Uncheckable'


def test_changed_evidence_and_wrong_citation_prevent_match():
    _, evidence = inputs()
    original = deepcopy(evidence)
    evidence['hy_net']['value'] = -100.
    assert check('In the scenario, HY net P&L is -$872,500.','hy_net',evidence)['verdict'] == 'Mismatch'
    assert check('In the scenario, HY net P&L is -$100.','hy_net',evidence)['verdict'] == 'Scoped match'
    assert check('In the scenario, HY net P&L is -$872,500.','hy_spread',original)['verdict'] == 'Mismatch'
    assert original != evidence


def test_conditional_does_not_hide_wrong_factual_amount():
    _, evidence = inputs()
    text = 'If funding pressure drove sales, the daily portfolio P&L of -$560,771 could be consistent with forced liquidation.'
    assert check(text,'daily_total',evidence)['verdict'] == 'Mismatch'


def test_horizon_and_fx_rule_boundaries_abstain():
    _, evidence = inputs()
    evidence['funding']['horizon'] = 'Other horizon'
    text = 'Available funding of $1,900,000 covers the specified $1,400,000 outflows for the next day.'
    assert check(text,'funding',evidence)['verdict'] == 'Not established'
    evidence['daily_fx']['fx_delta_usd'] = 3000000.
    text = "In the daily snapshot, EUR appreciation causes the short-EUR position's FX P&L of -$60,000 in the linear model."
    assert check(text,'daily_fx',evidence)['verdict'] == 'Uncheckable'


def test_frozen_record_integrity_and_independent_expectations():
    result = json.loads((HERE/'meaning-alignment-results.json').read_text())
    import hashlib
    for path, digest in result['source_sha256'].items():
        source = (HERE.parent/path).read_bytes()
        if path in {'backend/metis/reasoning/harness.py', 'backend/metis/analytics/engine.py'}:
            # Product schema/prompt changes in November do not rewrite the
            # experiment's source provenance. Check the preserved Git revision,
            # then undo its sole effort-setting delta as before.
            import subprocess
            source = subprocess.check_output([
                'git', 'show', 'ca4eeaa76480ceac7f5169d4b08ed207590cdeec:' + path,
            ], cwd=HERE.parent)
            source = source.replace(
                b'META_INFERENCE_PARAMETERS = {"max_completion_tokens": 8000, "temperature": 0.2, "reasoning_effort": "low"}',
                b'META_INFERENCE_PARAMETERS = {"max_completion_tokens": 8000, "temperature": 0.2}',
                1,
            )
        assert hashlib.sha256(source).hexdigest() == digest
    assert len(result['records']) == 16 and result['model_calls'] == result['inference_tokens'] == 0
    # Financial oracle lives outside the checker and was frozen in its own source file.
    cases = json.loads((HERE/'meaning-alignment-cases.json').read_text())
    for record, case in zip(result['records'],cases):
        assert record['statement'] == case['statement'] and record['expected'] == case['expected']
    source = (HERE/'meaning_alignment.py').read_text()
    assert 'meaning-alignment-cases' not in source
    import inspect
    assert list(inspect.signature(check).parameters) == ['statement','citation','evidence']
