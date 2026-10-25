"""Counted-card source plumbing for FR1/TR5, with complete original replay.

DESIGN CHECK: LESSONS 3-5 and Week3 source/control defaults read 2026-10-25.
Every session remains in the census. A pilot is explicitly incomplete and has
no scientific admission. Source provenance uses the already sealed canonical
PMAP recovery and its exact P2/P6/raw joins, not selected-option indices.
"""
import hashlib
import json
from pathlib import Path
import time

from runners.stage9.common import digest
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_pmap_source import INPUTS,completed,bound_record
from .timing_pmap_source_recovery import Sources


def load(inputs,config):
    if set(config)!={'card','mode','expected_sessions','session_limit','seed'} or config['seed']!=20261026 or config['mode'] not in {'full','pilot','constructed'}:
        raise ValueError('frozen event-census configuration required')
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('constructed source fixture required')
        rows=read(inputs['fixture'])
        if len(rows)!=config['expected_sessions'] or config['session_limit']!=len(rows):raise ValueError('constructed census differs')
        return rows,None
    expected=1399 if config['mode']=='full' else 140
    if config['expected_sessions']!=1399 or config['session_limit']!=expected or set(inputs)!={'pmap_completion'}:
        raise ValueError('complete canonical population or first-tenth pilot required')
    parent=Path(inputs['pmap_completion']).resolve().parent
    completed(inputs['pmap_completion'],parent/'PLAN.json')
    plan=read(parent/'PLAN.json');sources=Sources({k:plan['inputs'][k] for k in INPUTS})
    if len(sources.p2)!=1399:raise ValueError('canonical source population changed')
    return sorted(sources.p2)[:expected],sources


def source_args(item,sources):
    if sources is None:return item,{}
    sid=item;pin=sources.metadata(sid)['source_hashes'];p=sources.inputs
    raw=(sources.root/sources.roster[sid]['path']).resolve()
    canonical=sources.root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
    args=dict(meta=sources.meta[sid],events=[json.loads(line) for line in raw.read_text(encoding='utf8').splitlines() if line.strip()],
              timeline=bound_record(p['session_index'],sources.p2[sid]),canonical=read(canonical),p6=bound_record(p['p6_index'],sources.p6[sid]))
    return args,pin


def run(output,inputs,config,prepare,assemble,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    selected,sources=load(inputs,config);start=time.process_time();sessions=[];pins=[]
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    for i,item in enumerate(selected):
        args,pin=source_args(item,sources);sid=args['meta']['session']
        value=prepare(**args);sessions.append(value);pins.append(dict(session=sid,source_hashes=pin))
        dest=output/'sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(dest)!=value:raise ValueError('event session does not replay')
        else:gzip_equal(dest,value)
        if sources is not None and sources.unit_binding(sid)!=pin:raise ValueError('source changed during event extraction')
        progress(output/'PROGRESS.json',dict(phase='verify-source' if verification else 'source',done=i+1,total=len(selected)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('event source yielded at complete session')
    value=assemble(sessions);value['summary'].update(full_population=config['mode']=='full',constructed=config['mode']=='constructed',scientific_admission=False)
    if config['mode']=='pilot':value['summary'].update(support=False,support_state='incomplete_cost_pilot')
    binding['source_units']=pins
    if verification:
        if read(output/'BINDING.json')!=binding or gzread(output/'EVENTS.json.gz')!=value or read(output/'SUMMARY.json')!=value['summary']:
            raise ValueError('complete event-census replay differs')
        return dict(verified=True,full_source_replay=True)
    write_equal(output/'BINDING.json',binding);gzip_equal(output/'EVENTS.json.gz',value);write_equal(output/'SUMMARY.json',value['summary'])
    cpu=time.process_time()-start
    if not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json',dict(cpu_seconds=cpu,new_sessions=len(selected),projected_full_source_and_replay_cpu_seconds=2*cpu*config['expected_sessions']/len(selected),
                                            excludes='prior/native/pilot charges and downstream feature/statistical work'))
    return dict(status='complete',counts_only=True,summary=value['summary'])


def menus(events,timeline,canonical):
    decisions={r['ordinal']:r for r in timeline.get('decisions',[])}
    result=[]
    for c in sorted((r for r in canonical['events'] if r['usable']),key=lambda r:r['ordinal']):
        p=decisions[c['ordinal']]
        if p['handling']!=c['decision']:raise ValueError('canonical handling join differs')
        ordinal=p['resolution_ordinal']
        if not c['ordinal']<=ordinal<len(events):raise ValueError('invalid menu resolution ordinal')
        result.append(dict(origin=c['ordinal'],resolution=ordinal,handling=c['decision'],
                           censored=str(p.get('latency_kind','')).startswith('right_censored'),
                           offers=[o['original'] for o in c['options']]))
    return result
