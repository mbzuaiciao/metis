"""Shared pure-Python protocol helpers. Importing this module never loads a model."""
import hashlib
import json
import os
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def read_json(path):
    return json.loads(Path(path).read_text())


def rows(name):
    return [json.loads(line) for line in (ROOT / name).read_text().splitlines()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_freeze():
    frozen = read_json(ROOT / 'freeze.json')
    for name, digest in frozen['sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f'Frozen preparation changed: {name}')
    return frozen


def config():
    return read_json(ROOT / 'config.json')


def messages(case, condition, probe):
    cfg = config()
    # The knowledge task is identical in A/B/C. B changes application instructions only.
    key = 'improved_instruction' if condition == 'B' and probe == 'application' else 'standard_instruction'
    return [{'role': 'system', 'content': cfg[key]},
            {'role': 'user', 'content': case[f'{probe}_probe']}]


def plan(condition):
    if condition not in ('A', 'B', 'C'):
        raise ValueError('Unknown condition')
    tasks = [dict(case_id=c['id'], probe=p, messages=messages(c, condition, p))
             for c in rows('heldout.jsonl') for p in ('knowledge', 'application')]
    random.Random(config()['order_seed']).shuffle(tasks)
    return tasks


def private_run(path):
    path = Path(path).resolve()
    boundary = (REPO / 'research' / 'runs').resolve()
    if not path.is_relative_to(boundary) or path == boundary:
        raise ValueError('Outputs must be in a new subdirectory of ignored research/runs/')
    os.umask(0o077)
    path.mkdir(parents=True, mode=0o700, exist_ok=False)
    return path


def runtime_metadata():
    import importlib.metadata
    packages = {}
    for package in ('torch', 'transformers', 'trl', 'peft', 'datasets', 'accelerate', 'huggingface-hub'):
        packages[package] = importlib.metadata.version(package)
    try:
        git_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
        git_status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO, text=True)
    except subprocess.CalledProcessError:
        git_head, git_status = 'unavailable', 'unavailable'
    return dict(packages=packages, git_head=git_head, git_status=git_status)


def local_snapshot(path):
    """Require the explicit HF snapshot path for the frozen revision, never a moving cache alias."""
    path = Path(path).expanduser().resolve()
    if path.name != config()['model_revision'] or not (path / 'config.json').is_file():
        raise ValueError('Pass the local HF snapshot directory ending in the frozen revision SHA')
    return str(path)


def enforce_versions():
    expected = dict(line.strip().split('==') for line in (ROOT / 'requirements.txt').read_text().splitlines()
                    if line.strip() and not line.startswith('#'))
    actual = runtime_metadata()['packages']
    for name, version in expected.items():
        # PyTorch CUDA wheel versions may have +cuNNN build tags; archive the full version.
        if actual[name].split('+')[0] != version:
            raise ValueError(f'{name}: expected {version}, found {actual[name]}')


def verify_adapter_import(adapter):
    """Accept only the original v3-trained artifact; never relabel it as v4 training."""
    adapter = Path(adapter)
    expected = read_json(ROOT/'ADAPTER_IMPORT.json')
    binding_path = adapter.parent/'training_binding.json'
    manifest_path = adapter.parent/'manifest.json'
    if (sha(binding_path) != expected['original_training_binding_sha256']
            or sha(manifest_path) != expected['original_training_manifest_sha256']):
        raise ValueError('Original v3 training binding or manifest changed')
    binding, manifest = read_json(binding_path), read_json(manifest_path)
    if (manifest.get('status') != 'complete'
            or binding.get('freeze_sha256') != expected['original_scientific_freeze_sha256']
            or binding.get('model_id') != config()['model_id']
            or binding.get('model_revision') != config()['model_revision']
            or binding.get('adapter_files') != expected['adapter_files']
            or {p.name for p in adapter.iterdir() if p.is_file()} != set(expected['adapter_files'])):
        raise ValueError('Only the frozen original v3 adapter may be imported')
    if any(sha(adapter/name) != digest for name,digest in expected['adapter_files'].items()):
        raise ValueError('Imported v3 adapter file changed')
    return binding


def verify_termination_record(record):
    tokens = record.get('generated_token_ids')
    if (not isinstance(tokens,list) or not tokens or len(tokens) > config()['generation']['max_new_tokens']
            or any(type(t) is not int or t<0 for t in tokens)
            or len(tokens) != record.get('completion_tokens')
            or tokens[-1] != 151645 or record.get('truncated') is not False):
        raise ValueError('Incomplete or inconsistent raw token evidence')
    expected = dict(eos_token_id=151645,last_token_id=tokens[-1],ended_with_eos=True,
        reached_token_limit=len(tokens)>=config()['generation']['max_new_tokens'],
        eos_positions=[i for i,t in enumerate(tokens) if t==151645],
        alternative_terminator_positions=[i for i,t in enumerate(tokens) if t==151643],
        observed_stop='eos',max_new_tokens=config()['generation']['max_new_tokens'])
    if record.get('termination') != expected:
        raise ValueError('Termination metadata changed')


def require_complete_baselines(run_paths):
    """Metadata-only gate before training imports, output creation or optimization.

    Parsing records does not authorize human inspection of response content.
    """
    if len(run_paths) != 2 or len({str(Path(x).resolve()) for x in run_paths}) != 2:
        raise ValueError('Two distinct complete A/B baseline directories required')
    checked = []
    for condition, path in zip('AB', run_paths):
        path = Path(path).resolve()
        manifest = read_json(path / 'manifest.json')
        if (manifest.get('condition') != condition or manifest.get('status') != 'complete'
                or manifest.get('freeze_sha256') != sha(ROOT / 'freeze.json')
                or manifest.get('config') != config()
                or any(manifest.get(k) != 40 for k in ('planned_calls', 'attempted', 'completed', 'saved'))
                or manifest.get('truncated') != 0):
            raise ValueError('Baseline is incomplete or belongs to another frozen study')
        if (manifest.get('generation_resolution') != dict(use_model_defaults=False,mode='greedy_search')
                or any(manifest.get('generation_config',{}).get(k)!=v for k,v in
                       dict(config()['generation'],eos_token_id=151645,pad_token_id=151643).items())):
            raise ValueError('Effective v4 baseline generation configuration changed')
        record_hashes = {}
        for task in plan(condition):
            name = f"{task['case_id']}-{task['probe']}.json"
            record = read_json(path / name)
            if (any(record.get(k) != task[k] for k in ('case_id', 'probe', 'messages'))
                    or record.get('condition') != condition or record.get('status') != 'complete'
                    or record.get('truncated') is not False or record.get('completion_tokens', 0) <= 0):
                raise ValueError('Baseline response missing, truncated, or mismatched')
            verify_termination_record(record)
            record_hashes[name] = sha(path / name)
        if manifest.get('record_sha256') != record_hashes:
            raise ValueError('Baseline record binding changed')
        checked.append(dict(condition=condition, path=str(path), manifest_sha256=sha(path / 'manifest.json'),
                            model_path=manifest.get('model_path'),
                            template_sha256=manifest.get('tokenizer_chat_template_sha256')))
    if (not checked[0]['template_sha256'] or checked[0]['template_sha256'] != checked[1]['template_sha256']
            or checked[0]['model_path'] != checked[1]['model_path']):
        raise ValueError('Baseline model/template mismatch')
    return checked
