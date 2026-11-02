"""Standard-library-only validation. No downloads, inference, training or GPU access."""
import ast
import csv
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from common import ROOT, REPO, config, messages, plan, read_json, rows, sha, verify_freeze
import score
import evaluate
from common import require_complete_baselines


class PreparationChecks(unittest.TestCase):
    def test_schema_counts_balance(self):
        for filename, count, per_domain in [('train.jsonl',60,15),('heldout.jsonl',20,5)]:
            data=rows(filename)
            self.assertEqual(len(data), count)
            self.assertEqual(sum(c['evidence_sufficient'] for c in data), count//2)
            self.assertEqual(Counter(c['domain'] for c in data),
                             Counter(dict.fromkeys(['hedge','liquidity','credit','attribution'],per_domain)))
            for c in data:
                self.assertIs(type(c['evidence_sufficient']), bool)
                self.assertEqual(c['evidence_sufficient'], not c['decision_critical_missing'])
                self.assertEqual(len(c['knowledge_required']), 3)
                for k in ('question','structure','evidence_provided','justified_answer','questions_unnecessary_when'):
                    self.assertTrue(c[k].strip())
            self.assertEqual(len({c['id'] for c in data}), count)
            self.assertEqual(len({c['application_probe'] for c in data}), count)

    def test_split_and_prior_direct_reuse(self):
        train, held=rows('train.jsonl'),rows('heldout.jsonl')
        for k in ('id','structure','question','evidence_provided'):
            self.assertFalse({c[k] for c in train} & {c[k] for c in held})
        prior_files=['observer-cases.json','evidence-grounded-cases.json','meaning-alignment-cases.json',
                     'investigation-completeness-cases-20261101.json']
        def strings(value):
            if isinstance(value,str): yield value
            elif isinstance(value,list):
                for item in value: yield from strings(item)
            elif isinstance(value,dict):
                for item in value.values(): yield from strings(item)
        normalize=lambda s: re.sub(r'\W+',' ',s.lower()).strip()
        old={normalize(s) for f in prior_files for s in strings(read_json(REPO/'research'/f))}
        for c in train+held:
            for field in ('question','evidence_provided','justified_answer'):
                self.assertNotIn(normalize(c[field]),old)

    def test_isolated_prompts_and_arm_controls(self):
        for case in rows('heldout.jsonl'):
            for probe in ('knowledge','application'):
                a=messages(case,'A',probe)
                b=messages(case,'B',probe)
                c=messages(case,'C',probe)
                self.assertEqual(a,c)
                self.assertEqual([m['role'] for m in a],['system','user'])
                self.assertNotIn(case['justified_answer'],json.dumps(a))
                self.assertNotIn(case['questions_unnecessary_when'],json.dumps(a))
                if probe=='knowledge':
                    self.assertEqual(a,b)
                    self.assertNotIn(case['evidence_provided'],a[1]['content'])
                else:
                    self.assertEqual(a[1],b[1])
                    self.assertNotEqual(a[0],b[0])

    def test_call_budget_order_and_settings(self):
        for c in 'ABC':
            tasks=plan(c)
            self.assertEqual(len(tasks),40)
            self.assertEqual(Counter(t['probe'] for t in tasks),Counter(knowledge=20,application=20))
            self.assertEqual(len({(t['case_id'],t['probe']) for t in tasks}),40)
            self.assertEqual([(t['case_id'],t['probe']) for t in tasks],
                             [(t['case_id'],t['probe']) for t in plan('A')])
        cfg=config()
        self.assertFalse(cfg['generation']['do_sample'])
        self.assertEqual(cfg['generation']['max_new_tokens'],512)
        self.assertEqual(cfg['lora']['r'],16)
        self.assertRegex(cfg['model_revision'],r'^[a-f0-9]{40}$')

    def test_python_parse_and_no_top_level_model_imports(self):
        for path in ROOT.glob('*.py'):
            tree=ast.parse(path.read_text(),filename=str(path))
            for node in tree.body:
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
                    self.assertFalse(any(n.split('.')[0] in ('torch','transformers','trl','peft','datasets') for n in names))

    def test_plan_and_help_block_network_and_model_imports(self):
        # Child audit hook makes accidental optional imports or network connects fail.
        runner='''import sys,runpy,contextlib,io,json
blocked={'torch','transformers','trl','peft','datasets','accelerate'}
def guard(event,args):
 if event=='socket.connect' or (event=='import' and args[0].split('.')[0] in blocked):
  raise RuntimeError('Forbidden in offline planning: '+event)
sys.addaudithook(guard)
sys.argv=json.loads(sys.argv[1])
try:
 with contextlib.redirect_stdout(io.StringIO()): runpy.run_path(sys.argv[0],run_name='__main__')
except SystemExit as e:
 if e.code not in (0,None): raise
'''
        commands=[['train.py'],['train.py','--help'],['score.py','--help']]
        commands += [['evaluate.py','--condition',c] for c in 'ABC']
        commands += [['evaluate.py','--help']]
        for command in commands:
            args=[str(ROOT/command[0])]+command[1:]
            result=subprocess.run([sys.executable,'-c',runner,json.dumps(args)],cwd=ROOT,
                                  capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_heldout_arithmetic_anchors(self):
        # Independently recomputed identities, not semantic scoring or model evaluation.
        for s in (0,50,70,80,100,130,1000000):
            net=s-max(s-100,0)+max(70-s,0)+2
            self.assertGreaterEqual(net,72)
            self.assertLessEqual(net,102)
        self.assertEqual((8-7,-3+2),(1,-1))
        self.assertEqual(3-4,-1)  # Intraday shortfall, even with positive final balance.
        self.assertEqual(3-4+5-2,2)
        self.assertEqual(3-1,2)  # FX prefunding gap.
        self.assertEqual(12-5-(4-1),4)
        self.assertEqual(min(max(7-5,0),10-5),2)
        self.assertAlmostEqual((.6-.5)*(.10-.06)+(.4-.5)*(.02-.06),.008)
        self.assertEqual(100*50-100*48-100*1-30,70)
        self.assertAlmostEqual(1000*(20.03-20)+10,40)
        # Same monthly active differences can imply different annual active returns.
        self.assertNotAlmostEqual(1.001**12-1, 1.011**12-1.01**12)
        self.assertNotAlmostEqual(12*.001, 1.001**12-1)
        self.assertEqual(36*16*(2*(2560+4096)+2*(2560+1024)),11796480)

    def test_ignored_output_boundary(self):
        result=subprocess.run(['git','check-ignore','research/runs/ka-offline-boundary-check'],
                              cwd=REPO,capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        from common import private_run
        with self.assertRaises(ValueError):
            private_run(ROOT/'unsafe-test-output')

    def test_freeze_and_corruption_detection(self):
        verify_freeze()
        with patch('common.sha',return_value='corrupted'):
            with self.assertRaises(ValueError): verify_freeze()

    def test_human_score_validation(self):
        self.assertEqual(score.bits('[1,0,1]',3),[1,0,1])
        for malformed in ('[true]','[2]','[]','["1"]'):
            with self.assertRaises(ValueError): score.bits(malformed,1)
        with self.assertRaises(ValueError): score.bit('')

    def test_scoring_pipeline_and_failure_denominators(self):
        # Fabricated arithmetic fixtures only, under a disposable temp dir. No financial responses.
        with tempfile.TemporaryDirectory(prefix='metis-ka-offline-') as temp:
            temp=Path(temp)
            cases=rows('heldout.jsonl')
            run_paths=[]
            for c in 'ABC':
                run=temp/c
                run.mkdir()
                run_paths.append(run)
                (run/'manifest.json').write_text(json.dumps({'condition':c,'freeze_sha256':sha(ROOT/'freeze.json')}))
                for case in cases:
                    for p in ('knowledge','application'):
                        if c=='B' and case['id']=='eval-01' and p=='application': continue
                        record=dict(condition=c,case_id=case['id'],probe=p,status='complete',response='OFFLINE FIXTURE ONLY')
                        (run/f"{case['id']}-{p}.json").write_text(json.dumps(record))
            out=temp/'packet'
            def fake_private(path):
                Path(path).mkdir()
                return Path(path)
            with patch('score.private_run',side_effect=fake_private): score.prepare(run_paths,out)
            key=read_json(out/'key.json')
            packet=read_json(out/'human_packet.json')
            self.assertEqual(len(packet),120)
            self.assertTrue(all('condition' not in r and 'case_id' not in r for r in packet))
            with self.assertRaises(ValueError): score.summarize(out)  # Blank sheet is not passing.
            table=[]
            by_id={c['id']:c for c in cases}
            for blind_id,identity in key.items():
                c,cid,p=(identity[k] for k in ('condition','case_id','probe'))
                row=dict.fromkeys(score.FIELDS,'')|{'blind_id':blind_id,'notes':'Artificial arithmetic fixture; no human rating.'}
                if identity['status']=='complete':
                    if p=='knowledge': row.update(knowledge_items='[1,1,1]',boundary_correct='1',knowledge_error='0')
                    else:
                        row.update(answer_correct='1',missing_items=json.dumps([1]*len(by_id[cid]['decision_critical_missing'])),
                                   unnecessary_request='0',unsupported_conclusion='0')
                        if c=='A' and cid=='eval-02': row['unnecessary_request']='1'
                        if c=='A' and cid=='eval-01': row['unsupported_conclusion']='1'
                table.append(row)
            def write_table(data):
                with (out/'scores.csv').open('w',newline='') as f:
                    writer=csv.DictWriter(f,fieldnames=score.FIELDS)
                    writer.writeheader();writer.writerows(data)
            write_table(table)
            result=score.summarize(out)
            self.assertEqual(result['conditions']['A']['application_accuracy']['correct'],18)
            self.assertEqual(result['conditions']['B']['application_accuracy']['correct'],19)
            self.assertEqual(result['conditions']['C']['application_accuracy']['correct'],20)
            self.assertEqual(result['conditions']['A']['failures_to_apply_demonstrated_knowledge']['eligible'],20)
            self.assertEqual(len(result['conditions']['A']['failures_to_apply_demonstrated_knowledge']['cases']),2)
            self.assertEqual(result['conditions']['B']['missing_evidence_detection']['evaluable_items'],9)
            self.assertEqual(result['conditions']['B']['application_complete'],19)
            self.assertEqual(result['comparisons']['C_vs_A']['gains'],['eval-01','eval-02'])
            write_table(table+table[:1])
            with self.assertRaises(ValueError): score.summarize(out)

    def test_v1_preservation_and_fixed_settings(self):
        inventory = read_json(ROOT / 'V1_MANIFEST.json')
        self.assertEqual(len(inventory['sha256']), 16)
        for name, digest in inventory['sha256'].items():
            self.assertEqual(sha(ROOT.parent / name), digest, name)
        original = read_json(ROOT.parent / 'config.json')
        corrected = config().copy()
        self.assertEqual(corrected.pop('study'), 'metis-knowledge-application-20261101-v3')
        original.pop('study')
        self.assertEqual(corrected, original)
        for name in ('train.jsonl', 'heldout.jsonl'):
            old = [json.loads(x) for x in (ROOT.parent / name).read_text().splitlines()]
            new = rows(name)
            self.assertEqual([(x['id'], x['domain'], x['structure'], x['evidence_sufficient']) for x in old],
                             [(x['id'], x['domain'], x['structure'], x['evidence_sufficient']) for x in new])

    def test_probe_keys_and_missingness_cues(self):
        for case in rows('heldout.jsonl'):
            self.assertTrue(case['knowledge_boundary'])
            self.assertNotEqual(case['knowledge_boundary'], case['questions_unnecessary_when'])
            self.assertNotIn(case['knowledge_boundary'], case['knowledge_probe'])
            self.assertIn('governing financial relationship', case['knowledge_probe'])
        for name in ('train.jsonl', 'heldout.jsonl'):
            for case in rows(name):
                if not case['evidence_sufficient']:
                    self.assertNotRegex(case['evidence_provided'].lower(),
                        r'\b(absent|unknown|omitted|unavailable|not supplied|not provided|not given|not known)\b')
                self.assertNotIn('complete mandated test', case['application_probe'])

    def test_separate_rater_packets(self):
        with tempfile.TemporaryDirectory(prefix='metis-ka-v2-packets-') as temp:
            temp = Path(temp)
            runs = []
            for c in 'ABC':
                run = temp/c
                run.mkdir()
                (run/'manifest.json').write_text(json.dumps(dict(condition=c, freeze_sha256=sha(ROOT/'freeze.json'))))
                runs.append(run)
            def private(path):
                Path(path).mkdir()
                return Path(path)
            out = temp/'packet'
            with patch('score.private_run', side_effect=private):
                score.prepare(runs, out)
            kp = read_json(out/'knowledge_packet.json')
            ap = read_json(out/'application_packet.json')
            self.assertEqual((len(kp), len(ap)), (60,60))
            for record in kp:
                self.assertEqual(record['probe'], 'knowledge')
                self.assertEqual(set(record['scoring_key']), {'knowledge_required','knowledge_boundary'})
                for field in ('decision_critical_missing','evidence_sufficient','justified_answer','questions_unnecessary_when'):
                    self.assertNotIn(field, json.dumps(record))
            for record in ap:
                self.assertNotIn('knowledge_required', record['scoring_key'])
                self.assertNotIn('knowledge_boundary', record['scoring_key'])
            self.assertEqual({r['blind_id'] for r in kp} & {r['blind_id'] for r in ap}, set())
            for probe in ('knowledge','application'):
                with (out/f'{probe}_scores.csv').open() as stream:
                    self.assertEqual(len(list(csv.DictReader(stream))),60)

    def test_truncation_stops_after_saved_response(self):
        tasks = plan('A')[:2]
        for failure in ('truncated', 'exception', 'empty'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory(prefix='metis-ka-v2-stop-') as temp:
                out = Path(temp)
                calls = []
                manifest = dict(condition='A', planned_calls=2)
                def fake_generate(task):
                    calls.append(task)
                    if failure == 'exception':
                        raise RuntimeError('Offline synthetic exception, no generation')
                    return dict(response='OFFLINE FIXTURE ONLY', completion_tokens=0 if failure=='empty' else 512,
                                truncated=True, status='truncated')
                with self.assertRaises(RuntimeError):
                    evaluate.collect(tasks, fake_generate, out, manifest)
                m = read_json(out/'manifest.json')
                self.assertEqual(len(calls),1)
                self.assertEqual(m['status'],'incomplete')
                self.assertEqual(m['attempted'],1)
                self.assertEqual(m['completed'],0)
                self.assertEqual(m['saved'],0 if failure=='exception' else 1)
                self.assertEqual(m['unavailable'],2-m['saved'])
                self.assertFalse((out/f"{tasks[1]['case_id']}-{tasks[1]['probe']}.json").exists())
                if failure != 'exception':
                    record=read_json(out/f"{tasks[0]['case_id']}-{tasks[0]['probe']}.json")
                    self.assertEqual(record['status'],'truncated')
        # Exercise the nonzero process boundary without importing any model library.
        program = """import tempfile
from pathlib import Path
from evaluate import collect
with tempfile.TemporaryDirectory() as d:
 collect([dict(case_id='fixture',probe='knowledge',messages=[])],
         lambda task:dict(response='FIXTURE',status='truncated',truncated=True),
         Path(d),dict(condition='A',planned_calls=1))
"""
        result=subprocess.run([sys.executable,'-c',program],cwd=ROOT,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('TruncatedResponse',result.stderr)

    def test_training_baseline_gate(self):
        with tempfile.TemporaryDirectory(prefix='metis-ka-v2-baselines-') as temp:
            temp=Path(temp)
            paths=[]
            for c in 'AB':
                out=temp/c
                out.mkdir()
                def fake(task):
                    return dict(response='OFFLINE FIXTURE ONLY',status='complete',truncated=False,completion_tokens=1)
                manifest=dict(condition=c,planned_calls=40,freeze_sha256=sha(ROOT/'freeze.json'),
                              config=config(),model_path='/offline-fixture',tokenizer_chat_template_sha256='fixture')
                evaluate.collect(plan(c),fake,out,manifest)
                paths.append(out)
            self.assertEqual(len(require_complete_baselines(paths)),2)
            self.assertRaises(ValueError,require_complete_baselines,[paths[0],paths[0]])
            original=(paths[1]/'manifest.json').read_text()
            for status in ('incomplete','started','failed'):
                m=json.loads(original);m['status']=status
                (paths[1]/'manifest.json').write_text(json.dumps(m))
                self.assertRaises(ValueError,require_complete_baselines,paths)
            (paths[1]/'manifest.json').write_text(original)
            task=plan('B')[0]
            source=paths[1]/f"{task['case_id']}-{task['probe']}.json"
            original_record=source.read_text()
            r=json.loads(original_record);r.update(status='truncated',truncated=True)
            source.write_text(json.dumps(r))
            self.assertRaises(ValueError,require_complete_baselines,paths)
            source.write_text(original_record+' ')
            self.assertRaises(ValueError,require_complete_baselines,paths)
            source.unlink()
            with self.assertRaises(FileNotFoundError): require_complete_baselines(paths)
            # Direct training CLI must reject the bad baseline before optional imports or output creation.
            output=temp/'must-not-exist'
            guard="""import sys,runpy,json
blocked={'torch','transformers','trl','peft','datasets','accelerate'}
def audit(event,args):
 if event=='socket.connect' or (event=='import' and args[0].split('.')[0] in blocked):
  raise AssertionError('FORBIDDEN OPTIONAL IMPORT OR NETWORK')
sys.addaudithook(audit)
sys.argv=json.loads(sys.argv[1])
runpy.run_path(sys.argv[0],run_name='__main__')
"""
            args=[str(ROOT/'train.py'),'--execute','--model-path','/unused','--out',str(output),
                  '--baseline-runs',*[str(x) for x in paths]]
            result=subprocess.run([sys.executable,'-c',guard,json.dumps(args)],cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn('FORBIDDEN OPTIONAL IMPORT OR NETWORK',result.stderr)
            self.assertFalse(output.exists())


class V3GenerationChecks(unittest.TestCase):
    def test_v2_content_identity_and_amendment_scope(self):
        inventory=read_json(ROOT/'V2_MANIFEST.json')
        for name,digest in inventory['sha256'].items():
            self.assertEqual(sha(ROOT.parent/'v2'/name),digest,name)
        matches=read_json(ROOT/'MATCHED_CONTENT.json')
        for name,digest in matches['identical_files'].items():
            self.assertEqual(sha(ROOT/name),digest,name)
            self.assertEqual(sha(ROOT.parent/'v2'/name),digest,name)
        old=read_json(ROOT.parent/'v2/config.json');new=config().copy()
        self.assertEqual(new.pop('study'),'metis-knowledge-application-20261101-v3')
        old.pop('study');self.assertEqual(new,old)
        self.assertEqual(sha(ROOT/'QWEN_GENERATION_DEFAULTS.json'),
                         '835fffe355c9438e7a25be099b3fccaa98350b83451f9fd2d99512e74f1ade48')
        old_tree=ast.parse((ROOT.parent/'v2/evaluate.py').read_text())
        new_tree=ast.parse((ROOT/'evaluate.py').read_text())
        self.assertEqual(ast.dump(next(n for n in old_tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect')),
                         ast.dump(next(n for n in new_tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect')))
        generate=next(n for n in ast.walk(new_tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='generate')
        self.assertIs(next(k.value.value for k in generate.keywords if k.arg=='use_model_defaults'),False)

    def test_effective_generation_guard_rejects_drift(self):
        from types import SimpleNamespace
        cfg=config();values=dict(cfg['generation'],eos_token_id=151645,pad_token_id=151643)
        for change,mode,unused in (({},'greedy_search',{}),({'do_sample':True},'sample',{}),
                                  ({'num_beams':2},'greedy_search',{}),({'eos_token_id':151643},'greedy_search',{}),
                                  ({'pad_token_id':None},'greedy_search',{}),({'max_new_tokens':1024},'greedy_search',{}),
                                  ({},'sample',{}),({},'greedy_search',{'unexpected':True})):
            prepared=SimpleNamespace(**dict(values,**change),get_generation_mode=lambda:SimpleNamespace(value=mode))
            model=SimpleNamespace(_prepare_generation_config=lambda requested,**kwargs:(prepared,unused))
            if change or mode!='greedy_search' or unused:
                with self.assertRaises(ValueError):evaluate.prepare_greedy_generation(model,None,cfg)
            else:self.assertIs(evaluate.prepare_greedy_generation(model,None,cfg),prepared)

    def test_actual_pinned_transformers_resolution(self):
        import os
        python=os.environ.get('METIS_TRANSFORMERS_PYTHON')
        if not python:
            self.skipTest('UNVERIFIED: no local Transformers 4.56.2 environment; never installs or substitutes 5.x')
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        result=subprocess.run([python,'-B',str(ROOT/'generation_regression.py')],
                              cwd=ROOT,text=True,capture_output=True,env=env,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        report=json.loads(result.stdout)
        self.assertEqual(report['transformers_version'],'4.56.2')
        self.assertEqual(report['v2_effective_mode'],'sample')
        self.assertEqual(report['v3_effective_mode'],'greedy_search')
        self.assertTrue(report['identical_ABC'])
        self.assertEqual(report['generation_calls'],0)


if __name__=='__main__':
    unittest.main(verbosity=2)
