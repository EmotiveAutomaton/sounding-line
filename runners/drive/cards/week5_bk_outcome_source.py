"""WC2/FR1 source successors using the authenticated complete R1 ledger.

DESIGN CHECK: LESSONS 2--5 and CONTROLS 1--7, 2026-11-07. Original
windows, matching and held-out profiles are unchanged. R1 physical insertions
replace only the obsolete parser; missing comparators remain explicit. A
sealed session is reusable only under its exact full input binding. Verification
reconstructs every session and the complete original aggregation.
"""
import copy
import hashlib
from pathlib import Path
from types import FunctionType, SimpleNamespace
import time

from runners.stage9.common import digest
from . import week3_frames_io as io
from . import week3_frames_inputs as fr
from . import week3_outcome_blocks_inputs as wc
from . import week4_shared_spans_h1 as r1
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress


def configuration(config):
    if set(config)!={'card','mode','max_wall_seconds'} or config['card'] not in ('WC2-inputs','FR1-inputs') or config['mode'] not in ('full','pilot','constructed'):
        raise ValueError('Fixed WC2/FR1 R1-cache source contract required')
    if type(config['max_wall_seconds']) not in (int,float) or not 30<=config['max_wall_seconds']<=1500:
        raise ValueError('Bounded source quantum required')
    return dict(card=config['card'],mode=config['mode'],expected_sessions=1399,
                session_limit=140 if config['mode']=='pilot' else 1399,seed=20261026)


def load(inputs,config):
    cfg=configuration(config)
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('Constructed-only source required')
        rows=read(inputs['fixture'])
        if not rows or len({r['meta']['session'] for r in rows})!=len(rows):raise ValueError('Invalid fixture population')
        return rows,None,None
    if set(inputs)!={'r1_root','pmap_completion'}:raise ValueError('Full R1 and PMAP completions required')
    root=authenticate(inputs['r1_root']);plan=read(root/'PLAN.json');summary=read(root/'output/SUMMARY.json')
    if plan['module']!='runners.drive.cards.week4_record' or plan['config']!=dict(card='R1',mode='full',expected_sessions=1399) or (summary['card'],summary['mode'],summary['sessions'])!=('R1','full',1399):
        raise ValueError('Complete original R1 population required')
    pinned={Path(k).resolve():v for k,v in plan['pins'].items()}
    if pinned.get(Path(r1.__file__).resolve())!=filehash(r1.__file__):raise ValueError('R1 parser differs from the completed source')
    selected,sources=io.load(dict(pmap_completion=inputs['pmap_completion']),cfg)
    rows=read(root/'output/INDEX.json');index={r['session']:r for r in rows}
    if len(index)!=len(rows) or set(index)!=set(sources.p2):raise ValueError('Exact R1/PMAP population equality required')
    return selected,sources,(root/'output',index)


def prepare(args,spans,card):
    """Use immutable R1 records without mutating either frozen module."""
    provider=lambda *unused:copy.deepcopy(spans)
    if card=='WC2-inputs':
        fn=FunctionType(wc.prepare_session.__code__,dict(wc.__dict__,spans=provider))
        value=fn(**args)
        unsupported=[e for e in value['events'] if not e['span']['comparator_supported']]
        value['unsupported_comparator_events']=unsupported
        value['events']=[e for e in value['events'] if e['span']['comparator_supported']]
        value['audit']['single_option_or_absent_comparator_events']=len(unsupported)
        value['audit']['single_option_deleted_complete_windows']=sum(e['kind']=='deleted' and e['window'] is not None for e in unsupported)
    else:
        patched=SimpleNamespace(**dict(wc.__dict__,spans=provider))
        fn=FunctionType(fr.prepare_session.__code__,dict(fr.__dict__,wc2=patched))
        value=fn(**args)
    value['r1_audit']=dict(physical_insertions=len(spans),canonical=sum(s['canonical'] for s in spans),
                          comparator_unsupported=sum(not s['comparator_supported'] for s in spans))
    return value


