"""Separate source-only PMAP recovery; scientific implementation unchanged.

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
from .timing_pmap_source_recovery import Sources,dictionary
from .timing_pmap_source import INPUTS
from datetime import datetime
from .timing_pmap_stats import prepare,fake_one,summarize

CONFIG=dict(card='PMAP',bootstrap_draws=2000,permutations=200,seed=20261018)
FORECAST_SECONDS=1800
EXTRA_INPUTS=frozenset(('failed_plan','failed_record','source_preflight'))
CUMULATIVE_CAP_SECONDS=5400


def validate(config):
    if config!=CONFIG or any(type(config[k]) is not int for k in ('bootstrap_draws','permutations','seed')):
        raise ValueError('exact frozen PMAP configuration required')


def input_binding(inputs,config):
    return dict(config=config,inputs={k:str(Path(v).resolve()) if k=='repo_root' else filehash(v) for k,v in sorted(inputs.items())})


def recovery(inputs, config):
    """Authenticate the first failed attempt, full metadata preflight and its cost."""
    validate(config)
    if set(inputs)!=INPUTS|EXTRA_INPUTS: raise ValueError('exact PMAP recovery inputs required')
    base={k:inputs[k] for k in INPUTS}
    plan_path=Path(inputs['failed_plan']).resolve();failed_path=Path(inputs['failed_record']).resolve()
    if plan_path.name!='PLAN.json' or failed_path!=plan_path.parent/'FAILED.json':raise ValueError('failed attempt paths differ')
    plan,failed=read(plan_path),read(failed_path);root=Path(base['repo_root']).resolve()
    if plan['module']!='runners.drive.cards.timing_pmap' or plan['config']!=CONFIG or plan['inputs']!=base:
        raise ValueError('original PMAP source/configuration differs')
    if failed.get('status')!='FAILED' or failed.get('engineering_retry_available') is not True:
        raise ValueError('PMAP engineering retry unavailable')
    if plan['max_wall_seconds']!=CUMULATIVE_CAP_SECONDS or plan['forecast_cpu_seconds']!=FORECAST_SECONDS:
        raise ValueError('original PMAP limits differ')
    for name,expected in plan['pins'].items():
        if filehash(root/name)!=expected:raise ValueError('original source pin changed')
    stderr=plan_path.parent/'execute.stderr.log'
    if "ValueError: source session populations differ" not in stderr.read_text(encoding='utf8'):
        raise ValueError('failure is not the population preflight defect')
    oldout=plan_path.parent/'output'
    if {p.relative_to(oldout).as_posix() for p in oldout.rglob('*') if p.is_file()}!={'INPUT_BINDING.json'}:
        raise ValueError('original attempt passed source initialization')
    if read(oldout/'INPUT_BINDING.json')!=input_binding(base,config):raise ValueError('original input binding differs')
    owner=read(plan_path.parent/'OWNER.json')
    if owner['plan_sha256']!=filehash(plan_path):raise ValueError('failed owner plan differs')
    prior=(datetime.fromisoformat(failed['at'])-datetime.fromisoformat(owner['at'])).total_seconds()
    if not math.isfinite(prior) or prior<0 or prior>=CUMULATIVE_CAP_SECONDS:raise ValueError('invalid original attempt cost')
    preflight=read(inputs['source_preflight'])
    if (preflight.get('status')!='PASSED' or preflight['input_binding']!=input_binding(base,config)
        or preflight['failed_plan_sha256']!=filehash(plan_path) or preflight['failed_record_sha256']!=filehash(failed_path)
        or preflight['source_sha256']!=filehash(Path(__file__).with_name('timing_pmap_source_recovery.py'))):
        raise ValueError('source preflight authentication differs')
    identity=dict(failed_plan_sha256=filehash(plan_path),failed_record_sha256=filehash(failed_path),
        failed_stderr_sha256=filehash(stderr),failed_owner_sha256=filehash(plan_path.parent/'OWNER.json'),
        preflight_sha256=filehash(inputs['source_preflight']),charged_prior_seconds=prior,
        cumulative_cap_seconds=CUMULATIVE_CAP_SECONDS,population=preflight['population'])
    return base,identity,preflight


def check_preflight(sources, preflight):
    if sources.population!=preflight['population'] or [r['session'] for r in preflight['units']]!=sorted(sources.p2):
        raise ValueError('preflight source population changed')
    return {r['session']:r['source_hashes'] for r in preflight['units']}


def assignments(rows):
    rng=np.random.default_rng(CONFIG['seed']); labels=np.array([r['writer'] for r in rows],dtype=object)
    for _ in range(CONFIG['permutations']):
        yield {r['session']:str(w) for r,w in zip(rows,rng.permutation(labels))}


def execute(output:Path,inputs:dict,config:dict)->dict:
    validate(config); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic(); base,identity,preflight=recovery(inputs,config)
    write_equal(output/'RECOVERY_SOURCE.json',identity)
    timing=output/'ACTIVE_TIME.json'
    previous=float(read(timing)['seconds']) if timing.exists() else identity['charged_prior_seconds']
    elapsed=lambda:previous+time.monotonic()-started
    binding=input_binding(inputs,config); write_equal(output/'INPUT_BINDING.json',binding)
    sources=Sources(base); expected=check_preflight(sources,preflight); rows=[]; total=len(sources.p2)

    def checkpoint(phase,done,total_units):
        seconds=elapsed(); progress(timing,dict(seconds=seconds))
        if seconds>CUMULATIVE_CAP_SECONDS:raise RuntimeError('PMAP cumulative time cap exceeded')
        progress(output/'PROGRESS.json',dict(phase=phase,done=done,total=total_units,active_seconds=seconds))
        if (output/'YIELD_REQUEST.json').exists():
            return dict(status='yielded',phase=phase,completed=done,total=total_units,active_seconds=seconds,
                resume='same PLAN/config; authenticate completed session/permutation receipts; skip exact saved units')
        return None

    for sid in sorted(sources.p2):
        dest=output/'sessions'/(sid+'.json.gz'); receipt=output/'sessions'/(sid+'.receipt.json')
        source_binding=sources.unit_binding(sid)
        if source_binding!=expected[sid]:raise ValueError('preflight unit source changed')
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
    artifacts=['RECOVERY_SOURCE.json','INPUT_BINDING.json','STYLE_DICTIONARY.json','PROFILES.json.gz','PRIMARY.json']
    artifacts += [p.relative_to(output).as_posix() for folder in ('sessions','permutations') for p in sorted((output/folder).glob('*'))]
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,artifacts)
    checkpoint('complete',200,200)
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic(); validate(config); output=Path(output); check_binding(output,inputs,config)
    base,identity,preflight=recovery(inputs,config)
    if read(output/'RECOVERY_SOURCE.json')!=identity:raise ValueError('recovery source identity changed')
    if read(output/'INPUT_BINDING.json')!=input_binding(inputs,config):raise ValueError('input binding changed')
    sources=Sources(base); expected=check_preflight(sources,preflight); rows=[]
    for sid in sorted(sources.p2):
        row=sources.session(sid)
        if row['source_hashes']!=expected[sid]:raise ValueError('preflight unit source changed')
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
    total=float(read(output/'ACTIVE_TIME.json')['seconds'])+time.monotonic()-started
    if total>CUMULATIVE_CAP_SECONDS:raise RuntimeError('PMAP cumulative verification cap exceeded')
    return dict(verified=True,primary=result['primary'],cumulative_seconds=total,charged_prior_seconds=identity['charged_prior_seconds'])
