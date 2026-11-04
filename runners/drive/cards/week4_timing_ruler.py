"""Week4 per-writer timing ruler, separate from PP1's pooled instrument.

DESIGN CHECK: Week4 section0.5; LESSONS2-5 and PP1 source/mechanical rules
reviewed 2026-11-02. Known separated lognormal classes must recover ordering;
rescaling one writer's speed cannot alter posterior classes. Missing rulers,
nonconvergence and collapse stay explicit. This supplies no psychological
label or outcome contrast. Stops use 1-fast posterior, including long pauses.
"""
from pathlib import Path
from collections import Counter,defaultdict
import math,time
import numpy as np
from sklearn.mixture import GaussianMixture
from threadpoolctl import threadpool_limits
from .week3_pause_instrument import load
from .week3_pause_model import arrays,mechanics
from .timing_p6 import write_equal,gzip_equal,gzread
from .timing_census import read,filehash

SEED=20261102
CONFIG=dict(card='W4-timing-ruler',seed=SEED,expected_sessions=1399)

def fit_mixture(z):
    z=np.asarray(z,float)
    if len(z)<30 or not np.isfinite(z).all() or len(np.unique(z))<3:raise ValueError('Mixture lacks finite support')
    model=GaussianMixture(n_components=3,covariance_type='full',reg_covar=1e-6,tol=1e-4,max_iter=500,n_init=1,
        random_state=SEED,means_init=np.quantile(z,[.2,.65,.95]).reshape(3,1)).fit(z.reshape(-1,1))
    order=np.argsort(model.means_.ravel());means=model.means_.ravel()[order];weights=model.weights_[order]
    if not model.converged_ or np.any(np.diff(means)<=1e-6) or np.any(weights<=1e-6):raise ValueError('Mixture nonconvergence or collapse')
    return model.predict_proba(z.reshape(-1,1))[:,order],dict(log_means=means.tolist(),variances=model.covariances_.ravel()[order].tolist(),
        weights=weights.tolist(),iterations=int(model.n_iter_))

def writer_ruler(items):
    within=[r['corrected_log_seconds'] for r in items if r['location']=='within_word']
    if not within:return dict(state='unsupported',reason='No within-word ruler'),[]
    baseline=float(np.median(within));z=np.array([r['corrected_log_seconds']-baseline for r in items])
    try:posterior,fit=fit_mixture(z)
    except ValueError as error:return dict(state='invalid',reason=str(error)),[]
    records=[]
    for row,prob in zip(items,posterior):
        onset=row['target']=='single_character_insert' and row['location'] in ('before_word','before_sentence','before_paragraph')
        records.append({k:row[k] for k in ('session','ordinal','previous_ordinal','location','target','interval_seconds','seconds')}|
            dict(fast=float(prob[0]),hesitation=float(prob[1]),slowest=float(prob[2]),onset=onset,
                 stop=bool(onset and prob[0]<.5),break_interval=row['interval_seconds']>60))
    return dict(state='fitted',within_word_geometric_median_seconds=math.exp(baseline),mixture=fit,intervals=len(items)),records

def stretch_hesitancy(onsets):
    """First onset excluded; absent internal onsets remain unsupported."""
    inside=onsets[1:]
    if not inside:return dict(state='unsupported',hesitancy=None)
    if any(r['interval_seconds']>60 for r in inside):return dict(state='break',hesitancy=None)
    if any(not r['onset'] for r in inside):raise ValueError('Stretch supplied a non-onset interval')
    return dict(state='eligible',hesitancy=float(np.mean([1-r['fast'] for r in inside])))

def thirds(values):
    finite=np.asarray(values,float)
    if not len(finite) or not np.isfinite(finite).all():raise ValueError('Finite stretch values required')
    low,high=np.quantile(finite,[1/3,2/3])
    # Ties cannot put the same stretch into both arms. A degenerate split stays
    # middle; a later case check decides support without arbitrary tie breaking.
    if low==high:return ['middle']*len(values),[float(low),float(high)]
    return [('flow' if v<low else 'hesitant' if v>high else 'middle') for v in finite],[float(low),float(high)]

def compute(rows):
    mechanical={};details={}
    with threadpool_limits(limits=1):
        for genre in ('argumentative','creative'):
            selected=[r for r in rows if r['genre']==genre]
            coefficient,fit=mechanics(arrays(selected));mechanical[genre]=coefficient;details[genre]=fit
        groups=defaultdict(list)
        for row in rows:
            for item in row['intervals']:
                groups[row['writer']].append(dict(item,session=row['session'],
                    corrected_log_seconds=math.log(item['interval_seconds'])-mechanical[row['genre']]*int(item['next_upper_or_punctuation'])))
        writer_models={};sessions={r['session']:[] for r in rows}
        for writer,items in sorted(groups.items()):
            model,records=writer_ruler(items);writer_models[writer]=model
            for r in records:sessions[r['session']].append(r)
    roster=[{k:r[k] for k in ('session','writer','prompt','timestamp','genre','session_order')} for r in rows]
    summary=dict(sessions=len(rows),writers=len(groups),fit_states=dict(Counter(r['state'] for r in writer_models.values())),
        represented_intervals=sum(map(len,sessions.values())),source_intervals=sum(len(r['intervals']) for r in rows),
        normalization='Per-writer within-word geometric median after separately fitted genre PP1 mechanical correction.',
        readout='Ordered per-writer mixture posteriors; no psychological component identification or scientific effect.',scientific_admission=False)
    return summary,dict(mechanical_by_genre=mechanical,mechanical_fits=details,writers=writer_models),roster,sessions

def run(output,inputs,config,verification=False):
    if config!=CONFIG:raise ValueError('Frozen timing-ruler configuration required')
    start=time.process_time();rows=load(inputs,'corpus');summary,models,roster,sessions=compute(rows)
    if len(rows)!=config['expected_sessions']:raise ValueError('Source population changed')
    binding={k:filehash(v) for k,v in inputs.items()};output=Path(output)
    values={'SUMMARY.json':summary,'PRIVATE_MODELS.json':models,'PRIVATE_ROSTER.json':roster,'BINDING.json':binding}
    if verification:
        for key,value in values.items():
            if read(output/key)!=value:raise ValueError('Timing ruler replay differs: '+key)
        if gzread(output/'INTERVALS.json.gz')!=sessions:raise ValueError('Timing posterior replay differs')
        return dict(verified=True,full_source_model_replay=True)
    for key,value in values.items():write_equal(output/key,value)
    gzip_equal(output/'INTERVALS.json.gz',sessions)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start))
    return dict(status='complete',scientific_admission=False)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

def known_items(scale=1):
    rng=np.random.default_rng(SEED);z=np.r_[rng.normal(-2,.15,240),rng.normal(0,.15,120),rng.normal(2,.15,60)]
    return [dict(session='fixture',ordinal=i,previous_ordinal=i-1,location='within_word' if i<200 else 'before_word',
        target='single_character_insert',interval_seconds=float(np.exp(t)*scale),seconds=float(i),corrected_log_seconds=float(t+math.log(scale))) for i,t in enumerate(z)]
