"""Plan or explicitly submit one synthetic Modal smoke call; never resubmit.

Default mode is offline. Infrastructure history is best effort, so ambiguity is INCONCLUSIVE.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import traceback
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
                        timeout=840, startup_timeout=30,
                        retries=0, min_containers=0, max_containers=1,
                        buffer_containers=0, scaledown_window=2, max_inputs=1,
                        serialized=True, include_source=False)
# Exact public option names only; this never permits option VALUES through redaction.
PUBLIC_MODAL_FIELDS = frozenset(FUNCTION_OPTIONS) | {
    'container_idle_timeout', 'task_idle_timeout_secs', 'timeout_secs', 'startup_timeout_secs',
    'ephemeral_disk', 'ephemeral_disk_mb',
}
HISTORY_LIMITATION = (
    'Modal call-graph history is best effort, not a complete physical-attempt ledger. '
    'A single observed successful task does not establish uninterrupted execution.'
)
RESULT_WAIT_SECONDS = 900


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def validate_function_options(options=None):
    options = FUNCTION_OPTIONS if options is None else options
    # This bounded smoke uses the platform default disk quota. An explicit override
    # needs a separate review, even if it meets the server's 512 GiB..3 TiB range.
    if options.get('ephemeral_disk') is not None:
        raise ValueError('Smoke requires default ephemeral_disk; remove the explicit disk override')
    # SDK 1.2.3 checks only >0 locally. FunctionCreate enforces this stricter server range.
    window = options['scaledown_window']
    if type(window) is not int or not 2 <= window <= 3600:
        raise ValueError('Modal scaledown_window must be an integer between 2 and 3600 (inclusive)')


def sanitize(text):
    """Redact diagnostic text; never emit environment dumps, source lines or locals."""
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', str(text))
    # Values are used transiently for matching only, never serialized or printed.
    values = {value for key, value in os.environ.items() if value and
              (len(value) >= 4 or re.search(r'TOKEN|SECRET|PASSWORD|CREDENTIAL|API_KEY', key, re.I))}
    for value in sorted(values, key=len, reverse=True):
        text = text.replace(value, '[REDACTED_ENV_VALUE]')
    text = re.sub(r'(?i)\b(?:authorization|bearer|password|token|secret|api[_-]?key|credential|private[_-]?data)\b\s*[:=]?\s*[^\s,;]+',
                  '[REDACTED_CREDENTIAL]', text)
    text = re.sub(r'\b(?:ak-|as-|sk-|hf_|ghp_|github_pat_)[A-Za-z0-9_.-]+', '[REDACTED_TOKEN]', text)
    text = re.sub(r'\beyJ[A-Za-z0-9_.-]+', '[REDACTED_TOKEN]', text)
    text = re.sub(r'(?i)https?://[^\s<>]+', '[REDACTED_URL]', text)
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[REDACTED_EMAIL]', text)
    text = re.sub(r'(?:/(?:Users|home|private|tmp|root|opt)/|[A-Za-z]:\\)[^\s<>]+', '[REDACTED_PATH]', text)
    text = re.sub(r'(?s)\{.*\}', '[REDACTED_STRUCTURED_DATA]', text)
    # Credential/env/path filtering has priority over this narrow name-only allowlist.
    fields = '|'.join(re.escape(name) for name in sorted(PUBLIC_MODAL_FIELDS))
    text = re.sub(r'''(["'`])(''' + fields + r''')\1''', lambda match: match[2], text)
    text = re.sub(r'''(["'`]).*?\1''', '[REDACTED_QUOTED_VALUE]', text)
    text = re.sub(r'\b[A-Za-z0-9_+/=-]{32,}\b', '[REDACTED_OPAQUE_VALUE]', text)
    return text[:8192]


def exception_diagnostic(exc, phase):
    """Preserve stack locations and chained exceptions, without source/locals/absolute paths."""
    chain, seen = [], set()
    current = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        frames = [dict(file=sanitize(Path(frame.f_code.co_filename).name), line=line,
                       function=sanitize(frame.f_code.co_name))
                  for frame, line in (traceback.walk_tb(current.__traceback__) if current.__traceback__ else [])]
        chain.append(dict(type=type(current).__name__, module=type(current).__module__,
                          message=sanitize(current), frames=frames))
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    formatted = []
    for item in reversed(chain):
        formatted.append('Traceback (source lines and locals omitted):')
        formatted.extend(f"  File {frame['file']}, line {frame['line']}, in {frame['function']}"
                         for frame in item['frames'])
        formatted.append(item['type']+': '+item['message'])
    return dict(phase=phase, caught_at_utc=utc_now(), type=type(exc).__name__, module=type(exc).__module__,
                message=sanitize(exc), traceback='\n'.join(formatted), chain=chain)


class RedactedOutput(io.TextIOBase):
    """Line buffer so tokens split across writes cannot bypass terminal redaction."""
    def __init__(self, target):
        self.target, self.pending = target, ''

    def write(self, text):
        self.pending += text
        while '\n' in self.pending or '\r' in self.pending:
            end = min(i for i in (self.pending.find('\n'), self.pending.find('\r')) if i >= 0)
            line, self.pending = self.pending[:end], self.pending[end+1:]
            self.target.write(sanitize(line)+'\n')
        return len(text)

    def flush(self):
        # Keep incomplete lines buffered until finish(), including when Rich calls flush().
        self.target.flush()

    def finish(self):
        if self.pending:
            self.target.write(sanitize(self.pending))
            self.pending = ''
        self.target.flush()

    def isatty(self):
        return False


@contextlib.contextmanager
def initialization_output():
    stdout, stderr = RedactedOutput(sys.stdout), RedactedOutput(sys.stderr)
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            import modal
            # In SDK 1.2.3 show_progress=False does not create an OutputManager.
            with modal.enable_output():
                yield
    finally:
        stdout.finish()
        stderr.finish()


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
        snapshot['diagnostic'] = exception_diagnostic(exc, 'call_history')
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
    validate_function_options()
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
    validate_function_options()  # Also protect direct callers before any SDK construction.
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
    """One intentional submission; phase diagnostics never retry a failed operation."""
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
                  termination_status='not_submitted', cleanup_status='not_started', history=[],
                  phase='local_construction', phase_history=[], exceptions=[])
    result, call, app_exited = None, None, False
    captured = set()

    def save():
        temporary = out/'report.json.tmp'
        temporary.write_text(json.dumps(record, indent=2))
        temporary.replace(out/'report.json')

    def phase(name):
        record['phase'] = name
        record['phase_history'].append(dict(phase=name, started_at_utc=utc_now()))
        save()

    def error(exc):
        if id(exc) in captured:
            return
        captured.add(id(exc))
        diagnostic = exception_diagnostic(exc, record['phase'])
        record['exceptions'].append(diagnostic)
        if 'local_error_type' not in record:
            record.update(local_error_type=diagnostic['type'], error_phase=diagnostic['phase'],
                          exception_message=diagnostic['message'], traceback=diagnostic['traceback'])
        save()
        # The report is private; terminal diagnostics use the same redaction.
        print(diagnostic['traceback'], file=sys.stderr)

    phase('local_construction')
    try:
        with initialization_output():
            app, smoke = build_candidate(pins)
            phase('app_initialization')
            with app.run():
                try:
                    phase('submission')
                    record.update(app_id=app.app_id, function_id=smoke.object_id,
                                  intentional_submissions=1, submitted_at_utc=utc_now(),
                                  termination_status='submission_acknowledgement_unknown')
                    save()
                    call = smoke.spawn(expected_hashes, submission_id)
                    record.update(function_call_id=call.object_id, submission_acknowledged=True,
                                  termination_status='awaiting_result')
                    phase('result_retrieval')
                    record['history'].append(history_snapshot(call))
                    result = call.get(timeout=RESULT_WAIT_SECONDS)
                    record['result_received_at_utc'] = utc_now()
                    record['termination_status'] = 'result_received'
                    record['remote_result'] = result
                    phase('result_received')
                except BaseException as exc:
                    error(exc)  # Preserve the failure phase before cleanup changes the current phase.
                    raise
                finally:
                    if call is not None:
                        phase('call_cleanup')
                        record['history'].append(history_snapshot(call))
                        try:
                            call.cancel(terminate_containers=True)
                            record['cleanup_status'] = 'cancel_requested'
                        except Exception as exc:
                            record.update(cleanup_status='cancel_request_failed', cleanup_error_type=type(exc).__name__)
                            error(exc)
                    phase('app_shutdown')
            app_exited = True
            phase('complete')
    except BaseException as exc:
        error(exc)
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
    parser.add_argument('--out', default='research/runs/ka-modal-smoke-v2-04')
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
