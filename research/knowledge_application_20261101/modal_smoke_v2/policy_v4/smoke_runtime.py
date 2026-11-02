"""UNEXECUTED synthetic runtime; no experiment dataset or application imports.

At most one optimizer step per physical execution (four toy copies for accumulation=4).
An 840-second process watchdog includes imports/download/model work after entry.
"""
import hashlib
import json
import math
import os
import signal
import uuid
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import threading
import time

MODEL_ID = 'Qwen/Qwen3-4B-Instruct-2507'
REVISION = 'cdbee75f17c01a7cc42f958dc650907174af0554'
EXPECTED_GPU = 'L40S'
MAX_STEPS = 1
WATCHDOG_SECONDS = 840
SYNTHETIC_USER = 'Return exactly the label: cobalt.'
SYNTHETIC_TARGET = 'cobalt.'


def check_mask(prompt_ids, full_ids, labels, eos_id):
    """Exact token identity/mask checks, also testable with pure Python fixtures."""
    n = len(prompt_ids)
    if not prompt_ids or full_ids[:n] != prompt_ids or len(full_ids) <= n:
        raise ValueError('Invalid assistant completion boundary')
    if full_ids[-1] != eos_id:
        raise ValueError('Expected assistant EOS at the end of the training sequence')
    if len(labels) != len(full_ids) or labels[:n] != [-100] * n or labels[n:] != full_ids[n:]:
        raise ValueError('Actual collator labels must mask all prompt and only prompt tokens')


def verify_versions(requirements):
    import importlib.metadata
    actual = {}
    for line in requirements.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        package, version = line.strip().split('==')
        actual[package] = importlib.metadata.version(package)
        if actual[package].split('+')[0] != version:
            raise ValueError(f'Pinned version mismatch for {package}')
    return actual


def execution_metadata(submission_id):
    # Allowlist only public execution identifiers; never dump the environment or identity token.
    metadata = dict(submission_id=submission_id, execution_id=str(uuid.uuid4()),
                    started_at_utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
                    container_id=os.environ.get('MODAL_TASK_ID'), image_id=os.environ.get('MODAL_IMAGE_ID'),
                    region=os.environ.get('MODAL_REGION'), cloud_provider=os.environ.get('MODAL_CLOUD_PROVIDER'))
    try:
        import modal
        metadata['input_id'] = modal.current_input_id()
        metadata['function_call_id'] = modal.current_function_call_id()
    except Exception as exc:
        metadata['identity_error_type'] = type(exc).__name__
    return metadata


