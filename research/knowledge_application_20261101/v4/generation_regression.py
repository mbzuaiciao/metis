"""Actual pinned config/processor regression with synthetic tensors only,no model inference."""
import argparse
import hashlib
import inspect
import json
import os
import sys
from types import SimpleNamespace,MethodType
from common import ROOT,sha,verify_freeze,private_run

def check():
    verify_freeze()
    import transformers,torch
    from transformers import GenerationConfig
    from transformers.generation.logits_process import NoRepeatNGramLogitsProcessor
    from transformers.generation.utils import GenerationMixin
    if transformers.__version__!='4.56.2':
        raise RuntimeError('Actual Transformers4.56.2 required;no substitute')
    p=NoRepeatNGramLogitsProcessor(20);passed=[]
    def check(name,ok):assert ok,name;passed.append(name)
    def apply(seq,scores=None):
     if scores is None:scores=torch.zeros((1,100),dtype=torch.float32)
     return p(torch.tensor([seq],dtype=torch.long),scores)
    seq=list(range(1,21));prefix=seq[:-1]
    check('before_20gram_no_ban',torch.isfinite(apply(prefix)).all().item())
    check('first_20gram_allowed',torch.isfinite(apply(prefix))[0,20].item())
    scores=torch.arange(100,dtype=torch.float32).unsqueeze(0);result=apply(seq+prefix,scores)
    check('repeated_20gram_completion_banned',torch.isneginf(result[0,20]).item())
    check('only_matching_continuation_changed',torch.equal(result[0,:20],scores[0,:20]) and torch.equal(result[0,21:],scores[0,21:]) and torch.equal(scores,torch.arange(100,dtype=torch.float32).unsqueeze(0)))
    check('shorter_repetition_can_remain',torch.isfinite(apply(prefix+prefix[:-1]))[0,19].item())
    # Tokens1..20 can represent a legitimate verbatim phrase in a prompt;no semantic exemption.
    check('prompt_copy_and_legitimate_phrase_also_blocked',torch.isneginf(apply(seq+[80]+prefix))[0,20].item())
    batch=p(torch.tensor([seq+prefix,list(range(40,79))]),torch.zeros(2,100));check('independent_batch_histories',torch.isneginf(batch[0,20]).item() and torch.isfinite(batch[1,20]).item())
    scores=torch.full((1,100),-10.0);scores[0,20]=10;scores[0,21]=9;scores[0,99]=0
    result=apply(seq+prefix,scores);check('does_not_force_EOS',int(result.argmax(-1).item())==21 and torch.isfinite(result[0,99]).item())
    check('EOS_has_no_special_exemption',torch.isneginf(apply(prefix+[99,80]+prefix))[0,99].item())
    # Exercise real config resolution and real processor construction,no model object/forward/generate.
    defaults=json.loads((ROOT/'QWEN_GENERATION_DEFAULTS.json').read_text());cfg=json.loads((ROOT/'config.json').read_text())
    stub=SimpleNamespace(generation_config=GenerationConfig(**defaults),device=torch.device('cpu'))
    stub._merge_criteria_processor_list=MethodType(GenerationMixin._merge_criteria_processor_list,stub)
    requested=GenerationConfig(**cfg['generation'],eos_token_id=151645,pad_token_id=151643)
    effective,unused=GenerationMixin._prepare_generation_config(stub,requested,use_model_defaults=False)
    check('actual_resolution_preserves_frozen_greedy_and_constraint',not unused and effective.do_sample is False and effective.num_beams==1 and effective.no_repeat_ngram_size==20 and effective.max_new_tokens==512 and effective.eos_token_id==151645 and effective.pad_token_id==151643)
    processors=GenerationMixin._get_logits_processor(stub,effective,input_ids_seq_length=5,device='cpu')
    check('actual_greedy_processor_list_installs_constraint',len(processors)==1 and isinstance(processors[0],NoRepeatNGramLogitsProcessor) and processors[0].ngram_size==20)
    effective.no_repeat_ngram_size=0
    check('frozen_zero_setting_has_no_ngram_processor',len(GenerationMixin._get_logits_processor(stub,effective,input_ids_seq_length=5,device='cpu'))==0)

    stub._prepare_generation_config=MethodType(GenerationMixin._prepare_generation_config,stub)
    from evaluate import prepare_greedy_generation
    prepared={}
    for arm in 'ABC':
        req=GenerationConfig(**cfg['generation'],eos_token_id=151645,pad_token_id=151643)
        prepared[arm]=prepare_greedy_generation(stub,req,cfg)
        again,unused=GenerationMixin._prepare_generation_config(stub,prepared[arm],use_model_defaults=False)
        assert not unused and again.to_dict()==prepared[arm].to_dict()
    check('identical_ABC_idempotent_prepared_config',prepared['A'].to_dict()==prepared['B'].to_dict()==prepared['C'].to_dict())
    original_cfg=dict(cfg['generation']);original_cfg.pop('no_repeat_ngram_size')
    original,_=GenerationMixin._prepare_generation_config(stub,GenerationConfig(**original_cfg,eos_token_id=151645,pad_token_id=151643),use_model_defaults=False)
    expected_original=prepared['A'].to_dict();expected_original['no_repeat_ngram_size']=0
    check('only_effective_policy_difference_is_ngram20',original.to_dict()==expected_original)
    return dict(status='passed',transformers_version=transformers.__version__,torch_version=torch.__version__,
        freeze_sha256=sha(ROOT/'freeze.json'),evaluation_sha256=sha(ROOT/'evaluate.py'),
        regression_sha256=sha(ROOT/'generation_regression.py'),qwen_defaults_sha256=sha(ROOT/'QWEN_GENERATION_DEFAULTS.json'),
        processor_source_sha256=hashlib.sha256(inspect.getsource(NoRepeatNGramLogitsProcessor).encode()).hexdigest(),
        checks=passed,checks_passed=len(passed),identical_ABC=True,v4_effective_mode='greedy_search',
        v4_effective_config=prepared['A'].to_dict(),model_weights_loaded=False,forward_calls=0,generation_calls=0)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    def guard(event,args):
        if event in {'socket.connect','socket.getaddrinfo','subprocess.Popen','os.system'}:
            raise RuntimeError('Forbidden runtime access')
    sys.addaudithook(guard)
    result=check()
    out=private_run(args.out)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],checks_passed=result['checks_passed'],freeze_sha256=result['freeze_sha256'])))

if __name__=='__main__':main()
