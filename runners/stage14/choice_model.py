"""P04/SL9 candidate-level panel mixed logit with frozen feature rivals.

DESIGN CHECK: LESSONS 2-5; Train 2009 chapters 6 and 11, primary source read.
NULL: pooled/position or wrong-writer posterior performs equally; writer labels
cannot improve uniform planted choices. ALTERNATIVE: past-choice posterior over
random coefficients improves later choices. A finite mixing distribution is a
discrete mixed logit, not a claim that psychological types exist. The fit uses
complete offer sets and known-writer future partitions, conditional on uptake.
"""
from collections import defaultdict
import re, numpy as np
from scipy.optimize import minimize
from scipy.special import softmax,logsumexp
from .common import read,freeze,digest
from .adaptive import proper
from .uncertainty_v2 import contrast

def basic(document,alternatives):
    prior=set(re.findall(r'\w+',document[-512:].lower()));result=[]
    for i,text in enumerate(alternatives):
        words=re.findall(r'\w+',text.lower());bag=set(words)
        result.append([float(i==0),i/max(1,len(alternatives)-1),np.log1p(len(text))/8,
            np.mean([len(w) for w in words])/10 if words else 0,len(bag&prior)/max(1,len(bag)),
            text.count(',')/max(1,len(words)),text.count('?')/max(1,len(words)),
            float(text[:1].isupper()),len(bag)/max(1,len(words))])
    a=np.asarray(result);return a-a.mean(axis=0)

def packed(cases):
    sizes=np.array([len(c['x']) for c in cases]);starts=np.r_[0,np.cumsum(sizes)[:-1]]
    x=np.concatenate([c['x'] for c in cases]);y=starts+np.array([c['truth'] for c in cases])
    return x,sizes,starts,y

def objective(beta,pack,weights,penalty):
    x,sizes,starts,y=pack;z=x@beta;maximum=np.maximum.reduceat(z,starts)
    ez=np.exp(z-np.repeat(maximum,sizes));den=np.add.reduceat(ez,starts);p=ez/np.repeat(den,sizes)
    value=np.dot(weights,maximum+np.log(den)-z[y])/weights.sum()+penalty*np.dot(beta,beta)/2
    d=p.copy();d[y]-=1
    return float(value),x.T@(d*np.repeat(weights/weights.sum(),sizes))+penalty*beta

def fit(cases,classes,penalty,seed=141010):
    pack=packed(cases);writers=sorted({c['writer'] for c in cases});wi=np.array([writers.index(c['writer']) for c in cases]);n=len(writers)
    d=pack[0].shape[1];rng=np.random.default_rng(seed);betas=rng.normal(0,.1,(classes,d));mix=np.ones(classes)/classes;history=[]
    for iteration in range(40):
        logl=np.zeros((n,classes))
        for k,beta in enumerate(betas):
            z=pack[0]@beta;mx=np.maximum.reduceat(z,pack[2]);den=np.add.reduceat(np.exp(z-np.repeat(mx,pack[1])),pack[2])
            chosen=z[pack[3]]-mx-np.log(den);np.add.at(logl[:,k],wi,chosen)
        posterior=softmax(logl+np.log(mix),axis=1)
        value=float(logsumexp(logl+np.log(mix),axis=1).sum());history.append(value)
        for k in range(classes):
            result=minimize(objective,betas[k],args=(pack,posterior[wi,k]+1e-9,penalty),jac=True,method='L-BFGS-B',options={'maxiter':300,'ftol':1e-10})
            if not result.success:raise ValueError('candidate optimizer failed: '+str(result.message))
            betas[k]=result.x
        mix=(posterior.sum(axis=0)+.1)/(n+.1*classes)
        if iteration>3 and abs(history[-1]-history[-2])<1e-5*(1+abs(history[-2])):break
    # Recompute writer posteriors at the FINAL coefficient values.
    logl=np.zeros((n,classes))
    for k,beta in enumerate(betas):
        z=pack[0]@beta;mx=np.maximum.reduceat(z,pack[2]);den=np.add.reduceat(np.exp(z-np.repeat(mx,pack[1])),pack[2])
        np.add.at(logl[:,k],wi,z[pack[3]]-mx-np.log(den))
    return dict(betas=betas.tolist(),population=mix.tolist(),posterior={w:p.tolist() for w,p in zip(writers,softmax(logl+np.log(mix),axis=1))},iterations=iteration+1,likelihood_trace=history,
        algorithm='finite 40-step EM; convergence trace retained, not continuous-Gaussian integration')

