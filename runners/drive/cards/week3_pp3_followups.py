"""Frozen first-generation PP3.s, PP3.m and PP3.p, with complete controls.

DESIGN CHECK: LESSONS 3-5 and CONTROLS reread 2026-10-26. NULL: constant
features reproduce the prior and zero contrast; reassignment removes known
signal on average. ALTERNATIVE: separable labels survive held projects, an
edit-only signal disappears under edit ablation, retained timing signal stays.
Exact solver parity and complete source/parent bindings precede interpretation.
Failure is invalid, never null. Shared interval bands remain exhaustive.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.linalg import cho_factor
from sklearn.tree import DecisionTreeClassifier
from . import week3_pp3_analysis as m
from .timing_p6 import write_equal
from runners.stage14.common import filehash


def specifications(family):
    if family=='s':return [('ridge_0.1',.1),('ridge_10',10.)]
    if family=='m':return [('remove_edit',1.)]
    if family=='p':return [('tree_depth5_leaf25',1.)]
    raise ValueError('unknown first-generation card')


def fit_design(x,train,test,alpha):
    mean=x[train].mean(axis=0);scale=x[train].std(axis=0);scale=np.where(scale>1e-12,scale,1.)
    z=(x[train]-mean)/scale;t=(x[test]-mean)/scale
    return z,t,cho_factor(z.T@z+np.eye(z.shape[1])*alpha,lower=True,check_finite=True)


def designs(x,c,projects,family,alpha):
    second=x[:,[i for i in range(24) if not 3<=i<=11]] if family=='m' else np.column_stack([x,c])
    out=[]
    for project in np.unique(projects):
        train=np.flatnonzero(projects!=project);test=np.flatnonzero(projects==project)
        out.append((int(project),train,test,[fit_design(x,train,test,alpha),fit_design(second,train,test,alpha)]))
    return out


def tree_probabilities(train,test,y,k):
    model=DecisionTreeClassifier(criterion='entropy',max_depth=5,min_samples_leaf=25,random_state=20261026,class_weight=None)
    model.fit(train,y);result=np.zeros((len(test),k));result[:,model.classes_]=model.predict_proba(test)
    if not np.allclose(result.sum(axis=1),1) or np.any(result<0):raise ValueError('invalid tree probability')
    return result


def evaluate(d,y,p,a,tree=False):
    if not tree:return m.evaluate(d,y,p,a)
    n=len(y);p3=np.empty((2,n,3));p15=np.empty((n,len(m.CLASSES)));base3=np.empty((n,3));base15=np.empty_like(p15)
    for project,train,test,arms in d:
        prior=np.bincount(y[train],minlength=len(m.CLASSES))/len(train)
        base15[test]=prior;base3[test]=[prior[m.MAP==k].sum() for k in range(3)]
        for arm,(z,t,_) in enumerate(arms):
            p3[arm,test]=tree_probabilities(z,t,m.MAP[y[train]],3)
            if arm==0:p15[test]=tree_probabilities(z,t,y[train],len(m.CLASSES))
    yy=m.MAP[y];loss=[]
    for prob in [p3[0],p3[1],base3]:loss.append(np.bincount(a,weights=.5*((prob-np.eye(3)[yy])**2).sum(axis=1),minlength=a.max()+1))
    return dict(cm3=np.stack([m.confusion(yy,prob,a,3) for prob in p3]),cm15=m.confusion(y,p15,a,len(m.CLASSES)),base3=m.confusion(yy,base3,a,3),base15=m.confusion(y,base15,a,len(m.CLASSES)),loss=np.array(loss))


def wide_fixture():
    x,c,y,p,a=m.fixture();return np.tile(x,(1,8)),c,y,p,a


def primary_draws(real,refs,weights,family):
    score=m.f1(np.einsum('bg,agij->baij',weights,real['cm3']))
    if family=='m':return score[:,0]-score[:,1]
    prior=m.f1(np.einsum('bg,gij->bij',weights,real['base3']))
    delta=[]
    for start in range(0,len(weights),50):
        ref=m.f1(np.einsum('bg,ngij->bnij',weights[start:start+50],refs['cm3'][0,:,0],optimize=True))
        delta.extend((score[start:start+50,0,None]-ref).mean(axis=1).tolist())
    return np.minimum(score[:,0]-prior,np.array(delta))


def known_answers(family):
    x,c,y,p,a=wide_fixture();tree=family=='p'
    for name,alpha in specifications(family):
        d=designs(x,c,p,family,alpha);real=evaluate(d,y,p,a,tree)
        assert m.f1(real['cm3'][0].sum(axis=0))>.95
        constant=evaluate(designs(np.zeros_like(x),np.zeros_like(c),p,family,alpha),y,p,a,tree)
        assert np.array_equal(constant['cm3'][0],constant['base3'])
        assert abs(constant['loss'][0].sum()-constant['loss'][2].sum())<1e-9
        refs={k:np.repeat(np.repeat(v[None,None],8,axis=1),2,axis=0) for k,v in constant.items()}
        draws=primary_draws(constant,refs,np.ones((1,a.max()+1)),family)
        assert draws.item()==0 and m.states.contrast_state(0,0,0)=='null'
        rng=np.random.default_rng(783);null=[m.f1(evaluate(d,m.permute(y,p,rng),p,a,tree)['cm3'][0].sum(axis=0)) for _ in range(8)]
        assert np.mean(null)<.55
    base=m.build_designs(x,c,p);new=designs(x,c,p,'s',1.)
    old=m.evaluate(base,y,p,a);new=evaluate(new,y,p,a)
    assert all(np.array_equal(old[k],new[k]) for k in old)
    if family=='m':
        only=np.zeros_like(x);only[:,3:6]=x[:,:3]
        ab=evaluate(designs(only,c,p,'m',1.),y,p,a)
        assert m.f1(ab['cm3'][0].sum(axis=0))>.95 and np.array_equal(ab['cm3'][1],ab['base3'])
        timing=np.zeros_like(x);timing[:,:3]=x[:,:3]
        kept=evaluate(designs(timing,c,p,'m',1.),y,p,a)
        assert m.f1(kept['cm3'][1].sum(axis=0))>.95
    return dict(separable=True,constant_exact_null=True,reassignment=True,original_ridge_parity=True,ablation_gates=family=='m')


def source(inputs,mode):
    if mode=='constructed':
        if inputs:raise ValueError('fixture receives no corpus')
        return wide_fixture(),None
    if set(inputs)!={'prepared','source_identity','parent'}:raise ValueError('missing source or parent')
    parent=Path(inputs['parent']);complete=json.loads((parent/'COMPLETE.json').read_text())
    if not complete['fresh_process_verified']:raise ValueError('parent not verified')
    for rel,h in complete['outputs'].items():
        if filehash(parent/rel)!=h:raise ValueError('parent output differs')
    summary=json.loads((parent/'output/SUMMARY.json').read_text())
    if not summary['scientific_admission'] or summary['summaries']['author']['primary']['state']!='positive':raise ValueError('wrong parent route')
    return m.read_source({k:v for k,v in inputs.items() if k!='parent'},'main'),summary


def run(output,inputs,config):
    family=config.get('family');specifications(family)
    mode=config.get('mode');n={'constructed':8,'cost':20,'main':200}.get(mode)
    if set(config)!={'family','mode','permutations'} or n!=config['permutations']:raise ValueError('unfrozen mode or bank')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);known=known_answers(family)
    (x,c,y,p,a),parent=source(inputs,mode);counts=np.bincount(a);group_count=a.max()+1
    rng=np.random.default_rng(m.CONTRACT['seed']+97);weights={k:m.resample_weights(a,p,k,rng,2000) for k in ['author','project']}
    results={};all_primary={k:[] for k in weights};points=[]
    for name,alpha in specifications(family):
        d=designs(x,c,p,family,alpha);real=evaluate(d,y,p,a,family=='p')
        if family=='m' and parent is not None:
            if real['cm3'][0].sum(axis=0).tolist()!=parent['confusion_matrices']['cm3'][0]:raise ValueError('source parent baseline parity failed')
        banks=[]
        for bank,groups in enumerate([p,a]):
            rng=np.random.default_rng(m.CONTRACT['seed']+bank);records=[]
            for draw in range(n):
                record=evaluate(d,m.permute(y,groups,rng),p,a,family=='p');records.append(record)
                if draw%5==0:write_equal(output/f'{name}_{bank}_{draw:03d}.json',dict(bank=bank,draw=draw,fingerprints={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in record.items()}))
            banks.append(records)
        refs={k:np.array([[r[k] for r in bank] for bank in banks]) for k in real}
        summaries={}
        for kind,w in weights.items():
            summaries[kind],null=m.summarize(real,refs,w,counts)
            all_primary[kind].append(primary_draws(real,refs,w,family))
        point=float(primary_draws(real,refs,np.ones((1,group_count)),family)[0]);points.append(point)
        if mode=='main':
            references=[]
            for bank in range(2):
                for arm in range(2):
                    v=null[bank,:,arm];actual=m.f1(real['cm3'][arm].sum(axis=0))
                    references.append(dict(bank=bank,arm=arm,mean=float(v.mean()),ci95=np.quantile(v,[.025,.975]).tolist(),p=float((1+(v>=actual).sum())/(len(v)+1))))
            if family=='m':
                for bank in range(2):
                    v=null[bank,:,0]-null[bank,:,1];references.append(dict(bank=bank,contrast='full_minus_ablated',mean=float(v.mean()),ci95=np.quantile(v,[.025,.975]).tolist(),p=float((1+(v>=point).sum())/(len(v)+1))))
            results[name]=dict(summaries=summaries,point=point,references=references,confusion_matrices={k:v.sum(axis=1 if k=='cm3' else 0).tolist() for k,v in real.items() if k!='loss'})
    info=dict(family=family,mode=mode,rows=len(y),projects=len(np.unique(p)),authors=len(np.unique(a)),known_answers=known,permutations_per_reference=n,bootstrap=2000,scientific_admission=mode=='main',descriptive=True,followup_generation=1,descendants_allowed=False)
    if mode=='main':
        info['variants']=results;info['primary']={}
        for kind,draws in all_primary.items():
            values=np.min(draws,axis=0) if family=='s' else draws[0]
            effect=min(points) if family=='s' else points[0];ci=np.quantile(values,[.025,.975]).tolist()
            info['primary'][kind]=dict(effect=effect,ci95=ci,state=m.states.contrast_state(effect,*ci))
        info['arm1_meaning']='process without edit block' if family=='m' else 'process plus content'
        info['auxiliary_field_names']='For mechanism, content_* keys denote ablated-minus-full; the card primary reverses that sign.' if family=='m' else 'Same as parent'
        if family=='s':info['parent_anchor']=parent['summaries'] if parent is not None else None
    write_equal(output/'SUMMARY.json',info);return info


def execute(output,inputs,config):return run(output,inputs,config)


def verify(output,inputs,config):
    expected=json.loads((Path(output)/'SUMMARY.json').read_text());actual=run(output,inputs,config)
    if expected!=actual:raise ValueError('fresh complete follow-up replay differs')
    return dict(verified=True,all_models_references_and_bootstraps_replayed=True,scientific_admission=config['mode']=='main',family=config['family'])
