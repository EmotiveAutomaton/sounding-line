"""Discarded activation timing and explicit-state capability admission.

DESIGN CHECK: LESSONS 3–5; CONTROLS 6. NULL: neutral zero-dose intervention and
repeated forward logits agree, hooks clean up. ALTERNATIVE: competent reader
exceeds the brief's action/state floors. Failed gates forbid mechanistic verdicts.
One predeclared adapter repair permits a shorter equivalent task rendering, no
test outcomes or thresholds altered. Here the original interface only is run.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import time
import traceback
from .common import RAW, contract, digest, freeze, gpu_service, now, read, source_pins
from .world import POLICIES, prepare, prompt

def run(root=RAW, model_index=0):
    import torch
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock
    from runners.stage9.process_identity import native_identity
    from .hf import Reader, MODELS
    root=Path(root); out=root/f'pilot-{model_index}-v1'
    if (out/'COMPLETE.json').exists():
        receipt=read(out/'COMPLETE.json')
        if digest(read(out/'ROWS.json'))!=receipt['rows_sha256']:raise ValueError('pilot rows changed')
        return receipt
    contract(root); prepare(root/'fixture')
    freeze(out/'SOURCE.json',source_pins())
    freeze(out/'NATIVE.json',native_identity())
    public=read(root/'fixture/dev-public.json')
    truth=read(root/'fixture/dev-evaluator.json')
    acquire_gpu_lock('Stage11.2 discarded capability pilot')
    reader=None
    try:
        with gpu_service(root,f'pilot-{model_index}',reservation=1200):
            reader=Reader(MODELS[model_index],stop_at=time.monotonic()+1170)
            rows=[]; times=[]
            # First 32 literal requests include captures for activation/forward timing.
            for i,unit in enumerate(public):
                state=truth[i]['queries'][0]; pair=(state['preference'],state['skill'])
                for question in ['action','belief','goal']:
                    text=prompt(unit,0,arm='no_history',explicit=pair,question=question)
                    r,states=reader.score(text,n=4 if question=='action' else 2,capture=len(rows)<32)
                    times.append(r['seconds'])
                    target=max(range(4),key=state['probabilities'].__getitem__) if question=='action' else state[question]
                    row=dict(unit=unit['unit'],question=question,target=target,**r)
                    rows.append(row)
                    freeze(out/'calls'/f'{len(rows):04d}.json',row)
                    if states:
                        torch.save(dict(states=states,identity=r['identity']),out/'calls'/f'{len(rows):04d}-states.pt')
            text=prompt(public[0],0,'no_history',explicit=POLICIES[0])
            baseline,_,_=reader.forward(text)
            repeat,_,_=reader.forward(text)
            zero_errors=[]; cleanup=[]
            for layer in reader.layers:
                before=len(reader.blocks[layer]._forward_hooks)
                with reader.patch(layer,delta=torch.zeros(reader.model.config.hidden_size,device='cuda')):
                    patched,_,_=reader.forward(text)
                zero_errors.append(float((baseline-patched).abs().max()))
                cleanup.append(len(reader.blocks[layer]._forward_hooks)==before)
                try:
                    with reader.patch(layer,delta=None):raise RuntimeError('deliberate cleanup fixture')
                except RuntimeError:pass
                cleanup.append(len(reader.blocks[layer]._forward_hooks)==before)
            action=[r for r in rows if r['question']=='action']; factual=[r for r in rows if r['question']!='action']
            accuracy=lambda rr:sum(max(range(len(r['probabilities'])),key=r['probabilities'].__getitem__)==r['target'] for r in rr)/len(rr)
            aa,sa=accuracy(action),accuracy(factual)
            jitter=float((baseline-repeat).abs().max()); tolerance=max(1e-6,2*jitter)
            import numpy as np
            result=dict(status='complete',admitted=aa>=.70 and sa>=.80 and max(zero_errors)<=tolerance and all(cleanup),
                action_accuracy=aa,state_accuracy=sa,action_n=len(action),state_n=len(factual),
                zero_max_errors=zero_errors,numerical_tolerance=tolerance,repeat_jitter=jitter,cleanup=cleanup,
                model=reader.bound,first32_p50=float(np.median(times[:32])),first32_p90=float(np.quantile(times[:32],.9)),
                rows_sha256=digest(rows),finished=now(),scope='development capability/instrument; not test science')
            freeze(out/'ROWS.json',rows)
            freeze(out/'COMPLETE.json',result)
            return {k:result[k] for k in ['status','admitted','first32_p50','first32_p90']}
    except BaseException as exc:
        freeze(out/'FAILED.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()))
        raise
    finally:
        if reader is not None:reader.close()
        release_gpu_lock()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--model-index',type=int,default=0)
    a=p.parse_args();print(run(a.root,a.model_index))
