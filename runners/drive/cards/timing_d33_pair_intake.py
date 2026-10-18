"""D33 paired-history input/support audit only; no regression or outcomes fitted.

DESIGN CHECK: LESSONS3-5, October18. Authenticate and reconstruct the frozen
78,602 rows / 41 writers before matching. Unsupported targets remain explicit,
never disappear from an estimand. Future sessions, outcome-based matching,
changed primary values or a forged checkpoint refuse. This audit cannot make
a scientific positive/negative finding or admit P7's different word event.
"""
from __future__ import annotations

from pathlib import Path
import math
import time

from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal,progress
from .timing_stats import bind,check_binding
from .timing_d33 import make_rows
from .timing_d33_match import primary_roster,matched_other
from .timing_pmap_source import completed,bound_record

CONFIG=dict(card='D33.pair-intake',variants=['pair','pair2'],seed=20261018)
INPUTS={'d33_completion','p6_index','p6_completion','tc_primary','tc_completion'}
PRIMARY_ROWS=78602
PRIMARY_WRITERS=41
FORECAST_SECONDS=600
CUMULATIVE_CAP_SECONDS=1800


def load(inputs,config):
    if config!=CONFIG or type(config['seed']) is not int or set(inputs)!=INPUTS:raise ValueError('exact frozen paired-intake inputs/config required')
    root=Path(inputs['d33_completion']).resolve().parent
    for name in ('PLAN.json','output/D33_INTERMEDIATES.json.gz','output/D33_PRIMARY.json'):
        completed(inputs['d33_completion'],root/name)
    plan=read(root/'PLAN.json')
    if plan['module']!='runners.drive.cards.timing_d33' or plan['config']!=dict(extension=False,bootstrap_draws=2000,seed=20261017):
        raise ValueError('original D33 primary plan differs')
    if plan['inputs']!={k:inputs[k] for k in INPUTS-{'d33_completion'}}:
        raise ValueError('paired input population differs from original primary')
    completed(inputs['p6_completion'],inputs['p6_index']);completed(inputs['tc_completion'],inputs['tc_primary'])
    index=read(inputs['p6_index'])
    if len({r['session'] for r in index})!=len(index):raise ValueError('duplicate P6 session')
    records=[bound_record(inputs['p6_index'],r) for r in index]
    if any((r['session'],r['writer'])!=(i['session'],i['writer']) for r,i in zip(records,index)):
        raise ValueError('P6 indexed identity differs')
    saved=gzread(root/'output/D33_INTERMEDIATES.json.gz')
    mode=read(inputs['tc_primary'])['timing_mode']
    if mode not in ('per_character','first_character_delta'):raise ValueError('original timing support invalid')
    fresh_rows,tuning,exclusions=make_rows(records,mode)
    if fresh_rows!=saved['rows'] or tuning!=saved['tuning'] or exclusions!=saved['exclusions']:
        raise ValueError('original primary rows/tuning do not reconstruct from exact P6 source')
    if len(fresh_rows)!=PRIMARY_ROWS or len({r['writer'] for r in fresh_rows})!=PRIMARY_WRITERS:
        raise ValueError('original 78602-word/41-writer primary population differs')
    roster,by_writer=primary_roster(fresh_rows,records,tuning)
    lookup={r['session']:r for r in records};targets=[]
    for writer,parts in sorted(roster['writers'].items()):
        for split in ('calibration_sessions','evaluation_sessions'):
            for sid in parts[split]:targets.append(dict(writer=writer,session=sid,split=split.split('_')[0]))
    return saved,roster,by_writer,lookup,targets


def unit(target,variant,by_writer,lookup):
    proof,_=matched_other(by_writer,lookup[target['session']],exclude_prompt=variant=='pair2')
    return dict(target=target,variant=variant,proof=proof)


