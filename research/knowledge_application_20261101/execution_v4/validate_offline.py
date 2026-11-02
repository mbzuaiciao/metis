"""Offline execution-only checks;no app.run,hydration,cloud or model access."""
import ast
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v4_entry',ROOT/'execute.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)

class ExecutionChecks(unittest.TestCase):
    def test_frozen_sources_private_upload_boundary(self):
        files,cfg,pins,_=entry.preparation()
        self.assertEqual(len(pins),7)
        self.assertTrue(all(p.resolve().is_relative_to(entry.V4) for p in files.values()))
        self.assertFalse(any('runs' in p.parts for p in files.values()))
        self.assertEqual(cfg['generation']['no_repeat_ngram_size'],20)
        self.assertEqual(entry.LIMITS,{'baseline':4200,'C':2400})

    def test_resources_one_submit_no_training(self):
        source=(ROOT/'execute.py').read_text();tree=ast.parse(source)
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='spawn' for n in ast.walk(tree)),1)
        f=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='function')
        kw={x.arg:x.value for x in f.keywords}
        for k,v in {'gpu':'L40S','retries':0,'max_inputs':1,'scaledown_window':2,'startup_timeout':30,'max_containers':1,'min_containers':0}.items():self.assertEqual(kw[k].value,v)
        self.assertNotIn('ephemeral_disk',kw)
        self.assertNotIn("['train.py'",source);self.assertNotIn('SFTTrainer',source)
        self.assertIn("status='INCONCLUSIVE'",source);self.assertIn('physical_history_complete=False',source)
        self.assertIn('call.cancel(terminate_containers=True)',source)

    def test_budget_gate_conservative_no_reset(self):
        a=dict(prior_cost_upper_usd=8,prior_gpu_seconds_upper=4200,additional_cost_reserve_usd=5)
        self.assertAlmostEqual(entry.budget('baseline',a)['projected_total_usd'],17.3724016)
        for change in [{'prior_cost_upper_usd':20},{'prior_gpu_seconds_upper':14000},{'prior_cost_upper_usd':float('nan')},{'additional_cost_reserve_usd':-1}]:
            with self.assertRaises(ValueError):entry.budget('baseline',dict(a,**change))

    def test_pending_acceptance_and_repair_scope_fail_closed(self):
        good=dict(freeze_sha256=entry.FREEZE,accepted=True,modal_history_limitation_accepted=True,
            post_heldout_repair_accepted=True,import_original_v3_adapter_accepted=True,human_reviewer='synthetic',accepted_at_utc='synthetic')
        entry.require_acceptance(good)
        for k in good:
            with self.assertRaises(ValueError):entry.require_acceptance(dict(good,**{k:False}))

    def test_original_adapter_archive_strips_v3_responses(self):
        data,expected=entry.load_adapter_run(entry.REPO/'research/runs/ka-v3-train-01')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(len(z.namelist()),13)
            self.assertTrue(all(n.startswith('train/') for n in z.namelist()))
            self.assertFalse(any('eval-' in n for n in z.namelist()))
            self.assertEqual(entry.hashlib.sha256(z.read('train/adapter/adapter_model.safetensors')).hexdigest(),expected['adapter_files']['adapter_model.safetensors'])
        with patch.object(entry,'sha',return_value='tampered'):
            with self.assertRaises(ValueError):entry.load_adapter_run(entry.REPO/'research/runs/ka-v3-train-01')

    def test_c_accepts_only_fresh_complete_v4_baseline_bundle(self):
        sys.path.insert(0,str(entry.V4))
        fixture=entry.load_module('v4_fixtures',entry.V4/'validate_offline.py')
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            for c in 'AB':fixture.complete_fixture(p/c,c)
            data=entry.bundle(p);entry.validate_baseline_bundle(data)
            m=json.loads((p/'A/manifest.json').read_text());m['freeze_sha256']='v3';(p/'A/manifest.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):entry.validate_baseline_bundle(entry.bundle(p))
            (p/'train').mkdir();(p/'train/forbidden').write_text('synthetic')
            with self.assertRaises(ValueError):entry.validate_baseline_bundle(entry.bundle(p))

    def test_generation_evidence_requires_actual_version_and_v4_policy(self):
        good=dict(status='passed',transformers_version='4.56.2',freeze_sha256=entry.FREEZE,
            evaluation_sha256=entry.sha(entry.V4/'evaluate.py'),regression_sha256=entry.sha(entry.V4/'generation_regression.py'),
            qwen_defaults_sha256=entry.sha(entry.V4/'QWEN_GENERATION_DEFAULTS.json'),v4_effective_mode='greedy_search',
            identical_ABC=True,generation_calls=0,forward_calls=0,model_weights_loaded=False,checks_passed=14,
            v4_effective_config=dict(json.loads((entry.V4/'config.json').read_text())['generation'],eos_token_id=151645,pad_token_id=151643))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'report.json';p.write_text(json.dumps(good));entry.require_generation_regression(p)
            for change in [{'transformers_version':'5.0'},{'freeze_sha256':'v3'},{'checks_passed':13},{'generation_calls':1},{'v4_effective_config':{}}]:
                p.write_text(json.dumps(dict(good,**change)))
                with self.assertRaises(ValueError):entry.require_generation_regression(p)

    def test_offline_plan_and_train_stage_rejected_without_optional_imports(self):
        guard='''import sys,runpy
blocked={'modal','torch','transformers','trl','peft','datasets','huggingface_hub'}
def guard(event,args):
 if event in {'socket.connect','socket.getaddrinfo'} or (event=='import' and args[0].split('.')[0] in blocked):raise RuntimeError('FORBIDDEN')
sys.addaudithook(guard);sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
'''
        for args,code in [([],0),(['--stage','C'],0),(['--stage','train'],2),(['--execute'],2)]:
            r=subprocess.run([sys.executable,'-B','-c',guard,str(ROOT/'execute.py'),*args],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,code,r.stderr);self.assertNotIn('FORBIDDEN',r.stderr)

    def test_unknown_assignment_requires_recorded_history_acceptance(self):
        good=dict(technical_status='complete',cleanup_confirmed=True,function_call_id='call',
                  remote=dict(function_call_id='call',container_id='task',input_id='input',execution_id='execution'),
                  history=[dict(nodes=[dict(function_call_id='call',task_id='task')])])
        self.assertTrue(entry.eligible(good))
        for history in ([],[dict(complete=False,nodes=[dict(function_call_id='call',task_id='',status='PENDING')])]):
            pending=dict(good,history=history,status='INCONCLUSIVE',physical_history_complete=False)
            self.assertFalse(entry.eligible(pending))
            accepted=dict(pending,request=dict(acceptance=dict(modal_history_limitation_accepted=True)))
            before=json.dumps(accepted,sort_keys=True)
            self.assertTrue(entry.eligible(accepted))
            self.assertEqual(json.dumps(accepted,sort_keys=True),before)
        for change in ({'history':[dict(error_type='fixture',nodes=[])]},
                       {'history':[dict(truncated=True,nodes=[])]},
                       {'remote':{}},{'restart_or_reassignment_detected':True},
                       {'technical_status':'incomplete'},{'cleanup_confirmed':False},
                       {'diagnostic':{'type':'fixture'}}):
            self.assertFalse(entry.eligible(dict(good,**change)))
        for key in ('function_call_id','container_id','input_id','execution_id'):
            self.assertFalse(entry.eligible(dict(good,remote=dict(good['remote'],**{key:''}))))
        # Positive conflicting assignments block even if the saved summary flag is false.
        self.assertFalse(entry.eligible(dict(good,restart_or_reassignment_detected=False,
            history=[dict(nodes=[dict(function_call_id='call',task_id='other-task')])])))

    def test_artifacts_safe_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'source').mkdir();(root/'source'/'test.txt').write_text('fixture')
            data=entry.bundle(root/'source');entry.extract(data,root/'dest')
            self.assertEqual((root/'dest/test.txt').read_text(),'fixture')
            with self.assertRaises(ValueError):entry.extract(data,root/'dest')
            for name in ('../escape','/tmp/escape'):
                stream=io.BytesIO()
                with zipfile.ZipFile(stream,'w') as archive:archive.writestr(name,'fixture')
                with self.assertRaises(ValueError):entry.extract(stream.getvalue(),root/'unsafe')

    def test_sanitized_remote_diagnostics_and_exit_code(self):
        secret='secret-fixture-value-never-record'
        source='research/knowledge_application_20261101/v4/freeze.json'
        with patch.dict(os.environ,{'TEST_SECRET':secret}):
            try:
                private_response='private-response-fixture'
                raise FileNotFoundError(2,'Missing resource token='+secret,entry.REMOTE+'/'+source)
            except FileNotFoundError as exc:
                result=entry.remote_diagnostic(exc,'frozen_file_hash_verification',{source:'fixture'})
            encoded=json.dumps(result)
            self.assertNotIn(secret,encoded)
            self.assertNotIn(private_response,encoded)
            self.assertNotIn('private_response',encoded)
            self.assertNotIn('/opt/',encoded)
            self.assertIn(source,encoded)
            self.assertEqual(result['phase'],'frozen_file_hash_verification')
        private=FileNotFoundError(2,'Missing resource','/private/customer/private.csv')
        self.assertNotIn('private.csv',json.dumps(entry.remote_diagnostic(private,'fixture',{})))
        with patch.dict(os.environ,{'TEST_SECRET':'git'}):
            self.assertNotIn('missing_filename=git',entry.remote_diagnostic(
                FileNotFoundError(2,'Missing','git'),'fixture',{})['message'])
        result=entry.remote_diagnostic(subprocess.CalledProcessError(7,['python','private-value']),
                                       'A_subprocess',{})
        self.assertEqual(result['chain'][0]['subprocess_returncode'],7)
        self.assertNotIn('private-value',json.dumps(result))

    def test_synthetic_c_plumbing_and_failure_preservation_without_runtime(self):
        from types import SimpleNamespace
        sys.path.insert(0,str(entry.V4))
        fixture=entry.load_module('v4_remote_fixtures',entry.V4/'validate_offline.py')
        import common
        imported,_=entry.load_adapter_run(entry.REPO/'research/runs/ka-v3-train-01')
        fake_modules=dict(modal=SimpleNamespace(current_input_id=lambda:'input',current_function_call_id=lambda:'call'),
            torch=SimpleNamespace(cuda=SimpleNamespace(device_count=lambda:1,get_device_name=lambda:'NVIDIA L40S',is_bf16_supported=lambda:True)))
        for fail in (False,True):
            with tempfile.TemporaryDirectory() as temp:
                temp=Path(temp);base=temp/'base';base.mkdir()
                for c in 'AB':fixture.complete_fixture(base/c,c)
                previous=entry.bundle(base);snapshot=temp/'snapshot';snapshot.mkdir()
                fake_modules['huggingface_hub']=SimpleNamespace(snapshot_download=lambda **kwargs:snapshot)
                calls=[]
                def fake_run(command,**kwargs):
                    calls.append(command)
                    self.assertIn('--condition',command);self.assertIn('C',command)
                    self.assertNotIn('train.py',' '.join(command))
                    out=Path(command[command.index('--out')+1])
                    if not fail:fixture.complete_fixture(out,'C')
                    else:
                        out.mkdir()
                        manifest=dict(planned_calls=40,condition='C')
                        def truncated(task):
                            return dict(response='SYNTHETIC',completion_tokens=512,status='truncated',truncated=True,
                                **fixture.evaluate.termination_metadata([7]*512))
                        try:fixture.evaluate.collect(common.plan('C'),truncated,out,manifest)
                        except fixture.evaluate.TruncatedResponse:raise subprocess.CalledProcessError(1,command)
                request=dict(stage='C',source_files={},adapter_bundle_sha256=entry.hashlib.sha256(imported).hexdigest(),
                    smoke_pip_freeze='fixture',model_id='fixture',model_revision='fixture',snapshot_sha256={},config=common.config())
                def output(command,**kwargs):
                    return 'No broken requirements found.' if 'check' in command else 'fixture'
                with patch.dict(sys.modules,fake_modules),patch.object(entry,'REMOTE',str(temp/'remote')),patch.object(entry,'runtime_preflight'),patch.object(common,'enforce_versions'),patch.object(common,'runtime_metadata',return_value={}),patch.object(entry.subprocess,'check_output',side_effect=output),patch.object(entry.subprocess,'run',side_effect=fake_run):
                    result=entry.remote_stage(request,previous,imported)
                self.assertEqual(len(calls),1)
                self.assertEqual(result['report']['status'],'incomplete' if fail else 'complete')
                with zipfile.ZipFile(io.BytesIO(result['artifacts'])) as z:
                    manifest=json.loads(z.read('C/manifest.json'))
                    self.assertEqual(manifest['saved'],1 if fail else 40)
                    if fail:self.assertEqual(manifest['failure_type'],'TruncatedResponse')
                    self.assertIn('train/adapter/adapter_model.safetensors',z.namelist())

    def test_installed_modal_definition_only(self):
        sdk=os.environ.get('METIS_SMOKE_SDK_PYTHON')
        if not sdk:self.skipTest('Existing Modal 1.2.3 interpreter not supplied')
        program='''import sys,importlib.util,importlib.metadata,os,json

def guard(event,args):
 if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto','subprocess.Popen','os.system'}:
  raise RuntimeError('FORBIDDEN_NETWORK_OR_PROCESS')
 if event=='import' and args[0].split('.')[0] in {'torch','transformers','trl','peft','datasets','accelerate','huggingface_hub'}:
  raise RuntimeError('FORBIDDEN_MODEL_IMPORT')
sys.addaudithook(guard)
spec=importlib.util.spec_from_file_location('execution_entry',sys.argv[1]);entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
import modal
from unittest.mock import patch
assert importlib.metadata.version('modal')=='1.2.3'
# Exact proved image ID lookup is intentionally NOT exercised offline.
# Lazy placeholder image validates native definition arguments only, with no build.
native_apt=modal.Image.apt_install
with patch.object(modal.Image,'apt_install',autospec=True,side_effect=native_apt) as apt:
 for stage in entry.LIMITS:
  app,fn=entry.build(stage,{},modal.Image.debian_slim(python_version='3.12'))
  assert app.app_id is None and not fn.is_hydrated
  assert fn.spec.ephemeral_disk is None
  assert fn.spec.gpus=='L40S'
 assert apt.call_count==2
 assert all(call.args[1:]==('git',) and not call.kwargs for call in apt.call_args_list)
print('LOCAL_DEFINITIONS_OK')
'''
        env={k:v for k,v in os.environ.items() if not k.startswith('MODAL_')}
        env.update(MODAL_CONFIG_PATH=os.devnull,MODAL_PROFILE='default',PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sdk,'-B','-c',program,str(ROOT/'execute.py')],env=env,
                              text=True,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('LOCAL_DEFINITIONS_OK',result.stdout)


if __name__=='__main__':unittest.main(verbosity=2)
