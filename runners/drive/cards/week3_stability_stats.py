"""WC4 prompt-adjusted variance profiles and complete-label reference rebuilding.

DESIGN CHECK: LESSONS3-5 and controls read 2026-10-25. Under exchangeable writer
labels, the real-minus-reference advantage is zero in expectation; a stable
writer-specific pattern raises it, reversal lowers it. Identical population
profiles have no estimable correlation, never perfect reliability. Entire prompts stay in one half.
Missing session properties and insufficient within-half replication are explicit.
"""
from collections import defaultdict

import numpy as np
from threadpoolctl import threadpool_limits

from .week3_stability_inputs import PROPERTIES


def prepare(rows):
    rows=sorted(rows,key=lambda r:r['session'])
    eligible=[r for r in rows if r['event_eligible'] and not r['missing']]
    grouped=defaultdict(list)
    for r in eligible:grouped[r['writer']].append(r)
    split={};excluded={}
    for w,sessions in sorted(grouped.items()):
        earliest={}
        for r in sessions:earliest[r['prompt']]=min(earliest.get(r['prompt'],r['timestamp']),r['timestamp'])
        order={p:i%2 for i,p in enumerate(sorted(earliest,key=lambda p:(earliest[p],p)))}
        count=[sum(order[r['prompt']]==h for r in sessions) for h in (0,1)]
        if len(earliest)<2 or min(count)<2:excluded[w]=dict(prompts=len(earliest),sessions_per_half=count)
        else:split[w]=order
    # Keep all eligible sessions in prompt adjustment and label banks, including
    # writers without their own estimable profile. Recipient counts per prompt
    # are fixed by the permutation, so the admitted support cannot change.
    names=sorted(split);labels=np.asarray([r['writer'] for r in eligible],object)
    x=np.asarray([[r['properties'][k] for k in PROPERTIES] for r in eligible],float)
    prompts={p:np.asarray([i for i,r in enumerate(eligible) if r['prompt']==p],int) for p in sorted({r['prompt'] for r in eligible})}
    residual=x.copy()
    for idx in prompts.values():residual[idx]-=residual[idx].mean(0)
    return dict(rows=eligible,names=names,labels=labels,split=split,residual=residual,prompts=prompts,
                support=dict(source_sessions=len(rows),source_writers=len({r['writer'] for r in rows}),eligible_sessions=len(eligible),
                             below_50_events=sum(not r['event_eligible'] for r in rows),missing_properties=sum(r['event_eligible'] and bool(r['missing']) for r in rows),
                             admitted_writers=len(names),excluded_writers=excluded))


def profiles(prepared,labels):
    out=[]
    for w in prepared['names']:
        halves=[]
        for h in (0,1):
            idx=[i for i,r in enumerate(prepared['rows']) if labels[i]==w and prepared['split'][w][r['prompt']]==h]
            if len(idx)<2:raise ValueError('WC4 reassignment changed variance support')
            halves.append(np.var(prepared['residual'][idx],axis=0,ddof=1))
        out.append(halves)
    v=np.asarray(out,float)
    if not len(v):return v,None
    denominator=v.mean(0)
    if np.any(denominator<=1e-24):return v,None
    return v,v/denominator


def agreement(ratios):
    """Eight correlations across writers, not cosine across properties."""
    a,b=ratios[:,0].copy(),ratios[:,1].copy();a-=a.mean(0);b-=b.mean(0)
    denominator=np.linalg.norm(a,axis=0)*np.linalg.norm(b,axis=0)
    if np.any(denominator<=1e-20):return None
    return np.sum(a*b,axis=0)/denominator


