"""Exact Transformers 4.56.2 configuration-only regression. No weights or inference."""
import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
import sys
from types import MethodType, SimpleNamespace
from common import ROOT, config, private_run, read_json, sha, verify_freeze


def check():
    verify_freeze()
    actual=importlib.metadata.version('transformers')
    if actual!='4.56.2':
        raise RuntimeError('Requires installed Transformers 4.56.2; no substitute version')
    from transformers import GenerationConfig
    from transformers.generation.utils import GenerationMixin
    from evaluate import prepare_greedy_generation
    defaults=read_json(ROOT/'QWEN_GENERATION_DEFAULTS.json')
    model=SimpleNamespace(generation_config=GenerationConfig(**defaults))
    # Bind the actual installed library method to a config-only object, not a model.
    model._prepare_generation_config=MethodType(GenerationMixin._prepare_generation_config,model)
    cfg=config()
    def requested():
        return GenerationConfig(**cfg['generation'],eos_token_id=151645,pad_token_id=151643,bos_token_id=None)
    original=requested()
    old,unused=model._prepare_generation_config(original,use_model_defaults=None)
    assert not unused
    assert old.do_sample is True and old.get_generation_mode().value=='sample'
    assert (old.temperature,old.top_k,old.top_p)==(.7,20,.8)
    assert original.do_sample is False  # The saved v2 object does not show the runtime copy's override.
    for effective in (old,):
        assert (effective.eos_token_id,effective.pad_token_id,effective.num_beams,effective.max_new_tokens)==(151645,151643,1,512)
    prepared={arm:prepare_greedy_generation(model,requested(),cfg) for arm in 'ABC'}
    # Resolve a second time exactly as generate(use_model_defaults=False) will do.
    for arm,effective in prepared.items():
        again,unused=model._prepare_generation_config(effective,use_model_defaults=False)
        assert not unused and again.to_dict()==effective.to_dict()
        assert again.do_sample is False and again.get_generation_mode().value=='greedy_search'
        assert (again.eos_token_id,again.pad_token_id,again.num_beams,again.max_new_tokens)==(151645,151643,1,512)
        assert again.repetition_penalty==1.0 and again.use_cache is True
    assert prepared['A'].to_dict()==prepared['B'].to_dict()==prepared['C'].to_dict()
    return dict(status='passed',transformers_version=actual,freeze_sha256=sha(ROOT/'freeze.json'),
                evaluation_sha256=sha(ROOT/'evaluate.py'),regression_sha256=sha(ROOT/'generation_regression.py'),
                qwen_defaults_sha256=sha(ROOT/'QWEN_GENERATION_DEFAULTS.json'),
                installed_resolution_method_sha256=hashlib.sha256(inspect.getsource(GenerationMixin._prepare_generation_config).encode()).hexdigest(),
                v2_effective_mode='sample',v3_effective_mode='greedy_search',
                v3_effective_config=prepared['A'].to_dict(),identical_ABC=True,
                model_weights_loaded=False,forward_calls=0,generation_calls=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',help='Optional fresh private research/runs/ directory for passing evidence')
    args=parser.parse_args()
    def guard(event,args):
        if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto','subprocess.Popen','os.system'}:
            raise RuntimeError('Forbidden network/process operation in configuration-only regression')
    sys.addaudithook(guard)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_IMPLICIT_TOKEN='1')
    try:
        result=check()
    except (importlib.metadata.PackageNotFoundError,ImportError,RuntimeError) as exc:
        print(json.dumps(dict(status='unverified',reason=type(exc).__name__,required='Installed Transformers 4.56.2; never installs or downloads')))
        return 2
    if args.out:
        out=private_run(args.out)
        (out/'report.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
