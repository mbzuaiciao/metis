"""Forty independent single-turn generations per condition; no automatic quality judging."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from common import (ROOT, config, enforce_versions, local_snapshot, plan, private_run,
                    read_json, runtime_metadata, sha, verify_freeze)



class TruncatedResponse(RuntimeError):
    """Saved output did not terminate at EOS; the arm must stop."""


def collect(tasks, generate, out, manifest):
    """Serial collection with a pure callback for offline stop-rule regression tests."""
    out = Path(out)
    manifest.update(attempted=0, completed=0, saved=0, truncated=0,
                    status='started', record_sha256={})
    try:
        for task in tasks:
            manifest['attempted'] += 1
            manifest['last_task'] = {k: task[k] for k in ('case_id', 'probe')}
            record = dict(**task, condition=manifest['condition'], **generate(task))
            name = f"{task['case_id']}-{task['probe']}.json"
            (out / name).write_text(json.dumps(record, indent=2))
            manifest['saved'] += 1
            manifest['record_sha256'][name] = sha(out / name)
            if record['status'] != 'complete' or record['truncated']:
                manifest['truncated'] += int(record['truncated'])
                raise TruncatedResponse('Saved non-EOS output; stop with remaining tasks unavailable')
            manifest['completed'] += 1
            (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        manifest['status'] = 'complete'
    except Exception as exc:
        manifest.update(status='incomplete', failure_type=type(exc).__name__)
        raise
    finally:
        manifest['unavailable'] = manifest['planned_calls'] - manifest['saved']
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--condition', choices=['A', 'B', 'C'], required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--model-path')
    parser.add_argument('--adapter', help='Required for C only; fixed training run adapter directory')
    parser.add_argument('--out')
    args = parser.parse_args()
    verify_freeze()
    tasks = plan(args.condition)
    if not args.execute:
        print(json.dumps({'condition': args.condition, 'tasks': tasks}, indent=2))
        return
    if not args.model_path or not args.out or (args.condition == 'C') != bool(args.adapter):
        parser.error('Execution needs --model-path, --out, and --adapter for C only')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    enforce_versions()
    model_path = local_snapshot(args.model_path)
    cfg = config()
    binding = None
    if args.adapter:
        adapter = Path(args.adapter).resolve()
        binding = read_json(adapter.parent / 'training_binding.json')
        if (binding['model_revision'] != cfg['model_revision'] or binding['model_id'] != cfg['model_id']
                or binding['freeze_sha256'] != sha(ROOT / 'freeze.json')):
            raise ValueError('Adapter training provenance does not match frozen study')
        for name, digest in binding['adapter_files'].items():
            if sha(adapter / name) != digest:
                raise ValueError('Adapter artifact changed')
    out = private_run(args.out)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, set_seed
    set_seed(cfg['seed'])
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported() or torch.cuda.device_count() != 1:
        raise RuntimeError('Expose exactly one BF16-capable CUDA GPU')
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True, trust_remote_code=False,
                      torch_dtype=torch.bfloat16, attn_implementation='sdpa').to('cuda')
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False, local_files_only=True)
    model.eval()
    generation = GenerationConfig(**cfg['generation'], eos_token_id=tokenizer.eos_token_id,
                                  pad_token_id=tokenizer.pad_token_id, bos_token_id=tokenizer.bos_token_id)
    manifest = dict(condition=args.condition, config=cfg, runtime=runtime_metadata(), model_path=model_path,
        adapter_binding=binding, freeze_sha256=sha(ROOT / 'freeze.json'), planned_calls=40,
        tokenizer_chat_template_sha256=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
        generation_config=generation.to_dict(), gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda,
        attempted=0, completed=0, status='started',
        start_time_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    loop_start = time.perf_counter()
    def generate(task):
        # Fresh system/user only; no cross-call state or reused knowledge answer.
        rendered = tokenizer.apply_chat_template(task['messages'], tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(rendered, add_special_tokens=False, return_tensors='pt').to('cuda')
        if inputs['input_ids'].shape[-1] > cfg['max_input_tokens']:
            raise ValueError('Input exceeds frozen bound; do not truncate')
        torch.cuda.synchronize()
        start = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(**inputs, generation_config=generation)
        torch.cuda.synchronize()
        elapsed = time.perf_counter()-start
        tokens = output[0, inputs['input_ids'].shape[-1]:].tolist()
        truncated = not tokens or tokens[-1] != tokenizer.eos_token_id
        return dict(response=tokenizer.decode(tokens, skip_special_tokens=True),
                    prompt_tokens=inputs['input_ids'].shape[-1], completion_tokens=len(tokens),
                    elapsed_seconds=elapsed, truncated=truncated,
                    status='truncated' if truncated else 'complete',
                    prompt_sha256=hashlib.sha256(rendered.encode()).hexdigest())
    try:
        collect(tasks, generate, out, manifest)
    finally:
        manifest.update(loop_elapsed_seconds=time.perf_counter()-loop_start,
                        peak_allocated_bytes=torch.cuda.max_memory_allocated())
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))



if __name__ == '__main__':
    main()
