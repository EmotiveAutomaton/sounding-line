"""Complete TR4 contrasts and reference banks; import has no corpus side effects.

DESIGN CHECK: LESSONS 3-5 and CONTROLS read 2026-10-27. Equal-share NULL
has zero paired gain; ALTERNATIVE persistent change rewards adaptation.
Undefined rank reliability is unsupported, never zero. All references rebuild
fitted state and paired uncertainty resamples the same real writers in every arm.
"""
from collections import defaultdict
import time
import numpy as np
from scipy.stats import rankdata
from . import week3_tr4_models as m

CLASSES=('accept','edit','dismiss','ignore')
SEED=20261026


def prepare(census):
    rows=census['rows']; by=defaultdict(list); seen=set()
    for r in rows:
        if r['session'] in seen: raise ValueError('duplicate session')
        seen.add(r['session']); by[r['writer']].append(r)
        if r['half'] not in ('discovery','test'): raise ValueError('unrecognized split')
        if not np.isfinite([r['start'],r['end']]).all() or r['end']<r['start']:
            raise ValueError('invalid session interval')
        m.counts([r['counts'][c] for c in CLASSES])
    split=census['split']
    if split['seed']!=SEED or split['session_counts']!={w:len(v) for w,v in by.items()} or set(split['writers'])!=set(by):
        raise ValueError('frozen split population differs')
    if any(r['half']!=split['writers'][r['writer']] for r in rows): raise ValueError('frozen split assignment differs')
    groups=[]; retained=[]
    for writer,source in sorted(by.items()):
        source=sorted(source,key=lambda r:(r['start'],r['session']))
        if len({r['half'] for r in source})!=1: raise ValueError('writer crosses frozen split')
        data=np.asarray([[r['counts'][c] for c in CLASSES] for r in source],dtype=np.int64)
        strict=True; observed=0; eligible=len(source)>=12; mask=[]
        for i,r in enumerate(source):
            if i and source[i-1]['end']>=r['start']: strict=False
            reason=('below_twelve_sessions' if not eligible else 'ambiguous_prefix' if not strict
                    else 'before_last_third' if i<2*len(source)//3 else 'missing_target'
                    if not data[i].sum() else 'missing_history' if not observed else None)
            mask.append(reason is None)
            retained.append(dict(session=r['session'],writer=writer,reason=reason,scoreable=reason is None))
            observed+=bool(data[i].sum())
        half=len(source)//2
        rel=eligible and strict and all(np.count_nonzero(x.sum(axis=1))>=2 for x in (data[:half],data[half:]))
        groups.append(dict(writer=writer,half=source[0]['half'],rows=source,data=data,
                           mask=np.asarray(mask),reliability=bool(rel)))
    if len(retained)!=len(rows): raise ValueError('census coverage differs')
    return groups,retained


def tune(groups):
    totals={key:[] for key in ('rate','hazard')}
    for g in groups:
        if g['half']!='discovery' or not g['mask'].any(): continue
        e=[np.full(4,.25) for _ in m.RATES]; cp=[m.ChangePoint(h) for h in m.HAZARDS]
        el=[]; cl=[]; n=0
        for x,use in zip(g['data'],g['mask']):
            if use:
                el.append([m.log_loss(x,p) for p in e]); cl.append([m.log_loss(x,c.predict()) for c in cp])
            if x.sum():
                p=m.shares(x); e=[p.copy() if not n else (1-a)*v+a*p for a,v in zip(m.RATES,e)]; n+=1
            for c in cp: c.update(x)
        totals['rate'].append(np.mean(el,axis=0)); totals['hazard'].append(np.mean(cl,axis=0))
    if not totals['rate']: raise ValueError('no supported discovery writers')
    means={k:np.mean(v,axis=0) for k,v in totals.items()}
    return dict(rate=m.RATES[int(np.argmin(means['rate']))],hazard=m.HAZARDS[int(np.argmin(means['hazard']))],
                discovery_writers=len(totals['rate']),losses={k:v.tolist() for k,v in means.items()})


def primary(g,data=None,all_models=False,parameters=None):
    data=g['data'] if data is None else data
    if all_models:
        model=m.SixForecasts(parameters['rate'],parameters['hazard']); names=m.NAMES
    else:
        model=m.GaussianBank(); total=np.zeros(4); n=0; names=('whole','kalman')
    losses=[]
    for x,use in zip(data,g['mask']):
        if all_models: p,_=model.predict()
        else: p=dict(whole=total/n if n else np.full(4,.25),kalman=model.predict()[0])
        if use: losses.append([m.log_loss(x,p[k]) for k in names])
        model.update(x)
        if not all_models and x.sum(): total+=m.shares(x); n+=1
    if not losses: return None
    means=dict(zip(names,np.mean(losses,axis=0).tolist()))
    return dict(losses=means,gain=means['whole']-means['kalman'],sessions=len(losses))


def variance(data):
    model=m.GaussianBank()
    for x in data: model.update(x)
    return float(model.grid[int(np.argmax(model.likelihood))])


def profile(data):
    j=len(data)//2
    return [variance(data[:j]),variance(data[j:])]


def correlations(profiles):
    """Spearman along the penultimate (writer) axis, including repeated draws."""
    a=np.asarray(profiles,float)
    if a.shape[-2]<3: return np.full(a.shape[:-2],np.nan)
    ranks=rankdata(a,axis=-2); ranks-=ranks.mean(axis=-2,keepdims=True)
    cross=np.sum(ranks[...,0]*ranks[...,1],axis=-1)
    denom=np.sqrt(np.sum(ranks[...,0]**2,axis=-1)*np.sum(ranks[...,1]**2,axis=-1))
    return np.divide(cross,denom,out=np.full(cross.shape,np.nan),where=denom>0)


