"""Complete crossed explicit-state gate; one frozen interface repair per model.

DESIGN CHECK: LESSONS 3–5. NULL: factual copying alone cannot pass the four-way
action gate; ALTERNATIVE: competent rule execution passes >=.70 / >=.80.
Every combination of goal, belief, skill, preference and tools is checked.
The initial 360M timing pilot is retained, not promoted from its easier slice.
Test cases are unopened. Both original and failed repair records remain.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import time
import traceback
from .common import RAW, atomic, digest, freeze, gpu_service, now, read, source_pins
from .world import make_unit, prompt

def interface(unit,q,pair,question,version):
    text=prompt(unit,q,'no_history',explicit=pair,question=question)
    if version==0:return text
    # Single predeclared interface repair: train-only worked examples and answer cue.
    examples=[]
    from .world import reference
    for i in range(4):
        u,t=make_unit('train',i+8)
        state=t['queries'][i]; pk=(state['preference'],state['skill'])
        ex=prompt(u,i,'no_history',explicit=pk,question=question)
        answer=max(range(4),key=state['probabilities'].__getitem__) if question=='action' else state[question]
        examples.append(ex+'\nAnswer: '+'ABCD'[answer])
    return '\n\n'.join(examples)+'\n\n'+text+'\nAnswer:'

def run(root=RAW,model_index=1):
    from .hf import Reader,MODELS
    from soundingline.gpulock import acquire_gpu_lock,release_gpu_lock
    from runners.stage9.process_identity import native_identity
    import numpy as np
    import torch
    root=Path(root); out=root/f'admission-{model_index}'
    if (out/'COMPLETE.json').exists():return verify(out)
    freeze(out/'SOURCE.json',source_pins()); freeze(out/'NATIVE.json',native_identity())
    public=read(root/'fixture/dev-public.json'); truth=read(root/'fixture/dev-evaluator.json')
    acquire_gpu_lock('Stage11.2 capability admission');reader=None
    try:
        with gpu_service(root,f'admission-{model_index}',reservation=1200):
            reader=Reader(MODELS[model_index],stop_at=time.monotonic()+1170,precision='bfloat16')
            versions=[]
            for version in (0,1):
                rows=[]
                for i,unit in enumerate(public):
                    # Each policy occurs at each encounter; q must not alias i % 4.
                    q=(i//4)%4; state=truth[i]['queries'][q]
                    pair=(state['preference'],state['skill'])
                    for question in ['action','belief','goal']:
                        text=interface(unit,q,pair,question,version)
                        prediction,_=reader.score(text,n=4 if question=='action' else 2,capture=False)
                        target=max(range(4),key=state['probabilities'].__getitem__) if question=='action' else state[question]
                        rows.append(dict(unit=unit['unit'],encounter=q,question=question,target=target,**prediction))
                        freeze(out/f'v{version}'/'calls'/f'{len(rows):04d}.json',rows[-1])
                accuracy=lambda rr:sum(max(range(len(r['probabilities'])),key=r['probabilities'].__getitem__)==r['target'] for r in rr)/len(rr)
                action=accuracy([r for r in rows if r['question']=='action'])
                factual=accuracy([r for r in rows if r['question']!='action'])
                text=interface(public[0],0,(0,0),'action',version)
                baseline,_,_=reader.forward(text); repeat,_,_=reader.forward(text)
                tolerance=max(1e-6,2*float((baseline-repeat).abs().max()))
                errors=[];clean=[]
                for layer in reader.layers:
                    n=len(reader.blocks[layer]._forward_hooks)
                    with reader.patch(layer,delta=torch.zeros(reader.model.config.hidden_size,device='cuda')):
                        z,_,_=reader.forward(text)
                    errors.append(float((baseline-z).abs().max()));clean.append(n==len(reader.blocks[layer]._forward_hooks))
                ok=action>=.70 and factual>=.80 and max(errors)<=tolerance and all(clean)
                record=dict(version=version,action_accuracy=action,state_accuracy=factual,admitted=ok,
                    zero_errors=errors,tolerance=tolerance,cleanup=clean,rows_sha256=digest(rows),
                    p50_seconds=float(np.median([r['seconds'] for r in rows])),p90_seconds=float(np.quantile([r['seconds'] for r in rows],.9)))
                freeze(out/f'v{version}'/'ROWS.json',rows);freeze(out/f'v{version}'/'RESULT.json',record)
                versions.append(record)
                if ok:break
            return freeze(out/'COMPLETE.json',dict(status='complete',model=reader.bound,admitted=versions[-1]['admitted'],
                interface_version=versions[-1]['version'],versions=versions,finished=now(),
                repair='four training examples and answer cue; thresholds and test population unchanged'))
    except BaseException as exc:
        freeze(out/'FAILED.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()));raise
    finally:
        if reader is not None:reader.close()
        release_gpu_lock()

def verify(out):
    import math
    receipt=read(out/'COMPLETE.json')
    for v in receipt['versions']:
        rows=read(out/f'v{v["version"]}'/'ROWS.json')
        if digest(rows)!=v['rows_sha256']:raise ValueError('admission raw binding changed')
        for r in rows:
            x=r['letter_logprobs']; m=max(x); p=[math.exp(a-m)/sum(math.exp(b-m) for b in x) for a in x]
            if max(abs(a-b) for a,b in zip(p,r['probabilities']))>2e-6:raise ValueError('raw probability replay failed')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--model-index',type=int,default=1)
    a=p.parse_args();r=run(a.root,a.model_index);print({'status':r['status'],'admitted':r['admitted']})
