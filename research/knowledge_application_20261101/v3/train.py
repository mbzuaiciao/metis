"""One fixed completion-only SFT run; requires separately authorized execution."""
import argparse
import json
import os
import time
from pathlib import Path
from common import (ROOT, config, enforce_versions, local_snapshot, messages, private_run,
                    rows, runtime_metadata, sha, verify_freeze, require_complete_baselines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Run training; not authorized by preparation')
    parser.add_argument('--model-path')
    parser.add_argument('--out')
    parser.add_argument('--baseline-runs', nargs=2, metavar=('A_RUN', 'B_RUN'))
    args = parser.parse_args()
    verify_freeze()
    cfg = config()
    if not args.execute:
        print(json.dumps({'mode': 'plan_only', 'examples': 60, 'config': cfg}, indent=2))
        return
    if not args.model_path or not args.out or not args.baseline_runs:
        parser.error('--execute requires --model-path, --out and --baseline-runs A_RUN B_RUN')
    baselines = require_complete_baselines(args.baseline_runs)
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', WANDB_DISABLED='true')
    enforce_versions()
    model_path = local_snapshot(args.model_path)
    if any(b['model_path'] != model_path for b in baselines):
        raise ValueError('Training must use the same snapshot as the complete baselines')
    out = private_run(args.out)
    # Optional packages are imported only after explicit execution and freeze checks.
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer
    set_seed(cfg['seed'])
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError('One BF16-capable CUDA GPU required; no automatic fallback')
    if torch.cuda.device_count() != 1:
        raise RuntimeError('Expose exactly one GPU with CUDA_VISIBLE_DEVICES')
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        raise ValueError('Expected Qwen pad token')
    template_sha = __import__('hashlib').sha256(tokenizer.chat_template.encode()).hexdigest()
    if any(b['template_sha256'] != template_sha for b in baselines):
        raise ValueError('Training tokenizer template differs from baselines')
    dataset = []
    token_total = 0
    for case in rows('train.jsonl'):
        prompt_messages = messages(case, 'A', 'application')
        prefix = tokenizer.apply_chat_template(prompt_messages, tokenize=False, add_generation_prompt=True)
        full = tokenizer.apply_chat_template(prompt_messages + [{'role': 'assistant', 'content': case['justified_answer']}],
                                             tokenize=False, add_generation_prompt=False).rstrip('\n')
        if not full.startswith(prefix):
            raise ValueError('Chat template is not prefix-compatible')
        prompt_ids = tokenizer(prefix, add_special_tokens=False)['input_ids']
        full_ids = tokenizer(full, add_special_tokens=False)['input_ids']
        if full_ids[:len(prompt_ids)] != prompt_ids:
            raise ValueError('Tokenizer boundary would corrupt completion mask')
        if len(full_ids) > cfg['max_train_tokens']:
            raise ValueError(f"Training example would truncate: {case['id']}")
        token_total += len(full_ids)
        dataset.append(dict(prompt=prefix, completion=full[len(prefix):]))
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True, trust_remote_code=False,
                                                torch_dtype=torch.bfloat16, attn_implementation='sdpa')
    model.config.use_cache = False
    t = cfg['training']
    trainer = SFTTrainer(
        model=model, processing_class=tokenizer, train_dataset=Dataset.from_list(dataset),
        peft_config=LoraConfig(**cfg['lora']),
        args=SFTConfig(output_dir=str(out / 'adapter'), num_train_epochs=t['epochs'],
            learning_rate=t['learning_rate'], per_device_train_batch_size=t['batch_size'],
            gradient_accumulation_steps=t['gradient_accumulation_steps'],
            warmup_steps=t['warmup_steps'], weight_decay=t['weight_decay'],
            lr_scheduler_type=t['lr_scheduler_type'], max_grad_norm=t['max_grad_norm'],
            seed=cfg['seed'], data_seed=cfg['data_seed'], bf16=True, fp16=False,
            gradient_checkpointing=True, gradient_checkpointing_kwargs={'use_reentrant': False},
            optim='adamw_torch', max_length=cfg['max_train_tokens'], packing=False,
            completion_only_loss=True, assistant_only_loss=False, eos_token=tokenizer.eos_token,
            save_strategy='no', eval_strategy='no', logging_steps=1, report_to='none', push_to_hub=False))
    # Inspect actual collated labels: prompt tokens must not contribute to the loss.
    for i, source in enumerate(dataset):
        item = trainer.train_dataset[i]
        prompt_len = len(tokenizer(source['prompt'], add_special_tokens=False)['input_ids'])
        batch = trainer.data_collator([item])
        labels = batch['labels'][0].tolist()
        if not all(x == -100 for x in labels[:prompt_len]) or not any(x != -100 for x in labels[prompt_len:]):
            raise ValueError('Completion-only label masking failed')
    manifest = dict(config=cfg, baseline_binding=baselines, runtime=runtime_metadata(), model_path=model_path,
        tokenizer_chat_template_sha256=__import__('hashlib').sha256(tokenizer.chat_template.encode()).hexdigest(),
        freeze_sha256=sha(ROOT / 'freeze.json'), training_examples=60,
        input_and_target_tokens_per_epoch=token_total, nominal_epochs=t['epochs'],
        gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda,
        trainable_parameters=sum(p.numel() for p in trainer.model.parameters() if p.requires_grad),
        start_time_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    start = time.perf_counter()
    try:
        result = trainer.train()
        trainer.save_model(str(out / 'adapter'))
        tokenizer.save_pretrained(out / 'adapter')
        # Bind evaluation to this base revision and frozen preparation, not just a PEFT path.
        binding = dict(model_id=cfg['model_id'], model_revision=cfg['model_revision'],
                       freeze_sha256=sha(ROOT / 'freeze.json'),
                       adapter_files={p.name: sha(p) for p in (out / 'adapter').iterdir() if p.is_file()})
        (out / 'training_binding.json').write_text(json.dumps(binding, indent=2))
        manifest['metrics'] = result.metrics
        manifest['status'] = 'complete'
    except Exception as exc:
        manifest.update(status='failed', failure_type=type(exc).__name__)
        raise
    finally:
        manifest.update(elapsed_seconds=time.perf_counter()-start,
                        peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                        peak_reserved_bytes=torch.cuda.max_memory_reserved())
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
