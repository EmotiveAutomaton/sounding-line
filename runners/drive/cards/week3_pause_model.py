"""PP1 three-component timing instrument and exact crossed-model contrasts.

DESIGN CHECK: LESSONS 3-5 and Week3 PP1, 2026-10-25. Middle-component
probability, not a fixed pause threshold, is the target. A mechanical capital
effect alone must be removed by the mid-sentence calibration. Writer speed is
normalized inside every bootstrap. Mixture nonconvergence, missing mechanical
support and nonidentifiable contrasts refuse; no successful-only inference.
"""
from collections import defaultdict
import math

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from sklearn.mixture import GaussianMixture
from threadpoolctl import threadpool_limits

from . import crossed_reml_certified as certified
from . import crossed_reml_stable as crossed
from .week3_pause_inputs import LOCATIONS

SEED = 20261026
CONTRASTS = ('sentence_minus_word', 'paragraph_minus_sentence', 'revision_minus_sentence')


def arrays(rows):
    """No genre pooling; writers without a within-word ruler stay disclosed."""
    genres = {r['genre'] for r in rows}
    if len(genres) != 1:
        raise ValueError('PP1 genres must be analyzed separately')
    bases = defaultdict(list)
    for row in rows:
        for x in row['intervals']:
            if x['location']=='within_word': bases[row['writer']].append(math.log(x['interval_seconds']))
    baselines = {w:float(np.median(v)) for w,v in sorted(bases.items())}
    records = [(r,x) for r in rows if r['writer'] in baselines for x in r['intervals'] if x['location'] in LOCATIONS]
    if not records:
        raise ValueError('PP1 has no supported typed intervals')
    y = np.array([math.log(x['interval_seconds'])-baselines[r['writer']] for r,x in records])
    return dict(log_interval=y, raw_interval=np.array([x['interval_seconds'] for r,x in records]), location=np.array([x['location'] for r,x in records]),
                mechanical=np.array([int(x['next_upper_or_punctuation']) for r,x in records],float),
                training=np.array([x['mechanical_training'] for r,x in records],bool),
                time=np.array([x['seconds']/60 for r,x in records]),
                order=np.array([r['session_order'] for r,x in records],float),
                writers=[r['writer'] for r,x in records], prompts=[r['prompt'] for r,x in records],
                session=[r['session'] for r,x in records], baselines=baselines,
                excluded_writers=sorted({r['writer'] for r in rows}-set(baselines)),
                genre=next(iter(genres)))


def full_fit(x,y,writers,prompts):
    """Recover every fixed coefficient from the certified exact GLS solution."""
    x=np.asarray(x,float)
    fit=certified.fit(x,y,writers,prompts)
    p=crossed.prepare(x,y,writers,prompts)
    d=np.sqrt(np.r_[np.repeat(fit['writer_variance_ratio'],p['writer_levels']),np.repeat(fit['marker_variance_ratio'],p['marker_levels'])])
    diagonal=sparse.diags(d,format='csc')
    factor=splu(sparse.eye(len(d),format='csc')+diagonal@p['ztz']@diagonal)
    u=d[:,None]*p['zth']; cross=p['hth']-u.T@factor.solve(u)
    scaled=np.linalg.solve(cross[:-1,:-1],cross[:-1,-1])
    beta=np.full(x.shape[1],np.nan)
    keep=p['kept_columns']; beta[keep]=scaled[:-1]/x.std(0)[keep]
    if not np.isclose(beta[0],fit['effect'],rtol=1e-10,atol=1e-12):
        raise ValueError('PP1 full fixed-effect reconstruction differs')
    return beta,fit


def mechanics(a):
    ids=np.flatnonzero(a['training'])
    if not len(ids) or len(np.unique(a['mechanical'][ids])) != 2:
        raise ValueError('mid-sentence mechanical indicator lacks both levels')
    x=np.column_stack([a['mechanical'][ids], a['location'][ids]=='before_word', a['time'][ids], a['order'][ids]])
    b,fit=full_fit(x,a['log_interval'][ids],[a['writers'][i] for i in ids],[a['prompts'][i] for i in ids])
    return float(b[0]),fit


