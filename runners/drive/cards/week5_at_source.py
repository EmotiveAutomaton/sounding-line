"""Private AT source from authenticated P6 production and Week4 timing ruler.

DESIGN CHECK: LESSONS 2--5, CONTROLS 1--6, 2026-11-07. Exact character
provenance distinguishes repeated occurrences; deleted words remain counted.
Changed hashes, incomplete rosters and duplicate onset joins refuse under both
null and alternative. Missing timing support is exposed rather than imputed.
"""
from collections import Counter
from pathlib import Path
import json

from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .week5_at_scoring import context_rows,frozen_sessions,digest


def authenticate(root):
    root=Path(root);done=read(root/'COMPLETE.json')
    if done.get('status')!='COMPLETE' or not done.get('fresh_process_verified'):
        raise ValueError('Source lacks complete independent verification')
    for name,expected in done['outputs'].items():
        path=root/name
        path.resolve().relative_to(root.resolve())
        if filehash(path)!=expected:
            raise ValueError('Source output changed: '+name)
    return root


def load_sources(inputs):
    if set(inputs)!={'p6_root','timing_root','raw_roster','repo_root'}:
        raise ValueError('Exact AT source inputs required')
    p6=authenticate(inputs['p6_root'])
    timing=authenticate(inputs['timing_root'])
    index=read(p6/'output/P6_INDEX.json')
    raw=read(inputs['raw_roster'])
    roster={r['session']:r for r in raw}
    posteriors=gzread(timing/'output/INTERVALS.json.gz')
    timing_roster={r['session']:r for r in read(timing/'output/PRIVATE_ROSTER.json')}
    if len(roster)!=len(raw) or len({r['session'] for r in index})!=len(index):
        raise ValueError('Duplicate source session identity')
    if {r['session'] for r in index}!=set(posteriors) or set(posteriors)!=set(timing_roster):
        raise ValueError('P6/timing population mismatch')
    return p6,index,roster,posteriors,timing_roster


def produce(output,inputs,config,verifying=False):
    if config not in ({}, {'batch_words':256}):
        raise ValueError('Undeclared source configuration')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    p6,index,roster,posteriors,timing_roster=load_sources(inputs)
    chosen=set(frozen_sessions([r['session'] for r in index]))
    source_pins={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') and k!='repo_root'
                 else filehash(v) for k,v in inputs.items() if k!='repo_root'}
    binding=digest(source_pins)
    entries=[];counts=Counter();batches=[]
    for n,meta in enumerate(sorted(index,key=lambda r:r['session'])):
        p=p6/'output'/meta['file']
        if filehash(p)!=meta['sha256']:
            raise ValueError('P6 session changed')
        record=gzread(p);rawmeta=roster[meta['session']]
        rawpath=(Path(inputs['repo_root'])/rawmeta['path']).resolve()
        rawpath.relative_to(Path(inputs['repo_root']).resolve())
        if filehash(rawpath)!=rawmeta['source_sha256']:
            raise ValueError('Raw event source changed')
        events=[json.loads(line) for line in rawpath.read_text(encoding='utf8').splitlines() if line]
        locations=context_rows(events,record['words'])
        posterior={r['ordinal']:r for r in posteriors[meta['session']]}
        if len(posterior)!=len(posteriors[meta['session']]):
            raise ValueError('Ambiguous timing-onset join')
        session_rows=[];session=timing_roster[meta['session']]
        for word,location in zip(record['words'],locations):
            counts['all_production_occurrences']+=1
            if not word['is_word']:
                counts['punctuation_occurrences']+=1;continue
            counts['typed_words']+=1
            post=posterior.get(word['ordinal'])
            eligible=bool(post and post['onset'] and word['pause_seconds'] and word['pause_seconds']>0
                          and word['first_delta_characters']==1)
            counts['timing_supported' if eligible else 'timing_unsupported']+=1
            counts['final_supported' if location['final_supported'] else 'final_unsupported']+=1
            row=dict(location,row_key=f'{n:04d}:{word["index"]}',session=record['session'],
                     writer=record['writer'],genre=session['genre'],prompt=record['prompt'],
                     at_typing_frozen20=meta['session'] in chosen,timing_supported=eligible,
                     length=word['length'],sentence_start=word['sentence_start'],
                     paragraph_start=location['final_prefix'] is not None and
                         (not location['final_prefix'].strip() or location['final_prefix'].endswith('\n')),
                     after_punctuation=word['after_punctuation'],position=word['index'],
                     population_surprisal=word['population_surprisal'],
                     log_frequency=word['population_log_frequency'],pause_seconds=word['pause_seconds'],
                     fast=post['fast'] if post else None)
            session_rows.append(row)
        relative=f'sessions/session-{n:04d}.json.gz';path=output/relative
        payload=dict(binding=binding,rows=session_rows)
        if verifying:
            if gzread(path)!=payload:raise ValueError('AT source replay differs')
        else:gzip_equal(path,payload)
        entries.append(dict(file=relative,sha256=filehash(path),words=len(session_rows)))
        for context in ('final','at_typing'):
            selected=[r for r in session_rows if r[context+'_prefix'] is not None
                      and (context=='final' or r['at_typing_frozen20'])]
            for offset in range(0,len(selected),256):
                dest=f'batches/{context}-{n:04d}-{offset//256:04d}.json.gz'
                subset=selected[offset:offset+256]
                if verifying:
                    if gzread(output/dest)!=subset:raise ValueError('Batch replay differs')
                else:gzip_equal(output/dest,subset)
                batches.append(dict(context=context,file=dest,sha256=filehash(output/dest),words=len(subset)))
        progress(output/'PROGRESS.json',dict(phase='source_verify' if verifying else 'source',sessions=n+1,total=len(index)))
    summary=dict(status='complete',sessions=len(index),writers=len({r['writer'] for r in index}),
                 counts=dict(counts),frozen_at_typing_sessions=len(chosen),source_pins=source_pins,
                 scientific_admission=False)
    outputs={'INDEX.json':entries,'BATCHES.json':batches,'SUMMARY.json':summary}
    for name,value in outputs.items():
        if verifying:
            if read(output/name)!=value:raise ValueError('AT aggregate replay differs')
        else:write_equal(output/name,value)
    return dict(verified=True,complete_source_replay=True) if verifying else summary


def execute(output,inputs,config):return produce(output,inputs,config)
def verify(output,inputs,config):return produce(output,inputs,config,True)
