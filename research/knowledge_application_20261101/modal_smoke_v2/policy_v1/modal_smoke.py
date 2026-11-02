"""Plan a synthetic Modal smoke test. --execute is blocked by provider retry semantics.

No Modal import, image build or resource operation occurs in default/blocked modes.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V2 = ROOT.parent / 'v2'
V2_FREEZE_SHA256 = '4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91'
MODAL_VERSION = '1.2.3'
GPU = 'L40S'
FUNCTION_OPTIONS = dict(gpu=GPU, cpu=(2.0, 2.0), memory=(32768, 32768),
                        ephemeral_disk=51200, timeout=840, startup_timeout=30,
                        retries=0, min_containers=0, max_containers=1,
                        buffer_containers=0, scaledown_window=1, max_inputs=1,
                        serialized=True, include_source=False)
BLOCKERS = (
    'Modal GPU Functions may restart after preemption and container crashes despite retries=0; '
    'at-most-one GPU attempt and an aggregate 15-minute billed bound cannot be guaranteed. '
    'Non-preemptible GPU Functions are not supported. No execution under the current constraints.',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preparation():
    # Read only the freeze, config and requirements, never scenario datasets or private archives.
    if sha(V2 / 'freeze.json') != V2_FREEZE_SHA256:
        raise ValueError('Unexpected frozen v2 manifest')
    frozen = json.loads((V2 / 'freeze.json').read_text())
    for name in ('config.json', 'requirements.txt'):
        if sha(V2 / name) != frozen['sha256'][name]:
            raise ValueError(f'Frozen input changed: {name}')
    cfg = json.loads((V2 / 'config.json').read_text())
    pins = [s.strip() for s in (V2 / 'requirements.txt').read_text().splitlines()
            if s.strip() and not s.startswith('#')]
    smoke = json.loads((ROOT / 'smoke_freeze.json').read_text())
    for name, digest in smoke['sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f'Smoke source changed: {name}')
    return cfg, pins, {name: frozen['sha256'][name] for name in ('config.json', 'requirements.txt')}


def build_candidate(pins):
    """UNEXECUTED candidate definition; called only after the fail-closed gate.

    Official SDK compatibility is documentation-only. No whole-repository upload.
    """
    import importlib.metadata
    import modal
    if importlib.metadata.version('modal') != MODAL_VERSION:
        raise ValueError('Use exactly the documented Modal client pin')
    image = (modal.Image.debian_slim(python_version='3.12')
             .uv_pip_install(*pins)
             .env({'HF_HOME': '/tmp/metis-smoke-hf', 'HF_HUB_DISABLE_TELEMETRY': '1',
                   'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1', 'WANDB_DISABLED': 'true',
                   'PYTHONPATH': '/opt/metis-smoke'})
             .add_local_file(ROOT / 'smoke_runtime.py', '/opt/metis-smoke/smoke_runtime.py')
             .add_local_file(V2 / 'config.json', '/opt/metis-smoke/config.json')
             .add_local_file(V2 / 'requirements.txt', '/opt/metis-smoke/requirements.txt'))
    app = modal.App('metis-v2-synthetic-smoke', include_source=False)

    @app.function(image=image, **FUNCTION_OPTIONS)
    def smoke(expected_hashes):
        from smoke_runtime import run
        return run(expected_hashes)

    return app, smoke


def launch_candidate(pins, expected_hashes, out):
    """One submitted input, no application-level retries. Currently unreachable via CLI."""
    import os
    out = Path(out).resolve()
    boundary = (REPO / 'research' / 'runs').resolve()
    if not out.is_relative_to(boundary) or out == boundary:
        raise ValueError('Output must be a new private research/runs/ subdirectory')
    os.umask(0o077)
    out.mkdir(parents=True, mode=0o700, exist_ok=False)
    app, smoke = build_candidate(pins)
    try:
        with app.run():  # Ephemeral app, not deploy/serve/detached execution.
            result = smoke.remote(expected_hashes)
        (out / 'report.json').write_text(json.dumps(result, indent=2))
    except Exception as exc:
        (out / 'failure.json').write_text(json.dumps({'status': 'failed', 'type': type(exc).__name__}))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--out', default='research/runs/ka-modal-smoke-v2-01')
    args = parser.parse_args()
    cfg, pins, hashes = preparation()
    if not args.execute:
        print(json.dumps(dict(status='prepared_execution_blocked', model_id=cfg['model_id'],
                              model_revision=cfg['model_revision'], v2_freeze_sha256=V2_FREEZE_SHA256,
                              modal_version=MODAL_VERSION, dependencies=pins,
                              options=FUNCTION_OPTIONS, optimizer_steps_max=1,
                              synthetic_unique_examples=1, microbatches=4,
                              blockers=BLOCKERS), indent=2))
        return
    if BLOCKERS:
        parser.error('NO-GO: ' + ' '.join(BLOCKERS))
    launch_candidate(pins, hashes, args.out)


if __name__ == '__main__':
    main()