def paired_bootstrap(bank,draws):
    """Rebuild nonlinear correlations on the same real-writer draws in every arm.

    Column scaling by the half's population variance cancels in correlation,
    so retaining those scales is exactly equivalent to recomputing them for
    each draw. Center once before weighted moments for numerical stability.
    """
    x=bank[:,:,0].copy();y=bank[:,:,1].copy();x-=x.mean(1,keepdims=True);y-=y.mean(1,keepdims=True)
    w=bank.shape[1];real=[];difference=[];invalid=0
    with threadpool_limits(limits=2):
        for start in range(0,len(draws),32):
            weights=np.asarray([np.bincount(row,minlength=w)/w for row in draws[start:start+32]])
            def moment(z):return np.einsum('bw,rwd->brd',weights,z,optimize=True)
            mx,my=moment(x),moment(y);xx=moment(x*x)-mx*mx;yy=moment(y*y)-my*my
            denominator=np.sqrt(np.maximum(xx,0)*np.maximum(yy,0));valid=np.all(denominator>1e-20,axis=(1,2))
            invalid+=int(np.sum(~valid))
            correlations=np.divide(moment(x*y)-mx*my,denominator,out=np.zeros_like(denominator),where=denominator>1e-20).mean(2)
            real.extend(correlations[valid,0].tolist());difference.extend((correlations[valid,0]-correlations[valid,1:].mean(1)).tolist())
    return real,difference,invalid


def analyze(rows,config):
    p=prepare(rows);names=p['names']
    if len(names)<3:return dict(card='WC4',state='unsupported_writers',support=p['support'],scientific_admission=False)
    variances,ratio=profiles(p,p['labels'])
    if ratio is None:return dict(card='WC4',state='unsupported_zero_population_variance',support=p['support'],scientific_admission=False)
    real=agreement(ratio)
    if real is None:return dict(card='WC4',state='unsupported_between_writer_variation',support=p['support'],scientific_admission=False)
    rng=np.random.default_rng(config['seed']);fake=[];bank=[ratio]
    for _ in range(config['permutations']):
        labels=p['labels'].copy()
        for idx in p['prompts'].values():labels[idx]=rng.permutation(labels[idx])
        _,control=profiles(p,labels)
        if control is None:return dict(card='WC4',state='unsupported_null_population_variance',support=p['support'],scientific_admission=False)
        scores=agreement(control)
        if scores is None:return dict(card='WC4',state='unsupported_null_between_writer_variation',support=p['support'],scientific_admission=False)
        fake.append(scores);bank.append(control)
    fake=np.asarray(fake);reference=fake.mean(1)
    draws=rng.integers(0,len(names),size=(config['bootstraps'],len(names)))
    real_boot,bootstrap,invalid=paired_bootstrap(np.asarray(bank),draws)
    if invalid:return dict(card='WC4',state='unsupported_cluster_resampling',support=p['support'],invalid_resamples=invalid,scientific_admission=False)
    effect=float(real.mean()-reference.mean());interval=np.quantile(bootstrap,[.025,.975]).tolist()
    mean=float(reference.mean());sd=float(reference.std(ddof=1));biased=abs(mean)>.25*sd if sd else mean!=0
    pv=float((1+sum(reference>=real.mean()))/(len(reference)+1))
    if biased:state='descriptive_only_biased_reference'
    elif interval[0]>0 and pv<.05:state='positive'
    elif interval[1]<0:state='negative'
    else:state='not_detected_sensitivity_unquantified'
    return dict(card='WC4',state=state,support=p['support'],properties=list(PROPERTIES),
                primary=dict(real_reliability=float(real.mean()),real_ci95=np.quantile(real_boot,[.025,.975]).tolist(),
                             real_minus_permutation_mean=effect,paired_writer_ci95=interval,
                             reference=dict(mean=mean,sd=sd,ci95=np.quantile(reference,[.025,.975]).tolist(),one_sided_p=pv,biased_reference=bool(biased))),
                profiles={w:dict(variances=variances[i].tolist(),ratios=ratio[i].tolist()) for i,w in enumerate(names)},
                feature_reliability=dict(zip(PROPERTIES,real.tolist())),split=p['split'],reference_feature_scores=fake.tolist(),scientific_admission=state in {'positive','negative'},
                inference='repeatability of relative observed variability, not identification of controlled goals or open-loop disturbances',
                sensitivity='not quantified at a useful effect until a separate instrument check',descriptive_probabilities_only=True)
