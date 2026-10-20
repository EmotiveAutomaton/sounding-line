"""Authenticated raw revision ledgers for the commissioned D30 follow-ups.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-6 reread October19. Under both null
and alternative every original occurrence and event must reconstruct exactly.
Changed sources, invented edits, missing sessions and altered saved rows refuse;
they never become a zero revision count. Known source edits, UTF-16 boundaries,
reentry, source/output tampering and full native replay precede corpus dispatch.
This input-only pilot classifies no burst, runs no statistic and admits no main.
"""
from pathlib import Path
import hashlib,time
from .timing_revision_source import Sources, INPUTS
from .timing_census import read,filehash
from .timing_p6 import gzip_equal,gzread,write_equal
from .timing_stats import bind,check_binding
from runners.stage14.common import atomic

CONFIG=dict(mode='pilot',expected_sessions=1399,session_limit=10,cumulative_wall_seconds=900)

def validate(config):
    if config==CONFIG:return
    if (set(config)==set(CONFIG) and config['mode']=='constructed'
        and type(config['expected_sessions']) is int and 1<=config['expected_sessions']<=10
        and config['session_limit']==config['expected_sessions'] and config['cumulative_wall_seconds']==120):return
    raise ValueError('exact revision pilot or bounded constructed scope required')

def load(inputs,config):
    validate(config)
    if set(inputs)!=INPUTS:raise ValueError('exact revision source inputs required')
    sources=Sources(inputs)
    if sources.population['primary_sessions']!=config['expected_sessions']:raise ValueError('revision input population differs')
    return sources,sources.population['primary_session_ids'][:config['session_limit']]

def relative(sid):return 'sessions/'+hashlib.sha256(sid.encode()).hexdigest()+'.json.gz'

def work(output,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    validate(config);started=time.monotonic();timing=output/'ACTIVE_TIME.json'
    prior=read(timing)['seconds'] if timing.exists() else 0.
    def elapsed():return prior+time.monotonic()-started
    def guard():
        if elapsed()>config['cumulative_wall_seconds']:raise TimeoutError('combined revision source/replay ceiling')
    try:
        if operation=='verify':check_binding(output,inputs,config)
        source,selected=load(inputs,config)
        binding=dict(config=config,inputs={k:filehash(p) for k,p in sorted(inputs.items()) if k!='repo_root'},
                     repo_root=str(source.root),selected=selected)
        if operation=='execute':write_equal(output/'INPUTS.json',binding)
        elif read(output/'INPUTS.json')!=binding:raise ValueError('revision source binding changed')
        index=[];occurrences=events=clocks=0;peak_bytes=0
        for sid in selected:
            guard();value=source.session(sid);target=output/relative(sid)
            if operation=='execute':gzip_equal(target,value)
            elif gzread(target)!=value:raise ValueError('revision raw replay differs')
            index.append(dict(session=sid,file=relative(sid),sha256=filehash(target),source_hashes=value['source_hashes']))
            occurrences+=value['occurrence_count'];events+=sum(len(r['changes']) for r in value['revision_events']);clocks+=len(value['delta_clock'])
            peak_bytes=max(peak_bytes,target.stat().st_size);guard()
            if operation=='execute':
                atomic(output/'PROGRESS.json',dict(completed=len(index),total=len(selected),phase='raw-revision-source'))
                if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed=len(index),total=len(selected),scientific_admission=False)
        summary=dict(card='D30-revision-input-pilot',mode=config['mode'],primary_sessions=source.population['primary_sessions'],
            selected_sessions=len(index),selection='first sorted primary session IDs',upstream_only_sessions=len(source.population['upstream_only_session_ids']),
            original_occurrences=occurrences,retained_changes=events,delta_events=clocks,largest_compressed_session_bytes=peak_bytes,
            classification_performed=False,scientific_admission=False,main_admitted=False)
        if operation=='execute':
            write_equal(output/'INDEX.json',index);write_equal(output/'SUMMARY.json',summary)
            paths=['INPUTS.json','INDEX.json','SUMMARY.json']+[r['file'] for r in index]
            if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
            else:bind(output,inputs,config,paths)
        elif read(output/'INDEX.json')!=index or read(output/'SUMMARY.json')!=summary:raise ValueError('revision summary/index differs')
        guard()
        return summary if operation=='execute' else dict(verified=True,summary=summary,full_uncached_replay=True,cumulative_seconds=elapsed())
    finally:atomic(timing,dict(seconds=elapsed()))

def execute(output,inputs,config):return work(output,inputs,config,'execute')
def verify(output,inputs,config):return work(output,inputs,config,'verify')
