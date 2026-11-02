"""Offline by default; explicitly submit exactly one frozen scientific stage to Modal."""
import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
import errno
import re
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V2 = ROOT.parent / 'v2'
SMOKE = ROOT.parent / 'modal_smoke_v2'
FREEZE = '4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91'
# Phase allowances include model download/loading; no automatic next stage.
LIMITS = {'baseline': 4200, 'train': 4200, 'C': 2400}
RATE = .000542 + 2*.0000131 + 32*.00000222
REMOTE = '/opt/metis-execution'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sanitize_message(value):
    """Diagnostics only: no source lines, locals, environment dump or raw payload."""
    text = str(value)
    values = {v for k,v in os.environ.items() if v and
              (len(v)>=4 or re.search(r'TOKEN|SECRET|PASSWORD|CREDENTIAL|API_KEY',k,re.I))}
    for value in sorted(values,key=len,reverse=True):
        text = text.replace(value,'[REDACTED_ENV_VALUE]')
    text = re.sub(r'(?i)\b(?:authorization|bearer|password|token|secret|api[_-]?key|credential|private[_-]?data)\b\s*[:=]?\s*[^\s,;]+',
                  '[REDACTED_CREDENTIAL]',text)
    text = re.sub(r'\b(?:ak-|as-|sk-|hf_|ghp_|github_pat_|eyJ)[A-Za-z0-9_.-]+','[REDACTED_TOKEN]',text)
    text = re.sub(r'(?i)https?://[^\s<>]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[REDACTED_ADDRESS]',text)
    text = re.sub(r'(?:/(?:Users|home|private|tmp|root|opt)/|[A-Za-z]:\\)[^\s<>]+','[REDACTED_PATH]',text)
    text = re.sub(r'(?s)\{.*\}','[REDACTED_STRUCTURED_DATA]',text)
    text = re.sub(r'''(["'`]).*?\1''','[REDACTED_QUOTED_VALUE]',text)
    text = re.sub(r'\b[A-Za-z0-9_+/=-]{32,}\b','[REDACTED_OPAQUE_VALUE]',text)
    return text[:8192]


def remote_diagnostic(exc, phase, source_files):
    """Retain only allowlisted missing names; arbitrary private filenames stay masked."""
    allowed = {'git':'git','nvidia-smi':'nvidia-smi','python':'python','python3':'python3',
               'python3.12':'python3.12',sys.executable:Path(sys.executable).name}
    for name in source_files:
        if (name.startswith('research/knowledge_application_20261101/')
                and '..' not in Path(name).parts):
            allowed[name]=name
            allowed[str(Path(REMOTE)/name)]=name
    chain,seen=[],set()
    current=exc
    while current is not None and id(current) not in seen and len(chain)<8:
        seen.add(id(current))
        filename=getattr(current,'filename',None)
        safe_name=allowed.get(str(filename)) if filename is not None else None
        # Credentials take precedence even if their value resembles a public name.
        if safe_name and any(v in (str(filename),safe_name) for k,v in os.environ.items()
                             if v and re.search(r'TOKEN|SECRET|PASSWORD|CREDENTIAL|API_KEY',k,re.I)):
            safe_name=None
        if isinstance(current,subprocess.CalledProcessError):
            message='Subprocess exited with status '+str(current.returncode)
        elif isinstance(current,subprocess.TimeoutExpired):
            message='Subprocess exceeded its configured timeout'
        else:
            message=sanitize_message(current)
        if filename is not None:
            message+='; missing_filename='+ (safe_name or '[REDACTED_FILENAME]')
        frames=[dict(file=sanitize_message(Path(frame.f_code.co_filename).name),line=line,
                     function=sanitize_message(frame.f_code.co_name))
                for frame,line in (traceback.walk_tb(current.__traceback__) if current.__traceback__ else [])]
        item=dict(type=type(current).__name__,message=message,frames=frames)
        if filename is not None:item['missing_filename']=safe_name or '[REDACTED_FILENAME]'
        if isinstance(current,subprocess.CalledProcessError):item['subprocess_returncode']=current.returncode
        chain.append(item)
        current=current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    return dict(phase=phase,caught_at_utc=utc_now(),type=type(exc).__name__,
                message=chain[0]['message'],chain=chain)


