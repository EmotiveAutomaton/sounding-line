"""SM2/SM3 aligned handling baselines, completed cells only.

DESIGN CHECK: LESSONS 2-5. NULL: effort permutation retains the distribution
but breaks its alignment; a sharper wrong model loses proper score. ALTERNATIVE:
weighted own history improves paired writer loss beyond unweighted and shuffle.
Penalty selection uses past calibration only; wide intervals remain unresolved.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[_name]='1'
from collections import defaultdict
import math,time
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
from .data import RAW,ACTIONS,key
from runners.stage14.common import read,freeze,atomic,filehash

def features(r,prior,annotated):
    doc=set(r['document'][-1200:].lower().split());menus=r['menu']
    overlap=max((len(doc & set(s.lower().split()))/max(1,len(set(s.lower().split()))) for s in menus),default=0)
    prev=r.get('previous_handling',prior[-1]['handling'] if prior else None)
    x=[1,len(menus)/10,np.log1p(np.mean([len(s) for s in menus]))/8,overlap,
       np.log1p(r['decision_index'])/10]+[float(prev==c) for c in ACTIONS]
    if annotated:
        for c in ACTIONS:
            rows=[p for p in prior if p['handling']==c]
            chars=[p['effort']['chars_typed_after'] for p in rows]
            latency=[p['effort']['decide_seconds'] for p in rows if p['effort']['decide_seconds'] is not None]
            x.extend([np.log1p(np.mean(chars))/8 if chars else 0,np.log1p(np.median(latency))/8 if latency else 0,float(not latency)])
    return np.array(x,dtype=float)

def matrix(rows,annotated):
    histories=defaultdict(list);out=[]
    for r in rows:
        past=[p for p in histories[r['writer']] if p['resolved_at']<=r['open_at']]
        out.append(features(r,past,annotated));histories[r['writer']].append(r)
    return np.array(out)

def global_fit(x,y):
    d=x.shape[1]
    def f(v):
        w=v.reshape(d,4);p=softmax(x@w,axis=1)
        loss=-np.log(np.maximum(p[np.arange(len(y)),y],1e-300)).mean()+.005*(w[1:]**2).sum()
        p[np.arange(len(y)),y]-=1;p/=len(y);grad=x.T@p;grad[1:]+=.01*w[1:]
        return loss,grad.ravel()
    result=minimize(f,np.zeros(d*4),jac=True,method='L-BFGS-B',options={'maxiter':500})
    if not result.success:raise ValueError('pooled optimization failed')
    return result.x.reshape(d,4)

def intercept_fit(logits,y,weights,penalty):
    weights=np.asarray(weights,dtype=float);weights=weights/weights.sum()
    def f(r):
        p=softmax(logits+r,axis=1);loss=-np.sum(weights*np.log(np.maximum(p[np.arange(len(y)),y],1e-300)))+penalty*np.sum(r*r)
        p[np.arange(len(y)),y]-=1
        return loss,(p*weights[:,None]).sum(0)+2*penalty*r
    result=minimize(f,np.zeros(4),jac=True,method='L-BFGS-B')
    if not result.success:raise ValueError('writer optimization failed')
    return result.x

def proper(p,y):
    return dict(half_brier=float(.5*np.sum((p-np.eye(4)[y])**2)),log_loss=float(-np.log(max(p[y],1e-300))))

def run():
    folder=RAW/'baselines-v1'
    if folder.exists():raise ValueError('existing attempt cannot be rerun')
    folder.mkdir(parents=True);started=time.time()
    data=RAW/'data-v2';training=read(data/'TRAINING.json');targets=[r for r in read(data/'EVALUATOR.json') if not r['pilot']]
    wanted={r['writer'] for r in targets}
    freeze(folder/'INPUTS.json',{p.name:filehash(p) for p in data.glob('*.json')})
    all_history={r['key']:r for a in training.values() for r in a['history']}
    all_history=sorted(all_history.values(),key=lambda r:(r['open_at'],r['key']))
    training={w:c for w,c in training.items() if w in wanted}
    results=[];fits=[]
    try:
        for w,config in training.items():
            own=config['history'];own=sorted(own,key=lambda r:(r['open_at'],r['key']))
            n=max(4,int(.8*len(own)));cal=own[n:]
            if not cal:raise ValueError('empty historical calibration')
            split=min(r['open_at'] for r in cal)
            selected={};predictions={}
            for annotated in (False,True):
                past=[r for r in all_history if r['resolved_at']<split]
                x=matrix(past,annotated);y=np.array([ACTIONS.index(r['handling']) for r in past])
                W=global_fit(x,y);ownpast=[r for r in past if r['writer']==w]
                ox=matrix(ownpast,annotated);oy=np.array([ACTIONS.index(r['handling']) for r in ownpast])
                cx=np.array([features(r,[p for p in ownpast if p['resolved_at']<=r['open_at']],annotated) for r in cal]);cy=np.array([ACTIONS.index(r['handling']) for r in cal])
                candidates=[]
                for penalty in (.01,.1,1.,10.):
                    residual=intercept_fit(ox@W,oy,np.ones(len(oy)),penalty)
                    cp=softmax(cx@W+residual,axis=1)
                    candidates.append((np.mean([proper(p,t)['half_brier'] for p,t in zip(cp,cy)]),penalty))
                penalty=min(candidates)[1];selected[str(annotated)]=penalty
                past=[r for r in all_history if r['resolved_at']<=config['cutoff']]
                x=matrix(past,annotated);y=np.array([ACTIONS.index(r['handling']) for r in past]);W=global_fit(x,y)
                ownpast=[r for r in past if r['writer']==w];ox=matrix(ownpast,annotated);oy=np.array([ACTIONS.index(r['handling']) for r in ownpast])
                ts=[r for r in targets if r['writer']==w];tx=np.array([features(r,ownpast,annotated) for r in ts])
                costs=np.array([1+np.log1p(r['effort']['chars_typed_after']/50) for r in ownpast])
                shuffled=np.random.default_rng(int(key(w,'effort')[:16],16)).permutation(costs)
                arms={'B-mixlogit':np.ones(len(ownpast))} if not annotated else {'P04-effort-features':np.ones(len(ownpast)),'P04-E':costs,'P04-E-shuffle':shuffled}
                for name,weights in arms.items():
                    residual=intercept_fit(ox@W,oy,weights,penalty);predictions[name]=softmax(tx@W+residual,axis=1)
            pop=np.bincount(y,minlength=4)+1.;pop/=pop.sum();writer=np.bincount(oy,minlength=4)+4*pop;writer/=writer.sum()
            last=.45*writer+.55*np.eye(4)[oy[-1]]
            for i,t in enumerate(ts):
                ps={name:np.asarray(rows[i]) for name,rows in predictions.items()};ps.update({'B-pop':pop,'B-writer':writer,'B-last':last})
                truth=ACTIONS.index(t['handling'])
                results.append(dict(key=t['key'],writer=w,prompt=t['prompt'],pilot=t['pilot'],
                                    probabilities={name:p.tolist() for name,p in ps.items()},scores={name:proper(p,truth) for name,p in ps.items()}))
            fits.append(dict(writer=w,cutoff=config['cutoff'],penalties=selected,train_keys=[r['key'] for r in past]))
            atomic(folder/'PROGRESS.json',dict(at=time.time(),writers=len(fits),total=len(training)))
        freeze(folder/'PREDICTIONS.json',results);freeze(folder/'FITS.json',fits)
        # Whole completed cell; inferential analysis remains a separate saved-output consumer.
        freeze(folder/'COMPLETE.json',dict(status='COMPLETE',writers=len(fits),targets=len(results),
            wall_seconds=time.time()-started,outputs={p.name:filehash(p) for p in folder.glob('*.json') if p.name!='PROGRESS.json'}))
    except Exception as exc:
        freeze(folder/'FAILED.json',dict(status='FAILED',type=type(exc).__name__,error=str(exc),wall_seconds=time.time()-started));raise

if __name__=='__main__':run()
