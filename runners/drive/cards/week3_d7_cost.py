"""D7 complete-writer cost instrument; private predictions, no science verdict.

DESIGN CHECK: LESSONS 3-5. Same work under NULL/ALTERNATIVE. Whole fits,
penalty selection and held-out scoring replay; never forecast from one matrix
solve. Refuse incomplete or changed producer evidence and unsupported units.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,freeze,atomic
from . import week3_d7_models as m

CONFIG=dict(card='D7-cost',schema=1,seed=20261026,writers=5,arms=3,safety_factor=3)


def source(inputs):
    if set(inputs)!={'source_complete','source_rows','source_landing'}:raise ValueError('Input contract differs')
    complete=Path(inputs['source_complete']);c=read(complete);landing=read(inputs['source_landing'])
    if c['status']!='COMPLETE' or not c['fresh_process_verified'] or not landing['full_write_through'] or landing['completion_sha256']!=filehash(complete):raise ValueError('Source admission incomplete')
    for f,h in c['outputs'].items():
        if filehash(complete.parent/f)!=h:raise ValueError('Source output changed')
    rows_path=Path(inputs['source_rows']);key=rows_path.resolve().relative_to(complete.parent.resolve()).as_posix()
    if c['outputs'].get(key)!=filehash(rows_path):raise ValueError('Unbound rows')
    rows=read(rows_path)
    if len(rows)!=16855 or len(m.writers(rows))!=61:raise ValueError('Source population differs')
    return rows


def probe(output,label,rows,selected_limit):
    allgroups=m.writers(rows);groups={};excluded={}
    for w,rs in allgroups.items():
        part,reason=m.partition(rs)
        if reason:excluded[w]=reason
        else:groups[w]=rs
    selected=sorted(groups,key=lambda w:(-len(groups[w]),w))[:selected_limit]
    if not selected:raise ValueError('No supported writers')
    records=[];timings=[]
    for w in selected:
        unit=groups[w];base=m.label_array(unit);observed=np.array([i for i,r in enumerate(unit) if r['dwell_observed']],int)
        for arm in range(CONFIG['arms']):
            started=time.process_time();labels=base.copy()
            if arm:
                order=np.random.default_rng(CONFIG['seed']+arm).permutation(observed)
                labels[observed]=base[order]
            results=[m.compare(unit,response,cost,labels) for response in m.RESPONSES for cost in m.COSTS]
            records.append(dict(writer=w,arm=arm,results=results));timings.append(time.process_time()-started)
            atomic(Path(output)/'PROGRESS.json',dict(phase=label,done=len(records),total=len(selected)*CONFIG['arms']))
            if (Path(output)/'YIELD_REQUEST.json').exists() or (Path(output).parent/'STOP').exists():raise InterruptedError('D7 cost boundary yield')
    return records,dict(supported_writers=len(groups),excluded_writers=len(excluded),all_writers=len(allgroups),selected_writers=len(selected),max_complete_writer_cpu_seconds=max(timings)),excluded


def run(output,inputs,config,verify=False,loader=source):
    if config!=CONFIG:raise ValueError('Frozen cost configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config)
    if (output/'BINDING.json').exists() and read(output/'BINDING.json')!=binding:raise ValueError('Changed binding')
    rows=loader(inputs);human,ht,ex=probe(output,'verify-human' if verify else 'human',rows,config['writers'])
    constructed,ct,cx=probe(output,'verify-constructed' if verify else 'constructed',m.world(),12)
    values={'BINDING.json':binding,'PRIVATE_FITS.json':dict(human=human,constructed=constructed),'SUPPORT.json':dict(exclusions=ex,constructed_exclusions=cx,human_rows=len(rows),timing_only=True,scientific_admission=False)}
    for name,value in values.items():
        if verify:
            if read(output/name)!=value:raise ValueError('Fresh complete fit replay differs: '+name)
        else:freeze(output/name,value)
    timing=dict(human=ht,constructed=ct)
    freeze(output/('VERIFY_TIMING.json' if verify else 'EXECUTE_TIMING.json'),timing)
    if verify:
        previous=read(output/'EXECUTE_TIMING.json');worst={k:max(timing[k]['max_complete_writer_cpu_seconds'],previous[k]['max_complete_writer_cpu_seconds']) for k in timing}
        # Complete six-setting writer work per arm, both phases, full controls
        # and calibration envelope. Reporting allowance covers bootstrap and I/O.
        human_cpu=6*(worst['human']*ht['supported_writers']*401+60)
        calibration_cpu=6*(worst['constructed']*ct['supported_writers']*401*30+60)
        freeze(output/'FORECAST.json',dict(human_cpu_seconds=human_cpu,calibration_cpu_seconds=calibration_cpu,full_cpu_seconds=human_cpu+calibration_cpu,both_passes=True,safety_factor=3,worlds=30,reference_arms=401,settings=6,scientific_admission=False,scope='Complete fitted workload envelope; final gates and reference implementation remain separate'))
    return dict(verified=True,full_fresh_fit_replay=True,timing_only=True) if verify else dict(status='complete',timing_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config,True)