def mixture(z):
    z=np.asarray(z,float)
    if len(z)<30 or not np.isfinite(z).all() or len(np.unique(z))<3:
        raise ValueError('three-component lognormal mixture lacks support')
    model=GaussianMixture(n_components=3,covariance_type='full',reg_covar=1e-6,tol=1e-4,max_iter=500,n_init=1,random_state=SEED,
                          means_init=np.quantile(z,[.2,.65,.95]).reshape(3,1))
    model.fit(z.reshape(-1,1))
    if not model.converged_:
        raise ValueError('three-component lognormal mixture did not converge')
    order=np.argsort(model.means_.ravel())
    means=model.means_.ravel()[order]; variances=model.covariances_.ravel()[order]; weights=model.weights_[order]
    if np.any(np.diff(means)<=1e-6) or np.any(weights<=1e-6):
        raise ValueError('three-component mixture collapsed')
    posterior=model.predict_proba(z.reshape(-1,1))[:,order]
    summary=dict(log_means=means.tolist(),log_variances=variances.tolist(),weights=weights.tolist(),
                 relative_median_durations=np.exp(means).tolist(),relative_mean_durations=np.exp(means+variances/2).tolist(),iterations=int(model.n_iter_),
                 normalization='ratio to writer within-word geometric median after global mechanical correction')
    return posterior,summary


def model(rows):
    a=arrays(rows)
    with threadpool_limits(limits=1):
        mechanical,mechanical_fit=mechanics(a)
        corrected=a['log_interval']-mechanical*a['mechanical']
        posterior,mix=mixture(corrected)
        loc=a['location']
        x=np.column_stack([loc=='before_sentence',loc=='before_paragraph',loc=='before_revision',loc=='within_word',a['mechanical'],a['time'],a['order']])
        beta,fit=full_fit(x,posterior[:,1],a['writers'],a['prompts'])
    if not np.isfinite(beta[:3]).all():
        raise ValueError('PP1 required boundary contrast absent')
    contrasts=dict(sentence_minus_word=float(beta[0]),paragraph_minus_sentence=float(beta[1]-beta[0]),revision_minus_sentence=float(beta[2]-beta[0]))
    locations={}
    for name in LOCATIONS:
        ix=loc==name
        slow=posterior[ix,1]; durations=np.exp(corrected[ix])
        locations[name]=dict(intervals=int(ix.sum()),hesitation_probability=float(slow.mean()) if ix.any() else None,
                             disengagement_probability=float(posterior[ix,2].mean()) if ix.any() else None,
                             slow_component_mean_seconds=float(slow@a['raw_interval'][ix]/slow.sum()) if slow.sum()>0 else None,
                             slow_component_mean_relative_duration=float(slow@durations/slow.sum()) if slow.sum()>0 else None)
    return dict(genre=a['genre'],intervals=len(corrected),writers=len(set(a['writers'])),prompts=len(set(a['prompts'])),
                excluded_writers_without_within_word=a['excluded_writers'],writer_log_baselines=a['baselines'],
                mechanical_coefficient=mechanical,mechanical_fit=mechanical_fit,mixture=mix,location_summary=locations,
                crossed_fit=fit,contrasts=contrasts)


def writer_resample(rows,indices):
    writers=sorted({r['writer'] for r in rows})
    groups={w:[r for r in rows if r['writer']==w] for w in writers}
    return [dict(r,writer=f'copy-{i}',session=f'copy-{i}:{r["session"]}') for i,j in enumerate(indices) for r in groups[writers[int(j)]]]


def profile_rows(rows,mechanical):
    """Equal-session log-duration ratios; typing-speed subtraction cancels.

    No writer's other half enters a session feature. These descriptive duration
    profiles are distinct from the middle-posterior primary instrument.
    """
    result=[]
    for row in rows:
        levels=defaultdict(list)
        for x in row['intervals']:
            if x['location'] in LOCATIONS:
                levels[x['location']].append(math.log(x['interval_seconds'])-mechanical*int(x['next_upper_or_punctuation']))
        baseline=float(np.mean(levels['within_word'])) if levels['within_word'] else None
        values=[float(np.mean(levels[k]))-baseline if levels[k] and baseline is not None else None for k in LOCATIONS[1:]]
        result.append({k:row[k] for k in ('session','writer','prompt','timestamp','genre')} | dict(features={'PP1.duration_hierarchy':values},accepted_share=0.))
    return result
