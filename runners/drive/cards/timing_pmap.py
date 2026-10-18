"""PMAP primary, all seven channels, and 200 paired fake-person controls.

DESIGN CHECK: LESSONS 3-5, October 18. Unique duplicated fingerprints identify
at 100%; identical fingerprints tie at chance. Signed/null/reversed serialized
fixtures validate the entire primary and fresh source reconstruction. Source
mutation, changed fixed configuration, or absent profiles cannot become nulls.
Owner alone dispatches under batch_runtime_v3 and the preserved cumulative cap.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
import time

import numpy as np

from .timing_census import read,write,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_stats import bind,check_binding
from .timing_pmap_source import Sources,dictionary
from .timing_pmap_stats import prepare,fake_one,summarize

CONFIG=dict(card='PMAP',bootstrap_draws=2000,permutations=200,seed=20261018)
FORECAST_SECONDS=1800


def validate(config):
    if config!=CONFIG or any(type(config[k]) is not int for k in ('bootstrap_draws','permutations','seed')):
        raise ValueError('exact frozen PMAP configuration required')


def input_binding(inputs,config):
    return dict(config=config,inputs={k:str(Path(v).resolve()) if k=='repo_root' else filehash(v) for k,v in sorted(inputs.items())})


def assignments(rows):
    rng=np.random.default_rng(CONFIG['seed']); labels=np.array([r['writer'] for r in rows],dtype=object)
    for _ in range(CONFIG['permutations']):
        yield {r['session']:str(w) for r,w in zip(rows,rng.permutation(labels))}


def execute(output:Path,inputs:dict,config:dict)->dict:
    validate(config); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic(); timing=output/'ACTIVE_TIME.json'
    previous=float(read(timing)['seconds']) if timing.exists() else 0.
    elapsed=lambda:previous+time.monotonic()-started
    binding=input_binding(inputs,config); write_equal(output/'INPUT_BINDING.json',binding)
    sources=Sources(inputs); rows=[]; total=len(sources.p2)

    def checkpoint(phase,done,total_units):
        seconds=elapsed(); progress(timing,dict(seconds=seconds))
        progress(output/'PROGRESS.json',dict(phase=phase,done=done,total=total_units,active_seconds=seconds))
        if (output/'YIELD_REQUEST.json').exists():
            return dict(status='yielded',phase=phase,completed=done,total=total_units,active_seconds=seconds,
                resume='same PLAN/config; authenticate completed session/permutation receipts; skip exact saved units')
        return None

    for sid in sorted(sources.p2):
        dest=output/'sessions'/(sid+'.json.gz'); receipt=output/'sessions'/(sid+'.receipt.json')
        source_binding=sources.unit_binding(sid)
        if receipt.exists():
            saved=read(receipt)
            if saved['source_hashes']!=source_binding or saved['sha256']!=filehash(dest):
                raise ValueError('session checkpoint binding changed')
            row=gzread(dest)
        else:
            row=sources.session(sid)
            if row['source_hashes']!=source_binding:raise ValueError('session source changed during extraction')
            gzip_equal(dest,row); write_equal(receipt,dict(source_hashes=source_binding,sha256=filehash(dest)))
        rows.append(row)
        yielded=checkpoint('sessions',len(rows),total)
        if yielded:return yielded
    roster=dictionary(rows); write_equal(output/'STYLE_DICTIONARY.json',roster)
    prepared=prepare(rows,roster); gzip_equal(output/'PROFILES.json.gz',prepared)
    source_time=output/'SOURCE_PHASE_TIME.json'
    if not source_time.exists():write_equal(source_time,dict(seconds=elapsed()))
    extraction_seconds=float(read(source_time)['seconds']); fakes=[]; measured_fake_seconds=0.
    for index,assignment in enumerate(assignments(rows)):
        dest=output/'permutations'/(str(index).zfill(3)+'.json.gz')
        receipt=output/'permutations'/(str(index).zfill(3)+'.receipt.json')
        if receipt.exists():
            measured=read(receipt)
            if measured['sha256']!=filehash(dest):raise ValueError('permutation checkpoint changed')
            value=gzread(dest)
            if value['assignment']!=assignment:raise ValueError('permutation assignment changed')
        else:
            unit_start=time.monotonic()
            value=fake_one(rows,roster,prepared,assignment); gzip_equal(dest,value)
            measured=dict(sha256=filehash(dest),elapsed_seconds=time.monotonic()-unit_start)
            write_equal(receipt,measured)
        if not math.isfinite(measured['elapsed_seconds']) or measured['elapsed_seconds']<0:raise ValueError('invalid control timing receipt')
        measured_fake_seconds+=measured['elapsed_seconds']
        fakes.append(value)
        if len(fakes)==20 and not (output/'FIRST_TENTH.json').exists():
            # Includes all source extraction, all channels and real inference,
            # 20 complete fake controls, and a full fresh verification allowance.
            overhead=max(0.,elapsed()-extraction_seconds-measured_fake_seconds)
            projection=2*(extraction_seconds+overhead+measured_fake_seconds*10)
            write_equal(output/'FIRST_TENTH.json',dict(completed_sessions=total,total_sessions=total,
                completed_permutations=20,total_permutations=200,active_seconds=elapsed(),
                projected_cpu_seconds=projection,forecast_cpu_seconds=FORECAST_SECONDS,
                source_phase_seconds=extraction_seconds,measured_control_seconds=measured_fake_seconds,resume_and_checkpoint_overhead_seconds=overhead,
                method='twice measured full source/real work plus extrapolated all-channel 200-control work; includes fresh verification',
                output_bytes_so_far=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())))
        yielded=checkpoint('permutations',len(fakes),200)
        if yielded:return yielded
    result=summarize(prepared,fakes)
    result['source_audit']=dict(sessions=len(rows),writers=len({r['writer'] for r in rows}),
        canonical_choice_disagreements=sum(r['canonical_choice_disagreements'] for r in rows),
        internal_added_characters=sum(r['internal_added_characters'] for r in rows),
        excluded_api_characters=sum(r['excluded_api_characters'] for r in rows),
        accepted_characters=sum(r['accepted_characters'] for r in rows),
        timing_modes=dict(Counter(r['tc_timing_mode'] for r in rows)))
    write_equal(output/'PRIMARY.json',result)
    artifacts=['INPUT_BINDING.json','STYLE_DICTIONARY.json','PROFILES.json.gz','PRIMARY.json']
    artifacts += [p.relative_to(output).as_posix() for folder in ('sessions','permutations') for p in sorted((output/folder).glob('*'))]
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,artifacts)
    checkpoint('complete',200,200)
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    validate(config); output=Path(output); check_binding(output,inputs,config)
    if read(output/'INPUT_BINDING.json')!=input_binding(inputs,config):raise ValueError('input binding changed')
    sources=Sources(inputs); rows=[]
    for sid in sorted(sources.p2):
        row=sources.session(sid)
        if row!=gzread(output/'sessions'/(sid+'.json.gz')):raise ValueError('saved session does not reconstruct from source')
        rows.append(row)
    roster=dictionary(rows)
    if roster!=read(output/'STYLE_DICTIONARY.json'):raise ValueError('shared style dictionary changed')
    prepared=prepare(rows,roster)
    if prepared!=gzread(output/'PROFILES.json.gz'):raise ValueError('profiles failed fresh reconstruction')
    fakes=[]
    for index,assignment in enumerate(assignments(rows)):
        value=fake_one(rows,roster,prepared,assignment)
        if value!=gzread(output/'permutations'/(str(index).zfill(3)+'.json.gz')):raise ValueError('fake control failed fresh reconstruction')
        fakes.append(value)
    result=summarize(prepared,fakes); saved=read(output/'PRIMARY.json')
    audit=dict(sessions=len(rows),writers=len({r['writer'] for r in rows}),
        canonical_choice_disagreements=sum(r['canonical_choice_disagreements'] for r in rows),
        internal_added_characters=sum(r['internal_added_characters'] for r in rows),
        excluded_api_characters=sum(r['excluded_api_characters'] for r in rows),
        accepted_characters=sum(r['accepted_characters'] for r in rows),
        timing_modes=dict(Counter(r['tc_timing_mode'] for r in rows)))
    result['source_audit']=audit
    if result!=saved:raise ValueError('primary failed fresh source reconstruction')
    return dict(verified=True,primary=result['primary'])