def finite(value):
    x=float(value); return x if np.isfinite(x) else None


def distribution(values):
    a=np.asarray(values,float); ok=np.isfinite(a)
    d=dict(total=int(a.size),undefined=int((~ok).sum()),supported=bool(a.size and ok.all()))
    if not d['supported']: return dict(d,mean=None,sd=None,interval=None)
    return dict(d,mean=float(a.mean()),sd=float(a.std(ddof=1)) if len(a)>1 else 0.,
                interval=np.quantile(a,[.025,.975]).tolist())


def paired_uncertainty(real,fakes,bootstraps,seed=SEED):
    real=np.asarray(real,float); fakes=np.asarray(fakes,float); n=len(real)
    # Any undefined reference invalidates that draw; none are silently dropped.
    real_r=finite(correlations(real)); fake_r=correlations(fakes)
    reference=distribution(fake_r)
    delta=real_r-reference['mean'] if real_r is not None and reference['supported'] else None
    draws=[]; rng=np.random.default_rng(seed)
    for _ in range(0,bootstraps,32):
        indices=rng.integers(n,size=(min(32,bootstraps-len(draws)),n)) if n else np.empty((min(32,bootstraps-len(draws)),0),int)
        a=correlations(real[indices]); b=correlations(fakes[:,indices]).mean(axis=0)
        draws.extend((a-b).tolist())
    return dict(real=real_r,reference=reference,real_minus_reference=delta,
                paired_bootstrap=distribution(draws),
                probability=(1+int(np.sum(fake_r>=real_r)))/(len(fake_r)+1) if delta is not None else None)


def outcome_shuffle(g,rng):
    x=g['data'].copy(); inds=np.flatnonzero(x.sum(axis=1)); x[inds]=x[rng.permutation(inds)]
    return x


def reassigned(groups,rng):
    data=[g['data'].copy() for g in groups]; pools=defaultdict(list)
    for i,g in enumerate(groups):
        for j,r in enumerate(g['rows']):
            if g['data'][j].sum(): pools[r['prompt']].append((i,j))
    for slots in pools.values():
        for target,source in zip(slots,rng.permutation(len(slots))):
            i,j=target; a,b=slots[int(source)]; data[i][j]=groups[a]['data'][b]
    return data


def run_analysis(census,outcome_repetitions=200,label_repetitions=1000,bootstraps=2000,progress=None):
    if min(outcome_repetitions,label_repetitions,bootstraps)<1: raise ValueError('positive reference sizes required')
    tick=time.process_time(); timings={}; groups,retained=prepare(census); parameters=tune(groups)
    test=[g for g in groups if g['half']=='test' and g['mask'].any()]
    measured=[dict(writer=g['writer'],**primary(g,all_models=True,parameters=parameters)) for g in test]
    gains=np.asarray([v['gain'] for v in measured]); estimate=float(gains.mean()) if len(gains) else None
    timings['forecasts']=time.process_time()-tick; tick=time.process_time()
    rng=np.random.default_rng(SEED); null=[]
    for i in range(outcome_repetitions):
        values=[primary(g,outcome_shuffle(g,rng))['gain'] for g in test]
        null.append(float(np.mean(values)) if values else float('nan'))
        if progress: progress('outcome-reference',i+1,outcome_repetitions)
    timings['outcome']=time.process_time()-tick; tick=time.process_time()
    rel_indices=[i for i,g in enumerate(groups) if g['half']=='test' and g['reliability']]
    real=np.asarray([profile(groups[i]['data']) for i in rel_indices],float).reshape(-1,2)
    full_q=[variance(groups[i]['data']) for i in rel_indices]
    timings['profiles']=time.process_time()-tick; tick=time.process_time()
    rng=np.random.default_rng(SEED); fake=[]
    for i in range(label_repetitions):
        data=reassigned(groups,rng); fake.append([profile(data[j]) for j in rel_indices])
        if progress: progress('label-reference',i+1,label_repetitions)
    fake=np.asarray(fake,float).reshape(label_repetitions,len(rel_indices),2)
    timings['labels']=time.process_time()-tick; tick=time.process_time()
    reliability=paired_uncertainty(real,fake,bootstraps)
    rng=np.random.default_rng(SEED)
    bootstrap=[float(gains[rng.integers(len(gains),size=len(gains))].mean()) for _ in range(bootstraps)] if len(gains)>=2 else [float('nan')]*bootstraps
    reference=distribution(null); uncertainty=distribution(bootstrap)
    biased=(abs(reference['mean'])>.25*reference['sd']) if reference['supported'] else None
    probability=(1+int(np.sum(np.asarray(null)>=estimate)))/(outcome_repetitions+1) if estimate is not None and reference['supported'] else None
    timings['uncertainty']=time.process_time()-tick
    status=('unsupported' if estimate is None or not uncertainty['supported'] or not reference['supported'] else
            'descriptive_only_biased_reference' if biased else 'positive' if uncertainty['interval'][0]>0 and probability<.05 else
            'negative' if uncertainty['interval'][1]<0 else 'not_detected_sensitivity_unestablished')
    result=dict(parameters=parameters,retained=retained,writer_losses=measured,
                primary=dict(estimate=estimate,writers=len(gains),bootstrap=uncertainty,reference=reference,
                             reference_biased=biased,probability=probability,status=status),
                reliability=dict(**reliability,writers=[groups[i]['writer'] for i in rel_indices],
                                 profiles=real.tolist(),full_variances=full_q),
                outcome_reference=[finite(x) for x in null],label_profiles=fake.tolist(),
                counts=dict(all_sessions=len(retained),all_writers=len(groups),scoreable_test_sessions=sum(v['sessions'] for v in measured)),
                descriptive=True)
    return result,timings
