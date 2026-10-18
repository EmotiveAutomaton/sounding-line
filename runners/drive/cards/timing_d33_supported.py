"""Separate authorized supported-match D33.pair / pair2 scientific handlers.

DESIGN CHECK: LESSONS3-5, October18. Freeze input-only support before calibration
or outcome fits. A signed planted own effect must survive a simultaneous donor;
null and reverse controls must remain null/reverse. Missing source or undefined
coefficient is invalid. Original full-population question remains open. No P7
baseline or fake-writer result is implied by this supported P6 comparison.
"""
from __future__ import annotations

import math
from pathlib import Path
import time

from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_stats import bind,check_binding
from .timing_d33_supported_source import Sources,calibrate,scientific_rows,INPUTS
from .timing_d33_supported_stats import run

FORECAST_SECONDS=1200
CUMULATIVE_CAP_SECONDS=1800


def configuration(variant):
    if variant not in ('pair','pair2'):raise ValueError('unknown supported-match variant')
    return dict(card='D33.'+variant+'-supported',variant=variant,bootstrap_draws=2000,
                permutations=200,seed=20261018)


def validate(inputs,config):
    if config!=configuration(config.get('variant')) or set(inputs)!=INPUTS or any(type(config[k]) is not int for k in ('bootstrap_draws','permutations','seed')):
        raise ValueError('exact supported D33 inputs/config required')


def binding(inputs,config):
    return dict(config=config,inputs={k:str(Path(v).resolve()) if k=='repo_root' else filehash(v) for k,v in sorted(inputs.items())})


def result(stats,roster,tuning,covariates,variant):
    if stats.get('state')=='complete':primary=stats['primary']['own']
    else:primary=stats
    return dict(card=configuration(variant)['card'],state=primary['state'],primary=primary,
        descriptive=True,original_full_population_question='OPEN: this is a separately authorized smaller supported population',
        coverage=roster['coverage'],calibration=tuning,statistics=stats,
        screen_audit={key:sum(int(word[key]) for value in covariates.values() for word in value['words'].values())
            for key in ('in_prompt','in_visible_text','in_previous_shown_suggestion','on_screen')},
        screen_audit_population='All positive-population-probability P6 occurrences in retained evaluation sessions; scoring rows separately fixed by original D33 eligibility',
        methods=dict(primary='own-history coefficient in joint own+matched-other random-intercept model, same original nuisance values plus screen/current-session cache covariates',
            histories='exact audit-selected earlier completed sessions and token budgets; pair2 excludes current prompt from both histories',
            calibration='both caches tuned on identical supported words within original chronological calibration partition; no evaluation tuning',
            sensitivity='original full-history own alpha and score replaces the supported-calibrated own score; clearly separate from pair2 prompt-excluded primary',
            uncertainty='2000 real-writer resamples; both focal coefficients and original-own sensitivity paired on each draw; histories/weights fixed',
            controls='200 within-real-writer own-surprise permutations and200 within-real-writer outcome permutations; seed20261018; no redraw on undefined fits',
            screen='raw document before first insertion; original prompt plus visible nonprompt text plus earlier displayed suggestion text; no current-event/future content',
            current_cache='same smoothed unigram/bigram formula on currently visible nonprompt text from raw transform; prompt/line boundaries preserved, adjacent typed/API text joined',
            event='Original frozen P6 casefold token/population scoring event; this card does not resolve or alter P7 common-word normalization'))


