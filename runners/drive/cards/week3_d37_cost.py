"""D37 whole-design cost probe, no partial scientific result.

DESIGN CHECK: LESSONS 3-5. NULL/ALTERNATIVE have identical workload. Complete
all five largest recipient units and one entire constructed world, then fresh
replay, before forecasting. No dropping unsupported fit or reducing references.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week3_d37_workload as w
from . import week3_d37_readers as m
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress

CONFIG=dict(card='D37-cost',schema=1,seed=w.SEED,recipients=5,arms=2,world=20,safety_factor=3)


def probe(output,label,rows,arrays,parts,y,selected):
    prepared={}; preprocess=[]; times=[]; histories=[]; results=[]
    for recipient in selected:
        start=time.process_time(); prepared[recipient]=m.prepare(rows,arrays,parts[recipient]); preprocess.append(time.process_time()-start)
    for arm in range(2):
        start=time.process_time(); labels=y if arm==0 else m.permute_targets(rows,y,w.SEED)
        history=m.prefix_counts(rows,labels); histories.append(time.process_time()-start)
        for recipient in selected:
            start=time.process_time(); predicted,fit=m.fit_recipient(rows,labels,prepared[recipient],history)
            # Include actual proper-score/session aggregation cost, without
            # exposing or interpreting the partial probe's scientific value.
            w.session_values(predicted)
            times.append(time.process_time()-start)
            results.append(dict(arm=arm,recipient=recipient,predictions=predicted,fit=fit))
            progress(Path(output)/'PROGRESS.json',dict(phase=label,completed=len(results),total=2*len(selected)))
    return results,dict(preprocess_max=max(preprocess),fit_max=max(times),history_max=max(histories),recipients=len(parts))


def forecast(timings):
    def component(t):return t['preprocess_max']*t['recipients']+(w.PERMUTATIONS+1)*(t['history_max']+t['fit_max']*t['recipients'])
    human=component(timings['human']); calibration=w.WORLDS*component(timings['constructed'])
    # Both passes and a frozen factor, plus a complete reporting allowance.
    return dict(human_cpu_seconds=6*(human+60),calibration_cpu_seconds=6*(calibration+60),
                full_cpu_seconds=6*(human+calibration+120),both_passes=True,safety_factor=3,worlds=w.WORLDS,
                human_recipients=41,permutations=w.PERMUTATIONS,bootstrap=w.BOOTSTRAP,scientific_admission=False)


def one_pass(output,inputs,config,verifying=False,loader=w.source):
    if config!=CONFIG:raise ValueError('Frozen cost configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config)
    if verifying and read(output/'BINDING.json')!=binding:raise ValueError('Changed cost binding')
    rows,arrays,parts,y,excluded=loader(inputs)
    counts={r:sum(row['session'] in set(p['train']) for row in rows) for r,p in parts.items()}
    selected=sorted(parts,key=lambda r:(-counts[r],r))[:config['recipients']]
    human,ht=probe(output,'verify-human' if verifying else 'human',rows,arrays,parts,y,selected)
    cr,ca,cp,cy,metadata=w.world(config['world'])
    constructed,ct=probe(output,'verify-constructed' if verifying else 'constructed',cr,ca,cp,cy,sorted(cp))
    record=dict(human=human,constructed=constructed)
    meta=dict(mode='cost-only',human_rows=len(rows),total_recipients=len(parts),selected=selected,excluded_recipients=len(excluded),constructed_world=config['world'],scientific_admission=False)
    if verifying:
        if read(output/'PRIVATE_FITS.json')!=record or read(output/'PROBE.json')!=meta:raise ValueError('Fresh complete cost-unit replay differs')
    else:
        write_equal(output/'BINDING.json',binding);write_equal(output/'PRIVATE_FITS.json',record);write_equal(output/'PROBE.json',meta)
    timing=dict(human=ht,constructed=ct)
    write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),timing)
    if verifying:
        previous=read(output/'EXECUTE_TIMING.json')
        worst={name:{key:max(value,previous[name][key]) for key,value in row.items()} for name,row in timing.items()}
        write_equal(output/'FORECAST.json',forecast(worst))
    return dict(verified=True,full_cost_unit_replay=True) if verifying else dict(status='complete',timing_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config,True)
