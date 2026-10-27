"""Frozen PP3 linear process-label classifier and complete reassignment banks.

DESIGN CHECK: LESSONS 1d,2,3-5 and CONTROLS read 2026-10-26. NULL: constant
features reproduce the training prior; label reassignment removes constructed
predictivity on average. ALTERNATIVE: separable process features predict labels
across held projects. Invalid source, probabilities, solves or fresh replay fail
closed, never become null. Shared interval states are exhaustive. Preparation,
native rehearsal and cost-only execution never license a scientific claim.
"""
from pathlib import Path
import gzip
import hashlib
import json
import time
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from sklearn.feature_extraction.text import HashingVectorizer
from runners.stage14.common import REPO, filehash
from . import states
from .timing_p6 import write_equal
from .week3_pp3_inputs import CONFIG as SOURCE_CONFIG, load, LABEL_MAP

CLASSES=tuple(sorted(LABEL_MAP));CATEGORIES=tuple(sorted(set(LABEL_MAP.values())))
MAP=np.array([CATEGORIES.index(LABEL_MAP[k]) for k in CLASSES])
CONTRACT=dict(seed=20261026,bootstrap=2000,ridge=1.,content_bins_per_state=128)


def simplex(a):
    a=np.asarray(a,dtype=float)
    u=np.sort(a,axis=1)[:,::-1];s=np.cumsum(u,axis=1)-1
    j=np.arange(1,a.shape[1]+1);r=(u-s/j>0).sum(axis=1)-1
    theta=s[np.arange(len(a)),r]/(r+1)
    p=np.maximum(a-theta[:,None],0)
    if not np.all(np.isfinite(p)) or not np.allclose(p.sum(axis=1),1,atol=1e-10):raise ValueError('invalid simplex')
    return p


def fit_design(x,train,test):
    mean=x[train].mean(axis=0);scale=x[train].std(axis=0);scale=np.where(scale>1e-12,scale,1.)
    z=(x[train]-mean)/scale;t=(x[test]-mean)/scale
    factor=cho_factor(z.T@z+np.eye(z.shape[1])*CONTRACT['ridge'],lower=True,check_finite=True)
    return z,t,factor


def predict(design,y):
    z,t,factor=design;prior=np.bincount(y,minlength=len(CLASSES))/len(y)
    target=np.eye(len(CLASSES))[y]
    coef=cho_solve(factor,z.T@(target-prior),check_finite=True)
    raw=t@coef+prior
    if not np.isfinite(raw).all():raise ValueError('invalid ridge solve')
    raw3=np.column_stack([raw[:,MAP==c].sum(axis=1) for c in range(3)])
    return simplex(raw3),simplex(raw),prior


def confusion(y,p,groups,k):
    out=np.zeros((groups.max()+1,k,k),dtype=np.int64)
    np.add.at(out,(groups,y,np.argmax(p,axis=1)),1)
    return out


def f1(cm):
    cm=np.asarray(cm);tp=np.diagonal(cm,axis1=-2,axis2=-1);den=cm.sum(axis=-1)+cm.sum(axis=-2)
    return np.divide(2*tp,den,out=np.zeros_like(tp,dtype=float),where=den>0).mean(axis=-1)


def permute(y,groups,rng):
    out=y.copy()
    for g in np.unique(groups):
        ix=np.flatnonzero(groups==g);out[ix]=y[ix][rng.permutation(len(ix))]
    return out


def evaluate(designs,y,projects,authors):
    n=len(y);p3=np.empty((2,n,3));p15=np.empty((n,len(CLASSES)));prior3=np.empty((n,3));prior15=np.empty((n,len(CLASSES)))
    for project,train,test,arms in designs:
        for arm,design in enumerate(arms):
            a,b,prior=predict(design,y[train]);p3[arm,test]=a
            if arm==0:
                p15[test]=b;prior15[test]=prior
                prior3[test]=np.array([prior[MAP==c].sum() for c in range(3)])
    yy=MAP[y];ng=authors.max()+1
    cm3=np.stack([confusion(yy,a,authors,3) for a in p3]);cm15=confusion(y,p15,authors,len(CLASSES))
    base3=confusion(yy,prior3,authors,3);base15=confusion(y,prior15,authors,len(CLASSES))
    losses=[]
    for a in [p3[0],p3[1],prior3]:
        loss=.5*((a-np.eye(3)[yy])**2).sum(axis=1)
        losses.append(np.bincount(authors,weights=loss,minlength=ng))
    return dict(cm3=cm3,cm15=cm15,base3=base3,base15=base15,loss=np.array(losses))