def predict(model,cases,writer=None):
    weights=np.asarray(model['posterior'].get(writer,model['population']));beta=np.asarray(model['betas'])
    return [(softmax(np.asarray(c['x'])@beta.T,axis=0)@weights).tolist() for c in cases]

def run(card,out,raw,tick):
    source=raw/'jobs'/card['requires'][0];rows=read(source/'READER.json');truth={r['key']:r for r in read(source/'EVALUATOR.json')};cases=[];excluded=[]
    vectors=None
    if card.get('embedding_job'):vectors=read(raw/'jobs'/card['embedding_job']/'FEATURES.json')
    for r in rows:
        t=truth[r['key']];e=r['evidence']
        if t['handling'] not in ('accept','edit'):continue
        if t['selected_index'] not in r['option_indices'] or len(e['alternatives'])<2:
            excluded.append(dict(key=r['key'],reason='no observed selection within multi-option support'));continue
        x=basic(e['document'],e['alternatives'])
        if vectors is not None:x=np.column_stack((x,np.asarray(vectors[r['key']])))
        cases.append({k:r[k] for k in ('key','writer','prompt','partition','timestamp')}|dict(x=x,truth=r['option_indices'].index(t['selected_index'])))
    result=[];models={};writers=sorted({c['writer'] for c in cases})
    for writer in writers:
        if len(models)>=card.get('writer_limit',999):break
        cal=[c for c in cases if c['writer']==writer and c['partition']=='calibration'];ev=[c for c in cases if c['writer']==writer and c['partition']=='evaluation']
        if not cal or not ev:excluded.append(dict(writer=writer,reason='no complete chosen-option calibration/evaluation'));continue
        cutoff=min(c['timestamp'] for c in cal);tr=[c for c in cases if c['partition']=='train' and c['timestamp']<cutoff]
        counts=defaultdict(int)
        for c in tr:counts[c['writer']]+=1
        if not counts[writer] or len(counts)<2:excluded.append(dict(writer=writer,reason='no past-only own/donor support'));continue
        donor=min((w for w in counts if w!=writer),key=lambda w:(abs(counts[w]-counts[writer]),w));options=[]
        pooled=fit(tr,1,.01)
        for k in (2,4):
            for penalty in (.01,.1):
                m=fit(tr,k,penalty);p=predict(m,cal,writer);loss=float(np.mean([proper(v,c['truth'])['half_brier'] for v,c in zip(p,cal)]));options.append((loss,k,penalty,m))
        loss,k,penalty,selected=min(options,key=lambda t:t[:3]);ps={'personal':predict(selected,ev,writer),'donor':predict(selected,ev,donor),'population':predict(selected,ev),'pooled':predict(pooled,ev)}
        for i,c in enumerate(ev):
            probs={a:v[i] for a,v in ps.items()};probs['uniform']=[1/len(c['x'])]*len(c['x']);probs['first']=[1.]+[0.]*(len(c['x'])-1)
            result.append({f:c[f] for f in ('key','writer','prompt','truth')}|dict(probabilities=probs,scores={a:proper(v,c['truth']) for a,v in probs.items()}))
        models[writer]=dict(cutoff=cutoff,max_training_time=max(c['timestamp'] for c in tr),training_keys_digest=digest([c['key'] for c in tr]),donor=donor,chosen_classes=k,penalty=penalty,calibration=[dict(loss=a,classes=b,penalty=p) for a,b,p,_ in options],model=selected,pooled=pooled)
        tick(dict(completed_writers=len(models),available_writers=len(writers)))
    if not result:raise ValueError('no complete candidate-level comparison')
    freeze(out/'PREDICTIONS.json',result);freeze(out/'MODELS.json',models);freeze(out/'EXCLUSIONS.json',excluded)
    freeze(out/'SUMMARY.json',dict(writers=len(models),choices=len(result),contrasts=[contrast(result,'personal',b) for b in ('donor','population','pooled','uniform','first')],
        method='candidate-level finite-mixture panel logit; exact discrete random-coefficient integration conditional on earlier choices',scope='exposed known-writer future choices conditional on acceptance/edit; fixed prompts; not private goals'))
    freeze(out/'ADMISSION.json',dict(admitted=True,execution_only=True,scientific_promotion=False))
