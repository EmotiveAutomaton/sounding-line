"""P01/P02/P04: frozen past-only rival and maker-residual complete block.

DESIGN CHECK: LESSONS 2-5; CONTROLS 1,2,6. NULL: own history performs like a
fixed training-donor history or pooled prior; additional sharpness alone fails.
ALTERNATIVE: maker-specific terms improve future proper loss on paired writers.
Hyperparameters use calibration only; test remains a separate descriptive set.
"""
from collections import defaultdict, Counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
from difflib import SequenceMatcher
from .common import read,freeze,digest
from .statistics import ACTIONS,score
from .uncertainty import contrast

def features(e):
    doc=e['document'];alts=e['alternatives']; lengths=[len(t) for t in alts]
    sims=[SequenceMatcher(None,doc[-200:],t[:200],autojunk=False).ratio() for t in alts]
    return np.array([1.,np.log1p(len(doc))/10,np.log1p(np.mean(lengths))/8,len(alts)/10,
        max(sims,default=0),float(np.mean(sims)) if sims else 0,float(np.std(lengths))/100,
        float(doc.rstrip().endswith(('.','?','!')))])

def fit(x,y,wi,nw,penalty,personal):
    d=x.shape[1];size=d*4+(nw*4 if personal else 0)
    def fun(v):
        w=v[:d*4].reshape(d,4);r=v[d*4:].reshape(nw,4) if personal else None
        logits=x@w+(r[wi] if personal else 0);p=softmax(logits,axis=1)
        loss=-np.log(np.maximum(p[np.arange(len(y)),y],1e-300)).mean()+.005*(w[1:]**2).sum()
        diff=p;diff[np.arange(len(y)),y]-=1;diff/=len(y)
        gw=x.T@diff;gw[1:]+=.01*w[1:]
        if personal:
            loss+=penalty*(r*r).sum()/nw
            gr=np.zeros_like(r);np.add.at(gr,wi,diff);gr+=2*penalty*r/nw
            return loss,np.concatenate([gw.ravel(),gr.ravel()])
        return loss,gw.ravel()
    result=minimize(fun,np.zeros(size),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-10})
    if not result.success:raise ValueError('fit did not converge: '+result.message)
    return dict(weights=result.x[:d*4].reshape(d,4).tolist(),residual=result.x[d*4:].reshape(nw,4).tolist() if personal else None,
        optimizer=dict(iterations=result.nit,converged=bool(result.success)))

def predict(model,x,wi):
    r=np.asarray(model['residual'])[wi] if model['residual'] is not None else 0
    return softmax(x@np.asarray(model['weights'])+r,axis=1)

def run(card,out,raw,tick):
    parent=raw/'jobs'/card['requires'][0]; rows=read(parent/'READER.json'); truth={r['key']:r for r in read(parent/'EVALUATOR.json')}
    writers=sorted({r['writer'] for r in rows});wmap={w:i for i,w in enumerate(writers)}
    part={p:[r for r in rows if r['partition']==p] for p in ('train','calibration','evaluation')}
    if any(not v for v in part.values()):raise ValueError('empty partition')
    arrays={p:(np.array([features(r['evidence']) for r in rs]),np.array([ACTIONS.index(truth[r['key']]['handling']) for r in rs]),np.array([wmap[r['writer']] for r in rs])) for p,rs in part.items()}
    result=[];fitted={};exclusions=[]
    train_time=np.array([r['timestamp'] for r in part['train']])
    # Every recipient has its own global cutoff. Another writer's later training
    # data cannot leak backwards into an earlier recipient's calibration or test.
    for target in writers:
        j=wmap[target];ci=np.array([i for i,r in enumerate(part['calibration']) if r['writer']==target]);ti=np.array([i for i,r in enumerate(part['evaluation']) if r['writer']==target])
        cutoff=min(part['calibration'][i]['timestamp'] for i in ci)
        mask=train_time<cutoff
        x,y,wi=(a[mask] for a in arrays['train']);cx,cy,cwi=(a[ci] for a in arrays['calibration']);tx,ty,twi=(a[ti] for a in arrays['evaluation'])
        donors=sorted(set(wi)-{j},key=lambda k:(abs(int((wi==k).sum())-int((wi==j).sum())),writers[k]))
        if not len(x) or not donors or not (wi==j).any():
            exclusions.append(dict(writer=target,reason='no past-only own/donor contrast at recipient cutoff'));continue
        donor=donors[0]
        global_prior=np.bincount(y,minlength=4)+1.;global_prior/=global_prior.sum()
        own=[]
        for k in range(len(writers)):
            q=np.bincount(y[wi==k],minlength=4)+4*global_prior;own.append(q/q.sum())
        own=np.array(own);pooled=fit(x,y,wi,len(writers),0,False);models=[]
        for penalty in (.01,.1,1.,10.):
            model=fit(x,y,wi,len(writers),penalty,True);p=predict(model,cx,cwi)
            models.append((float(np.mean([score(v,int(t))['half_brier'] for v,t in zip(p,cy)])),penalty,model))
        _,penalty,personal=min(models,key=lambda a:(a[0],a[1]))
        preds={'pooled_features':predict(pooled,tx,twi),'personal_features':predict(personal,tx,twi),
            'donor_features':predict(personal,tx,np.full(len(tx),donor)),
            'global_prior':np.tile(global_prior,(len(tx),1)),'own_history':own[twi],'donor_history':np.tile(own[donor],(len(tx),1))}
        for i,idx in enumerate(ti):
            r=part['evaluation'][idx]
            result.append(dict(key=r['key'],writer=target,prompt=r['prompt'],truth=int(ty[i]),
                probabilities={k:p[i].tolist() for k,p in preds.items()},scores={k:score(p[i],int(ty[i])) for k,p in preds.items()}))
        fitted[target]=dict(pooled=pooled,personal=personal,penalty=penalty,calibration=[dict(loss=a,penalty=b) for a,b,_ in models],
            donor=writers[donor],cutoff=cutoff,max_train_time=float(train_time[mask].max()),training_keys_digest=digest([r['key'] for r,t in zip(part['train'],mask) if t]))
        tick(dict(writers_fitted=len(fitted),eligible_writers=len(writers)))
    if not result:raise ValueError('no fully past-only comparison available')
    freeze(out/'PREDICTIONS.json',result)
    freeze(out/'MODELS.json',fitted);freeze(out/'EXCLUSIONS.json',exclusions)
    contrasts=[contrast(result,a,b) for a,b in [('personal_features','pooled_features'),('personal_features','donor_features'),('own_history','global_prior'),('own_history','donor_history')]]
    prompt_sensitivity={p:{m:float(np.mean([r['scores'][m]['half_brier'] for r in result if r['prompt']==p])) for m in preds} for p in sorted({r['prompt'] for r in result})}
    freeze(out/'SUMMARY.json',dict(contrasts=contrasts,attempted=len(result),writers=len(writers),prompt_sensitivity=prompt_sensitivity,
        type='descriptive future handling, not mental-goal inference or option identity',claim_limit='No fresh human confirmation; global shared training and fixed donor roster condition the interval.',
        unimplemented_rival='Frozen neural embeddings and candidate-level mixed logit remain separate cards; these are eight predeclared menu/context features.'))
