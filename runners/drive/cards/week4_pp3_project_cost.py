"""Measure the commissioned PP3.p1 whole-project route without scoring a result.

DESIGN CHECK: LESSONS 1d/2 and 3-5 reread in this continuous build.
NULL/ALTERNATIVE: original constant and separable known cases remain required.
Whole-project selection is seed-fixed before outcomes; partial projects, missing
authors, altered matrices, source changes and failed independent replay refuse.
Only runtime fingerprints and census counts are emitted, never empirical scores.
"""
from pathlib import Path
import hashlib
import time
import numpy as np
from . import week3_pp3_followups as original
from . import week3_pp3_analysis as model
from .timing_p6 import write_equal, progress
from .timing_census import read, filehash


def configuration(mode):
    if mode not in ('constructed', 'cost'):
        raise ValueError('Cost-only mode required')
    return dict(card='PP3.p1-project-cost', mode=mode, projects=3,
                selection_seed=20261102, full_projects=5, timing_draws=2,
                full_draws_per_bank=200, bootstrap=2000, family='p')


def subset(arrays, count=3):
    x,c,y,p,a=arrays
    ids=np.unique(p)
    if len(ids)!=5 or count!=3:
        raise ValueError('Frozen five-project source and three-project floor required')
    order=np.random.default_rng(20261102).permutation(ids)
    chosen=order[:count]
    keep=np.flatnonzero(np.isin(p,chosen))
    selected=tuple(v[keep].copy() for v in arrays)
    old_authors, mapped=np.unique(selected[4],return_inverse=True)
    _,mapped_projects=np.unique(selected[3],return_inverse=True)
    selected=(*selected[:3],mapped_projects,mapped)
    if any(len(np.unique(p[a==identity]))!=1 for identity in np.unique(a)):
        raise ValueError('Author is not project scoped')
    census=dict(source_rows=len(y),source_projects=len(ids),source_authors=len(np.unique(a)),
                selected_rows=len(keep),selected_projects=len(chosen),selected_authors=len(old_authors),
                source_project_rows={str(int(k)):int(np.sum(p==k)) for k in ids},
                selected_project_ids=[int(k) for k in chosen],selection_order=[int(k) for k in order],
                selected_source_ordinal_sha256=hashlib.sha256(keep.astype('<i8').tobytes()).hexdigest())
    assert len(keep)==sum(census['source_project_rows'][str(int(k))] for k in chosen)
    return selected,census


def fingerprints(value):
    return {k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in value.items()}


def calculate(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode')):
        raise ValueError('Frozen configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    clock=time.process_time();known=original.known_answers('p');known_cpu=time.process_time()-clock
    clock=time.process_time()
    if config['mode']=='constructed':
        if inputs:raise ValueError('Constructed cost has no human inputs')
        arrays=original.wide_fixture()
    else:
        arrays,_=original.source(inputs,'main')
    (x,c,y,p,a),census=subset(arrays)
    source_cpu=time.process_time()-clock
    clock=time.process_time();design=original.designs(x,c,p,'p',1.)
    design_cpu=time.process_time()-clock
    clock=time.process_time();real=original.evaluate(design,y,p,a,True)
    fit_times=[time.process_time()-clock];banks=[]
    for bank,groups in enumerate((p,a)):
        rng=np.random.default_rng(model.CONTRACT['seed']+bank);records=[]
        for draw in range(config['timing_draws']):
            progress(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',bank=bank,draw=draw))
            clock=time.process_time();record=original.evaluate(design,model.permute(y,groups,rng),p,a,True)
            fit_times.append(time.process_time()-clock);records.append(record)
        banks.append(records)
    clock=time.process_time()
    # Full-shape timing only. Repeated timing records are never an inferential bank.
    refs={k:np.array([[r[k] for r in bank] for bank in banks]) for k in real}
    refs={k:np.tile(v,(1,100,*([1]*(v.ndim-2)))) for k,v in refs.items()}
    assert all(v.shape[1]==200 for v in refs.values())
    rng=np.random.default_rng(model.CONTRACT['seed']+97)
    for kind in ('author','project'):
        weights=model.resample_weights(a,p,kind,rng,2000)
        model.summarize(real,refs,weights,np.bincount(a))
        original.primary_draws(real,refs,weights,'p')
    summary_cpu=time.process_time()-clock
    payload=dict(config=config,census=census,known_checks=known,
                 input_sha256={k:filehash(Path(v)/'COMPLETE.json') if Path(v).is_dir() else filehash(v) for k,v in inputs.items()},
                 real_fingerprint=fingerprints(real),timing_fingerprints=[[fingerprints(r) for r in bank] for bank in banks],
                 complete_project_selection=True,complete_source_replay=True,
                 empirical_scores_reported=False,scientific_admission=False,
                 timing_only_repeated_bank=True)
    timing=dict(known_cpu=known_cpu,source_cpu=source_cpu,design_cpu=design_cpu,
                fit_cpu=fit_times,summary_cpu=summary_cpu)
    if verifying:
        if read(output/'PROBE.json')!=payload:raise ValueError('Independent cost replay differs')
    else:write_equal(output/'PROBE.json',payload)
    write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),timing)
    if verifying:
        first=read(output/'EXECUTE_TIMING.json')
        fixed=sum(max(first[k],timing[k]) for k in ('known_cpu','source_cpu','design_cpu','summary_cpu'))
        fit=max(first['fit_cpu']+timing['fit_cpu'])
        forecast=6*(fixed+401*fit)+30
        write_equal(output/'FORECAST.json',dict(full_cpu_seconds=forecast,both_passes=True,safety_factor=3,
                    full_actual_refits=401,full_reference_draws_per_bank=200,bootstrap=2000,
                    repeated_records_only_for_summary_timing=True,scientific_admission=False))
    progress(output/'PROGRESS.json',dict(phase='complete',mode=config['mode']))
    return dict(verified=True,complete_source_and_timing_replay=True,scientific_admission=False) if verifying else dict(status='complete')


def execute(output,inputs,config):return calculate(output,inputs,config)
def verify(output,inputs,config):return calculate(output,inputs,config,True)
