"""Standard-library-only checks. Never imports Modal, Torch or any model library."""
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


entry = module('smoke_entry', ROOT / 'modal_smoke.py')
runtime = module('synthetic_runtime', ROOT / 'smoke_runtime.py')


class SmokePreparationChecks(unittest.TestCase):
    def test_frozen_config_and_pins(self):
        cfg, pins, hashes = entry.preparation()
        self.assertEqual(cfg['study'], 'metis-knowledge-application-20261101-v2')
        self.assertEqual((cfg['model_id'],cfg['model_revision']), (runtime.MODEL_ID,runtime.REVISION))
        self.assertEqual(len(pins),7)
        self.assertEqual(cfg['training']['gradient_accumulation_steps'],4)
        self.assertEqual(cfg['training']['batch_size'],1)
        self.assertEqual(cfg['lora']['r'],16)
        self.assertEqual(set(hashes), {'config.json','requirements.txt'})
        with patch.object(entry,'V2_FREEZE_SHA256','bad'):
            self.assertRaises(ValueError,entry.preparation)

    def test_no_model_import_or_network_in_plan_mode(self):
        guard = '''import sys,runpy,json
blocked={'modal','torch','transformers','trl','peft','datasets','accelerate','huggingface_hub'}
def guard(event,args):
 if event=='socket.connect' or (event=='import' and args[0].split('.')[0] in blocked):
  raise RuntimeError('FORBIDDEN_RUNTIME_ACCESS')
sys.addaudithook(guard)
sys.argv=json.loads(sys.argv[1])
runpy.run_path(sys.argv[0],run_name='__main__')
'''
        with tempfile.TemporaryDirectory(prefix='metis-smoke-offline-') as temp:
            out=Path(temp)/'not-created'
            for flags,code in (([],0),(['--help'],0)):
                result=subprocess.run([sys.executable,'-c',guard,
                    json.dumps([str(ROOT/'modal_smoke.py'),*flags])],cwd=entry.REPO,
                    text=True,capture_output=True,timeout=5)
                self.assertEqual(result.returncode,code,result.stderr)
                self.assertNotIn('FORBIDDEN_RUNTIME_ACCESS',result.stderr)
                self.assertFalse(out.exists())

    def test_syntax_and_import_boundaries(self):
        for path in ROOT.glob('*.py'):
            tree=ast.parse(path.read_text(),filename=str(path))
            for node in tree.body:
                if isinstance(node,ast.Import): names=[n.name.split('.')[0] for n in node.names]
                elif isinstance(node,ast.ImportFrom): names=[(node.module or '').split('.')[0]]
                else: continue
                self.assertFalse(set(names)&{'modal','torch','transformers','trl','peft','datasets','accelerate','huggingface_hub'})
        tree=ast.parse((ROOT/'modal_smoke.py').read_text())
        remote_calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
                      and isinstance(n.func,ast.Attribute) and n.func.attr=='spawn']
        self.assertEqual(len(remote_calls),1)
        self.assertNotIn('BLOCKERS', (ROOT/'modal_smoke.py').read_text())
        # Main dispatches once; submission itself is separately tested with fake SDK handles.
        with patch.object(sys,'argv',['modal_smoke.py','--execute']), \
                patch.object(entry,'launch_candidate',return_value=dict(status='INCONCLUSIVE',
                    technical_status='passed',submission_id='fixture',reasons=['ambiguous'])) as launch, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(entry.main(),2)
            self.assertEqual(launch.call_count,1)

    def test_exact_completion_mask(self):
        runtime.check_mask([1,2,3],[1,2,3,4,99],[-100,-100,-100,4,99],99)
        for prompt,full,labels in (
            ([1,2],[1,3,4,99],[-100,-100,4,99]),
            ([1,2],[1,2,4,99],[-100,2,4,99]),
            ([1,2],[1,2,4,99],[-100,-100,-100,99]),
            ([1,2],[1,2,4,99],[-100,-100,5,99]),
            ([1,2],[1,2,4,98],[-100,-100,4,98]),
            ([1,2],[1,2],[-100,-100]),
        ):
            with self.assertRaises(ValueError): runtime.check_mask(prompt,full,labels,99)

    def test_gpu_lifetime_and_single_step(self):
        options=entry.FUNCTION_OPTIONS
        self.assertEqual(options['gpu'],'L40S')
        self.assertEqual(options['retries'],0)
        self.assertEqual(options['max_containers'],1)
        self.assertEqual(options['max_inputs'],1)
        self.assertEqual(options['min_containers'],0)
        self.assertEqual(options['buffer_containers'],0)
        self.assertEqual(options['scaledown_window'],2)
        self.assertEqual(options['cpu'],(2.0,2.0))
        self.assertEqual(options['memory'],(32768,32768))
        self.assertLessEqual(options['timeout']+options['startup_timeout']+options['scaledown_window'],900)
        self.assertEqual(runtime.WATCHDOG_SECONDS, options['timeout'])
        self.assertEqual(runtime.MAX_STEPS,1)
        text=(ROOT/'smoke_runtime.py').read_text()
        tree=ast.parse(text)
        train_calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
                     and isinstance(n.func,ast.Attribute) and n.func.attr=='train']
        self.assertEqual(len(train_calls),1)
        sft=next(n for n in ast.walk(tree) if isinstance(n,ast.Call)
                 and isinstance(n.func,ast.Name) and n.func.id=='SFTConfig')
        keywords={n.arg:n.value for n in sft.keywords}
        self.assertEqual(keywords['max_steps'].id,'MAX_STEPS')
        self.assertTrue(keywords['completion_only_loss'].value)
        self.assertFalse(keywords['assistant_only_loss'].value)
        self.assertFalse(keywords['packing'].value)
        self.assertTrue(keywords['bf16'].value)
        self.assertFalse(keywords['fp16'].value)
        for key in ('learning_rate','gradient_accumulation_steps','warmup_steps','weight_decay',
                    'lr_scheduler_type','max_grad_norm','num_train_epochs'):
            self.assertIsInstance(keywords[key],ast.Subscript)
        self.assertIn('forward_backward_microbatches',text)
        self.assertIn("report['optimizer_steps'] > MAX_STEPS",text)
        self.assertIn("param._version != frozen_versions[name]",text)
        self.assertIn('torch.isfinite(logits).all()',text)

    def test_scaledown_server_range_preflight(self):
        for value in (2,3600):
            entry.validate_function_options(dict(scaledown_window=value))
        for value in (0,1,3601,None,True,2.0,'2'):
            with self.subTest(value=value),patch.dict(entry.FUNCTION_OPTIONS,scaledown_window=value):
                with self.assertRaisesRegex(ValueError,'scaledown_window'):
                    entry.build_candidate([])
                with self.assertRaisesRegex(ValueError,'scaledown_window'):
                    entry.preparation()

    def test_default_disk_preflight_and_only_option_change(self):
        old=module('previous_entry',ROOT/'policy_v4'/'modal_smoke.py')
        expected=dict(old.FUNCTION_OPTIONS)
        self.assertEqual(expected.pop('ephemeral_disk'),51200)
        self.assertEqual(entry.FUNCTION_OPTIONS,expected)
        entry.validate_function_options()
        entry.validate_function_options(dict(entry.FUNCTION_OPTIONS,ephemeral_disk=None))
        # Reject unsupported sizes and any unreviewed explicit quota for this smoke.
        for value in (0,51200,524287,3145729,524288,3145728,True,51200.0,'51200'):
            with self.subTest(value=value),patch.dict(entry.FUNCTION_OPTIONS,ephemeral_disk=value):
                with self.assertRaisesRegex(ValueError,'default ephemeral_disk'):
                    entry.build_candidate([])
                with self.assertRaisesRegex(ValueError,'default ephemeral_disk'):
                    entry.preparation()
        self.assertEqual((ROOT/'smoke_runtime.py').read_bytes(),
                         (ROOT/'policy_v4'/'smoke_runtime.py').read_bytes())

    def test_public_configuration_names_without_private_values(self):
        import os
        for name in entry.PUBLIC_MODAL_FIELDS:
            for quote in ('"',"'",'`'):
                message='Function '+quote+name+quote+' must be between 2 and 3600 (inclusive).'
                self.assertIn(name,entry.sanitize(message))
        self.assertIn('scaledown_window',entry.sanitize(
            "Function's `scaledown_window` must be between 2 and 3600 (inclusive)."))
        self.assertNotIn('private-value',entry.sanitize('timeout="private-value"'))
        self.assertNotIn('scaledown_window',entry.sanitize('private_data="scaledown_window"'))
        with patch.dict(os.environ,{'METIS_TEST_SECRET':'scaledown_window'}):
            self.assertNotIn('scaledown_window',entry.sanitize('Function `scaledown_window` invalid'))

    def test_upload_allowlist_and_no_case_access(self):
        entry_tree=ast.parse((ROOT/'modal_smoke.py').read_text())
        uploads=[n for n in ast.walk(entry_tree) if isinstance(n,ast.Call)
                 and isinstance(n.func,ast.Attribute) and n.func.attr=='add_local_file']
        self.assertEqual(len(uploads),3)
        remote_names={n.args[1].value for n in uploads}
        self.assertEqual(remote_names,{'/opt/metis-smoke/smoke_runtime.py',
                         '/opt/metis-smoke/config.json','/opt/metis-smoke/requirements.txt'})
        for name in ('modal_smoke.py','smoke_runtime.py'):
            text=(ROOT/name).read_text()
            for forbidden in ('train.jsonl','heldout.jsonl','from common','import metis',
                              'add_local_dir','add_local_python_source','Secret.from','Volume.',
                              '.deploy(','.map(','.generate('):
                self.assertNotIn(forbidden,text)
        self.assertEqual(runtime.SYNTHETIC_USER,'Return exactly the label: cobalt.')
        self.assertEqual(runtime.SYNTHETIC_TARGET,'cobalt.')
        result=subprocess.run(['git','check-ignore','research/runs/ka-modal-smoke-v2-01'],
                              cwd=entry.REPO,text=True,capture_output=True)
        self.assertEqual(result.returncode,0)

    def test_original_technical_checks_preserved(self):
        old=ast.parse((ROOT/'policy_v1'/'smoke_runtime.py').read_text())
        new=ast.parse((ROOT/'smoke_runtime.py').read_text())
        for name in ('check_mask','verify_versions','OneStepChecks'):
            a=next(n for n in ast.walk(old) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
            b=next(n for n in ast.walk(new) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
            self.assertEqual(ast.dump(a),ast.dump(b),name)
        def configuration(tree):
            return next(n for n in ast.walk(tree) if isinstance(n,ast.Call)
                        and isinstance(n.func,ast.Name) and n.func.id=='SFTConfig')
        self.assertEqual(ast.dump(configuration(old)),ast.dump(configuration(new)))
        for expression in ('param._version != frozen_versions[name]',
                           'torch.equal(state[n].cpu(),saved[n])',
                           'torch.isfinite(logits).all().item()',
                           "tokenizer.eos_token_id != 151645",
                           "batch['input_ids'][0].tolist() != full_ids"):
            self.assertIn(expression,(ROOT/'smoke_runtime.py').read_text())

    @staticmethod
    def complete_result(submission='submission', call='fc-1', task='task-1'):
        return dict(status='INCONCLUSIVE',technical_status='passed',optimizer_steps=1,
                    forward_backward_microbatches=4,base_frozen_checks_passed=True,
                    reload_exact=True,finite_reload_logits=True,termination_status='returned_normal',
                    execution=dict(submission_id=submission,function_call_id=call,input_id='in-1',
                                   container_id=task,execution_id='exec-1',started_at_utc='fixture-utc'))

    def test_ambiguous_restart_or_incomplete_cannot_pass(self):
        success=dict(nodes=[dict(function_call_id='fc-1',input_id='in-1',task_id='task-1',status='SUCCESS')],
                     complete=False)
        for result in (None, {}, [], 'malformed', dict(execution=None), self.complete_result()):
            verdict=entry.assess(result,'submission','fc-1',[success],
                                 'result_received','cancel_requested_and_app_context_exited')
            self.assertEqual(verdict['status'],'INCONCLUSIVE')
            self.assertFalse(verdict['physical_history_complete'])
        passed=entry.assess(self.complete_result(),'submission','fc-1',[success],
                            'result_received','cancel_requested_and_app_context_exited')
        self.assertEqual(passed['technical_status'],'passed')
        graph2=dict(nodes=[dict(function_call_id='fc-1',input_id='in-1',task_id='task-2',status='SUCCESS')])
        restarted=entry.assess(self.complete_result(),'submission','fc-1',[success,graph2],
                               'result_received','cancel_requested_and_app_context_exited')
        self.assertTrue(restarted['restart_or_reassignment_detected'])
        self.assertEqual(restarted['status'],'INCONCLUSIVE')
        for change in ({'optimizer_steps':0},{'finite_reload_logits':False},
                       {'termination_status':'signal_interruption','signal_observed':15},
                       {'technical_status':'failed'}):
            result=self.complete_result();result.update(change)
            verdict=entry.assess(result,'submission','fc-1',[],'result_received','cancel_request_failed')
            self.assertEqual(verdict['status'],'INCONCLUSIVE')
            self.assertEqual(verdict['technical_status'],'failed_or_incomplete')

    def test_history_snapshot_unavailable_and_task_changes(self):
        node=SimpleNamespace(input_id='in-1',function_call_id='fc-1',task_id='task-1',
                             status=SimpleNamespace(name='SUCCESS'),children=[])
        class Call:
            def get_call_graph(self): return [node]
        snap=entry.history_snapshot(Call())
        self.assertFalse(snap['complete'])
        self.assertEqual(snap['nodes'][0]['task_id'],'task-1')
        class Missing:
            def get_call_graph(self): raise RuntimeError('offline fixture')
        self.assertEqual(entry.history_snapshot(Missing())['error_type'],'RuntimeError')

    def test_single_submission_exception_cleanup_and_no_resubmission(self):
        for mode in ('complete','restart','get_error','spawn_error','graph_error','cleanup_error'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='metis-policy-offline-') as temp:
                repo=Path(temp)
                calls=dict(spawn=0,get=0,cancel=0,graph=0,app_exit=0)
                class Call:
                    object_id='fc-1'
                    def get_call_graph(self):
                        calls['graph']+=1
                        if mode=='graph_error': raise RuntimeError('offline graph unavailable')
                        task='task-2' if mode=='restart' and calls['graph']>1 else 'task-1'
                        return [SimpleNamespace(function_call_id='fc-1',input_id='in-1',task_id=task,
                                  status=SimpleNamespace(name='SUCCESS'),children=[])]
                    def get(self,timeout=None):
                        calls['get']+=1
                        self_timeout=timeout
                        if self_timeout!=900: raise AssertionError('unexpected wait cap')
                        if mode=='get_error': raise TimeoutError('offline timeout')
                        return SmokePreparationChecks.complete_result(submission=submission[0])
                    def cancel(self,terminate_containers=False):
                        calls['cancel']+=1
                        if not terminate_containers: raise AssertionError('must request container termination')
                        if mode=='cleanup_error': raise RuntimeError('offline cleanup failure')
                submission=[]
                class Function:
                    object_id='fu-1'
                    def spawn(self,hashes,sid):
                        calls['spawn']+=1;submission.append(sid)
                        if mode=='spawn_error': raise RuntimeError('offline acknowledgement lost')
                        return Call()
                class App:
                    app_id='ap-1'
                    @contextlib.contextmanager
                    def run(self):
                        try: yield
                        finally: calls['app_exit']+=1
                out=repo/'research'/'runs'/'fixture'
                with patch.object(entry,'REPO',repo),patch.object(entry,'build_candidate',return_value=(App(),Function())), \
                        patch.object(entry,'initialization_output',side_effect=contextlib.nullcontext), \
                        contextlib.redirect_stderr(io.StringIO()):
                    result=entry.launch_candidate([],{},out)
                    self.assertEqual(calls['spawn'],1)
                    self.assertEqual(calls['app_exit'],1)
                    self.assertEqual(calls['get'],0 if mode=='spawn_error' else 1)
                    self.assertEqual(calls['cancel'],0 if mode=='spawn_error' else 1)
                    self.assertEqual(result['intentional_submissions'],1)
                    self.assertEqual(result['status'],'INCONCLUSIVE')
                    self.assertEqual(json.loads((out/'report.json').read_text())['status'],'INCONCLUSIVE')
                    self.assertEqual(result['restart_or_reassignment_detected'],mode=='restart')
                    if mode=='complete': self.assertEqual(result['technical_status'],'passed')
                    # Reusing an output directory fails before building/submitting again.
                    with self.assertRaises(FileExistsError): entry.launch_candidate([],{},out)
                    self.assertEqual(calls['spawn'],1)

    def test_runtime_metadata_allowlist(self):
        # Fake only the two documented ID calls; no actual Modal import or resource access.
        fake=SimpleNamespace(current_input_id=lambda:'in-1',current_function_call_id=lambda:'fc-1')
        import os
        with patch.dict(sys.modules,{'modal':fake}),patch.dict(os.environ,
                {'MODAL_TASK_ID':'task-1','MODAL_IDENTITY_TOKEN':'MUST_NOT_BE_RECORDED'}):
            meta=runtime.execution_metadata('submission')
        self.assertEqual(meta['input_id'],'in-1')
        self.assertEqual(meta['container_id'],'task-1')
        self.assertNotIn('MUST_NOT_BE_RECORDED',json.dumps(meta))
        self.assertTrue(meta['execution_id'])
        self.assertTrue(meta['started_at_utc'])

    def test_sanitized_message_traceback_and_fragmented_terminal(self):
        import os
        secret='sentinel-auth-value-should-not-escape'
        private='sentinel private payload'
        with patch.dict(os.environ,{'METIS_TEST_SECRET':secret,'METIS_TEST_PRIVATE_DATA':private}):
            try:
                local_sensitive_value=secret
                raise ValueError('Invalid resource configuration; token='+secret+
                                 ' payload="'+private+'" path=/Users/person/private/report.txt')
            except ValueError as exc:
                diagnostic=entry.exception_diagnostic(exc,'app_initialization')
            encoded=json.dumps(diagnostic)
            self.assertNotIn(secret,encoded)
            self.assertNotIn(private,encoded)
            self.assertNotIn('local_sensitive_value',encoded)
            self.assertNotIn('/Users/person',encoded)
            self.assertEqual(diagnostic['phase'],'app_initialization')
            self.assertEqual(diagnostic['type'],'ValueError')
            self.assertIn('Invalid resource configuration',diagnostic['message'])
            self.assertIn('validate_offline.py',diagnostic['traceback'])
            self.assertTrue(diagnostic['chain'][0]['frames'])
            target=io.StringIO();stream=entry.RedactedOutput(target)
            stream.write('initializing token='+secret[:12]);stream.flush()
            self.assertEqual(target.getvalue(),'')
            stream.write(secret[12:]+'\n');stream.finish()
            self.assertNotIn(secret,target.getvalue())
            self.assertIn('REDACTED',target.getvalue())
        for value in ('Bearer as-abcdefghijklmnop', 'https://user:password@example.test/path?key=abc',
                      'email@example.test', 'private_data=some-private-text'):
            self.assertNotIn(value,entry.sanitize(value))

    def test_each_failure_phase_is_preserved_before_cleanup(self):
        for mode,wanted,submits in (
            ('construction','local_construction',0),('initialization','app_initialization',0),
            ('submission','submission',1),('retrieval','result_retrieval',1),
            ('cleanup','call_cleanup',1),('shutdown','app_shutdown',1)):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='metis-diagnostic-offline-') as temp:
                repo=Path(temp);counts={'spawn':0}
                class InvalidError(Exception): pass
                def fail(): raise InvalidError('Invalid resource configuration; token=as-private-sentinel')
                class Call:
                    object_id='fc-1'
                    def get_call_graph(self): return []
                    def get(self,timeout=None):
                        if mode=='retrieval': fail()
                        return None
                    def cancel(self,terminate_containers=False):
                        if mode=='cleanup': fail()
                class Function:
                    object_id='fu-1'
                    def spawn(self,*args):
                        counts['spawn']+=1
                        if mode=='submission': fail()
                        return Call()
                class App:
                    app_id='ap-1'
                    @contextlib.contextmanager
                    def run(self):
                        if mode=='initialization': fail()
                        yield
                        if mode=='shutdown': fail()
                def build(pins):
                    if mode=='construction': fail()
                    return App(),Function()
                out=repo/'research'/'runs'/'new-attempt'
                with patch.object(entry,'REPO',repo),patch.object(entry,'build_candidate',side_effect=build), \
                        patch.object(entry,'initialization_output',side_effect=contextlib.nullcontext), \
                        contextlib.redirect_stderr(io.StringIO()):
                    record=entry.launch_candidate([],{},out)
                saved=json.loads((out/'report.json').read_text())
                self.assertEqual(saved['error_phase'],wanted)
                self.assertEqual(saved['local_error_type'],'InvalidError')
                self.assertIn('Invalid resource configuration',saved['exception_message'])
                self.assertIn('validate_offline.py',saved['traceback'])
                self.assertNotIn('as-private-sentinel',json.dumps(saved))
                self.assertEqual(counts['spawn'],submits)
                self.assertEqual(saved['intentional_submissions'],submits)
                self.assertEqual(saved['status'],'INCONCLUSIVE')
                self.assertTrue(saved['phase_history'])

    def test_installed_sdk_123_definition_and_output_context_offline(self):
        import os
        sdk_python=os.environ.get('METIS_SMOKE_SDK_PYTHON')
        if not sdk_python:
            self.skipTest('Set METIS_SMOKE_SDK_PYTHON to an existing Modal 1.2.3 interpreter; never installs it')
        program="""import sys,importlib.util,importlib.metadata,io,contextlib,json

def guard(event,args):
 if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto','subprocess.Popen','os.system'}:
  raise RuntimeError('FORBIDDEN_NETWORK_OR_PROCESS')
 if event=='import' and args[0].split('.')[0] in {'torch','transformers','trl','peft','datasets','accelerate','huggingface_hub'}:
  raise RuntimeError('FORBIDDEN_MODEL_IMPORT')
sys.addaudithook(guard)
spec=importlib.util.spec_from_file_location('diagnostic_entry',sys.argv[1]);entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
import modal
import modal.output
assert importlib.metadata.version('modal')=='1.2.3'
# Exercise the actual installed SDK local validator and capture its actual protobuf
# construction. The 2..3600 range is server-side; SDK 1.2.3 locally accepts 1/3601.
import modal._functions as functions
from unittest.mock import patch
native_settings=functions.api_pb2.AutoscalerSettings
serialized=[]
def settings(*args,**kwargs):
 result=native_settings(*args,**kwargs);serialized.append(result.scaledown_window);return result
def noop(): pass
probe=modal.App('offline-validator-probe')
with patch.object(functions.api_pb2,'AutoscalerSettings',side_effect=settings):
 for value in (1,2,3600,3601):
  candidate=probe.function(name='offline_'+str(value),scaledown_window=value,serialized=True)(noop)
  assert not candidate.is_hydrated
assert serialized==[1,2,3600,3601],serialized
try:
 probe.function(scaledown_window=0,serialized=True)(noop)
except modal.exception.InvalidError as exc:
 assert 'scaledown_window' in str(exc) and '> 0' in str(exc)
else: raise AssertionError('Installed SDK native >0 validator did not reject zero')
# Verify actual SDK serialization aliases without entering _load / FunctionCreate.
import inspect,ast
source=ast.parse(inspect.getsource(functions))
legacy=[n for n in ast.walk(source) if isinstance(n,ast.keyword) and n.arg=='task_idle_timeout_secs']
assert sum(ast.unparse(n.value)=='scaledown_window or 0' for n in legacy)==1
# Definitions only: do NOT enter app.run, resolve/hydrate objects, build images, or submit a call.
pins=json.loads(sys.argv[2])
from modal._resources import convert_fn_config_to_resources_config
assert inspect.signature(modal.App.function).parameters['ephemeral_disk'].default is None
# Resource conversion is deferred until _load; exercise the real pure converter
# directly without entering _load or creating remote resources.
options=entry.FUNCTION_OPTIONS
result=convert_fn_config_to_resources_config(cpu=options['cpu'],memory=options['memory'],
 gpu=options['gpu'],ephemeral_disk=options.get('ephemeral_disk'))
assert result.ephemeral_disk_mb==0
assert not any(field.name=='ephemeral_disk_mb' for field,value in result.ListFields())
assert result.gpu_config.count==1
app,fn=entry.build_candidate(pins)
assert fn.spec.ephemeral_disk is None
assert app.app_id is None
assert not fn.is_hydrated
text=io.StringIO()
with contextlib.redirect_stdout(text),contextlib.redirect_stderr(text):
 with entry.initialization_output():
  assert modal.output._get_output_manager() is not None
  modal.output._get_output_manager().print('INIT_LOG_VISIBLE')
assert 'INIT_LOG_VISIBLE' in text.getvalue()
assert modal.output._get_output_manager() is None
print(json.dumps({'sdk':'1.2.3','definition_validated':True,'output_context_enabled':True,'native_scaledown_validation_checked':True,'app_run_entered':False,'function_hydrated':False}))
"""
        env=os.environ.copy()
        for key in tuple(env):
            if key.startswith('MODAL_'): env.pop(key)
        env.update(MODAL_CONFIG_PATH=os.devnull,MODAL_PROFILE='default',PYTHONDONTWRITEBYTECODE='1')
        _,pins,_=entry.preparation()
        result=subprocess.run([sdk_python,'-B','-c',program,str(ROOT/'modal_smoke.py'),json.dumps(pins)],
                              cwd=entry.REPO,env=env,text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,entry.sanitize(result.stderr))
        self.assertIn('"definition_validated": true',result.stdout)
        self.assertIn('"output_context_enabled": true',result.stdout)
        self.assertIn('"native_scaledown_validation_checked": true',result.stdout)
        self.assertNotIn('FORBIDDEN_',result.stderr)


if __name__=='__main__':
    unittest.main(verbosity=2)