def runtime_preflight(report, repo, source_files):
    """Check all explicit frozen uploads and Git before frozen version checks/model imports."""
    if not source_files:
        raise ValueError('Required frozen source upload manifest is absent')
    checks={name:(Path(repo)/name).is_file() for name in sorted(source_files)}
    report['preflight']=dict(frozen_files=checks,git_available=shutil.which('git') is not None,
                             checked_at_utc=utc_now())
    missing=[name for name,exists in checks.items() if not exists]
    if missing:
        raise FileNotFoundError(errno.ENOENT,'Required frozen file is missing',str(Path(repo)/missing[0]))
    if not report['preflight']['git_available']:
        raise FileNotFoundError(errno.ENOENT,'Required frozen preflight executable is unavailable','git')


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract(data, target):
    """Only relative regular-file entries, with a bounded total size; no symlinks."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(info.file_size for info in archive.infolist()) > 256*1024**2:
            raise ValueError('Artifact bundle exceeds 256 MiB bound')
        for info in archive.infolist():
            path = Path(info.filename)
            if (path.is_absolute() or '..' in path.parts or not path.parts
                    or (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('Unsafe artifact path')
            if not info.is_dir():
                dest = Path(target) / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    raise ValueError('Artifact would overwrite existing output')
                dest.write_bytes(archive.read(info))


def bundle(root):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(Path(root).rglob('*')):
            if file.is_file():
                archive.write(file, file.relative_to(root))
    return stream.getvalue()


def budget(stage, accounting):
    # Operator upper allowances are not claimed as an actual provider bill.
    for key in ('prior_cost_upper_usd', 'prior_gpu_seconds_upper', 'additional_cost_reserve_usd'):
        value = accounting[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('Nonnegative finite accounting allowances required')
    future = sum(LIMITS[k] + 120 for k in list(LIMITS)[list(LIMITS).index(stage):])
    estimated = accounting['prior_cost_upper_usd'] + accounting['additional_cost_reserve_usd'] + RATE*future
    if estimated > 20 or accounting['prior_gpu_seconds_upper'] + future > 4*3600:
        raise ValueError('STOP: remaining stages exceed $20 target or four-GPU-hour planning limit')
    return dict(target_usd=20, projected_total_usd=estimated, remaining_seconds_allowance=future,
                provider_billed_usd=accounting.get('provider_billed_usd'),
                limitation='Estimates and operator allowances, not a cloud billing cap')


def eligible(record):
    """Technical progression only, never an uninterrupted-execution PASS."""
    call = record.get('function_call_id')
    remote = record.get('remote', {})
    observed = [node for snapshot in record.get('history', []) for node in snapshot.get('nodes', [])
                if node.get('function_call_id') == call and node.get('task_id')]
    return bool(record.get('technical_status') == 'complete' and record.get('cleanup_confirmed')
                and not record.get('diagnostic') and not record.get('restart_or_reassignment_detected')
                and call and remote.get('function_call_id') == call
                and all(remote.get(k) for k in ('container_id', 'input_id', 'execution_id'))
                and observed and not any(s.get('error_type') or s.get('truncated')
                                         for s in record.get('history', [])))


def preparation():
    if sha(V2/'freeze.json') != FREEZE:
        raise ValueError('Scientific freeze changed')
    manifest = json.loads((V2/'freeze.json').read_text())
    files = {str((V2/name).relative_to(REPO)): V2/name for name in manifest['sha256']}
    # Normalize parent references for explicit file-only upload; no repository mount.
    files = {str(path.resolve().relative_to(REPO)): path.resolve() for path in files.values()}
    for name, digest in manifest['sha256'].items():
        if sha(V2/name) != digest:
            raise ValueError('Frozen scientific source changed')
    files[str((V2/'freeze.json').relative_to(REPO))] = V2/'freeze.json'
    source = json.loads((ROOT/'execution_freeze.json').read_text())
    if any(sha(ROOT/name) != digest for name,digest in source['sha256'].items()):
        raise ValueError('Execution preparation changed')
    smoke = load_module('smoke_plumbing', SMOKE/'modal_smoke.py')
    cfg, pins, _ = smoke.preparation()
    return files, cfg, pins, smoke


def build(stage, files, base_image):
    import importlib.metadata
    import modal
    if importlib.metadata.version('modal') != '1.2.3':
        raise ValueError('Modal 1.2.3 required')
    # Extend the successful smoke image with its confirmed missing system executable.
    # No Python package reinstall, image alias or GPU/environment fallback.
    image = (base_image.apt_install("git").env({'HF_HOME': REMOTE+'/hf', 'HF_HUB_DISABLE_TELEMETRY':'1',
                   'HF_HUB_DISABLE_IMPLICIT_TOKEN':'1', 'WANDB_DISABLED':'true'}))
    for name, path in files.items():
        image = image.add_local_file(path, REMOTE+'/'+name)
    image = image.add_local_file(ROOT/'execute.py',
                                REMOTE+'/research/knowledge_application_20261101/execution_v2/execute.py')
    app = modal.App('metis-frozen-v2-'+stage, include_source=False)
    @app.function(image=image, gpu='L40S', cpu=(2.,2.), memory=(32768,32768),
                  timeout=LIMITS[stage], startup_timeout=30, scaledown_window=2,
                  min_containers=0, max_containers=1, buffer_containers=0,
                  retries=0, max_inputs=1, serialized=True, include_source=False)
    def run(request, previous):
        sys.path.insert(0, REMOTE+'/research/knowledge_application_20261101/execution_v2')
        from execute import remote_stage
        return remote_stage(request, previous)
    return app, run


def remote_stage(request, previous):
    """Run original frozen CLIs unmodified. Only called inside the explicit GPU input."""
    import modal
    os.umask(0o077)
    start = time.monotonic()
    stage = request['stage']
    repo = Path(REMOTE)
    v2 = repo/'research/knowledge_application_20261101/v2'
    runs = repo/'research/runs/study'
    runs.mkdir(parents=True, exist_ok=False)
    report = dict(stage=stage, status='incomplete', started_at_utc=datetime.now(timezone.utc).isoformat(),
                  origin=request, execution_id=str(uuid.uuid4()), container_id=os.environ.get('MODAL_TASK_ID'),
                  image_id=os.environ.get('MODAL_IMAGE_ID'),
                  image_amendment=dict(system_packages=['git'],source_smoke_image_id=request.get('smoke_image_id')),
                  input_id=modal.current_input_id(), function_call_id=modal.current_function_call_id(),
                  provider_billed_usd=None, physical_history_complete=False)
    def phase(name):
        report['phase']=name
        report.setdefault('phase_history',[]).append(dict(phase=name,started_at_utc=utc_now()))
        (runs/(stage+'-execution.json')).write_text(json.dumps(report,indent=2))
    try:
        phase('restore_previous_artifacts')
        if previous:
            extract(previous, runs)
        phase('frozen_files_and_git_preflight')
        runtime_preflight(report,repo,request['source_files'])
        phase('frozen_module_import')
        sys.path.insert(0, str(v2))
        import common
        phase('frozen_file_hash_verification')
        common.verify_freeze()
        phase('frozen_version_verification')
        common.enforce_versions()
        phase('runtime_imports')
        import torch
        from huggingface_hub import snapshot_download
        phase('gpu_verification')
        if (torch.cuda.device_count()!=1 or 'L40S' not in torch.cuda.get_device_name()
                or not torch.cuda.is_bf16_supported()):
            raise RuntimeError('One BF16 L40S required; no fallback')
        report['gpu']=torch.cuda.get_device_name()
        phase('hardware_and_package_metadata')
        report['nvidia_smi']=subprocess.check_output(['nvidia-smi','-q'],text=True,timeout=20)
        report['runtime']=common.runtime_metadata()
        report['pip_freeze']=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True)
        if sorted(report['pip_freeze'].splitlines()) != sorted(request['smoke_pip_freeze'].splitlines()):
            raise ValueError('Package environment differs from successful smoke image')
        report['pip_check']=subprocess.check_output([sys.executable,'-m','pip','check'],text=True)
        phase('model_snapshot_download')
        download_start=time.monotonic()
        snapshot=Path(snapshot_download(repo_id=request['model_id'],revision=request['model_revision'],
                                       token=False,max_workers=1))
        report['download_elapsed_seconds']=time.monotonic()-download_start
        phase('model_snapshot_verification')
        hashes={str(p.relative_to(snapshot)):sha(p) for p in snapshot.rglob('*') if p.is_file()}
        if hashes != request['snapshot_sha256']:
            raise ValueError('Snapshot bytes differ from successful smoke')
        report['snapshot_sha256']=hashes
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        if stage=='baseline':
            commands=[('A',['evaluate.py','--condition','A'],1800),
                      ('B',['evaluate.py','--condition','B'],1800)]
        elif stage=='train':
            common.require_complete_baselines([runs/'A',runs/'B'])
            commands=[('train',['train.py','--baseline-runs',str(runs/'A'),str(runs/'B')],3600)]
        else:
            if json.loads((runs/'train/manifest.json').read_text()).get('status')!='complete':
                raise ValueError('Complete sole training run required')
            commands=[('C',['evaluate.py','--condition','C','--adapter',str(runs/'train/adapter')],1800)]
        for name,args,seconds in commands:
            phase(name+'_subprocess')
            remaining=int(LIMITS[stage]-60-(time.monotonic()-start))
            if remaining<=0:
                raise TimeoutError('Stage budget exhausted; no next command')
            with (runs/(name+'.stdout.txt')).open('w') as out, (runs/(name+'.stderr.txt')).open('w') as err:
                subprocess.run([sys.executable,*[str(v2/args[0]),*args[1:]],'--execute',
                                '--model-path',str(snapshot),'--out',str(runs/name)],
                               cwd=repo,stdout=out,stderr=err,check=True,timeout=min(seconds,remaining))
            manifest=json.loads((runs/name/'manifest.json').read_text())
            phase(name+'_completion_verification')
            if manifest.get('status')!='complete':
                raise ValueError('Incomplete stage; do not advance')
            if name in ('A','B','C'):
                report[name+'_tokens']={k:sum(json.loads(p.read_text()).get(k,0)
                    for p in (runs/name).glob('eval-*.json')) for k in ('prompt_tokens','completion_tokens')}
        if stage=='baseline':
            phase('baseline_completion_gate')
            common.require_complete_baselines([runs/'A',runs/'B'])
        report['status']='complete'
        phase('complete')
    except BaseException as exc:
        # CLI stderr is private in the returned bundle; no raw response printing.
        report.update(status='incomplete',failure_type=type(exc).__name__)
        report['diagnostic']=remote_diagnostic(exc,report.get('phase','initialization'),request.get('source_files',{}))
    finally:
        report['elapsed_seconds']=time.monotonic()-start
        report['ended_at_utc']=datetime.now(timezone.utc).isoformat()
        (runs/(stage+'-execution.json')).write_text(json.dumps(report,indent=2))
    return dict(report=report, artifacts=bundle(runs))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=LIMITS,default='baseline')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--out',default='research/runs/ka-v2-baselines-03')
    parser.add_argument('--previous',help='Previous stage private directory')
    parser.add_argument('--acceptance',help='Private human whole-protocol acceptance JSON')
    parser.add_argument('--accounting',help='Private reconciled usage/budget JSON; required every stage')
    args=parser.parse_args()
    files,cfg,pins,smoke=preparation()
    if not args.execute:
        print(json.dumps(dict(mode='offline_plan',stage=args.stage,freeze_sha256=FREEZE,
                             timeout=LIMITS[args.stage],calls=80 if args.stage=='baseline' else 40 if args.stage=='C' else 0,
                             nominal_optimizer_steps=45 if args.stage=='train' else 0)))
        return 0
    if not args.acceptance or not args.accounting:
        parser.error('Execution requires human acceptance and reconciled accounting')
    acceptance=json.loads(Path(args.acceptance).read_text())
    if (acceptance.get('freeze_sha256')!=FREEZE or acceptance.get('accepted') is not True
            or acceptance.get('modal_history_limitation_accepted') is not True
            or not acceptance.get('human_reviewer') or not acceptance.get('accepted_at_utc')):
        raise ValueError('Recorded human financial acceptance of entire freeze required')
    accounting=json.loads(Path(args.accounting).read_text())
    projection=budget(args.stage,accounting)
    previous=b''
    if args.stage!='baseline':
        if not args.previous:
            parser.error('Previous complete stage required')
        prior=Path(args.previous)
        record=json.loads((prior/'report.json').read_text())
        wanted='baseline' if args.stage=='train' else 'train'
        if record.get('stage')!=wanted or not eligible(record):
            raise ValueError('Prior stage not eligible; resolve interruption/cleanup before advancing')
        previous=(prior/'artifacts.zip').read_bytes()
        if sha(prior/'artifacts.zip')!=record.get('artifacts_sha256'):
            raise ValueError('Previous artifacts changed')
    elif args.previous:
        parser.error('No prior scientific stage allowed for baseline')
    proof=json.loads((REPO/'research/runs/ka-modal-smoke-v2-04/report.json').read_text())
    remote=proof.get('remote_result',{})
    if (proof.get('technical_status')!='passed' or remote.get('v2_freeze_sha256')!=FREEZE
            or remote.get('model_revision')!=cfg['model_revision']):
        raise ValueError('Matching successful synthetic smoke required')
    out=Path(args.out).resolve()
    boundary=(REPO/'research/runs').resolve()
    if not out.is_relative_to(boundary) or out==boundary:
        raise ValueError('Private fresh output required')
    os.umask(0o077)
    out.mkdir(parents=True,exist_ok=False)
    request=dict(stage=args.stage,model_id=cfg['model_id'],model_revision=cfg['model_revision'],
                 smoke_pip_freeze=remote['pip_freeze'],smoke_image_id=remote['execution']['image_id'],
                 smoke_report_sha256=sha(REPO/'research/runs/ka-modal-smoke-v2-04/report.json'),
                 snapshot_sha256=remote['snapshot_sha256'],freeze_sha256=FREEZE,
                 execution_freeze_sha256=sha(ROOT/'execution_freeze.json'),
                 source_files={name:sha(path) for name,path in files.items()},
                 git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
                 git_status=subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True),
                 config=cfg,acceptance=acceptance,accounting=accounting,budget=projection)
    record=dict(stage=args.stage,status='INCONCLUSIVE',technical_status='incomplete',
                physical_history_complete=False,intentional_submissions=0,request=request,history=[],
                started_at_utc=smoke.utc_now(),provider_billed_usd=None)
    local_start=time.monotonic()
    def save(): (out/'report.json').write_text(json.dumps(record,indent=2))
    save()
    call=None
    try:
        with smoke.initialization_output():
            import modal
            base_image=modal.Image.from_id(request['smoke_image_id'])
            app,fn=build(args.stage,files,base_image)
            with app.run():
                try:
                    record['intentional_submissions']=1
                    record['app_id']=app.app_id
                    save()
                    call=fn.spawn(request,previous)  # Exactly one intentional submission; never retry.
                    record['function_call_id']=call.object_id
                    record['history'].append(smoke.history_snapshot(call))
                    result=call.get(timeout=LIMITS[args.stage]+120)
                    if (result['report'].get('origin') != request or
                            result['report'].get('function_call_id') != call.object_id):
                        raise ValueError('Returned execution identity/provenance mismatch')
                    (out/'artifacts.zip').write_bytes(result['artifacts'])
                    extract(result['artifacts'],out/'artifacts')
                    record.update(remote=result['report'],technical_status=result['report']['status'],
                                  artifacts_sha256=sha(out/'artifacts.zip'))
                finally:
                    if call is not None:
                        record['history'].append(smoke.history_snapshot(call))
                        call.cancel(terminate_containers=True)
            record['cleanup_confirmed']=call is not None
    except BaseException as exc:
        record['diagnostic']=smoke.exception_diagnostic(exc,'stage_submission_or_retrieval')
    finally:
        tasks={n.get('task_id') for h in record['history'] for n in h.get('nodes',[]) if n.get('task_id')}
        if record.get('remote',{}).get('container_id'):
            tasks.add(record['remote']['container_id'])
        record['restart_or_reassignment_detected']=len(tasks)>1
        record['eligible_for_next_stage']=eligible(record)
        record['ended_at_utc']=smoke.utc_now()
        record['local_elapsed_seconds']=time.monotonic()-local_start
        # Hidden attempts remain unknowable; never turn this into uninterrupted PASS.
        save()
    print(json.dumps({k:record.get(k) for k in ('stage','status','technical_status','restart_or_reassignment_detected')}))
    return 2  # INCONCLUSIVE is not permission to repeat a scientific stage.


if __name__=='__main__':
    raise SystemExit(main())
