"""Plan or explicitly submit one synthetic Modal smoke call; never resubmit.

Default mode is offline. Infrastructure history is best effort, so ambiguity is INCONCLUSIVE.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
import time
import uuid
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
HISTORY_LIMITATION = (
    'Modal call-graph history is best effort, not a complete physical-attempt ledger. '
    'A single observed successful task does not establish uninterrupted execution.'
)
RESULT_WAIT_SECONDS = 900


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def history_snapshot(call):
    """Read public InputInfo fields once, never poll/retry or infer ledger completeness."""
    snapshot = dict(captured_at_utc=utc_now(), complete=False, nodes=[])
    try:
        stack = list(call.get_call_graph())
        while stack:
            node = stack.pop()
            if len(snapshot['nodes']) >= 256:
                snapshot['truncated'] = True
                break
            status = getattr(node, 'status', None)
            snapshot['nodes'].append(dict(
                input_id=getattr(node, 'input_id', None),
                function_call_id=getattr(node, 'function_call_id', None),
                task_id=getattr(node, 'task_id', None),
                status=getattr(status, 'name', str(status) if status is not None else None)))
            stack.extend(getattr(node, 'children', []))
    except Exception as exc:
        snapshot['error_type'] = type(exc).__name__
    return snapshot


def assess(result, submission_id, call_id, history, termination, cleanup):
    """No overall PASS from incomplete platform evidence, even if technical checks pass."""
    reasons = [HISTORY_LIMITATION]
    if not isinstance(result, dict):
        result = {}
    relevant = [n for snap in history for n in snap.get('nodes', [])
                if n.get('function_call_id') == call_id and call_id]
    tasks = {n['task_id'] for n in relevant if n.get('task_id')}
    execution = result.get('execution')
    if not isinstance(execution, dict):
        execution = {}
    if execution.get('container_id'):
        tasks.add(execution['container_id'])
    restart = len(tasks) > 1
    if restart:
        reasons.append('Multiple container assignments observed for this submission: restart or reassignment.')
    if termination != 'result_received':
        reasons.append('No complete result received: ' + termination)
    required_flags = ('base_frozen_checks_passed', 'reload_exact', 'finite_reload_logits')
    complete = (isinstance(result, dict) and result.get('technical_status') == 'passed'
                and result.get('optimizer_steps') == 1
                and result.get('forward_backward_microbatches') == 4
                and all(result.get(k) is True for k in required_flags)
                and result.get('termination_status') == 'returned_normal')
    if not complete:
        reasons.append('Technical checks failed, were interrupted, or are incomplete.')
    if (execution.get('submission_id') != submission_id or execution.get('function_call_id') != call_id
            or not all(execution.get(k) for k in ('input_id','container_id','execution_id','started_at_utc'))):
        reasons.append('Missing or mismatched execution identity.')
    if result and result.get('signal_observed'):
        reasons.append('Termination/interruption signal observed; preemption cannot be excluded.')
    if not relevant or any(snap.get('error_type') or snap.get('truncated') for snap in history):
        reasons.append('Call-graph evidence missing, unavailable or truncated.')
    if relevant and any(n.get('status') not in ('SUCCESS', 'PENDING') for n in relevant):
        reasons.append('Non-success termination status observed in call history.')
    if cleanup != 'cancel_requested_and_app_context_exited':
        reasons.append('Container/app cleanup not confirmed by local control flow.')
    return dict(status='INCONCLUSIVE', technical_status='passed' if complete else 'failed_or_incomplete',
                restart_or_reassignment_detected=restart, physical_history_complete=False,
                observed_container_ids=sorted(tasks), reasons=reasons)



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
    """UNEXECUTED candidate definition; called only for an explicit --execute invocation.

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
    def smoke(expected_hashes, submission_id):
        from smoke_runtime import run
        return run(expected_hashes, submission_id)

    return app, smoke


