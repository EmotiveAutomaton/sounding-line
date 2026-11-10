"""Native float64 scoring, independent arithmetic and resource-yield controls."""
from pathlib import Path
import math
from . import week5_at_scoring_v4 as scorer
from .timing_census import read
from .timing_p6 import write_equal


def loader(manifest):
    import torch
    from transformers import (GPT2Config,GPT2LMHeadModel,GPTNeoXConfig,GPTNeoXForCausalLM,
                              LlamaConfig,LlamaForCausalLM,Qwen2Config,Qwen2ForCausalLM)
    class Tokenizer:
        eos_token_id=0;bos_token_id=0
        def __call__(self,text,**kwargs):
            return dict(input_ids=[ord(c)%31+1 for c in text],offset_mapping=[(i,i+1) for i in range(len(text))])
    torch.set_num_threads(2);torch.manual_seed(4)
    common=dict(vocab_size=33,hidden_size=16,intermediate_size=32,num_hidden_layers=1,num_attention_heads=2,
                max_position_embeddings=64,bos_token_id=0,eos_token_id=0)
    models={'gpt2':lambda:GPT2LMHeadModel(GPT2Config(vocab_size=33,n_positions=64,n_embd=16,n_layer=1,n_head=2,bos_token_id=0,eos_token_id=0)),
            'neox':lambda:GPTNeoXForCausalLM(GPTNeoXConfig(**dict(common,rotary_pct=.5))),
            'llama':lambda:LlamaForCausalLM(LlamaConfig(**dict(common,num_key_value_heads=2))),
            'qwen2':lambda:Qwen2ForCausalLM(Qwen2Config(**dict(common,num_key_value_heads=2)))}
    return models[manifest['family']]().eval().double(),Tokenizer(),torch


def independent(model,tok,torch,row,saved):
    text=row['final_prefix']+row['target'];encoded=tok(text);raw=[0]+encoded['input_ids'];dropped=max(0,len(raw)-64);ids=raw[dropped:]
    positions=[i+1-dropped for i,(a,b) in enumerate(encoded['offset_mapping']) if b>len(row['final_prefix']) and a<len(text)]
    tensor=torch.tensor([ids],dtype=torch.long)
    with torch.inference_mode():
        logits=model(input_ids=tensor,use_cache=False).logits[0].float()
        losses=[];entropy=None
        for pos in positions:
            logit=logits[pos-1].double();lognormal=torch.logsumexp(logit,dim=0)
            losses.append(float(lognormal-logit[ids[pos]]))
            if entropy is None:
                logp=logit-lognormal;entropy=float(-(logp.exp()*logp).sum())
    error=max(abs(a-b) for a,b in zip(losses+[entropy],saved['native_token_nll']+[saved['entropy_nats']]))
    if error>1e-4 or saved['native_token_ids']!=[ids[i] for i in positions] or saved['prefix_tokens_dropped']!=dropped:
        raise ValueError('Independent full-forward arithmetic differs')
    return error


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture has no human inputs')
    root=Path(output);rows=[dict(row_key=str(i),final_prefix='a '*i,target=' b') for i in range(18)]
    rows.extend(dict(row_key=str(i+18),final_prefix=p,target=t) for i,(p,t) in enumerate([('a ','xy'),('a q ','z'),('a '*45,' xyz'),('b '*43,'q'),('','hello'),('abc','!')]))
    old_loader=scorer.load_model;old_progress=scorer.progress;scorer.load_model=loader;all_errors=[]
    try:
        for family in ('gpt2','neox','llama','qwen2'):
            out=root/family;manifest=dict(model='constructed-'+family,family=family,revision='fixture')
            marker=out/'YIELD_REQUEST.json'
            def progress(path,value):
                old_progress(path,value)
                if value['words']==8:write_equal(marker,dict(reason='constructed resource interrupt'))
            if not verifying:
                scorer.progress=progress
                value=scorer.score_batch(out,rows,manifest,context_length=64)
                if value.get('status')!='yielded' or value['completed']!=8:raise ValueError('Sealed block yield missing')
                marker.unlink();scorer.progress=old_progress
            value=scorer.score_batch(out,rows,manifest,context_length=64,verifying=verifying)
            if verifying and not value.get('verified'):raise ValueError('Independent handler replay missing')
            model,tok,torch=loader(manifest)
            for i,row in enumerate(rows):
                saved=read(out/f'block-{i//8:05d}.json')['values'][i%8]['score']
                all_errors.append(independent(model,tok,torch,row,saved))
            if read(out/'SUMMARY.json')['numerical_spec']!=scorer.NUMERICAL_SPEC:raise ValueError('Precision not bound')
    finally:scorer.load_model=old_loader;scorer.progress=old_progress
    receipt=dict(fixture_only=True,architectures=['GPT2','GPTNeoX','Llama','Qwen2'],all_rows_independent_arithmetic=True,
                 resource_yield_resumed=True,prefix_extension_shortening_divergence_rollover=True,numerical_spec=scorer.NUMERICAL_SPEC,
                 max_independent_arithmetic_error=max(all_errors))
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Numerical fixture changed')
        return dict(verified=True,all_architectures_and_cases_replayed=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
