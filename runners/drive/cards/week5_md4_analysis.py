"""MD4/B1 equal-person mood-drift contrasts on an authenticated source.

DESIGN CHECK: whole-person uncertainty; the cohort is observational. A practical
null does not license an absence claim without sensitivity. Slopes are per
minute on the original unit mood scale, not normalized by observed effects.
"""
from __future__ import annotations
import json,time
from pathlib import Path
import numpy as np
import pandas as pd
from .week5_md4_source import save,sha

SEED=20261107
BAR=.002
CONDITIONS=('rest','visuomotor','random_gambling')

def load(inputs,config):
    path=Path(inputs['ratings']);receipt=json.loads((path.parent/'SOURCE.json').read_text('utf8'))
    if not receipt.get('complete') or receipt['ratings_sha256']!=sha(path):raise ValueError('incomplete or changed MD4 source')
    verified=json.loads((path.parent/'VERIFIED.json').read_text('utf8'))
    if not verified.get('verified') or not verified.get('all_values_checked'):raise ValueError('unverified MD4 source')
    if receipt.get('constructed')!=bool(config.get('constructed_fixture',False)):raise ValueError('constructed/source scope mismatch')
    return pd.read_parquet(path)

def slopes(frame,window=None,excluded_cohorts=(),independent=False):
    output=[];audit=dict(total_people=int(frame.person.nunique()),short_series=0,excluded_cohort_people=0)
    for person,data in frame.groupby('person',sort=True):
        if data.cohort.nunique()!=1 or data.condition.nunique()!=1:raise ValueError('ambiguous person condition')
        cohort=data.cohort.iloc[0];condition=data.condition.iloc[0]
        if condition not in CONDITIONS:raise ValueError('unknown condition')
        if cohort in excluded_cohorts:audit['excluded_cohort_people']+=1;continue
        data=data.sort_values('rating_order')
        if data.rating_order.duplicated().any():raise ValueError('duplicate rating key')
        if window is not None:data=data[data.minute<=window]
        x=data.minute.to_numpy(float);y=data.mood.to_numpy(float)
        if not np.isfinite(x+y).all() or (y<0).any() or (y>1).any():raise ValueError('invalid mood/time values')
        if len(x)<3 or np.ptp(x)<2:audit['short_series']+=1;continue
        if not np.all(np.diff(x)>0) or x[0]!=0:raise ValueError('nonincreasing or shifted first-block clock')
        if independent:
            b=float(np.linalg.lstsq(np.column_stack([np.ones(len(x)),x]),y,rcond=None)[0][1])
        else:
            xc=x-x.mean();b=float(xc@(y-y.mean())/(xc@xc))
        output.append(dict(person=person,cohort=cohort,condition=condition,slope=b,ratings=len(x),span_minutes=float(np.ptp(x))))
    return output,audit

def rule(interval,rest_interval,supported=True):
    if not supported or interval is None:return 'inconclusive'
    low,high=interval
    if low>BAR and rest_interval is not None and rest_interval[1]<0:return 'supports'
    if -BAR<=low and high<=BAR:return 'against'
    if high < -BAR:return 'against'
    return 'inconclusive'

def summarize(rows,draws=2000,seed=SEED,progress=None):
    values={c:np.array([r['slope'] for r in rows if r['condition']==c],dtype=float) for c in CONDITIONS}
    counts={c:len(v) for c,v in values.items()};rng=np.random.default_rng(seed)
    samples={c:np.empty(draws) for c,v in values.items() if len(v)>=2}
    for c in samples:
        v=values[c]
        for i in range(draws):
            samples[c][i]=float(v[rng.integers(0,len(v),len(v))].mean())
            if progress is not None:progress()
    def interval(v):return [float(x) for x in np.quantile(v,[.025,.975])]
    estimates={c:dict(people=counts[c],slope=float(v.mean()) if len(v) else None,
                      interval=interval(samples[c]) if c in samples else None) for c,v in values.items()}
    contrasts={}
    for name,a,b in [('visuomotor_minus_rest','visuomotor','rest'),('random_minus_rest','random_gambling','rest'),('visuomotor_minus_random','visuomotor','random_gambling')]:
        contrasts[name]=dict(estimate=float(values[a].mean()-values[b].mean()) if counts[a] and counts[b] else None,
                             interval=interval(samples[a]-samples[b]) if a in samples and b in samples else None)
    support=counts['rest']>=20 and counts['visuomotor']>=20
    primary=contrasts['visuomotor_minus_rest']
    cohorts={c:dict(people=sum(r['cohort']==c for r in rows),mean_slope=float(np.mean([r['slope'] for r in rows if r['cohort']==c]))) for c in sorted({r['cohort'] for r in rows})}
    return dict(conditions=estimates,contrasts=contrasts,cohorts=cohorts,draws=draws,seed=seed,
                primary_support=support,reading=rule(primary['interval'],estimates['rest']['interval'],support),
                minimum_effect_sensitivity_required_before_absence=True,
                scope='adult first-visit cohort-qualified persons; observational condition mix',
                uncertainty='whole persons resampled independently within condition; equal-person mean OLS slopes')