def launch_candidate(pins, expected_hashes, out):
    """One intentional submission; failures never submit again. No cloud state is created in plan mode."""
    import os
    out = Path(out).resolve()
    boundary = (REPO / 'research' / 'runs').resolve()
    if not out.is_relative_to(boundary) or out == boundary:
        raise ValueError('Output must be a new private research/runs/ subdirectory')
    os.umask(0o077)
    out.mkdir(parents=True, mode=0o700, exist_ok=False)
    start = time.perf_counter()
    submission_id = str(uuid.uuid4())
    record = dict(status='INCONCLUSIVE', submission_id=submission_id, intentional_submissions=0,
                  submission_acknowledged=False, started_at_utc=utc_now(),
                  v2_freeze_sha256=V2_FREEZE_SHA256, smoke_freeze_sha256=sha(ROOT/'smoke_freeze.json'),
                  termination_status='not_submitted', cleanup_status='not_started', history=[])
    result, call, app_exited = None, None, False

    def save():
        temporary = out/'report.json.tmp'
        temporary.write_text(json.dumps(record, indent=2))
        temporary.replace(out/'report.json')

    save()  # Interrupted local processes leave an INCONCLUSIVE record, never a stale PASS.
    try:
        app, smoke = build_candidate(pins)
        with app.run():  # Ephemeral app; the call handle stays attached until cleanup.
            try:
                record.update(app_id=app.app_id, function_id=smoke.object_id,
                              intentional_submissions=1, submitted_at_utc=utc_now(),
                              termination_status='submission_acknowledgement_unknown')
                save()  # Persist intent before RPC: a lost acknowledgement never triggers resubmission.
                call = smoke.spawn(expected_hashes, submission_id)
                record.update(function_call_id=call.object_id, submission_acknowledged=True,
                              termination_status='awaiting_result')
                save()
                record['history'].append(history_snapshot(call))
                result = call.get(timeout=RESULT_WAIT_SECONDS)
                record['result_received_at_utc'] = utc_now()
                record['termination_status'] = 'result_received'
                record['remote_result'] = result
            finally:
                if call is not None:
                    record['history'].append(history_snapshot(call))
                    try:
                        call.cancel(terminate_containers=True)
                        record['cleanup_status'] = 'cancel_requested'
                    except Exception as exc:
                        record.update(cleanup_status='cancel_request_failed', cleanup_error_type=type(exc).__name__)
                save()
        app_exited = True
    except BaseException as exc:
        record.update(local_error_type=type(exc).__name__)
        if record['termination_status'] != 'result_received':
            record['termination_status'] = 'exception_or_interruption_without_result'
    finally:
        if app_exited and record['cleanup_status'] == 'cancel_requested':
            record['cleanup_status'] = 'cancel_requested_and_app_context_exited'
        record.update(assess(result, submission_id, record.get('function_call_id'), record['history'],
                             record['termination_status'], record['cleanup_status']))
        if record.get('local_error_type'):
            record['reasons'].append('Local exception or interruption: '+record['local_error_type'])
        record.update(ended_at_utc=utc_now(), elapsed_seconds=time.perf_counter()-start)
        save()
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--out', default='research/runs/ka-modal-smoke-v2-01')
    args = parser.parse_args()
    cfg, pins, hashes = preparation()
    if not args.execute:
        print(json.dumps(dict(status='prepared_requires_separate_execution_authorization', model_id=cfg['model_id'],
                              model_revision=cfg['model_revision'], v2_freeze_sha256=V2_FREEZE_SHA256,
                              modal_version=MODAL_VERSION, dependencies=pins,
                              options=FUNCTION_OPTIONS, optimizer_steps_max=1,
                              synthetic_unique_examples=1, microbatches=4,
                              physical_history_complete=False, history_limitation=HISTORY_LIMITATION), indent=2))
        return
    record = launch_candidate(pins, hashes, args.out)
    print(json.dumps({k: record[k] for k in ('status','technical_status','submission_id','reasons')}, indent=2))
    return 2 if record['status'] == 'INCONCLUSIVE' else 0


if __name__ == '__main__':
    raise SystemExit(main())