def run(expected_hashes, submission_id):
    start = time.perf_counter()
    report = dict(status='INCONCLUSIVE', technical_status='incomplete', termination_status='running',
                  model_id=MODEL_ID, model_revision=REVISION, optimizer_steps=0,
                  forward_backward_microbatches=0, example='one nonfinancial label-copy example', phases={},
                  v2_freeze_sha256='4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91')
    def event(kind):
        print('METIS_SMOKE_EVENT '+json.dumps(dict(event=kind, report=report), sort_keys=True), flush=True)

    def expire():
        report.update(termination_status='watchdog_exit_124', elapsed_seconds=time.perf_counter()-start)
        event('interrupted')
        os._exit(124)  # A provider restart remains possible; local wait/cancel bounds observation only.

    watchdog = threading.Timer(WATCHDOG_SECONDS, expire)
    watchdog.daemon = True
    watchdog.start()
    previous_handlers = {}
    def interrupted(signum, frame):
        report.update(signal_observed=signum, termination_status='signal_interruption')
        event('interrupted')
        raise InterruptedError('Smoke interrupted; any result is inconclusive')

    torch = None
    try:
        report['execution'] = execution_metadata(submission_id)
        event('started')
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous_handlers[sig] = signal.signal(sig, interrupted)
        source = Path('/opt/metis-smoke')
        for name in ('config.json', 'requirements.txt'):
            if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected_hashes[name]:
                raise ValueError('Shipped frozen config/requirements digest mismatch')
        cfg = json.loads((source / 'config.json').read_text())
        if (cfg['model_id'], cfg['model_revision']) != (MODEL_ID, REVISION):
            raise ValueError('Unexpected model or revision')
        report['packages'] = verify_versions((source / 'requirements.txt').read_text())
        report['frozen_config'] = cfg
        import gc
        import importlib.metadata
        import subprocess
        import torch as torch_module
        torch = torch_module
        from datasets import Dataset
        from peft import LoraConfig, PeftModel, get_peft_model_state_dict
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback, set_seed
        from trl import SFTConfig, SFTTrainer
        from huggingface_hub import snapshot_download
        report['pip_freeze'] = subprocess.check_output(
            ['python', '-m', 'pip', 'freeze'], text=True, timeout=20)
        report['pip_check'] = subprocess.check_output(
            ['python', '-m', 'pip', 'check'], text=True, timeout=20)
        report['nvidia_smi'] = subprocess.check_output(['nvidia-smi', '-q'], text=True, timeout=10)
        if (not torch.cuda.is_available() or torch.cuda.device_count() != 1
                or not torch.cuda.is_bf16_supported()):
            raise RuntimeError('Exactly one BF16 CUDA GPU required')
        props = torch.cuda.get_device_properties(0)
        if EXPECTED_GPU not in props.name or not 44 <= props.total_memory / 2**30 <= 50:
            raise RuntimeError('Expected exactly one 48GB-class L40S; no fallback')
        report.update(gpu=props.name, total_vram_bytes=props.total_memory, cuda=torch.version.cuda)
        torch.cuda.reset_peak_memory_stats()
        set_seed(cfg['seed'])
        phase = time.perf_counter()
        # Fresh ephemeral cache. No secret/token injection; public model only. No explicit retry loop.
        snapshot = Path(snapshot_download(repo_id=MODEL_ID, revision=REVISION, token=False,
                                         max_workers=1, local_files_only=False))
        if snapshot.name != REVISION:
            raise ValueError('Snapshot is not the frozen revision')
        # Hash every downloaded artifact while the watchdog is active, including weight shards.
        report['snapshot_sha256'] = {str(f.relative_to(snapshot)): hashlib.file_digest(f.open('rb'), 'sha256').hexdigest()
                                     for f in snapshot.rglob('*') if f.is_file()}
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False)
        if (tokenizer.eos_token != '<|im_end|>' or tokenizer.eos_token_id != 151645
                or tokenizer.pad_token_id is None or tokenizer.pad_token_id == tokenizer.eos_token_id):
            raise ValueError('Unexpected EOS/padding tokens')
        report.update(tokenizer_chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
                      eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id)
        messages = [{'role': 'system', 'content': cfg['standard_instruction']},
                    {'role': 'user', 'content': SYNTHETIC_USER}]
        prefix = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        full = tokenizer.apply_chat_template(messages + [{'role': 'assistant', 'content': SYNTHETIC_TARGET}],
                                             tokenize=False, add_generation_prompt=False).rstrip('\n')
        if not prefix.endswith('<|im_start|>assistant\n') or not full.startswith(prefix):
            raise ValueError('Template assistant prefix mismatch')
        prompt_ids = tokenizer(prefix, add_special_tokens=False)['input_ids']
        full_ids = tokenizer(full, add_special_tokens=False)['input_ids']
        if len(full_ids) > cfg['max_train_tokens']:
            raise ValueError('Synthetic sequence would truncate')
        report.update(prompt_tokens=len(prompt_ids), sequence_tokens=len(full_ids),
                      target_tokens=len(full_ids)-len(prompt_ids))
        model = AutoModelForCausalLM.from_pretrained(str(snapshot), local_files_only=True,
                    trust_remote_code=False, torch_dtype=torch.bfloat16, attn_implementation='sdpa')
        if model.config.model_type != 'qwen3' or model.config._attn_implementation != 'sdpa':
            raise ValueError('Unexpected model architecture or attention implementation')
        model.config.use_cache = False
        report['phases']['download_tokenizer_model_seconds'] = time.perf_counter()-phase
        t = cfg['training']
        if t['batch_size'] != 1 or t['gradient_accumulation_steps'] != 4:
            raise ValueError('Unexpected fixed microbatch configuration')

        class OneStepChecks(TrainerCallback):
            def on_substep_end(self, args, state, control, **kwargs):
                report['forward_backward_microbatches'] += 1

            def on_pre_optimizer_step(self, args, state, control, model=None, optimizer=None, **kwargs):
                if state.global_step != 0 or report['optimizer_steps'] != 0:
                    raise RuntimeError('A second optimizer step is forbidden')
                trainable = {id(p) for p in model.parameters() if p.requires_grad}
                if {id(p) for group in optimizer.param_groups for p in group['params']} != trainable:
                    raise ValueError('Optimizer contains frozen base parameters or misses adapters')
                nonzero = 0
                for name, param in model.named_parameters():
                    if param.requires_grad:
                        if 'lora_' not in name or param.grad is None or not torch.isfinite(param.grad).all().item():
                            raise ValueError('Expected finite LoRA-only gradients')
                        nonzero += int(torch.count_nonzero(param.grad).item() > 0)
                    elif param.grad is not None:
                        raise ValueError('Frozen base parameter received a gradient')
                if not nonzero:
                    raise ValueError('No nonzero LoRA gradient')
                # Initial LoRA A gradients may legitimately be zero while B receives a gradient.
                report['nonzero_lora_gradient_tensors'] = nonzero
                report['learning_rate_used'] = optimizer.param_groups[0]['lr']

            def on_optimizer_step(self, args, state, control, **kwargs):
                report['optimizer_steps'] += 1
                report['forward_backward_microbatches'] += 1
                if report['optimizer_steps'] > MAX_STEPS:
                    raise RuntimeError('Optimizer-step cap exceeded')

        with tempfile.TemporaryDirectory(prefix='metis-smoke-only-') as work:
            # Four copies of ONE unique toy example preserve accumulation=4 in a single optimizer step.
            row = dict(prompt=prefix, completion=full[len(prefix):])
            trainer = SFTTrainer(model=model, processing_class=tokenizer,
                train_dataset=Dataset.from_list([row.copy() for _ in range(4)]),
                peft_config=LoraConfig(**cfg['lora']), callbacks=[OneStepChecks()],
                args=SFTConfig(output_dir=work, max_steps=MAX_STEPS, num_train_epochs=t['epochs'],
                    learning_rate=t['learning_rate'], per_device_train_batch_size=t['batch_size'],
                    gradient_accumulation_steps=t['gradient_accumulation_steps'],
                    warmup_steps=t['warmup_steps'], weight_decay=t['weight_decay'],
                    lr_scheduler_type=t['lr_scheduler_type'], max_grad_norm=t['max_grad_norm'],
                    seed=cfg['seed'], data_seed=cfg['data_seed'], bf16=True, fp16=False,
                    gradient_checkpointing=True, gradient_checkpointing_kwargs={'use_reentrant': False},
                    optim='adamw_torch', max_length=cfg['max_train_tokens'], packing=False,
                    completion_only_loss=True, assistant_only_loss=False, eos_token=tokenizer.eos_token,
                    save_strategy='no', eval_strategy='no', logging_steps=1, report_to='none', push_to_hub=False))
            for item in trainer.train_dataset:
                batch = trainer.data_collator([item])
                if batch['input_ids'][0].tolist() != full_ids:
                    raise ValueError('TRL preprocessing changed the expected full token sequence')
                check_mask(prompt_ids, full_ids, batch['labels'][0].tolist(), tokenizer.eos_token_id)
            if trainer.model.get_base_model().dtype != torch.bfloat16:
                raise ValueError('Unexpected base precision')
            frozen_versions = {n: p._version for n,p in trainer.model.named_parameters() if not p.requires_grad}
            trainable = [(n,p) for n,p in trainer.model.named_parameters() if p.requires_grad]
            if not frozen_versions or not trainable or any('lora_' not in n for n,p in trainable):
                raise ValueError('Expected frozen base and LoRA-only trainable parameters')
            report['trainable_parameters'] = sum(p.numel() for n,p in trainable)
            report['trainable_dtypes'] = sorted({str(p.dtype) for n,p in trainable})
            if report['trainable_parameters'] != 11796480 or report['trainable_dtypes'] != ['torch.float32']:
                raise ValueError('Unexpected LoRA parameter count or precision')
            phase = time.perf_counter()
            torch.cuda.synchronize()
            result = trainer.train()
            torch.cuda.synchronize()
            report['phases']['one_optimizer_step_seconds'] = time.perf_counter()-phase
            if (trainer.state.global_step != 1 or report['optimizer_steps'] != 1
                    or report['forward_backward_microbatches'] != 4 or not math.isfinite(result.training_loss)):
                raise ValueError('Expected exactly four microbatches and one finite optimizer step')
            for name,param in trainer.model.named_parameters():
                if name in frozen_versions and (param.requires_grad or param.grad is not None
                                                or param._version != frozen_versions[name]):
                    raise ValueError('Base weights were unfrozen, differentiated or mutated in-place')
            report['base_frozen_checks_passed'] = True
            adapter = Path(work)/'disposable_adapter'
            trainer.save_model(str(adapter))
            saved = {n: p.detach().cpu().clone() for n,p in get_peft_model_state_dict(trainer.model).items()}
            report['adapter_sha256'] = {f.name: hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
                                         for f in adapter.iterdir() if f.is_file()}
            report['training_loss'] = result.training_loss
            # No generated text or financial judgment. Check teacher-forced finite logits after reload.
            del trainable, batch, item, trainer, model
            gc.collect()
            torch.cuda.empty_cache()
            phase = time.perf_counter()
            base = AutoModelForCausalLM.from_pretrained(str(snapshot), local_files_only=True,
                        trust_remote_code=False, torch_dtype=torch.bfloat16, attn_implementation='sdpa').to('cuda')
            reloaded = PeftModel.from_pretrained(base, str(adapter), is_trainable=False, local_files_only=True)
            state = get_peft_model_state_dict(reloaded)
            if set(state) != set(saved) or any(not torch.equal(state[n].cpu(),saved[n]) for n in state):
                raise ValueError('Reloaded adapter tensors differ from saved tensors')
            reloaded.eval()
            inputs = tokenizer(full, add_special_tokens=False, return_tensors='pt').to('cuda')
            with torch.inference_mode():
                logits = reloaded(**inputs, use_cache=False).logits
            torch.cuda.synchronize()
            if logits.device.type != 'cuda' or not torch.isfinite(logits).all().item():
                raise ValueError('Reloaded GPU logits are nonfinite or on wrong device')
            report.update(reload_exact=True, finite_reload_logits=True,
                          reload_logits_shape=list(logits.shape), technical_status='passed',
                          termination_status='returned_normal')
            report['phases']['reload_forward_seconds'] = time.perf_counter()-phase
        return report
    except Exception as exc:
        report.update(technical_status='failed', failure_type=type(exc).__name__)
        if report['termination_status'] == 'running':
            report['termination_status'] = 'exception'
        return report
    finally:
        watchdog.cancel()
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
        report['elapsed_seconds'] = time.perf_counter()-start
        if torch is not None and torch.cuda.is_initialized():
            report['peak_allocated_bytes'] = torch.cuda.max_memory_allocated()
            report['peak_reserved_bytes'] = torch.cuda.max_memory_reserved()
        # Capture sanitized diagnostics even when no successful return reaches the local wrapper.
        report['ended_at_utc'] = datetime.now(timezone.utc).isoformat()
        event('finished')
