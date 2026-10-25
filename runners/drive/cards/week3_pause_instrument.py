"""PP1 complete instrument, full-refit writer uncertainty and profile controls.

DESIGN CHECK: the source exclusions, mechanical ruler and three components
remain identical under every bootstrap. Unfit draws refuse rather than vanish.
Identification uses independent donor/probe/gallery writer roles from WA0.h1;
identical features tie, and a context-only signal cannot acquire person credit.
All final numerical objects are reconstructed from source in fresh verification.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

from . import week3_pause_model as model
from . import week3_identification as identification
from . import week3_identification_crossfit as crossfit
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal
from .week3_pieces_coverage import authenticated
from runners.stage14.common import atomic

CONFIG = dict(mode='corpus',seed=model.SEED,bootstrap_draws=2000,permutations=1000)


def configuration(config):
    if set(config)!=set(CONFIG) or config['mode'] not in {'corpus','constructed'} or config['seed']!=model.SEED:
        raise ValueError('frozen PP1 instrument configuration required')
    if any(type(config[k]) is not int or config[k]<2 for k in ('bootstrap_draws','permutations')):
        raise ValueError('PP1 positive complete controls required')
    if config['mode']=='corpus' and config!=CONFIG:
        raise ValueError('full PP1 bootstrap and empirical null counts required')


def load(inputs,mode):
    if set(inputs)!={'input_complete','intervals','input_result','input_binding'}:
        raise ValueError('exact completed PP1 inputs required')
    for key in ('intervals','input_result','input_binding'):
        authenticated(inputs['input_complete'],inputs[key])
    binding=read(inputs['input_binding'])
    for path,digest in binding['original_source_bindings'].items():
        if filehash(path)!=digest: raise ValueError('PP1 original source changed')
    rows=gzread(inputs['intervals']); summary=read(inputs['input_result'])
    if mode=='corpus' and (binding.get('config',{}).get('mode')!='corpus' or summary.get('sessions')!=1399 or summary.get('card')!='PP1-inputs'):
        raise ValueError('corpus PP1 requires the full authenticated canonical input census')
    if len(rows)!=summary['sessions'] or len({r['session'] for r in rows})!=len(rows):
        raise ValueError('PP1 prepared census differs')
    if {r['genre'] for r in rows}!={'creative','argumentative'}:
        raise ValueError('PP1 requires both separately analyzed genres')
    return rows


def json_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def profile_controls(rows,mechanical,config,checkpoint):
    features=model.profile_rows(rows,mechanical)
    x,slices=identification.feature_matrix(features)
    writers,groups,halves,excluded=identification.split(features)
    profiles=identification.means(x,groups,writers)
    summaries,detail=crossfit.analyze_group(features,config,checkpoint=lambda fold,done,total:checkpoint('identification-fold-'+str(fold),done,total))
    reliability=identification.pmap.reliability(profiles[:,0,:],profiles[:,1,:],list(model.LOCATIONS[1:]))
    return dict(definition='equal-session mean log geometric-duration ratio to within-word, after frozen global mechanical adjustment; writer typing-speed normalization cancels exactly',
                primary_instrument=False,results=summaries,reliability=reliability,halves=halves,excluded=excluded,
                writer_profiles={w:[[None if not np.isfinite(v) else float(v) for v in part] for part in profiles[i]] for i,w in enumerate(writers)}),detail


def genre_analysis(rows,config,checkpoint=lambda *args:None,fit_callback=lambda *args:None):
    started=time.process_time(); observed=model.model(rows);fit_callback('observed',time.process_time()-started)
    writers=sorted({r['writer'] for r in rows});rng=np.random.default_rng(config['seed'])
    bank=[]
    for draw in range(config['bootstrap_draws']):
        selected=rng.integers(0,len(writers),len(writers))
        started=time.process_time(); fitted=model.model(model.writer_resample(rows,selected));fit_callback('bootstrap',time.process_time()-started)
        bank.append(dict(writer_indices=selected.tolist(),contrasts=fitted['contrasts'],mechanical_coefficient=fitted['mechanical_coefficient'],
                         mixture=fitted['mixture'],crossed_fit=fitted['crossed_fit']))
        checkpoint('bootstrap',draw+1,config['bootstrap_draws'])
    contrasts={}
    for name in model.CONTRASTS:
        a=np.array([b['contrasts'][name] for b in bank]);lo,hi=np.quantile(a,[.025,.975])
        contrasts[name]=dict(effect=observed['contrasts'][name],ci_low=float(lo),ci_high=float(hi),draws=len(bank),
                             uncertainty='whole-writer percentile bootstrap; typing baseline, mechanical fit, mixture and crossed regression reestimated in every draw')
    primary=contrasts['sentence_minus_word']
    passed=primary['ci_low']>0
    started=time.process_time()
    profiles,detail=profile_controls(rows,observed['mechanical_coefficient'],config,checkpoint)
    fit_callback('identification',time.process_time()-started)
    result=dict(genre=observed['genre'],instrument=observed,contrasts=contrasts,gradient_pass=passed,
                gradient_state='positive' if passed else 'negative' if primary['ci_high']<0 else 'not_detected',
                hierarchy_profiles=profiles,
                route=dict(coauthor_timing_cards=['PP2','PP4','PP5','PP6','PP7'] if passed else [],
                           stop_timing_claims=not passed,
                           fail_fallback='ScholaWrite within-writer PP2 only, or KLiCKe PP2 if intaken; no cross-writer PP4 or PP5(ii)' if not passed else None))
    return result,dict(bootstrap=bank,profile_references=detail)


def compute(output,rows,config,verification=False,fit_callback=lambda *args:None):
    result={};details={}
    for genre in ('creative','argumentative'):
        def checkpoint(phase,done,total):
            atomic(Path(output)/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,genre=genre,done=done,total=total))
            if (Path(output)/'YIELD_REQUEST.json').exists() or (Path(output).parent/'STOP').exists():
                raise InterruptedError('PP1 yielded at complete fit/reference boundary')
        result[genre],details[genre]=genre_analysis([r for r in rows if r['genre']==genre],config,checkpoint,
            lambda phase,seconds:fit_callback(genre,phase,seconds))
    return dict(card='PP1',status='complete',full_card_complete=True,scientific_admission=config['mode']=='corpus',
                genres=result,all_genres_gradient_pass=all(r['gradient_pass'] for r in result.values()),
                license_scope='a passing gradient licenses the timing instrument only, separately by genre; profile identity requires both empirical/context controls'),details


def run(output,inputs,config,verification=False):
    configuration(config);output=Path(output)
    rows=load(inputs,config['mode'])
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config)
    with threadpool_limits(limits=1): result,details=compute(output,rows,config,verification)
    if verification:
        if read(output/'PP1_BINDING.json')!=binding or read(output/'PP1_RESULT.json')!=result or gzread(output/'PP1_REFERENCES.json.gz')!=details:
            raise ValueError('PP1 complete fit/reference reconstruction differs')
        return dict(verified=True,full_replay=True,scientific_admission=config['mode']=='corpus')
    write_equal(output/'PP1_BINDING.json',binding)
    write_equal(output/'PP1_RESULT.json',result)
    gzip_equal(output/'PP1_REFERENCES.json.gz',details)
    return result


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
