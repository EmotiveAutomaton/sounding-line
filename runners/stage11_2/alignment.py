"""Within-checkpoint low-rank distributed interchange, with frozen base weights.

DESIGN CHECK: LESSONS 3–5; DAS methods and pyvene reference inspected. NULL:
invertible coordinate changes alone preserve predictions; random and shuffled
alignments can match spurious steering. ALTERNATIVE: a trained subspace transfers
the intended counterfactual beyond norm-matched controls with <=5-point ordinary
capability loss. Failed capability forbids mechanistic interpretation.
"""
from __future__ import annotations
import argparse
import copy
from pathlib import Path
import random
import time
import traceback
from .common import RAW,digest,filehash,freeze,gpu_service,now,read,source_pins
from .world import POLICIES,decode,distribution,enumerate_predict,prompt

def interchange(base,donor,basis,alpha=1.0):
    """Columns orthonormal: equivalent to rotate, replace selected coords, invert."""
    q=basis.to(device=base.device,dtype=base.dtype)
    return base+alpha*((donor.to(base)-base)@q)@q.T

def counterfactual(unit,q,variable):
    changed=copy.deepcopy(unit);obs=changed['queries'][q]['observation']
    key='last_notice_seen_by_maker' if variable=='belief' else 'requested_item'
    choices=['red above blue','blue above red'] if variable=='belief' else ['red','blue']
    obs[key]=choices[1-choices.index(obs[key])]
    return changed

def public_prompt(unit,q,question='action'):
    state=enumerate_predict(unit['history'],unit['queries'][q]['observation'])
    pair=POLICIES[max(range(4),key=state['weights'].__getitem__)]
    return prompt(unit,q,'no_history',explicit=pair,question=question)

