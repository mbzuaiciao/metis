"""Offline wrapper checks; no Modal execution, model imports or downloads."""
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
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('execution_entry',ROOT/'execute.py')
entry=importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class ReadinessChecks(unittest.TestCase):
    def test_sources_and_private_upload_boundary(self):
        files,cfg,pins,smoke=entry.preparation()
        self.assertEqual(len(files),21)
        self.assertEqual(len(pins),7)
        self.assertEqual(cfg['model_revision'],'cdbee75f17c01a7cc42f958dc650907174af0554')
        self.assertTrue(all(p.resolve().is_relative_to(entry.REPO/'research/knowledge_application_20261101')
                            for p in files.values()))
        self.assertFalse(any('runs/' in name or '.git' in name for name in files))
        self.assertIn('research/knowledge_application_20261101/v2/train.py',files)
        self.assertEqual(entry.sha(entry.V2/'freeze.json'),entry.FREEZE)

    def test_budget_stops_and_finite_values(self):
        accounting=dict(prior_cost_upper_usd=2,prior_gpu_seconds_upper=300,additional_cost_reserve_usd=2)
        self.assertLess(entry.budget('baseline',accounting)['projected_total_usd'],20)
        for change in ({'prior_cost_upper_usd':19},{'prior_gpu_seconds_upper':14000},
                       {'prior_cost_upper_usd':float('nan')},{'additional_cost_reserve_usd':-1}):
            with self.assertRaises(ValueError): entry.budget('baseline',dict(accounting,**change))
        self.assertEqual(entry.LIMITS,dict(baseline=4200,train=4200,C=2400))
        self.assertGreater(entry.budget('baseline',accounting)['remaining_seconds_allowance'],
                           entry.budget('train',accounting)['remaining_seconds_allowance'])

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

    def test_uploaded_module_repository_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'research/knowledge_application_20261101/execution_v2/execute.py'
            path.parent.mkdir(parents=True)
            path.write_bytes((ROOT/'execute.py').read_bytes())
            mod=entry.load_module('uploaded_entry',path)
            self.assertEqual(mod.REPO,Path(temp).resolve())
            self.assertEqual(mod.V2,Path(temp).resolve()/'research/knowledge_application_20261101/v2')

    def test_no_advancement_after_incomplete_history_or_identity(self):
        good=dict(technical_status='complete',cleanup_confirmed=True,function_call_id='call',
                  remote=dict(function_call_id='call',container_id='task',input_id='input',execution_id='execution'),
                  history=[dict(nodes=[dict(function_call_id='call',task_id='task')])])
        self.assertTrue(entry.eligible(good))
        for change in ({'history':[]},{'history':[dict(error_type='fixture',nodes=[])]},
                       {'remote':{}},{'restart_or_reassignment_detected':True},
                       {'technical_status':'incomplete'},{'cleanup_confirmed':False},
                       {'diagnostic':{'type':'fixture'}}):
            self.assertFalse(entry.eligible(dict(good,**change)))

    def test_offline_plan_and_execution_prerequisite(self):
        guard='''import sys,runpy
blocked={'modal','torch','transformers','trl','peft','datasets','accelerate','huggingface_hub'}
def guard(event,args):
 if event in {'socket.connect','socket.getaddrinfo'} or (event=='import' and args[0].split('.')[0] in blocked):
  raise RuntimeError('FORBIDDEN_RUNTIME_ACCESS')
sys.addaudithook(guard)
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
'''
        for args,code in (([],0),(['--help'],0),(['--execute'],2)):
            result=subprocess.run([sys.executable,'-B','-c',guard,str(ROOT/'execute.py'),*args],
                                  capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,code,result.stderr)
            self.assertNotIn('FORBIDDEN_RUNTIME_ACCESS',result.stderr)

    def test_static_single_submit_stage_and_checks(self):
        text=(ROOT/'execute.py').read_text();tree=ast.parse(text)
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                             and n.func.attr=='spawn' for n in ast.walk(tree)),1)
        fn=next(n for n in ast.walk(tree) if isinstance(n,ast.Call)
                and isinstance(n.func,ast.Attribute) and n.func.attr=='function')
        opts={k.arg:k.value for k in fn.keywords}
        self.assertEqual(opts['gpu'].value,'L40S')
        self.assertEqual(opts['retries'].value,0)
        self.assertEqual(opts['scaledown_window'].value,2)
        self.assertEqual(opts['max_inputs'].value,1)
        self.assertNotIn('ephemeral_disk',opts)
        for marker in ('common.require_complete_baselines','check=True','local_files_only',):
            if marker=='local_files_only':
                self.assertIn(marker,(entry.V2/'evaluate.py').read_text())
            else:self.assertIn(marker,text)
        self.assertIn("'--condition','A'",text);self.assertIn("'--condition','B'",text)
        self.assertIn("'--condition','C'",text)
        self.assertNotIn('max_steps=',text)
        self.assertNotIn('SFTConfig(',text)
        self.assertNotIn('model.generate(',text)
        self.assertNotIn('add_local_dir',text)
        self.assertIn("snapshot bytes differ",text.lower())
        self.assertIn("status='INCONCLUSIVE'",text)

    def test_baseline_stage_stops_without_replacement(self):
        for mode in ('complete','A_failure','snapshot_mismatch'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);snapshot=root/'snapshot';snapshot.mkdir()
                (snapshot/'config.json').write_text('{}')
                commands=[]
                fake_modal=SimpleNamespace(current_input_id=lambda:'input-fixture',
                                           current_function_call_id=lambda:'call-fixture')
                fake_torch=SimpleNamespace(cuda=SimpleNamespace(device_count=lambda:1,
                    get_device_name=lambda:'NVIDIA L40S',is_bf16_supported=lambda:True))
                common=SimpleNamespace(verify_freeze=lambda:None,enforce_versions=lambda:None,
                    runtime_metadata=lambda:{},require_complete_baselines=lambda paths:None)
                request=dict(stage='baseline',model_id='fixture',model_revision='fixture',
                             source_files={'snapshot/config.json':entry.sha(snapshot/'config.json')},
                             smoke_pip_freeze='fixture==1\n',snapshot_sha256=
                             {} if mode=='snapshot_mismatch' else {'config.json':entry.sha(snapshot/'config.json')})
                def run(command,**kwargs):
                    commands.append(command)
                    name=command[command.index('--condition')+1]
                    if mode=='A_failure':raise subprocess.CalledProcessError(1,command)
                    out=Path(command[command.index('--out')+1]);out.mkdir()
                    (out/'manifest.json').write_text(json.dumps({'status':'complete'}))
                    self.assertTrue(kwargs['check'])
                fake_hub=SimpleNamespace(snapshot_download=lambda **kwargs:str(snapshot))
                old_path=list(sys.path)
                try:
                    with patch.object(entry,'REMOTE',str(root)),patch.dict(sys.modules,
                            {'modal':fake_modal,'torch':fake_torch,'huggingface_hub':fake_hub,'common':common}), \
                            patch.object(entry.subprocess,'run',side_effect=run), \
                            patch.object(entry.subprocess,'check_output',return_value='fixture==1\n'), \
                            patch.object(entry.shutil,'which',return_value='/fixture/git'), \
                            patch.dict(os.environ):
                        result=entry.remote_stage(request,b'')
                finally:sys.path[:]=old_path
                self.assertEqual(len(commands),2 if mode=='complete' else 1 if mode=='A_failure' else 0)
                self.assertEqual(result['report']['status'],'complete' if mode=='complete' else 'incomplete')
                self.assertTrue(result['artifacts'])
                if mode=='A_failure':
                    self.assertEqual(result['report']['diagnostic']['phase'],'A_subprocess')
                    self.assertEqual(result['report']['diagnostic']['chain'][0]['subprocess_returncode'],1)

    def test_function_configuration_unchanged_from_failed_preparation(self):
        def configuration(path):
            tree=ast.parse(path.read_text())
            return next(n for n in ast.walk(tree) if isinstance(n,ast.Call)
                        and isinstance(n.func,ast.Attribute) and n.func.attr=='function')
        self.assertEqual(ast.dump(configuration(ROOT/'execute.py')),
                         ast.dump(configuration(ROOT/'preflight_v1/execute.py')))
        old=entry.load_module('old_execution_entry',ROOT/'preflight_v1/execute.py')
        self.assertEqual(entry.LIMITS,old.LIMITS)
        self.assertEqual(entry.RATE,old.RATE)

    def test_only_git_system_layer_added(self):
        tree=ast.parse((ROOT/'execute.py').read_text())
        build=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build')
        calls=[n for n in ast.walk(build) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        apt=[n for n in calls if n.func.attr=='apt_install']
        self.assertEqual(len(apt),1)
        self.assertEqual(apt[0].func.value.id,'base_image')
        self.assertEqual([n.value for n in apt[0].args],['git'])
        self.assertEqual(apt[0].keywords,[])
        self.assertFalse(any(n.func.attr in ('uv_pip_install','pip_install','run_commands') for n in calls))
        self.assertIn("runtime_preflight(report,repo,request['source_files'])",(ROOT/'execute.py').read_text())

    def test_missing_git_and_upload_fail_before_model_import(self):
        source='research/knowledge_application_20261101/v2/common.py'
        for missing in ('git','file'):
            with self.subTest(missing=missing),tempfile.TemporaryDirectory() as temp:
                repo=Path(temp);file=repo/source
                if missing=='git':
                    file.parent.mkdir(parents=True);file.write_text('# fixture')
                report={}
                with patch.object(entry.shutil,'which',return_value=None if missing=='git' else '/fixture/git'):
                    try:entry.runtime_preflight(report,repo,{source:'fixture'})
                    except FileNotFoundError as exc:
                        diagnostic=entry.remote_diagnostic(exc,'frozen_files_and_git_preflight',{source:'fixture'})
                        self.assertEqual(diagnostic['type'],'FileNotFoundError')
                        self.assertTrue(diagnostic['caught_at_utc'])
                        self.assertTrue(diagnostic['chain'][0]['frames'])
                        if missing=='git':
                            self.assertEqual(diagnostic['chain'][0]['missing_filename'],'git')
                            self.assertIn('missing_filename=git',diagnostic['message'])
                        else:
                            # A real remote known path is retained as a public relative path.
                            with patch.object(entry,'REMOTE',str(repo)):
                                diagnostic=entry.remote_diagnostic(exc,'frozen_files_and_git_preflight',{source:'fixture'})
                            self.assertEqual(diagnostic['chain'][0]['missing_filename'],source)
                    else:self.fail('Missing dependency was accepted')
                self.assertEqual(report['preflight']['frozen_files'][source],missing=='git')
                self.assertEqual(report['preflight']['git_available'],missing!='git')

    def test_sanitized_remote_diagnostics_and_exit_code(self):
        secret='secret-fixture-value-never-record'
        source='research/knowledge_application_20261101/v2/freeze.json'
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

    def test_frozen_git_invocation_is_required_not_bypassed(self):
        import importlib.metadata
        common=entry.load_module('frozen_preflight_common',entry.V2/'common.py')
        pins=dict(s.split('==') for s in (entry.V2/'requirements.txt').read_text().splitlines()
                  if s and not s.startswith('#'))
        with patch.object(importlib.metadata,'version',side_effect=lambda name:pins[name]), \
                patch.object(common.subprocess,'check_output',side_effect=FileNotFoundError(2,'Missing','git')) as call:
            with self.assertRaises(FileNotFoundError):common.enforce_versions()
        self.assertEqual(call.call_args.args[0],['git','rev-parse','HEAD'])

    def test_runtime_preflight_exception_is_saved_and_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            source='research/knowledge_application_20261101/v2/freeze.json'
            request=dict(stage='baseline',source_files={source:'fixture'})
            fake_modal=SimpleNamespace(current_input_id=lambda:'input',current_function_call_id=lambda:'call')
            with patch.object(entry,'REMOTE',temp),patch.dict(sys.modules,{'modal':fake_modal}), \
                    patch.object(entry.shutil,'which',return_value=None), \
                    patch.object(entry.subprocess,'run') as run:
                result=entry.remote_stage(request,b'')
            self.assertEqual(result['report']['status'],'incomplete')
            self.assertEqual(result['report']['phase'],'frozen_files_and_git_preflight')
            self.assertEqual(result['report']['diagnostic']['chain'][0]['missing_filename'],source)
            self.assertEqual(run.call_count,0)
            with zipfile.ZipFile(io.BytesIO(result['artifacts'])) as archive:
                saved=json.loads(archive.read('baseline-execution.json'))
            self.assertEqual(saved,result['report'])
            self.assertEqual(saved['failure_type'],'FileNotFoundError')

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
 assert apt.call_count==3
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