def build_designs(x,content,projects):
    both=np.column_stack([x,content]);out=[]
    for project in np.unique(projects):
        test=np.flatnonzero(projects==project);train=np.flatnonzero(projects!=project)
        if not len(train) or not len(test):raise ValueError('empty project split')
        out.append((int(project),train,test,[fit_design(x,train,test),fit_design(both,train,test)]))
    return out


def fixture():
    rng=np.random.default_rng(417);projects=np.repeat(np.arange(5),90);y=np.tile(np.arange(90)%len(CLASSES),5)
    authors=projects*2+(np.arange(len(y))%2);x=np.eye(3)[MAP[y]]+rng.normal(0,.02,(len(y),3))
    return x,rng.normal(size=(len(y),4)),y,projects,authors


def known_answers():
    x,c,y,p,a=fixture();d=build_designs(x,c,p);real=evaluate(d,y,p,a)
    assert f1(real['cm3'][0].sum(axis=0))>.95
    z=np.zeros_like(x);constant=evaluate(build_designs(z,np.zeros_like(c),p),y,p,a)
    assert np.array_equal(constant['cm3'][0],constant['base3'])
    assert abs(constant['loss'][0].sum()-constant['loss'][2].sum())<1e-9
    rng=np.random.default_rng(79);null=[]
    for _ in range(12):null.append(f1(evaluate(d,permute(y,p,rng),p,a)['cm3'][0].sum(axis=0)))
    assert np.mean(null)<.55
    return dict(separable_signal_recovered=True,constant_features_equal_prior=True,reassignment_removes_signal=True)


def read_source(inputs,mode):
    if mode=='constructed':
        if inputs:raise ValueError('fixture has no source inputs')
        return fixture()
    if set(inputs)!={'prepared','source_identity'}:raise ValueError('exact source inputs required')
    root=Path(inputs['prepared']);complete=json.loads((root/'COMPLETE.json').read_text())
    if not complete['fresh_process_verified']:raise ValueError('unverified prepared source')
    for rel,h in complete['outputs'].items():
        if filehash(root/rel)!=h:raise ValueError('prepared output differs')
    with gzip.open(root/'output/ROWS.jsonl.gz','rt',encoding='utf8') as f:prepared=[json.loads(l) for l in f]
    rows=load({'source_identity':inputs['source_identity']},SOURCE_CONFIG)
    if len(prepared)!=len(rows):raise ValueError('incomplete source')
    for ordinal,(r,q) in enumerate(zip(rows,prepared)):
        if (q['source_ordinal']!=ordinal or q['label']!=r['label'] or q['category']!=r['high-level']
            or q['before_sha256']!=hashlib.sha256(r['before text'].encode()).hexdigest()
            or q['after_sha256']!=hashlib.sha256(r['after text'].encode()).hexdigest()):raise ValueError('source join differs')
    vectorizer=HashingVectorizer(n_features=CONTRACT['content_bins_per_state'],alternate_sign=False,norm='l2',token_pattern=r'(?u)\b\w+\b',lowercase=True)
    content=np.column_stack([vectorizer.transform(r[key] for r in rows).toarray() for key in ['before text','after text']])
    projects=np.unique([r['project'] for r in prepared],return_inverse=True)[1]
    authors=np.unique([r['author'] for r in prepared],return_inverse=True)[1]
    y=np.array([CLASSES.index(r['label']) for r in prepared]);x=np.array([r['features'] for r in prepared])
    if len(rows)!=61504 or len(np.unique(projects))!=5 or len(np.unique(authors))!=12:raise ValueError('population differs')
    return x,content,y,projects,authors


def resample_weights(authors,projects,kind,rng,n):
    ng=authors.max()+1
    if kind=='author':return rng.multinomial(ng,np.full(ng,1/ng),size=n)
    groups=np.unique(projects);counts=rng.multinomial(len(groups),np.full(len(groups),1/len(groups)),size=n)
    membership=np.array([np.unique(projects[authors==a]).item() for a in range(ng)])
    return counts[:,membership]