def yielded(output,started,seconds):
    return (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists() or time.monotonic()-started>=seconds


def run(output,inputs,config,verifying=False):
    started=time.monotonic();cpu=time.process_time();root=Path(output);root.mkdir(parents=True,exist_ok=True)
    cfg=configuration(config)
    if yielded(root,started,config['max_wall_seconds']):return dict(status='yielded',operation='outcome-source',scientific_admission=False)
    selected,sources,cache=load(inputs,config)
    pins={k:filehash(Path(v)/'COMPLETE.json') if k=='r1_root' else filehash(v) for k,v in inputs.items()}
    binding=dict(config=dict(cfg,expected_sessions=len(selected)) if cfg['mode']=='constructed' else cfg,inputs=pins,
                 source_revision='week5-r1-cache-v1',session_roster=digest([r['meta']['session'] for r in selected] if sources is None else selected))
    if verifying:
        if read(root/'BINDING.json')!=binding:raise ValueError('Source binding changed')
    else:write_equal(root/'BINDING.json',binding)
    sessions=[];index=[];new=0
    for ordinal,item in enumerate(selected):
        args,pin=io.source_args(item,sources);sid=args['meta']['session']
        if sources is None:spans=r1.spans(args['events'],args['timeline'],args['canonical']);r1pin=digest(spans)
        else:
            base,entries=cache;entry=entries[sid];path=(base/entry['file']).resolve();path.relative_to(base.resolve())
            if filehash(path)!=entry['sha256']:raise ValueError('R1 session checksum changed')
            record=gzread(path)
            if (record['session'],record['writer'],record['source_sha256'])!=(sid,args['meta']['writer'],pin['raw']):raise ValueError('R1/raw source identity mismatch')
            spans=record['record'];r1pin=entry['sha256']
        unit=dict(binding=digest(binding),source_hashes=pin,r1_sha256=r1pin,session=sid)
        name=f'sessions/session-{ordinal:04d}.json.gz';path=root/name;seal=path.with_suffix('.seal.json')
        if seal.exists():
            receipt=read(seal)
            if receipt.get('unit')!=unit or not path.exists() or receipt.get('sha256')!=filehash(path):raise ValueError('Source checkpoint seal differs')
            saved=gzread(path)
        else:saved=None
        if verifying or saved is None:
            value=prepare(args,spans,config['card'])
            if verifying:
                if saved is None or saved!=value:raise ValueError('Fresh source checkpoint replay differs')
            else:
                gzip_equal(path,value);write_equal(seal,dict(unit=unit,sha256=filehash(path)));new+=1
        else:value=saved
        if sources is not None and sources.unit_binding(sid)!=pin:raise ValueError('Source changed during preparation')
        sessions.append(value);index.append(dict(session=sid,file=name,sha256=filehash(path)))
        progress(root/'PROGRESS.json',dict(phase='verify-source' if verifying else 'source',done=ordinal+1,total=len(selected)))
        if yielded(root,started,config['max_wall_seconds']):return dict(status='yielded',operation='outcome-source',sessions=ordinal+1,scientific_admission=False)
    # Original aggregation only sees eligible comparison events; all original
    # sessions and unsupported spans remain in sealed private session records.
    value=(wc.assemble if config['card']=='WC2-inputs' else fr.assemble)(copy.deepcopy(sessions))
    value['summary'].update(full_population=config['mode']=='full',constructed=config['mode']=='constructed',scientific_admission=False,
        source_revision='verified R1 physical insertion cache; original windows and profiles',
        r1_physical_insertions=sum(s['r1_audit']['physical_insertions'] for s in sessions),
        r1_comparator_unsupported=sum(s['r1_audit']['comparator_unsupported'] for s in sessions))
    if config['mode']=='pilot':value['summary'].update(support=False,support_state='incomplete_cost_pilot')
    for name,payload in [('INDEX.json',index),('SUMMARY.json',value['summary'])]:
        if verifying:
            if read(root/name)!=payload:raise ValueError('Complete source aggregation differs')
        else:write_equal(root/name,payload)
    if verifying:
        if gzread(root/'EVENTS.json.gz')!=value:raise ValueError('Complete event/profile replay differs')
    else:gzip_equal(root/'EVENTS.json.gz',value)
    if pins!={k:filehash(Path(v)/'COMPLETE.json') if k=='r1_root' else filehash(v) for k,v in inputs.items()}:raise ValueError('Source binding changed')
    timing=root/('VERIFY_TIME.json' if verifying else 'EXECUTE_TIME.json')
    if not timing.exists():write_equal(timing,dict(cpu_seconds=time.process_time()-cpu,new_sessions=new,sessions=len(selected),
        excludes='Prior segments, original attempts and downstream features/statistics; native ledger is cumulative authority'))
    return dict(verified=True,complete_session_and_aggregation_replay=True) if verifying else dict(status='complete',counts_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