def execute(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);validate(inputs,config)
    previous=read(output/'ACTIVE_TIME.json')['seconds'] if (output/'ACTIVE_TIME.json').exists() else 0.
    if not math.isfinite(previous) or previous<0:raise ValueError('invalid supported D33 cumulative time')
    elapsed=lambda:previous+time.monotonic()-started
    write_equal(output/'INPUTS.json',binding(inputs,config))
    source=Sources(inputs);variant=config['variant'];roster=source.roster_for(variant)
    # This immutable artifact precedes even calibration, not merely regression.
    write_equal(output/'SUPPORTED_ROSTER.json',roster)
    tuning=calibrate(roster,source.units[variant],source.lookup);write_equal(output/'CALIBRATION.json',tuning)
    ids=sorted({sid for sid,_ in roster['retained_keys']});covariates={}

    def checkpoint(phase,done,total):
        seconds=elapsed();progress(output/'ACTIVE_TIME.json',dict(seconds=seconds))
        progress(output/'PROGRESS.json',dict(phase=phase,done=done,total=total,seconds=seconds))
        if seconds>CUMULATIVE_CAP_SECONDS:raise RuntimeError('supported D33 cumulative cap exceeded')
        return (output/'YIELD_REQUEST.json').exists()

    for sid in ids:
        value=source.covariates(sid);gzip_equal(output/'sessions'/(sid+'.json.gz'),value);covariates[sid]=value
        if checkpoint('screen-source',len(covariates),len(ids)):
            return dict(status='yielded',phase='screen-source',complete=len(covariates),total=len(ids))
    unsupported=[w for w,v in tuning.items() if not v['valid'] and roster['writers'][w]['retained_evaluation_words']]
    if unsupported:
        stats=dict(state='invalid',reason='retained evaluation writers have no supported calibration words',writers=unsupported)
    elif not roster['retained_keys']:
        stats=dict(state='invalid',reason='no supported original evaluation words')
    else:
        rows=scientific_rows(source.saved,roster,source.units[variant],source.lookup,tuning,covariates)
        gzip_equal(output/'DESIGN.json.gz',rows);source_seconds=elapsed()
        def fitted(receipt):
            if receipt['blocks']==1 and not (output/'FIRST_TENTH.json').exists():
                projection=2*(source_seconds+10*receipt['measured_block_seconds'])
                write_equal(output/'FIRST_TENTH.json',dict(**receipt,active_seconds=elapsed(),projected_cpu_seconds=projection,
                    forecast_cpu_seconds=FORECAST_SECONDS,source_seconds=source_seconds,
                    method='Source-inclusive first200paired bootstrap refits in both models plus20controls of both types; extrapolated and doubled for full fresh verification'))
            return checkpoint('joint-inference',receipt['blocks'],10)
        stats=run(rows,draws=config['bootstrap_draws'],permutations=config['permutations'],seed=config['seed'],
                  checkpoint=output/'inference',checkpoint_callback=fitted)
        if stats.get('status')=='yielded':return dict(stats,card=config['card'])
    primary=result(stats,roster,tuning,covariates,variant);write_equal(output/'PRIMARY.json',primary)
    artifacts=['INPUTS.json','SUPPORTED_ROSTER.json','CALIBRATION.json','PRIMARY.json']
    artifacts += [p.relative_to(output).as_posix() for p in sorted((output/'sessions').glob('*.gz'))]
    artifacts += [p.relative_to(output).as_posix() for p in sorted((output/'inference').glob('*.json'))]
    artifacts += [name for name in ('DESIGN.json.gz','FIRST_TENTH.json') if (output/name).exists()]
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,artifacts)
    checkpoint('complete',1,1)
    return primary


def verify(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);validate(inputs,config);check_binding(output,inputs,config)
    if read(output/'INPUTS.json')!=binding(inputs,config):raise ValueError('supported inputs changed')
    source=Sources(inputs);variant=config['variant'];roster=source.roster_for(variant)
    if roster!=read(output/'SUPPORTED_ROSTER.json'):raise ValueError('supported roster differs from frozen audit')
    tuning=calibrate(roster,source.units[variant],source.lookup)
    if tuning!=read(output/'CALIBRATION.json'):raise ValueError('paired calibration differs from source')
    covariates={}
    for sid in sorted({sid for sid,_ in roster['retained_keys']}):
        value=source.covariates(sid)
        if value!=gzread(output/'sessions'/(sid+'.json.gz')):raise ValueError('screen covariates differ from raw source')
        covariates[sid]=value
    unsupported=[w for w,v in tuning.items() if not v['valid'] and roster['writers'][w]['retained_evaluation_words']]
    if unsupported:stats=dict(state='invalid',reason='retained evaluation writers have no supported calibration words',writers=unsupported)
    elif not roster['retained_keys']:stats=dict(state='invalid',reason='no supported original evaluation words')
    else:
        rows=scientific_rows(source.saved,roster,source.units[variant],source.lookup,tuning,covariates)
        if rows!=gzread(output/'DESIGN.json.gz'):raise ValueError('supported design differs from source')
        stats=run(rows,draws=config['bootstrap_draws'],permutations=config['permutations'],seed=config['seed'])
    primary=result(stats,roster,tuning,covariates,variant)
    if primary!=read(output/'PRIMARY.json'):raise ValueError('supported primary differs from fresh full inference')
    seconds=read(output/'ACTIVE_TIME.json')['seconds']+time.monotonic()-started
    if seconds>CUMULATIVE_CAP_SECONDS:raise RuntimeError('supported D33 verification cumulative cap exceeded')
    return dict(verified=True,primary=primary['primary'],cumulative_seconds=seconds)
