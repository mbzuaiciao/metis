"""Offline v4 source/stop-rule/import tests;optional pinned synthetic regression,no models."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import common
import evaluate
import score
from common import ROOT,config,sha,plan


def complete_fixture(folder,condition):
    folder.mkdir()
    manifest=dict(condition=condition,freeze_sha256=sha(ROOT/'freeze.json'),config=config(),planned_calls=40,
        model_path='/fixture',tokenizer_chat_template_sha256='fixture',
        generation_resolution=dict(use_model_defaults=False,mode='greedy_search'),
        generation_config=dict(config()['generation'],eos_token_id=151645,pad_token_id=151643))
    def fake(task):
        return dict(response='SYNTHETIC FIXTURE',completion_tokens=1,status='complete',truncated=False,
                    **evaluate.termination_metadata([151645]))
    evaluate.collect(plan(condition),fake,folder,manifest)
    return manifest


class V4Checks(unittest.TestCase):
    def test_freeze_content_and_only_one_policy_change(self):
        common.verify_freeze()
        matched=common.read_json(ROOT/'MATCHED_CONTENT.json')
        for name,digest in matched['byte_identical_to_v3'].items():
            self.assertEqual(sha(ROOT/name),digest)
            self.assertEqual((ROOT/name).read_bytes(),(ROOT.parent/'v3'/name).read_bytes())
        old=common.read_json(ROOT.parent/'v3/config.json')
        old['study']=config()['study'];old['generation']['no_repeat_ngram_size']=20
        self.assertEqual(old,config())
        self.assertFalse((ROOT/'train.py').exists())
        self.assertEqual(sha(ROOT.parent/'v3/freeze.json'),matched['parent_v3_freeze_sha256'])

    def test_same_cases_prompts_order_and_arm_controls(self):
        old_common=importlib.util.spec_from_file_location('parent_common',ROOT.parent/'v3/common.py')
        parent=importlib.util.module_from_spec(old_common);old_common.loader.exec_module(parent)
        self.assertEqual(len(common.rows('train.jsonl')),60)
        self.assertEqual(len(common.rows('heldout.jsonl')),20)
        for arm in 'ABC':
            self.assertEqual(plan(arm),parent.plan(arm));self.assertEqual(len(plan(arm)),40)
        for case in common.rows('heldout.jsonl'):
            for probe in ('knowledge','application'):
                self.assertEqual(common.messages(case,'A',probe),common.messages(case,'C',probe))
                self.assertEqual([m['role'] for m in common.messages(case,'A',probe)],['system','user'])

    def test_token_diagnostics_preserve_eos_policy(self):
        for tokens,stop in [([], 'empty_output'),([151643],'non_eos_return'),([9]*512,'non_eos_at_token_limit'),([9,151645],'eos'),([9]*511+[151645],'eos')]:
            d=evaluate.termination_metadata(tokens)
            self.assertEqual(d['generated_token_ids'],tokens);self.assertEqual(d['termination']['observed_stop'],stop)
        self.assertEqual(evaluate.termination_metadata([151643])['termination']['alternative_terminator_positions'],[0])
        r=dict(completion_tokens=2,truncated=False,**evaluate.termination_metadata([9,151645]))
        common.verify_termination_record(r)
        for change in ({'completion_tokens':1},{'generated_token_ids':[151643]}, {'termination':{}}, {'truncated':True}):
            with self.assertRaises(ValueError):common.verify_termination_record(dict(r,**change))

    def test_save_truncation_and_stop_no_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest=dict(planned_calls=40,condition='C');calls=[]
            def fake(task):
                calls.append(task)
                return dict(response='SYNTHETIC',completion_tokens=512,status='truncated',truncated=True,
                            **evaluate.termination_metadata([7]*512))
            with self.assertRaises(evaluate.TruncatedResponse):evaluate.collect(plan('C'),fake,temp,manifest)
            self.assertEqual(len(calls),1);self.assertEqual(manifest['unavailable'],39)
            record=common.read_json(next(Path(temp).glob('eval-*.json')))
            self.assertEqual(len(record['generated_token_ids']),512)
            self.assertEqual(manifest['saved'],1);self.assertEqual(manifest['status'],'incomplete')

    def test_baseline_gate_rejects_tokens_hash_config_and_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            paths=[Path(temp)/c for c in 'AB']
            for path,c in zip(paths,'AB'):complete_fixture(path,c)
            self.assertEqual(len(common.require_complete_baselines(paths)),2)
            mpath=paths[1]/'manifest.json';original=mpath.read_text()
            for key,value in [('freeze_sha256','wrong'),('status','incomplete'),('truncated',1),('config',{}),('generation_config',{})]:
                m=json.loads(original);m[key]=value;mpath.write_text(json.dumps(m))
                with self.assertRaises(ValueError):common.require_complete_baselines(paths)
            mpath.write_text(original)
            record=next(paths[1].glob('eval-*.json'));old=record.read_bytes()
            record.write_bytes(old+b' ')
            with self.assertRaises(ValueError):common.require_complete_baselines(paths)
            record.write_bytes(old);r=json.loads(old);r['generated_token_ids']=[1];record.write_text(json.dumps(r))
            with self.assertRaises(ValueError):common.require_complete_baselines(paths)
            record.unlink()
            with self.assertRaises(FileNotFoundError):common.require_complete_baselines(paths)

    def test_original_adapter_binding_not_relabelled(self):
        original=common.REPO/'research/runs/ka-v3-train-01/artifacts/train/adapter'
        binding=common.verify_adapter_import(original)
        expected=common.read_json(ROOT/'ADAPTER_IMPORT.json')
        self.assertEqual(binding['freeze_sha256'],expected['original_scientific_freeze_sha256'])
        self.assertNotEqual(binding['freeze_sha256'],sha(ROOT/'freeze.json'))
        with patch.object(common,'sha',return_value='tampered'):
            with self.assertRaises(ValueError):common.verify_adapter_import(original)

    def test_no_training_code_and_generate_boundary(self):
        for file in ROOT.glob('*.py'):ast.parse(file.read_text())
        s=(ROOT/'evaluate.py').read_text()
        self.assertIn('model.generate(**inputs, generation_config=generation, use_model_defaults=False)',s)
        self.assertNotIn('SFTTrainer',s)
        self.assertEqual((ROOT/'score.py').read_bytes(),(ROOT.parent/'v3/score.py').read_bytes())
        self.assertNotIn('generated_token_ids',(ROOT/'score.py').read_text())

    def test_actual_pinned_config_and_fourteen_checks(self):
        python=os.environ.get('METIS_TRANSFORMERS_PYTHON')
        if not python:self.skipTest('Supply existing4.56.2 interpreter;no download')
        script="""import sys
sys.path.insert(0,sys.argv[1])
def guard(event,args):
 if event in {'socket.connect','socket.getaddrinfo','subprocess.Popen','os.system'}:raise RuntimeError('FORBIDDEN')
sys.addaudithook(guard)
from generation_regression import check
r=check();assert r['checks_passed']==14 and r['identical_ABC'];print('PINNED14_OK')
"""
        r=subprocess.run([python,'-B','-c',script,str(ROOT)],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('PINNED14_OK',r.stdout)


if __name__=='__main__':unittest.main(verbosity=2)