def analyse(frame,draws=2000,progress=None):
    primary,audit=slopes(frame);result=summarize(primary,draws,progress=progress)
    companions={}
    for label,window,excluded in [('common_five_minutes',5.,()),('without_feedback',None,('MotionFeedback',)),
                                 ('without_ordinal_ratings',None,('Numbers',))]:
        projected,counts=slopes(frame,window,excluded)
        companions[label]=dict(result=summarize(projected,draws,progress=progress),dispositions=counts)
    return dict(card='MD4',complete=True,primary=result,companions=companions,dispositions=audit,
                practical_bar_mood_units_per_minute=BAR,
                units='0–1 mood units per minute; multiply by100 for percentage-point slope',
                interpretation='Analyst-proposed interest proxy. Random gambling has no imposed learnability rank. Conditions and recruitment cohorts are confounded.',
                cross_cohort_identity='Sanitization removed platform links; different cohort codes are not asserted to be independently recruited people.',
                derivative='Derived from Jangraw et al. (2023), DOI10.1038/s41562-023-01519-7; acknowledgement to authors and NIMH.')

class RequestedYield(Exception):pass

def execute(output,inputs,config):
    draws=int(config.get('draws',2000))
    if draws!=2000 and not config.get('constructed_fixture'):raise ValueError('MD4 primary requires2000 whole-person draws')
    output=Path(output);frame=load(inputs,config);started=time.process_time();wall=time.monotonic();completed=0
    # Four fixed analyses, each up to three independent condition resamples.
    total=draws*sum(sum(sum(r['condition']==c for r in projected)>=2 for c in CONDITIONS)
                    for projected,_ in [slopes(frame),slopes(frame,5),slopes(frame,None,('MotionFeedback',)),slopes(frame,None,('Numbers',))])
    def progress():
        nonlocal completed
        completed+=1
        if completed%100:return
        record=dict(completed_condition_draws=completed,total_condition_draws=total,cpu_seconds=time.process_time()-started,
                    wall_seconds=time.monotonic()-wall)
        if completed>=max(1,total*.05) and not (output/'PILOT.json').exists():
            save(output/'PILOT.json',dict(record,forecast_cpu_seconds=record['cpu_seconds']*total/completed,basis='first100draw boundary at >=5% of all primary and companion condition draws'))
        if (output/'YIELD_REQUEST.json').exists():
            save(output/'CHECKPOINT.json',dict(record,restart_from_source_required=True));raise RequestedYield
    try:result=analyse(frame,draws,progress)
    except RequestedYield:return dict(status='yielded',reason='owner request',checkpoint='CHECKPOINT.json',restart_from_source_required=True)
    save(output/'SCIENCE.json',result);return dict(status='complete',card='MD4')

def verify(output,inputs,config):
    frame=load(inputs,config);expected=json.loads((Path(output)/'SCIENCE.json').read_text('utf8'))
    actual=analyse(frame,int(config.get('draws',2000)))
    if expected!=actual:raise ValueError('full MD4 replay mismatch')
    direct,_=slopes(frame,independent=True);normal,_=slopes(frame)
    if any(abs(a['slope']-b['slope'])>1e-11 for a,b in zip(direct,normal)) or len(direct)!=len(normal):raise ValueError('independent OLS mismatch')
    result=dict(verified=True,all_bootstrap_draws_recomputed=True,independent_person_OLS=True,people=len(direct))
    save(Path(output)/'VERIFIED.json',result);return result
