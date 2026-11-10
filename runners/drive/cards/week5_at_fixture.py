"""Human-free native AT scored-block and statistical signed-world fixtures."""
from pathlib import Path
import numpy as np
from . import week5_at_scoring_v2 as scorer
from .week5_at_scoring import ENGINE_MODELS
from .week5_at_analysis import at2,at3,at4
from .week5_at_history import estimate
from .timing_census import read
from .timing_p6 import write_equal


def rows():
    rng=np.random.default_rng(8);out=[]
    for w in range(15):
        for j in range(24):
            surprise,entropy=rng.normal(size=2);length=float(rng.integers(2,12));freq=float(rng.normal())
            y=.2*surprise+.3*entropy+.04*length+rng.normal(scale=.3)
            out.append(dict(writer=str(w),pause_seconds=float(np.exp(y)),fast=float(1/(1+np.exp(3*y))),
                length=length,log_frequency=freq,sentence_start=j%7==0,paragraph_start=j==0,
                position=j,population_surprisal=float(rng.normal()),scores={m:dict(surprisal_nats=float(surprise),
                entropy_nats=float(entropy)) for m in ENGINE_MODELS}))
    return out


def fixture_loader(manifest):
    import torch
    from transformers import GPT2Config,GPT2LMHeadModel
    class Tokenizer:
        eos_token_id=0;bos_token_id=0
        def __call__(self,text,**kwargs):
            return dict(input_ids=[ord(c)%31+1 for c in text],offset_mapping=[(i,i+1) for i in range(len(text))])
    torch.set_num_threads(2);torch.manual_seed(4)
    model=GPT2LMHeadModel(GPT2Config(vocab_size=33,n_positions=64,n_embd=16,n_layer=1,n_head=2,bos_token_id=0,eos_token_id=0)).eval()
    return model,Tokenizer(),torch


def statistics():
    data=rows();a=at2(data,list(ENGINE_MODELS),30);b=at3(data,ENGINE_MODELS[0],30);c=at4(data,ENGINE_MODELS[0],30)
    if a['secondary'][ENGINE_MODELS[0]]!=a['secondary'][ENGINE_MODELS[1]]:raise ValueError('Identical reader gains differ')
    if b['primary']['state']!='supports' or c['full_auc']<=c['baseline_auc']:raise ValueError('Planted timing signal not recovered')
    class ConstructedBank:
        writers=list(range(24))
        def __init__(self,signal):self.signal=signal
        def draw(self,writer,rng,*args):
            x=rng.normal(size=(80,8));values=[]
            for j in range(len(x)):
                values.append(dict(writer=str(writer),own_surprise=x[j,0],donor_surprise=x[j,1],
                    population_surprisal=x[j,2],length=x[j,3],log_frequency=x[j,4],sentence_start=x[j,5],
                    after_punctuation=x[j,6],on_screen=x[j,7],session_surprisal=x[j,2]+x[j,3],
                    log_pause=self.signal*x[j,0]+.1*x[j,1]+rng.normal(scale=.2)))
            return values,dict(redraws=0)
    signed=[]
    for effect in (.5,.1,-.3):
        bank=ConstructedBank(effect);value,_,error=estimate(bank,np.random.default_rng(1),bank.writers,5,'genre',True)
        if error:raise ValueError(error)
        signed.append(value)
    if not (signed[0]>.3 and abs(signed[1])<.02 and signed[2]<-.3):raise ValueError('AT1 personal/shared/reversal fixture failed')
    return dict(at2_identical_pair=True,at3_positive=True,at4_positive=True,at1_signed_contrasts=signed)


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Fixture has no outside inputs')
    root=Path(output);data=[dict(row_key=str(i),final_prefix='a '*i,target='b') for i in range(18)]
    original=scorer.load_model;scorer.load_model=fixture_loader
    try:
        result=scorer.score_batch(root/'scores',data,dict(model='constructed',revision='fixture'),context_length=64,verifying=verifying)
    finally:scorer.load_model=original
    tests=statistics()
    if verifying:
        if read(root/'FIXTURE.json')!=tests:raise ValueError('Statistical fixture replay differs')
        return dict(verified=True,actual_cpu_reader=True,scoring=result,complete_signed_world_replay=True)
    write_equal(root/'FIXTURE.json',tests);return dict(status='complete',fixture_only=True,scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
