"""Shared pure-Python protocol helpers. Importing this module never loads a model."""
import hashlib
import json
import os
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent


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
