"""Joint own/donor coefficients with paired real-writer cluster uncertainty.

DESIGN CHECK: LESSONS3-5, October18. Independent planted own and donor signals
recover their signs. Null and reversal remain visible. Collinear focal terms
refuse, while redundant nuisance columns preserve their exact column span.
Every outcome/surprise control retains the same rows, with200 fixed within-
writer permutations. Missing fits suppress p values; no successful-only tail.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
from scipy.optimize import minimize_scalar

from . import states_v2 as states
from .timing_census import read,filehash
from .timing_p6 import write_equal
from .timing_stats import sufficient

NAMES=('own_surprise','donor_surprise','intercept','population_surprisal','length','log_frequency',
       'sentence_start','after_punctuation','on_screen','session_surprisal')


def design(rows,original_own=False):
    x=np.asarray([[r['original_personal_surprise'] if original_own else r['own_surprise'],r['donor_surprise'],1.,
        r['population_surprisal'],r['length'],r['log_frequency'],r['sentence_start'],r['after_punctuation'],
        r['on_screen'],r['session_surprisal']] for r in rows],float)
    y=np.asarray([r['log_pause'] for r in rows],float)
    writers=np.asarray([r['writer'] for r in rows])
    if x.ndim!=2 or x.shape[1]!=len(NAMES) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('invalid supported design')
    return x,y,writers


def basis(groups):
    xx=sum(g['xx'] for g in groups)
    scale=np.sqrt(np.maximum(np.diag(xx),1e-30));standard=xx/np.outer(scale,scale)
    keep=[];omitted=[]
    # Preserve the nuisance column span, in declared column order. Never choose
    # among collinear focal terms by silently dropping the less convenient one.
    for j in range(2,len(xx)):
        if xx[j,j]>1e-10 and np.linalg.matrix_rank(standard[np.ix_(keep+[j],keep+[j])],tol=1e-9)>len(keep):keep.append(j)
        else:omitted.append(NAMES[j])
    for j in (1,0):
        if xx[j,j]<=1e-10:
            if j==0:raise ValueError('own-history coefficient has no support')
            omitted.append(NAMES[j]);continue
        if np.linalg.matrix_rank(standard[np.ix_(keep+[j],keep+[j])],tol=1e-9)<=len(keep):
            raise ValueError('focal own/donor coefficient not separately identifiable')
        keep.append(j)
    return sorted(keep),omitted


def fit(groups):
    keep,omitted=basis(groups)
    xx=sum(g['xx'] for g in groups);xy=sum(g['xy'] for g in groups);yy=sum(g['yy'] for g in groups)
    n=sum(g['n'] for g in groups)
    def solve(ratio):
        a,b,c=xx.copy(),xy.copy(),yy
        if ratio:
            for g in groups:
                weight=ratio/(1+g['n']*ratio)
                a-=weight*np.outer(g['sx'],g['sx']);b-=weight*g['sx']*g['sy'];c-=weight*g['sy']**2
        a,b=a[np.ix_(keep,keep)],b[keep];scale=np.sqrt(np.maximum(np.diag(a),1e-30));s=a/np.outer(scale,scale)
        if np.linalg.matrix_rank(s,tol=1e-9)!=len(keep):raise ValueError('bootstrap joint design not identifiable')
        beta=np.linalg.solve(s,b/scale)/scale;rss=max(c-float(beta@b),np.finfo(float).tiny)
        return n*np.log(rss/n)+sum(np.log1p(g['n']*ratio) for g in groups),beta
    optimum=minimize_scalar(lambda r:solve(float(np.exp(r)))[0],bounds=(-15,15),method='bounded',options={'xatol':1e-5})
    if not optimum.success or not math.isfinite(float(optimum.x)) or not math.isfinite(float(optimum.fun)):
        raise ValueError('random-intercept variance optimization failed or was nonfinite')
    ratio=float(np.exp(optimum.x))
    interior,boundary=solve(ratio)[0],solve(0.)[0]
    if not math.isfinite(interior) or not math.isfinite(boundary):
        raise ValueError('random-intercept variance objective was nonfinite')
    if interior>=boundary:ratio=0.
    _,beta=solve(ratio);coefficients={NAMES[j]:float(beta[k]) for k,j in enumerate(keep)}
    return dict(own=coefficients['own_surprise'],donor=coefficients.get('donor_surprise'),
        own_minus_donor=coefficients['own_surprise']-coefficients['donor_surprise'] if 'donor_surprise' in coefficients else None,
        variance_ratio=ratio,omitted_columns=omitted,coefficients=coefficients)


def interval(effect,draws):
    if effect is None or any(x is None for x in draws):return dict(state='invalid',reason='coefficient undefined in point or bootstrap fit')
    a=np.asarray(draws,float)
    if not len(a) or not np.isfinite(a).all():return dict(state='invalid',reason='nonfinite or absent paired bootstrap')
    low,high=map(float,np.quantile(a,[.025,.975]));se=0. if np.ptp(a)==0 else float(a.std(ddof=1))
    z=effect/se if se else None
    return dict(effect=effect,ci_low=low,ci_high=high,bootstrap_se=se,z=z,
        approximate_two_sided_wald_p=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None,
        state=states.contrast_state(effect,low,high),bootstrap_draws=len(draws),
        uncertainty='paired real-writer percentile bootstrap; joint regression refit; frozen calibrated histories')


def null_summary(values,observed):
    valid=np.asarray([v for v in values if v is not None],float);missing=len(values)-len(valid)
    result=dict(attempted=len(values),valid_draws=len(valid),invalid_draws=missing,
        state='invalid' if missing or not len(valid) else 'descriptive',one_sided_p=None)
    if len(valid):
        mean=float(valid.mean());sd=0. if np.ptp(valid)==0 else float(valid.std(ddof=1))
        lo,hi=map(float,np.quantile(valid,[.025,.975]))
        result.update(mean=mean,sd=sd,q025=lo,q975=hi,bias_flag=abs(mean)>.25*sd if sd else mean!=0.)
        if not missing and observed is not None:result['one_sided_p']=(1+int((valid>=observed).sum()))/(len(valid)+1)
    if missing:result['reason']='undefined fixed control fits retained; no successful-only p or redraw'
    return result


def run(rows,*,draws=2000,permutations=200,seed=20261018,checkpoint=None,checkpoint_callback=None):
    designs={arm:design(rows,arm=='original_own_sensitivity') for arm in ('primary','original_own_sensitivity')}
    writers=sorted(set(designs['primary'][2]));groups={k:sufficient(*v) for k,v in designs.items()}
    if len(writers)<3:return dict(state='invalid',reason='fewer than three supported real writers')
    points={}
    for arm,g in groups.items():
        try:points[arm]=fit(g)
        except ValueError as exc:
            if arm=='primary':return dict(state='invalid',reason=str(exc))
            points[arm]=dict(own=None,donor=None,own_minus_donor=None,reason=str(exc),state='invalid')
    config=dict(draws=draws,permutations=permutations,seed=seed)
    binding=hashlib.sha256(json.dumps(dict(rows=rows,config=config),sort_keys=True,allow_nan=False).encode()).hexdigest()
    root=Path(checkpoint) if checkpoint is not None else None
    samples=[];controls=[];rng=np.random.default_rng(seed);started=time.monotonic()
    # Interleave all inference workloads in ten blocks so the first tenth is
    # measured on both models, paired resampling and both control families.
    if draws%10 or permutations%10:raise ValueError('inference workload must divide into ten fixed blocks')
    for block in range(10):
        selected=[rng.integers(0,len(writers),len(writers)) for _ in range(draws//10)]
        # Independent deterministic control streams; no RNG consumption depends
        # on support, checkpoint reuse or a fit's success.
        source_rng=np.random.default_rng(np.random.SeedSequence([seed,block,1]))
        outcome_rng=np.random.default_rng(np.random.SeedSequence([seed,block,2]))
        path=root/f'block-{block:02}.json' if root is not None else None
        if path is not None and path.exists():
            value=read(path);seal=read(path.with_suffix('.receipt.json'))
            if seal['sha256']!=filehash(path) or value['binding']!=binding or value['block']!=block:
                raise ValueError('supported inference checkpoint binding differs')
            if len(value['samples'])!=draws//10 or len(value['controls'])!=permutations//10:
                raise ValueError('supported inference checkpoint size differs')
        else:
            unit_start=time.monotonic();b=[];c=[]
            for ids in selected:
                item={}
                for arm,g in groups.items():
                    try:item[arm]=fit([g[j] for j in ids]) if points[arm]['own'] is not None else points[arm]
                    except ValueError as exc:
                        if arm=='primary':return dict(state='invalid',reason='undefined bootstrap fit: '+str(exc))
                        item[arm]=dict(own=None,donor=None,own_minus_donor=None,reason=str(exc),state='invalid')
                b.append(item)
            x,y,w=designs['primary']
            for _ in range(permutations//10):
                shuffled_x=x.copy();shuffled_y=y.copy()
                for writer in writers:
                    ix=np.flatnonzero(w==writer)
                    shuffled_x[ix,0]=source_rng.permutation(x[ix,0]);shuffled_y[ix]=outcome_rng.permutation(y[ix])
                item={}
                for name,xx,yy in [('own_surprise',shuffled_x,y),('outcome',x,shuffled_y)]:
                    try:item[name]=dict(effect=fit(sufficient(xx,yy,w))['own'],reason=None)
                    except ValueError as exc:item[name]=dict(effect=None,reason=str(exc))
                c.append(item)
            value=dict(binding=binding,block=block,samples=b,controls=c)
            if path is not None:
                write_equal(path,value);write_equal(path.with_suffix('.receipt.json'),dict(sha256=filehash(path),seconds=time.monotonic()-unit_start))
        samples.extend(value['samples']);controls.extend(value['controls'])
        if checkpoint_callback is not None:
            response=checkpoint_callback(dict(blocks=block+1,total_blocks=10,completed_draws=len(samples),
                completed_permutations=len(controls),fit_seconds=time.monotonic()-started,
                measured_block_seconds=sum(read(p)['seconds'] for p in root.glob('block-*.receipt.json')) if root is not None else time.monotonic()-started))
            if response:return dict(status='yielded',completed_blocks=block+1,total_blocks=10)
    result=dict(state='complete',writers=len(writers),observations=len(rows),config=config,point_fits=points)
    for arm,point in points.items():
        result[arm]={k:interval(point[k],[v[arm][k] for v in samples]) for k in ('own','donor','own_minus_donor')}
    result['controls']={name:null_summary([c[name]['effect'] for c in controls],points['primary']['own']) for name in ('own_surprise','outcome')}
    result['control_fit_failures']={name:[dict(draw=i,reason=c[name]['reason']) for i,c in enumerate(controls) if c[name]['effect'] is None] for name in ('own_surprise','outcome')}
    return result