def capture(reader,public,out):
    import torch
    rows=[]
    for i,u in enumerate(public):
        q=(i//4)%4
        base=public_prompt(u,q); donor=public_prompt(counterfactual(u,q,'belief'),q)
        original,h,identity=reader.score(base,capture=True)
        changed,d,_=reader.score(donor,capture=True)
        rows.append(dict(unit=u['unit'],cluster=u['cluster'],q=q,base=base,donor=donor,
            h=h,d=d,original=original,changed=changed,identity=identity))
    # Activation cache binds every exact tokenized input, revision/layer/dtype.
    torch.save(rows,out)
    return rows

def linear_probe(train,labels,layer):
    import torch
    x=torch.cat([r['h'][layer] for r in train]);mean=x.mean(0);x=x-mean
    y=torch.tensor(labels,dtype=torch.float32)*2-1
    w=x.T@torch.linalg.solve(x@x.T+torch.eye(len(x)),y)
    return mean,w

def fit_basis(reader,train,targets,layer,rank,shuffle=False):
    import torch
    torch.manual_seed(112+rank+int(shuffle))
    width=train[0]['h'][layer].shape[-1]
    parameter=torch.nn.Parameter(torch.randn(width,rank,device='cuda')*.02)
    opt=torch.optim.Adam([parameter],lr=.01)
    labels=list(targets)
    if shuffle:random.Random(112).shuffle(labels)
    losses=[]
    for epoch in range(4):
        for i,row in enumerate(train):
            reader.check_time();opt.zero_grad()
            q,_=torch.linalg.qr(parameter,mode='reduced')
            donor=row['d'][layer].to('cuda')
            with reader.patch(layer,transform=lambda h:interchange(h,donor,q.to(h))):
                logits,_,_=reader.forward(row['base'],grad=True)
            loss=torch.nn.functional.cross_entropy(logits[reader.ids][None,:],torch.tensor([labels[i]],device=logits.device))
            loss.backward();opt.step();losses.append(float(loss.detach()))
    return torch.linalg.qr(parameter.detach(),mode='reduced')[0].cpu(),losses

def run(root=RAW,model_index=1,rank=8):
    import torch
    from .hf import Reader,MODELS
    from soundingline.gpulock import acquire_gpu_lock,release_gpu_lock
    root=Path(root);out=root/f'M2-{model_index}-rank{rank}'
    if (out/'COMPLETE.json').exists():return read(out/'COMPLETE.json')
    gate=read(root/f'admission-{model_index}/COMPLETE.json')
    if not gate['admitted']:
        return freeze(out/'BLOCKED.json',dict(status='blocked',reason='explicit-state capability failed',gate_sha256=digest(gate)))
    if rank not in (8,32):raise ValueError('rank not predeclared')
    freeze(out/'SOURCE.json',source_pins())
    # The un-repaired inference interface must match the actual admitted one.
    if gate['interface_version']!=0:
        return freeze(out/'BLOCKED.json',dict(status='blocked',reason='admitted example interface needs matched activation adapter; not silently transferred'))
    acquire_gpu_lock('Stage11.2 causal alignment');reader=None
    try:
        with gpu_service(root,f'M2-{model_index}-rank{rank}',10800):
            reader=Reader(MODELS[model_index],stop_at=time.monotonic()+10770,precision='bfloat16')
            train_public=read(root/'fixture/train-public.json');dev_public=read(root/'fixture/dev-public.json')
            train=capture(reader,train_public,out/'train.pt');dev=capture(reader,dev_public,out/'dev.pt')
            train_truth=read(root/'fixture/train-evaluator.json');dev_truth=read(root/'fixture/dev-evaluator.json')
            targets=[];belief_labels=[]
            for row,t in zip(train,train_truth):
                state=t['queries'][row['q']];p,k=state['preference'],state['skill']
                obs=counterfactual(train_public[len(targets)],row['q'],'belief')['queries'][row['q']]['observation']
                g,b=decode(obs);probs=distribution(p,k,g,b,obs['world_family'],obs['tools'])
                targets.append(max(range(4),key=probs.__getitem__));belief_labels.append(state['belief'])
            probe={layer:linear_probe(train,belief_labels,layer) for layer in reader.layers}
            layer_scores={}
            for layer,(mean,w) in probe.items():
                layer_scores[layer]=sum(int(((r['h'][layer][0]-mean)@w)>0)==t['queries'][r['q']]['belief'] for r,t in zip(dev,dev_truth))/len(dev)
            layer=max(reader.layers,key=lambda l:(layer_scores[l],-l))
            learned,loss=fit_basis(reader,train,targets,layer,rank)
            shuffled,shuffle_loss=fit_basis(reader,train,targets,layer,rank,shuffle=True)
            torch.manual_seed(112+rank)
            random_basis=torch.linalg.qr(torch.randn_like(learned),mode='reduced')[0]
            mean_direction=torch.stack([r['d'][layer][0]-r['h'][layer][0] for r in train]).mean(0)
            # Signed pair differences can cancel: use fitted state direction as the
            # declared mean-difference control instead, computed by class.
            h=torch.cat([r['h'][layer] for r in train]);labels=torch.tensor(belief_labels)
            mean_direction=h[labels==1].mean(0)-h[labels==0].mean(0)
            mean_basis=(mean_direction/mean_direction.norm().clamp_min(1e-12))[:,None]
            bases=dict(learned=learned,random=random_basis,shuffled=shuffled,mean=mean_basis)
            torch.save(dict(bases=bases,probe=probe,layer=layer,train_loss=loss,shuffle_loss=shuffle_loss),out/'FIT.pt')
            # Select the dose using only untouched dev ordinary-goal preservation.
            dose_rows=[]
            for dose in (.25,.5,1.0):
                base_correct=patched_correct=0
                for u,row,t in zip(dev_public,dev,dev_truth):
                    text=public_prompt(u,row['q'],'goal');base,_=reader.score(text,n=2)
                    delta=((row['d'][layer]-row['h'][layer])@learned)@learned.T*dose
                    with reader.patch(layer,delta=delta):patched,_=reader.score(text,n=2)
                    target=t['queries'][row['q']]['goal']
                    base_correct+=max(range(2),key=base['probabilities'].__getitem__)==target
                    patched_correct+=max(range(2),key=patched['probabilities'].__getitem__)==target
                    dose_rows.append(dict(unit=u['unit'],dose=dose,target=target,base=base,patched=patched))
                if (base_correct-patched_correct)/len(dev)<=.05:selected=dose
            freeze(out/'DOSES.json',dose_rows)
            if 'selected' not in locals():
                return freeze(out/'COMPLETE.json',dict(status='complete',admitted=False,reason='all doses fail ordinary capability',layer=layer,rank=rank))
            freeze(out/'SELECTION.json',dict(layer=layer,dose=selected,rank=rank,layer_scores=layer_scores,
                fit_sha256=filehash(out/'FIT.pt'),train_cache_sha256=filehash(out/'train.pt'),dev_cache_sha256=filehash(out/'dev.pt')))
            # All choices frozen before test data or evaluator is read.
            public=read(root/'fixture/test-public.json');test=capture(reader,public,out/'test.pt');rows=[]
            for unit,row in zip(public,test):
                h=row['h'][layer];d=row['d'][layer]
                intended=((d-h)@learned)@learned.T*selected
                other,_=reader.score(public_prompt(counterfactual(unit,row['q'],'goal'),row['q']),capture=True)
                _,wrong_states,_=reader.forward(public_prompt(counterfactual(unit,row['q'],'goal'),row['q']),capture=True)
                wrong=wrong_states[layer]-h
                deltas={'unmodified':torch.zeros_like(h),'wrong_variable':wrong}
                for name,basis in bases.items():deltas[name]=((d-h)@basis)@basis.T*selected
                for name,delta in deltas.items():
                    if name in ('wrong_variable','random','shuffled','mean'):
                        delta=delta*intended.norm()/delta.norm().clamp_min(1e-12)
                    with reader.patch(layer,delta=delta):pred,_=reader.score(row['base'])
                    rows.append(dict(unit=row['unit'],cluster=row['cluster'],q=row['q'],arm=name,
                        patch_norm=float(delta.norm()),projection_coordinates=(h@learned).tolist(),prediction=pred))
            freeze(out/'PREDICTIONS.json',rows)
            return freeze(out/'COMPLETE.json',dict(status='complete',admitted=True,rows=len(rows),
                predictions_sha256=digest(rows),selection_sha256=digest(read(out/'SELECTION.json')),
                scope='privileged controlled donor construction; public-history state estimate; not artifact-only intervention benefit'))
    except BaseException as exc:
        freeze(out/'FAILED.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()));raise
    finally:
        if reader is not None:reader.close()
        release_gpu_lock()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--model-index',type=int,default=1);p.add_argument('--rank',type=int,default=8)
    a=p.parse_args();print(run(a.root,a.model_index,a.rank)['status'])
