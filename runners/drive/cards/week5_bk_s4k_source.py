"""Authenticated, checkpointed KLICKE navigation reconstruction.

DESIGN CHECK: LESSONS 2/3/5; BK_S4K.md. Retain the full intake roster,
including parse failures. Every accepted session must reproduce its independently
exported final document. Both outcome directions obey the same source gates.
"""
from collections import Counter
from pathlib import Path
import json, time
from .week5_bk_klicke_intake import read, write, digest, collection_status
from .week5_bk_s4k_navigation import extract
from .timing_pmap_source import completed


def intake(inputs, mode):
    if set(inputs)!={'intake_complete'}: raise ValueError('Exact intake binding required')
    complete=Path(inputs['intake_complete']).resolve();root=complete.parent;out=root/'output'
    completed(complete,root/'PLAN.json');completed(complete,root/'VERIFIED.json')
    plan=read(root/'PLAN.json');verified=read(root/'VERIFIED.json')
    if plan['module']!='runners.drive.cards.week5_bk_klicke_intake_v2' or verified.get('independent_source_replay') is not True or verified.get('verified') is not True:
        raise ValueError('KLICKE independent whole-source receipt required')
    if plan['config']['mode']!=mode: raise ValueError('Constructed/human source scope mismatch')
    for name in ('INDEX.json','SUMMARY.json'): completed(complete,out/name)
    index=read(out/'INDEX.json');summary=read(out/'SUMMARY.json')
    if len(index)!=summary['sessions'] or (mode=='corpus' and len(index)!=4992): raise ValueError('Wrong source roster')
    if summary['collection_status']!='passes': raise ValueError('Intake collection gate failed')
    if len({r['session'] for r in index})!=len(index): raise ValueError('Duplicate source session')
    return complete,out,index


def source_record(complete,root,row):
    path=(root/row['path']).resolve();path.relative_to(root.resolve())
    completed(complete,path)
    if digest(path)!=row['sha256']: raise ValueError('Indexed source changed')
    record=read(path)
    if record['session']!=row['session']: raise ValueError('Source identity mismatch')
    return record


def project(record):
    if record.get('status')=='parse_failed':
        return dict(session=record['session'],status='source_parse_failed',reason=record['reason'])
    try: return dict(session=record['session'],status='reconstructed',windows={str(w):extract(record,w) for w in (30,60)})
    except (ValueError,UnicodeError) as error:
        return dict(session=record['session'],status='reconstruction_failed',reason=type(error).__name__ if isinstance(error,UnicodeError) else str(error))


def run(output,inputs,config,verification=False):
    if set(config)!={'card','mode','max_new_draws'} or config['card']!='BK-S4.k-source' or config['mode'] not in ('corpus','constructed') or type(config['max_new_draws']) is not int or config['max_new_draws']<1:
        raise ValueError('Frozen S4.k source config required')
    complete,source,index=intake(inputs,config['mode']);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    counts=Counter();censuses={str(w):Counter() for w in (30,60)};manifest=[];new=0;start=time.process_time()
    binding=dict(intake_complete_sha256=digest(complete),source_index_sha256=digest(source/'INDEX.json'))
    for i,row in enumerate(index):
        dest=output/'sessions'/f'{i:05d}.json.gz'
        if verification or not dest.exists():
            value=project(source_record(complete,source,row));new+=1
            if verification:
                if read(dest)!=value: raise ValueError('Independent navigation reconstruction mismatch')
            else: write(dest,value)
        else: value=read(dest)
        if value['session']!=row['session']: raise ValueError('Saved navigation identity mismatch')
        counts[value['status']]+=1
        for w,data in value.get('windows',{}).items(): censuses[w].update(data['census'])
        manifest.append(dict(ordinal=i,session=row['session'],path=dest.relative_to(output).as_posix(),sha256=digest(dest)))
        if not verification:
            (output/'PROGRESS.json').write_text(json.dumps(dict(sessions=i+1,total=len(index),cpu_seconds=time.process_time()-start)),encoding='utf8')
            if i+1<len(index) and (new>=config['max_new_draws'] or (output/'YIELD_REQUEST.json').exists()):
                write(output/'BINDING.json',binding)
                return dict(status='yielded',reason='navigation_session_boundary',completed_units=i+1,new_sessions=new)
    failed=len(index)-counts['reconstructed']
    summary=dict(sessions=len(index),counts=dict(counts),collection_status=collection_status(len(index),failed),
                 windows={w:dict(c) for w,c in censuses.items()},complete_population=True,
                 scientific_effect_computed=False,writer_basis='4992 deduplicated workers and texts, Tian et al.2025 section2.2/3')
    for name,value in [('INDEX.json',manifest),('SUMMARY.json',summary),('BINDING.json',binding)]:
        if verification:
            if read(output/name)!=value: raise ValueError('Navigation aggregate/source binding changed')
        else: write(output/name,value)
    return dict(verified=True,complete_source_replay=True,new_sessions=new) if verification else dict(status='complete',new_sessions=new)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
