"""Full raw revision input continuation; no burst or scientific classification.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-6 read for this continuation.
Null and alternative both require every original occurrence, exact pilot bytes,
authenticated raw sources and fresh replay. Missing/changed data fail closed.
Zero new work cannot supply a forecast. Prior execution and verification costs
are charged together; a projected excess pauses at a saved boundary, never null.
"""
from pathlib import Path
import math,time
from .timing_revision_source import Sources,INPUTS as SOURCE_INPUTS
from .timing_revision_input import relative,CONFIG as PILOT_CONFIG
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal
from .timing_stats import bind,check_binding
from runners.stage14.common import atomic

CONFIG=dict(mode='full',expected_sessions=1399,pilot_sessions=10,cumulative_wall_seconds=6900)
INPUTS=SOURCE_INPUTS|{'pilot_complete'}

def validate(config):
    if config==CONFIG:return
    if (set(config)==set(CONFIG) and config['mode']=='constructed' and
        type(config['expected_sessions']) is int and 1<=config['pilot_sessions']<config['expected_sessions']<=4
        and config['cumulative_wall_seconds']==120):return
    raise ValueError('exact full continuation or bounded constructed scope required')

def load(inputs,config):
    validate(config)
    if set(inputs)!=INPUTS:raise ValueError('exact continuation inputs required')
    original={k:inputs[k] for k in SOURCE_INPUTS};source=Sources(original)
    selected=source.population['primary_session_ids']
    if len(selected)!=config['expected_sessions']:raise ValueError('full source population differs')
    pilot=Path(inputs['pilot_complete']).parent;complete=read(inputs['pilot_complete'])
    if complete.get('status')!='COMPLETE' or not complete.get('fresh_process_verified'):raise ValueError('pilot is not verified complete')
    for name,h in complete['outputs'].items():
        p=(pilot/name).resolve();p.relative_to(pilot.resolve())
        if filehash(p)!=h:raise ValueError('pilot output changed')
    plan=read(pilot/'PLAN.json');verified=read(pilot/'VERIFIED.json')
    if plan['inputs']!=original or not verified.get('verified') or not verified.get('full_uncached_replay'):raise ValueError('pilot source or replay differs')
    if config['mode']=='full' and (plan['module']!='runners.drive.cards.timing_revision_input' or plan['config']!=PILOT_CONFIG):raise ValueError('wrong corpus pilot')
    index=read(pilot/'output/INDEX.json');binding=read(pilot/'output/INPUTS.json')
    if [x['session'] for x in index]!=selected[:config['pilot_sessions']] or binding['selected']!=selected[:config['pilot_sessions']]:raise ValueError('pilot prefix differs')
    if verified['summary']!=read(pilot/'output/SUMMARY.json'):raise ValueError('pilot summary differs')
    for row in index:
        if row['file']!=relative(row['session']) or filehash(pilot/'output'/row['file'])!=row['sha256']:raise ValueError('pilot record changed')
    return source,selected,pilot,{x['session']:x for x in index}

def work(output,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    timing=output/'ACTIVE_TIME.json';prior=read(timing)['seconds'] if timing.exists() else 0.
    def elapsed():return prior+time.monotonic()-started
    def guard():
        if elapsed()>config['cumulative_wall_seconds']:raise TimeoutError('combined revision continuation/replay ceiling')
    try:
        if operation=='verify':check_binding(output,inputs,config)
        source,selected,pilot,prefix=load(inputs,config)
        binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items() if k!='repo_root'},repo_root=str(source.root),selected=selected)
        if operation=='execute':write_equal(output/'INPUTS.json',binding)
        elif read(output/'INPUTS.json')!=binding:raise ValueError('full revision binding differs')
        index=[];occurrences=changes=clocks=largest=new_count=0;new_seconds=0.
        for sid in selected:
            guard();target=output/relative(sid)
            if operation=='execute' and sid in prefix:
                old=pilot/'output'/prefix[sid]['file'];data=old.read_bytes()
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists() and target.read_bytes()!=data:raise ValueError('retained pilot bytes changed')
                if not target.exists():target.write_bytes(data)
                value=gzread(target)
            else:
                start=time.monotonic();value=source.session(sid)
                if operation=='execute':gzip_equal(target,value)
                elif gzread(target)!=value:raise ValueError('full raw revision replay differs')
                if sid not in prefix:
                    new_count+=1;new_seconds+=time.monotonic()-start
            if sid in prefix and filehash(target)!=prefix[sid]['sha256']:raise ValueError('pilot prefix is not exact')
            index.append(dict(session=sid,file=relative(sid),sha256=filehash(target),source_hashes=value['source_hashes']))
            occurrences+=value['occurrence_count'];changes+=sum(len(r['changes']) for r in value['revision_events']);clocks+=len(value['delta_clock']);largest=max(largest,target.stat().st_size)
            if operation=='execute':
                atomic(output/'PROGRESS.json',dict(completed=len(index),total=len(selected),retained=len(prefix),phase='full-raw-revision-source'))
                if new_count>=max(1,math.ceil((len(selected)-len(prefix))*.1)) and not (output/'FIRST_TENTH.json').exists():
                    # New-work execution rate prices remaining preparation AND fresh replay.
                    projected=elapsed()+new_seconds/new_count*((len(selected)-len(index))+len(selected))
                    atomic(output/'FIRST_TENTH.json',dict(new_sessions=new_count,new_seconds=new_seconds,projected_seconds=projected,includes_fresh_replay=True))
                if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed=len(index),total=len(selected),scientific_admission=False)
            guard()
        summary=dict(card='D30-revision-input-full',mode=config['mode'],selected_sessions=len(index),retained_pilot_sessions=len(prefix),
            upstream_only_sessions=len(source.population['upstream_only_session_ids']),original_occurrences=occurrences,retained_changes=changes,delta_events=clocks,
            largest_compressed_session_bytes=largest,classification_performed=False,scientific_admission=False)
        if operation=='execute':
            write_equal(output/'INDEX.json',index);write_equal(output/'SUMMARY.json',summary)
            artifacts=['INPUTS.json','INDEX.json','SUMMARY.json']+[r['file'] for r in index]
            if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
            else:bind(output,inputs,config,artifacts)
        elif read(output/'INDEX.json')!=index or read(output/'SUMMARY.json')!=summary:raise ValueError('full source aggregation differs')
        guard()
        return summary if operation=='execute' else dict(verified=True,summary=summary,full_uncached_replay=True,pilot_bytes_exact=True,cumulative_seconds=elapsed())
    finally:atomic(timing,dict(seconds=elapsed()))

def execute(output,inputs,config):return work(output,inputs,config,'execute')
def verify(output,inputs,config):return work(output,inputs,config,'verify')