def summarize(real,refs,weights,counts):
    # Axes: banks, permutations, arms, author, class, class.
    current=f1(real['cm3'].sum(axis=1));prior=float(f1(real['base3'].sum(axis=0)))
    null=f1(refs['cm3'].sum(axis=3));means=null.mean(axis=1)
    effect=float(current[0]-max(prior,means[0,0]))
    observed=f1(np.einsum('bg,agij->baij',weights,real['cm3']))
    base=f1(np.einsum('bg,gij->bij',weights,real['base3']))
    # Bootstrap draw chunks bound memory without changing any draws.
    nullmean=[]
    for start in range(0,len(weights),50):
        cm=np.einsum('bg,ngij->bnij',weights[start:start+50],refs['cm3'][0,:,0],optimize=True)
        nullmean.extend(f1(cm).mean(axis=1).tolist())
    contrast=observed[:,0]-np.maximum(base,np.array(nullmean))
    ci=np.quantile(contrast,[.025,.975]).tolist()
    loss=real['loss'].sum(axis=1)/counts.sum();bootloss=(weights@real['loss'].T)/(weights@counts)[:,None]
    contentgain=observed[:,1]-observed[:,0]
    return dict(primary=dict(effect=effect,ci95=ci,state=states.contrast_state(effect,*ci),process_macro_f1=float(current[0]),prior_macro_f1=prior,reference_mean=float(means[0,0])),
        process_half_brier_gain_over_prior=dict(effect=float(loss[2]-loss[0]),ci95=np.quantile(bootloss[:,2]-bootloss[:,0],[.025,.975]).tolist()),
        content_macro_f1_gain=dict(effect=float(current[1]-current[0]),ci95=np.quantile(contentgain,[.025,.975]).tolist()),
        content_half_brier_gain_over_process=dict(effect=float(loss[0]-loss[1]),ci95=np.quantile(bootloss[:,0]-bootloss[:,1],[.025,.975]).tolist()),
        fifteen_way=dict(macro_f1=float(f1(real['cm15'].sum(axis=0))),prior_macro_f1=float(f1(real['base15'].sum(axis=0))),
            ci95=np.quantile(f1(np.einsum('bg,gij->bij',weights,real['cm15'])),[.025,.975]).tolist())),null


def run(output,inputs,config):
    if config not in [dict(mode='constructed',permutations=8),dict(mode='cost',permutations=20),dict(mode='main',permutations=200)]:raise ValueError('fixed modes required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter();known=known_answers();x,c,y,p,a=read_source(inputs,config['mode'])
    designs=build_designs(x,c,p);real=evaluate(designs,y,p,a);banks=[]
    for bank,groups in enumerate([p,a]):
        rng=np.random.default_rng(CONTRACT['seed']+bank);records=[]
        for draw in range(config['permutations']):
            record=evaluate(designs,permute(y,groups,rng),p,a);records.append(record)
            if draw%5==0:
                fingerprints={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in record.items()}
                write_equal(output/f'CHECKPOINT_{bank}_{draw:03d}.json',dict(bank=bank,draw=draw,fingerprints=fingerprints))
        banks.append(records)
    refs={k:np.array([[r[k] for r in bank] for bank in banks]) for k in real}
    rng=np.random.default_rng(CONTRACT['seed']+97);counts=np.bincount(a);summaries={}
    for kind in ['author','project']:
        weights=resample_weights(a,p,kind,rng,CONTRACT['bootstrap']);summaries[kind],null=summarize(real,refs,weights,counts)
    info=dict(mode=config['mode'],rows=len(y),projects=len(np.unique(p)),project_scoped_authors=len(np.unique(a)),known_answers=known,
        permutations_per_reference=config['permutations'],references=['within_project','within_project_author'],bootstrap=CONTRACT['bootstrap'],complete_source_rows=True,
        scientific_admission=config['mode']=='main',descriptive=True,elapsed_seconds=time.perf_counter()-start)
    if config['mode']=='main':
        info['summaries']=summaries
        info['reference_statistics']=[dict(bank=bank,arm=arm,mean=float(v.mean()),ci95=np.quantile(v,[.025,.975]).tolist(),p=float((1+(v>=f1(real['cm3'][arm].sum(axis=0))).sum())/(len(v)+1))) for bank in range(2) for arm in range(2) for v in [null[bank,:,arm]]]
        info['confusion_matrices']={k:v.sum(axis=1 if k=='cm3' else 0).tolist() for k,v in real.items() if k!='loss'}
        info['classes']=list(CLASSES);info['categories']=list(CATEGORIES)
        null15=f1(refs['cm15'].sum(axis=2));actual15=f1(real['cm15'].sum(axis=0))
        info['fifteen_references']=[dict(mean=float(v.mean()),ci95=np.quantile(v,[.025,.975]).tolist(),p=float((1+(v>=actual15).sum())/(len(v)+1))) for v in null15]
    # Timing is diagnostic only and excluded from immutable deterministic output.
    elapsed=info.pop('elapsed_seconds');write_equal(output/'SUMMARY.json',info)
    return dict(**info,elapsed_seconds=elapsed)


def execute(output,inputs,config):return run(output,inputs,config)


def verify(output,inputs,config):
    expected=json.loads((Path(output)/'SUMMARY.json').read_text(encoding='utf8'));actual=run(output,inputs,config);actual.pop('elapsed_seconds')
    if expected!=actual:raise ValueError('full independent classifier replay differs')
    return dict(verified=True,full_source_models_references_bootstrap_replay=True,scientific_admission=config['mode']=='main',rows=actual['rows'])
