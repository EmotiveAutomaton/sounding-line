"""Separately gated PMAP rhythm-minus-lean on saved session profiles only.

DESIGN CHECK: LESSONS3-5, October18. Unique planted rhythms beat constant lean,
reversal reverses the contrast, and equal fingerprints tie at exact chance.
Both channels share a complete fixed gallery; bootstrap resamples paired real
probe writers only. The same200 saved reassignments retain failed support and
bias warnings. No raw replay, new feature dictionary, model call or redraw.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
import time
import numpy as np

from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_stats import bind,check_binding
from .timing_pmap import assignments,CONFIG as ORIGINAL_CONFIG
from .timing_pmap_source import completed,ACTIONS
from .timing_pmap_stats import split_sessions,median,supported,channel_result,interval,distribution

CONFIG=dict(card='PMAP-rhythm',bootstrap_draws=2000,permutations=200,seed=20261018)
FORECAST_SECONDS=300
CUMULATIVE_CAP_SECONDS=900
CHANNELS=('lean','rhythm')


def validate(inputs,config):
    if set(inputs)!={'pmap_completion'} or config!=CONFIG or any(type(config[k]) is not int for k in ('bootstrap_draws','permutations','seed')):
        raise ValueError('exact PMAP extension inputs/config required')


def profiles(rows,bigrams,assignment=None):
    halves,excluded=split_sessions(rows,assignment);out={}
    for writer,parts in sorted(halves.items()):
        values=[]
        for sessions in parts:
            counts=Counter()
            for r in sessions:counts.update(r['handling'])
            n=sum(counts.values());timing=[r for r in sessions if r['tc_timing_mode']!='invalid']
            values.append(dict(lean=[counts[k]/n if n else None for k in ACTIONS],
                rhythm=[median([x for r in timing for x in r['within_intervals']]),median([x for r in timing for x in r['onset_intervals']])]+
                    [median([x for r in timing for x in r['bigram_intervals'].get(k,[])]) for k in bigrams]))
        out[writer]=values
    return out,excluded


def load(inputs,config):
    validate(inputs,config);root=Path(inputs['pmap_completion']).resolve().parent
    def authenticated(name):
        path=root/name;completed(inputs['pmap_completion'],path)
        return gzread(path) if path.suffix=='.gz' else read(path)
    plan=authenticated('PLAN.json')
    if plan['module'] not in ('runners.drive.cards.timing_pmap','runners.drive.cards.timing_pmap_recovery') or plan['config']!=ORIGINAL_CONFIG:
        raise ValueError('PMAP primary plan differs')
    primary=authenticated('output/PRIMARY.json');prepared=authenticated('output/PROFILES.json.gz')
    if primary['primary']!=prepared['primary'] or primary['primary']['state'] not in ('positive','marginal') or not prepared['extension_eligible']:
        raise ValueError('PMAP rhythm extension is not eligible')
    dictionary=authenticated('output/STYLE_DICTIONARY.json')
    complete=read(inputs['pmap_completion'])
    paths=sorted(n for n in complete['outputs'] if n.startswith('output/sessions/') and n.endswith('.json.gz'))
    rows=[authenticated(n) for n in paths]
    if not rows or len({r['session'] for r in rows})!=len(rows):raise ValueError('invalid saved session roster')
    rows.sort(key=lambda r:r['session'])
    actual,_=profiles(rows,dictionary['character_bigrams'])
    expected={w:[{c:part[c] for c in CHANNELS} for part in parts] for w,parts in prepared['profiles'].items()}
    if actual!=expected:raise ValueError('saved lean/rhythm profiles do not reconstruct')
    fakes=[]
    for i,assignment in enumerate(assignments(rows)):
        value=authenticated('output/permutations/'+str(i).zfill(3)+'.json.gz')
        if value['assignment']!=assignment:raise ValueError('saved fake assignment differs')
        fakes.append(value)
    return rows,dictionary,prepared,primary,fakes


def channels(values,roster,names):
    return {c:channel_result(values,c,roster,names[c]) for c in CHANNELS}


def contrast(values):
    if any('identification' not in values[c] for c in CHANNELS):return None
    return np.asarray(values['rhythm']['identification']['scores'])-values['lean']['identification']['scores']


def analyze(real,fakes,primary):
    scores=contrast(real)
    result=dict(card=CONFIG['card'],descriptive=True,channels=real,
        primary=interval(scores) if scores is not None else dict(state='invalid',reason='common rhythm/lean gallery lacks support'),
        original_primary=primary['primary'],extension='predefined rhythm minus lean; original primary retained',
        original_control_warnings=dict(primary_session_permutation_null=primary['primary_session_permutation_null'],
            fake_channels=primary['fake_channels']),permutations=200,seed=20261018,
        method='Same saved sessions and200 assignments; paired real-probe bootstrap2000; complete common B gallery fixed; no raw/model work')
    fake_scores=[contrast(f['channels']) for f in fakes]
    valid=[s for s in fake_scores if s is not None]
    null=distribution([float(s.mean()) for s in valid],result['primary'].get('effect'))
    null['invalid_draws']=len(fakes)-len(valid)
    if null['invalid_draws']:
        null.update(state='invalid',one_sided_p=None,reason='fixed support incomplete; no successful-only p or redraw')
    else:null['state']='descriptive'
    result['session_permutation_null']=null
    result['own_minus_fake']=interval(scores-np.mean(valid,axis=0)) if scores is not None and len(valid)==200 else dict(state='invalid',reason='real or fixed-fake common support missing')
    result['fake_channels']={}
    for c in CHANNELS:
        values=[f['channels'][c] for f in fakes if 'identification' in f['channels'][c]]
        result['fake_channels'][c]=dict(valid=len(values),invalid=200-len(values),
            chance_centered=distribution([v['identification']['accuracy']-v['identification']['chance'] for v in values]),
            identification=distribution([v['identification']['accuracy'] for v in values]))
    return result


def execute(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);validate(inputs,config)
    old=read(output/'ACTIVE_TIME.json')['seconds'] if (output/'ACTIVE_TIME.json').exists() else 0.
    if not math.isfinite(old) or old<0:raise ValueError('invalid cumulative PMAP extension time')
    elapsed=lambda:old+time.monotonic()-started
    write_equal(output/'INPUTS.json',dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config))
    rows,dictionary,prepared,primary,saved_fakes=load(inputs,config)
    values,_=profiles(rows,dictionary['character_bigrams'])
    roster=sorted(w for w,v in values.items() if all(supported(v,c) for c in CHANNELS))
    write_equal(output/'ROSTER.json',dict(writers=roster,excluded=sorted(set(values)-set(roster)),
        channel_coverage={c:sorted(w for w,v in values.items() if supported(v,c)) for c in CHANNELS},
        saved_primary_rosters={c:prepared['rosters'][c] for c in CHANNELS}))
    real=channels(values,roster,prepared['names']);write_equal(output/'REAL.json',real)
    source_seconds=elapsed();fakes=[]
    for i,saved in enumerate(saved_fakes):
        v,excluded=profiles(rows,dictionary['character_bigrams'],saved['assignment'])
        # Authenticate that the shared profile formulas reproduce the already
        # completed control, before recomputing on the extension's common gallery.
        for c in CHANNELS:
            if channel_result(v,c,prepared['rosters'][c],prepared['names'][c])!=saved['channels'][c]:
                raise ValueError('saved fake channel does not reconstruct')
        value=dict(channels=channels(v,roster,prepared['names']),split_excluded=excluded)
        gzip_equal(output/'permutations'/(str(i).zfill(3)+'.json.gz'),value);fakes.append(value)
        seconds=elapsed();progress(output/'ACTIVE_TIME.json',dict(seconds=seconds))
        progress(output/'PROGRESS.json',dict(complete=i+1,total=200,seconds=seconds))
        if i==19 and not (output/'FIRST_TENTH.json').exists():
            write_equal(output/'FIRST_TENTH.json',dict(completed=20,total=200,active_seconds=seconds,
                projected_cpu_seconds=2*(source_seconds+10*(seconds-source_seconds)),forecast_cpu_seconds=FORECAST_SECONDS,
                method='All authentication and real profiles plus20 complete controls extrapolated; doubled for fresh verification'))
        if seconds>CUMULATIVE_CAP_SECONDS:raise RuntimeError('PMAP extension cumulative cap exceeded')
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed=i+1,total=200)
    result=analyze(real,fakes,primary);write_equal(output/'PRIMARY.json',result)
    artifacts=['INPUTS.json','ROSTER.json','REAL.json','PRIMARY.json','FIRST_TENTH.json']+[p.relative_to(output).as_posix() for p in sorted((output/'permutations').glob('*.gz'))]
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,artifacts)
    progress(output/'ACTIVE_TIME.json',dict(seconds=elapsed()))
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);validate(inputs,config);check_binding(output,inputs,config)
    rows,dictionary,prepared,primary,saved_fakes=load(inputs,config)
    values,_=profiles(rows,dictionary['character_bigrams']);roster=sorted(w for w,v in values.items() if all(supported(v,c) for c in CHANNELS))
    expected=dict(writers=roster,excluded=sorted(set(values)-set(roster)),channel_coverage={c:sorted(w for w,v in values.items() if supported(v,c)) for c in CHANNELS},saved_primary_rosters={c:prepared['rosters'][c] for c in CHANNELS})
    if read(output/'ROSTER.json')!=expected:raise ValueError('extension common roster changed')
    real=channels(values,roster,prepared['names']);fakes=[]
    if real!=read(output/'REAL.json'):raise ValueError('extension real profiles differ')
    for i,saved in enumerate(saved_fakes):
        v,excluded=profiles(rows,dictionary['character_bigrams'],saved['assignment'])
        for c in CHANNELS:
            if channel_result(v,c,prepared['rosters'][c],prepared['names'][c])!=saved['channels'][c]:raise ValueError('saved fake source differs')
        value=dict(channels=channels(v,roster,prepared['names']),split_excluded=excluded)
        if value!=gzread(output/'permutations'/(str(i).zfill(3)+'.json.gz')):raise ValueError('extension fake differs from saved source')
        fakes.append(value)
    result=analyze(real,fakes,primary)
    if result!=read(output/'PRIMARY.json'):raise ValueError('extension primary differs from fresh source replay')
    seconds=read(output/'ACTIVE_TIME.json')['seconds']+time.monotonic()-started
    if seconds>CUMULATIVE_CAP_SECONDS:raise RuntimeError('PMAP extension cumulative verification cap exceeded')
    return dict(verified=True,primary=result['primary'],cumulative_seconds=seconds)
