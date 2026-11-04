"""Frozen S1 recurrence consumer and native known-answer validation.

DESIGN CHECK: Week4 S1, controls and LESSONS2-5 reviewed 2026-11-02.
Whole source joins, full nuisance support and signed known-answer controls
precede any human contrast. Null, positive, reversed, nuisance-only and
unidentifiable constructions retain distinct states. No post-outcome tuning.
"""
from pathlib import Path
from collections import defaultdict,Counter
import hashlib,time
from threadpoolctl import threadpool_limits
from . import week4_s1_stats as stats
from .timing_pmap_source import completed,bound_record
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read,filehash
from .timing_d33_match import earlier

def configuration(mode):
    if mode not in ('constructed','full'):raise ValueError('Unknown recurrence mode')
    return dict(card='S1-recurrence',mode=mode,seed=20261102)

def rows_from_sources(output,inputs,verification):
    if set(inputs)!={'nuisance_completion'}:raise ValueError('Exact completed controls required')
    nc=Path(inputs['nuisance_completion']);np=read(nc.parent/'PLAN.json');ns=nc.parent/'output'
    completed(nc,ns/'SUMMARY.json');summary=read(ns/'SUMMARY.json')
    if summary.get('mode')!='full':raise ValueError('Complete control inputs required')
    hc=Path(np['inputs']['histories_completion']);hp=read(hc.parent/'PLAN.json');wc=Path(hp['inputs']['windows_completion'])
    for n in ('WINDOWS.json.gz','FROZEN_DICTIONARY.json'):completed(wc,wc.parent/'output'/n)
    windows=gzread(wc.parent/'output/WINDOWS.json.gz');dictionary=set(read(wc.parent/'output/FROZEN_DICTIONARY.json')['words'])
    p6=hp['inputs']['p6_index'];completed(hp['inputs']['p6_completion'],p6);records=[bound_record(p6,r) for r in read(p6)]
    lookup={r['session']:r for r in records};by_writer=defaultdict(list)
    for r in records:by_writer[r['writer']].append(r)
    if len(lookup)!=1399 or {s['session']:s['writer'] for s in windows}!={s:r['writer'] for s,r in lookup.items()}:raise ValueError('Full window/source population differs')
    rows=[];census=Counter();bindings=[]
    for i,session in enumerate(windows):
        sid=session['session'];leaf=hashlib.sha256(sid.encode()).hexdigest()+'.json.gz';npath=ns/'sessions'/leaf
        if not npath.exists():census['history_or_window_unsupported_sessions']+=1;continue
        completed(nc,npath);nuisance=gzread(npath);hpath=hc.parent/'output/sessions'/leaf;completed(hc,hpath);history=gzread(hpath)
        if not history['proof']['supported'] or nuisance['writer']!=session['writer']:raise ValueError('Supported source identity differs')
        own_rows=earlier(by_writer[session['writer']],lookup[sid])
        if history['proof']['own_sessions']!=[r['session'] for r in own_rows]:
            if set(history['proof']['own_sessions'])!={r['session'] for r in own_rows}:raise ValueError('Own-history proof differs')
        own=stats.history_grams([seq for r in own_rows for seq in r['training_sequences']],dictionary)
        donor=stats.history_grams([seq for r in history['donor'] for seq in r['training_sequences']],dictionary)
        control={r['start_ordinal']:r for r in nuisance['rows']};candidates=[w for w in session['windows'] if w['grams'] and w['class'] in ('flow','hesitant')]
        if len(control)!=len(nuisance['rows']) or set(control)!={w['start_ordinal'] for w in candidates}:raise ValueError('Exact control/window join differs')
        source_rows=[]
        for w in candidates:
            c=control[w['start_ordinal']]
            if c['nuisance'] is None:census['missing_nuisance_windows']+=1;continue
            source_rows.append(dict(writer=session['writer'],session=sid,genre=session['genre'],start_ordinal=w['start_ordinal'],
                label=int(w['class']=='flow'),nuisance=c['nuisance'],outcome=stats.recurrence(w['grams'],own,donor)))
        dest=Path(output)/'sessions'/leaf;value=dict(session=sid,rows=source_rows)
        if verification:
            if gzread(dest)!=value:raise ValueError('Recurrence source replay differs')
        else:gzip_equal(dest,value)
        rows.extend(source_rows);census['included_windows']+=len(source_rows);census['history_supported_sessions']+=1
        bindings.append(dict(session=sid,controls=filehash(npath),history=filehash(hpath),scored=filehash(dest)))
        progress(Path(output)/'PROGRESS.json',dict(phase='verify-source' if verification else 'recurrence-source',done=i+1,total=len(windows)))
    return rows,dict(census),bindings

def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Frozen recurrence configuration required')
    start=time.process_time();output=Path(output)
    with threadpool_limits(limits=1):
        checks=stats.known_checks()
        if config['mode']=='constructed':
            if inputs:raise ValueError('No human source in native calibration')
            dictionary={'a','the'}
            assert stats.history_grams([['a','b','c','.','the','d','e','f']],dictionary)=={('the','<content>','<content>','<content>')}
            assert stats.recurrence([['a']]*2+[list('bc')],{('a',)},{('b','c')})==1/3
            values={'SUMMARY.json':dict(known_checks=checks,source_membership_checks=True,scientific_effect_computed=False)}
        else:
            # The full source-support check is already known before any scoring.
            nc=Path(inputs['nuisance_completion']);completed(nc,nc.parent/'output/SUMMARY.json');support=read(nc.parent/'output/SUMMARY.json')
            if support['supported_writers']<stats.CONFIG['min_writers']:
                values={'SUMMARY.json':dict(state='design cannot test',coverage=support,scientific_effect_computed=False,known_checks=checks)}
            else:
                rows,census,bindings=rows_from_sources(output,inputs,verification)
                primary,private=stats.analyze(rows);genres={};details={}
                for g in ('argumentative','creative'):genres[g],details[g]=stats.analyze([r for r in rows if r['genre']==g])
                values={'SUMMARY.json':dict(primary=primary,genres=genres,census=census,known_checks=checks,descriptive=True),
                    'PRIVATE_INFERENCE.json':dict(primary=private,genres=details),
                    'BINDING.json':dict(config=config,statistics=stats.CONFIG,inputs={k:filehash(v) for k,v in inputs.items()},sources=bindings)}
    import json
    for name,value in values.items():
        if verification:
            if read(output/name)!=json.loads(json.dumps(value)):raise ValueError('Complete recurrence/statistic replay differs')
        else:write_equal(output/name,value)
    if not verification:write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start))
    return dict(verified=True,complete_source_replay=True,complete_statistical_replay=True) if verification else dict(status='complete',scientific_admission=config['mode']=='full')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
