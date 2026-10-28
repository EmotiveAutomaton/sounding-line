"""Bounded progress I/O and exact checkpoint continuation for TR4.ic.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-27, especially shared-file retries,
immutable source compatibility and whole-prefix replay. NULL and ALTERNATIVE
use the identical unchanged parent consumer. No scientific gate changes.
Changed bindings, partial prefixes, persistent refusal and replay differences
must fail. A copied checkpoint alone is never independently verified.
"""
from pathlib import Path
import errno
import json
import os
import time
import uuid
from . import week3_tr4_sensitivity as original
from .timing_census import read,filehash
from .timing_pmap_source import completed
from .timing_p6 import write_equal

CONFIGS=original.CONFIGS


def progress(path,value,attempts=101,delay=.05):
    """Keep the last complete status, retry only access/sharing refusal, bounded."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+str(os.getpid())+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(value,sort_keys=True,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    try:
        for attempt in range(attempts):
            try:
                os.replace(temp,path)
                return
            except OSError as exc:
                if not (getattr(exc,'winerror',None) in (5,32,33) or exc.errno in (errno.EACCES,errno.EPERM)) or attempt+1==attempts:
                    raise
                time.sleep(delay)
    finally:
        if temp.exists():
            try:temp.unlink()
            except PermissionError:pass


def retained(manifest_path,config,base_inputs):
    m=read(manifest_path);source=Path(m['source_root']);plan=read(source/'PLAN.json')
    if filehash(source/'PLAN.json')!=m['plan_sha256'] or plan['config']!=config or plan['inputs']!=base_inputs:
        raise ValueError('checkpoint plan/config/input binding differs')
    if m['terminal_name'] not in ('COMPLETE.json','FAILED.json') or filehash(source/m['terminal_name'])!=m['terminal_sha256']:
        raise ValueError('checkpoint terminal binding differs')
    for path,h in plan['pins'].items():
        if filehash(path)!=h:raise ValueError('checkpoint source pin differs')
    names=sorted(m['files'])
    if names!=[f'{i:02d}.json' for i in range(len(names))] or len(names)>len(config['worlds']):
        raise ValueError('checkpoint prefix differs')
    out={}
    for i,name in enumerate(names):
        path=source/'output/cells'/name
        if filehash(path)!=m['files'][name]:raise ValueError('checkpoint bytes differ')
        cell=read(path);dose,seed=config['worlds'][i];world=original.construct(dose,seed)
        if cell['world']!=world or cell['world_sha256']!=original.digest(world) or cell['dose']!=dose or cell['seed']!=seed:
            raise ValueError('checkpoint construction differs')
        if not isinstance(cell['result'],dict):raise ValueError('checkpoint result missing')
        out[i]=(path,cell)
    return out


def run(output,inputs,config,verification=False):
    mode=config.get('mode')
    if mode not in ('constructed','main') or config!=CONFIGS[mode]:raise ValueError('frozen recovery configuration required')
    expected={'parent_landing','resume_manifest'}|({'cost_completion','cost_landing'} if mode=='main' else set())
    if set(inputs)!=expected:raise ValueError('recovery input bindings required')
    base_inputs={k:v for k,v in inputs.items() if k!='resume_manifest'}
    landing=read(inputs['parent_landing'])
    if not landing['full_write_through'] or landing['id']!='S15-TR4-20261027':raise ValueError('complete parent landing required')
    if mode=='main':
        cost=Path(inputs['cost_completion']);gate=read(inputs['cost_landing'])
        completed(cost,cost.parent/'output/SUMMARY.json')
        if not gate['full_write_through'] or not gate['admitted'] or gate['cost_completion_sha256']!=filehash(cost):raise ValueError('complete admitted cost required')
    prefix=retained(inputs['resume_manifest'],config,base_inputs)
    output=Path(output);output.mkdir(parents=True,exist_ok=True);(output/'cells').mkdir(exist_ok=True)
    started=time.process_time();cells=[]
    for index,(dose,seed) in enumerate(config['worlds']):
        world=original.construct(dose,seed);path=output/'cells'/f'{index:02d}.json'
        def update(phase,done,total):
            progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,world=index+1,worlds=len(config['worlds']),done=done,total=total))
            if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('TR4.ic recovery reference-boundary yield')
        if index in prefix and not verification:
            source,cell=prefix[index]
            if path.exists():
                if filehash(path)!=filehash(source):raise ValueError('retained destination differs')
            else:path.write_bytes(source.read_bytes())
            update('retained-execution-checkpoint',index+1,len(prefix))
        else:
            result,_=original.parent.run_analysis(world['census'],outcome_repetitions=config['outcomes'],label_repetitions=config['labels'],bootstraps=config['bootstraps'],progress=update)
            cell=dict(dose=dose,seed=seed,world=world,world_sha256=original.digest(world),result=result)
            if verification:
                if read(path)!=cell:raise ValueError('complete recovery cell replay differs')
            else:write_equal(path,cell)
        cells.append(cell)
    if len({x['world_sha256'] for x in cells})!=len(cells):raise ValueError('duplicate constructed evidence')
    payloads={'SUMMARY.json':original.summarize(cells),'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in base_inputs.items()}),
              'RECOVERY_BINDING.json':dict(inputs={k:filehash(v) for k,v in inputs.items()},retained_execution_cells=len(prefix),verification_reconstructs_every_cell=True)}
    for name,value in payloads.items():
        if verification:
            if read(output/name)!=value:raise ValueError('recovery summary replay differs')
        else:write_equal(output/name,value)
    if not verification and not (output/'TIMING.json').exists():write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,worlds=len(cells),retained_execution_cells=len(prefix)))
    if verification:return dict(verified=True,complete_input_replay=True,retained_cells_freshly_replayed=len(prefix),scientific_admission=False)
    return dict(status='complete',mode=mode,scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
