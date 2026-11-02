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

    def test_no_model_import_or_network_in_default_or_blocked_launch(self):
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
            for flags,code in (([],0),(['--execute','--out',str(out)],2),(['--help'],0)):
                result=subprocess.run([sys.executable,'-c',guard,
                    json.dumps([str(ROOT/'modal_smoke.py'),*flags])],cwd=entry.REPO,
                    text=True,capture_output=True,timeout=5)
                self.assertEqual(result.returncode,code,result.stderr)
                self.assertNotIn('FORBIDDEN_RUNTIME_ACCESS',result.stderr)
                if code: self.assertIn('NO-GO',result.stderr)
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
                      and isinstance(n.func,ast.Attribute) and n.func.attr=='remote']
        self.assertEqual(len(remote_calls),1)
        # The blocker gate is before launch in main; no execution bypass flag exists.
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        blocker=next(i for i,n in enumerate(main.body) if isinstance(n,ast.If)
                     and isinstance(n.test,ast.Name) and n.test.id=='BLOCKERS')
        launch=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Expr)
                    and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)
                    and n.value.func.id=='launch_candidate')
        self.assertLess(blocker,launch)
        self.assertTrue(entry.BLOCKERS)

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
        self.assertEqual(options['scaledown_window'],1)
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
                              '.deploy(','.spawn(','.map(','.generate('):
                self.assertNotIn(forbidden,text)
        self.assertEqual(runtime.SYNTHETIC_USER,'Return exactly the label: cobalt.')
        self.assertEqual(runtime.SYNTHETIC_TARGET,'cobalt.')
        result=subprocess.run(['git','check-ignore','research/runs/ka-modal-smoke-v2-01'],
                              cwd=entry.REPO,text=True,capture_output=True)
        self.assertEqual(result.returncode,0)


if __name__=='__main__':
    unittest.main(verbosity=2)
