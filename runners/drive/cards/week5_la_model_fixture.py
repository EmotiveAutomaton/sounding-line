"""Actual tiny masked-model forward and signed laughter statistic controls."""
from pathlib import Path
import numpy as np
from .week5_la import ResolutionScorer,conditional_fit,la2
from .timing_census import read
from .timing_p6 import write_equal


def fixture():
    import torch
    from transformers import RobertaConfig,RobertaForMaskedLM
    class Tokenizer:
        mask_token_id=3
        def __call__(self,text,**kwargs):return dict(input_ids=[ord(c)%30+4 for c in text])
        def build_inputs_with_special_tokens(self,ids):return [0]+ids+[2]
    torch.set_num_threads(2);torch.manual_seed(5)
    model=RobertaForMaskedLM(RobertaConfig(vocab_size=40,hidden_size=16,num_hidden_layers=1,num_attention_heads=2,
                                         intermediate_size=24,max_position_embeddings=66,pad_token_id=1,bos_token_id=0,eos_token_id=2)).eval()
    scorer=ResolutionScorer(model,Tokenizer(),torch,max_tokens=64,mask_batch=4)
    a=scorer.score('prior constructed words','current sentence')
    b=scorer.score('prior constructed words','current sentence')
    if a!=b:raise ValueError('Masked CPU scoring is not deterministic')
    for parameter in model.parameters():parameter.data.zero_()
    null=scorer.score('prior constructed words','current sentence')
    if null['resolution_nats_per_token']!=0:raise ValueError('Uniform masked reader must give exact zero resolution')
    cropped=scorer.score('x'*100,'y'*25)
    if cropped['old_tokens']!=36 or cropped['old_tokens_dropped']!=64:raise ValueError('Masked paired left crop differs')
    rng=np.random.default_rng(4);groups=[]
    for _ in range(120):
        x=rng.normal(size=(6,2));p=np.exp(x[:,0]);p/=p.sum();case=rng.choice(6,p=p)
        groups.append(np.vstack([x[case],np.delete(x,case,axis=0)]))
    positive=conditional_fit(groups)[0];negative=conditional_fit([x*np.array([-1,1]) for x in groups])[0]
    balanced=conditional_fit([np.roll(x,i,axis=0) for x in groups[:10] for i in range(6)])
    if positive<=.4 or negative>=-.4 or np.max(np.abs(balanced))>=1e-10:raise ValueError('Conditional signed/null fixture differs')
    pairs=[]
    for m in range(24):
        for j in range(8):
            same=j%2;ra,rb=rng.uniform(.01,.1,2)
            pairs.append(dict(meeting=str(m),same=same,rate_a=ra,rate_b=rb,joined=.2*same+.1*ra+.2*rb+rng.normal(scale=.02)))
    joining=la2(pairs,30)
    if joining['primary']['state']!='supports':raise ValueError('Joining signed world failed')
    return dict(fixture_only=True,actual_device=str(next(model.parameters()).device),actual_threads=torch.get_num_threads(),
                masked_determinism=True,uniform_resolution=null['resolution_nats_per_token'],
                paired_crop=True,conditional_positive=float(positive),conditional_negative=float(negative),
                conditional_exact_null=balanced.tolist(),joining_positive=True)


def execute(output,inputs,config):
    if inputs or config:raise ValueError('Fixture has no human source')
    write_equal(Path(output)/'FIXTURE.json',fixture());return dict(status='complete',fixture_only=True)
def verify(output,inputs,config):
    if read(Path(output)/'FIXTURE.json')!=fixture():raise ValueError('Laughter native fixture replay differs')
    return dict(verified=True,complete_masked_and_fit_replay=True)


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