def summary(records,roster,saved):
    variants={}
    for variant in CONFIG['variants']:
        values=[r for r in records if r['variant']==variant]
        unsupported=[r for r in values if not r['proof']['supported']]
        missing_sessions={r['target']['session'] for r in unsupported}
        missing_words=sum(r['session'] in missing_sessions for r in saved['rows'])
        variants[variant]=dict(target_sessions=len(values),supported_sessions=len(values)-len(unsupported),
            unsupported_sessions=[r['target'] for r in unsupported],original_primary_rows=PRIMARY_ROWS,
            unsupported_primary_rows=missing_words,retained_primary_rows=PRIMARY_ROWS,
            original_calibration_sessions_unchanged=True,exact_history_support_complete=not unsupported,scientific_scoring_admitted=False,
            disposition='exact history-size support ready for separately reviewed scientific runner' if not unsupported else 'HOLD: exact history support absent; no row or own-history change authorized')
    return dict(card=CONFIG['card'],status='input_audit_complete',scientific_result=False,
        primary_writers=len(roster['writers']),primary_rows=roster['rows'],variants=variants,
        method='Exact original P6 row reconstruction; only earlier completed other-writer session metadata/token counts used for matching; no regression or outcome-based tuning',
        matching_policy='Same session count and typed-token count, prompt agreement prioritized; only donor excess prefix trimmed at word boundaries, preserving existing sequence breaks',
        remaining='Screen/current-session covariates, matched-history calibration, 200 within-writer permutations and paired writer-bootstrap scientific runner remain separate.')


def execute(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    timing=output/'ACTIVE_TIME.json';previous=float(read(timing)['seconds']) if timing.exists() else 0.
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    write_equal(output/'INPUTS.json',binding)
    saved,roster,by_writer,lookup,targets=load(inputs,config)
    write_equal(output/'PRIMARY_ROSTER.json',roster)
    values=[];total=len(targets)*2
    for target in targets:
        for variant in CONFIG['variants']:
            path=output/'sessions'/variant/(target['session']+'.json')
            # Matching is cheap compared with source reads; fresh recomputation
            # authenticates any prior receipt before it can be reused.
            value=unit(target,variant,by_writer,lookup);write_equal(path,value);values.append(value)
            elapsed=previous+time.monotonic()-started
            progress(timing,dict(seconds=elapsed))
            if elapsed>CUMULATIVE_CAP_SECONDS:raise RuntimeError('paired intake cumulative time cap exceeded')
            progress(output/'PROGRESS.json',dict(completed=len(values),total=total,seconds=elapsed))
            if len(values)>=math.ceil(.1*total) and not (output/'FIRST_TENTH.json').exists():
                write_equal(output/'FIRST_TENTH.json',dict(projected_cpu_seconds=2*elapsed*total/len(values),forecast_cpu_seconds=FORECAST_SECONDS,
                    completed=len(values),total=total,variants_sampled=CONFIG['variants'],method='source-inclusive measured first tenth across both variants extrapolated, doubled for full fresh verification'))
            if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed=len(values),total=total)
    result=summary(values,roster,saved);write_equal(output/'SUMMARY.json',result)
    artifacts=['INPUTS.json','PRIMARY_ROSTER.json','SUMMARY.json']+[p.relative_to(output).as_posix() for p in sorted((output/'sessions').rglob('*.json'))]
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,artifacts)
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);check_binding(output,inputs,config)
    saved,roster,by_writer,lookup,targets=load(inputs,config)
    if roster!=read(output/'PRIMARY_ROSTER.json'):raise ValueError('original primary roster changed')
    values=[]
    for target in targets:
        for variant in CONFIG['variants']:
            value=unit(target,variant,by_writer,lookup)
            if value!=read(output/'sessions'/variant/(target['session']+'.json')):raise ValueError('source-based matched history differs')
            values.append(value)
    result=summary(values,roster,saved)
    if result!=read(output/'SUMMARY.json'):raise ValueError('support summary differs')
    elapsed=float(read(output/'ACTIVE_TIME.json')['seconds'])+time.monotonic()-started
    if elapsed>CUMULATIVE_CAP_SECONDS:raise RuntimeError('paired intake cumulative verification cap exceeded')
    return dict(verified=True,summary=result,cumulative_seconds=elapsed)
