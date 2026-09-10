"""Complete-seed factorial effects, distinct from development recipe selection.

DESIGN CHECK: C05/C07/X01/X11; LESSONS 3--5, CONTROLS 6.
NULL: identical recipes give zero, crossed family reversals stay visible, and one
lucky seed cannot replace the equal-seed mean. ALTERNATIVE: paired held-out effects
separate breadth, exposure and their interaction on the complete assigned grid.
Every failed fit/profile remains; any missing member closes its affected contrast.
Three seeds are a small replication set. No pooled family verdict, selection,
generation admission or confirmation follows from these discovery calculations.
"""
from .live_status import read as read_status
import argparse
from collections import defaultdict
import math
from pathlib import Path
import time
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.queue import inside,verify_committed,verify_disposition,verify_sources,writer
from runners.stage9.recipe_selection import PILOT_FITS,fitting_rows
from runners.stage9.scoring import paired_extended,classify,score_json
from runners.stage9.training_jobs import FITS,cell_identity

CONTRASTS={
    'breadth_expert':{'both_expert':1.,'original_expert':-1.},
    'breadth_mixed':{'both_mixed':1.,'original_mixed':-1.},
    'exposure_original':{'original_mixed':1.,'original_expert':-1.},
    'exposure_both':{'both_mixed':1.,'both_expert':-1.},
    'breadth_main':{'both_expert':.5,'both_mixed':.5,'original_expert':-.5,'original_mixed':-.5},
    'exposure_main':{'original_mixed':.5,'both_mixed':.5,'original_expert':-.5,'both_expert':-.5},
    'interaction':{'both_mixed':1.,'both_expert':-1.,'original_mixed':-1.,'original_expert':1.},
}


def summarize(rows,scope,draws=4000):
    expected=FITS if scope=='scientific' else PILOT_FITS if scope=='pilot' else ()
    if not expected or len(rows)!=len(expected) or {(r['family'],r['recipe'],r['seed']) for r in rows}!=set(expected):
        raise ValueError('factorial must retain every assigned fit')
    if any(r['status'] not in ('COMPLETE','FAILED','NOT_RUN') for r in rows):raise ValueError('factorial cannot read unfinished profiles')
    families={}
    for family in ('qwen','smollm'):
        own=[r for r in rows if r['family']==family];lookup={(r['recipe'],r['seed']):r for r in own}
        seeds=sorted({r['seed'] for r in own});effects={}
        for name,coefficients in CONTRASTS.items():
            unavailable=[{'recipe':recipe,'seed':seed,'reason':lookup.get((recipe,seed),{}).get('reason','fit or required profile absent')}
                for recipe in coefficients for seed in seeds if lookup.get((recipe,seed),{}).get('status')!='COMPLETE']
            if unavailable:
                effects[name]={'disposition':'NOT RUN WITH REASON','unavailable':unavailable,'excluded_fits':0};continue
            paired=[];common_units=None
            for seed in seeds:
                fits={recipe:lookup[(recipe,seed)] for recipe in coefficients}
                scores={recipe:{r['source_unit']:r for r in fit['choice_rows']} for recipe,fit in fits.items()}
                reference=next(iter(scores.values()));expected_units=set(reference)
                if any(len(fit['choice_rows'])!=len(scores[recipe]) or set(scores[recipe])!=expected_units for recipe,fit in fits.items()):
                    raise ValueError('factorial profiles have missing, repeated or different source questions')
                if len(expected_units)!=(192 if scope=='scientific' else 2):raise ValueError('full basic choice profile required')
                if common_units is not None and expected_units!=common_units:raise ValueError('seed profiles used different questions')
                common_units=expected_units
                for source_unit in sorted(expected_units):
                    entries=[scores[recipe][source_unit] for recipe in coefficients]
                    fields=('unit','source_unit','domain','law','purpose','target_type','rival_log_score')
                    if any({k:r[k] for k in fields}!={k:entries[0][k] for k in fields} for r in entries):
                        raise ValueError('factorial paired questions or comparator differ')
                    valid=all(r['valid'] for r in entries) and all(f['instrument_accepted'] for f in fits.values())
                    values={recipe:scores[recipe][source_unit]['reader_log_score'] for recipe in coefficients}
                    finite=all(type(x) in (int,float) and math.isfinite(x) for x in values.values())
                    difference=math.fsum(coefficients[k]*v for k,v in values.items()) if valid and finite else None
                    paired.append({**{k:entries[0][k] for k in fields if k!='rival_log_score'},'seed':seed,'valid':valid,
                        'difference':difference,'nonfinite_component':not finite})
            groups={'overall':paired}
            for field in ('domain','law'):
                for value in sorted({r[field] for r in paired}):groups[field+'|'+value]=[r for r in paired if r[field]==value]
            summaries={}
            def estimate_rows(subset,crossed=False):
                if any(r['nonfinite_component'] for r in subset):
                    return {'mean':None,'ci':None,'finite_estimate':False,'extended_mean':'undefined factorial contrast with nonfinite input',
                        'n_targets':len(subset),'n_units':len({r['unit'] for r in subset}),
                        'nonfinite_inputs':sum(r['nonfinite_component'] for r in subset),'excluded_targets':0,
                        'promotion_eligible':False,'disposition':'DESCRIPTIVE'}
                return paired_extended(subset,draws=draws,seed=9021,**({'second_cluster':'seed'} if crossed else {}))
            for group,subset in groups.items():
                valid=all(r['valid'] for r in subset)
                estimate=estimate_rows(subset,True) if valid else None
                per_seed={str(seed):estimate_rows([r for r in subset if r['seed']==seed])
                    for seed in seeds} if valid else {}
                summaries[group]={'estimate':estimate,'per_seed':per_seed,'assigned':len(subset),
                    'invalid':sum(not r['valid'] for r in subset),'nonfinite':sum(r['nonfinite_component'] for r in subset),
                    'disposition':classify(estimate,threshold=.05,descriptive=scope=='pilot') if valid else 'IMPLEMENTATION INVALID'}
            effects[name]={'coefficients':coefficients,'groups':summaries,'paired_rows_sha256':digest(score_json(paired)),
                'excluded_fits':0,'scientific_admission':False}
        families[family]={'effects':effects,'all_seed_profiles':own,'seed_count':len(seeds),
            'generation_scope':'complete basic generation profiles retained per fit; no feasibility-only model admission'}
    return {'families':families,'assigned_fits':len(rows),'scope':scope,'scientific_admission':False,
        'method':'equal-seed paired log-score effects; average repeated public questions before question-by-seed bootstrap',
        'limitation':'only three scientific training seeds per recipe; paired design preserves the seed result and both model families separately',
        'practical_effect_nats':.05,'development_selection_used_for_effect':False}


def complete_job(plan,queue,status,key,module):
    jobs=[j for j in plan['jobs'] if j['id']==key]
    if len(jobs)!=1 or jobs[0]['module']!=module:raise ValueError('factorial points at a different declared operation')
    job=jobs[0];current=status['jobs'][key]
    if current['status'] in ('FAILED','NOT_RUN'):
        verify_disposition(queue,job,current)
        item=read(queue/current['disposition_path'])
        if item['cell_identity']!=digest({'manifest_sha256':digest(plan),'job':job}):raise ValueError('profile failure identity differs')
        return None,{'status':current['status'],'reason':item['reason'],'disposition_sha256':current['disposition_sha256']}
    if current['status']!='COMPLETE':raise ValueError('factorial source job still running')
    verify_committed(queue,job,plan,digest(plan));directory=(REPO/job['produces']).parent
    done=read(directory/'COMPLETE.json');identity=read(directory/'IDENTITY.json')
    if done.get('execution_complete') is not True or done['identity_sha256']!=digest(identity):raise ValueError('source profile incomplete')
    if closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:raise ValueError('source profile changed')
    return directory,{'status':'COMPLETE','complete_sha256':file_hash(directory/'COMPLETE.json')}


def source_queues(manifest,queue,scope,fit_manifest=None,fit_queue=None):
    """A completed fitting queue can precede a separately identified profile queue."""
    if (fit_manifest is None)!=(fit_queue is None):raise ValueError('both fitting manifest and queue are required')
    manifest,queue=map(inside,(manifest,queue))
    fit_manifest=inside(fit_manifest) if fit_manifest is not None else manifest
    fit_queue=inside(fit_queue) if fit_queue is not None else queue
    fits,fit_sha=fitting_rows(fit_manifest,fit_queue,scope)
    plan=read(manifest);status=read_status(queue/'STATUS.json');manifest_sha=digest(plan)
    if (status['manifest_sha256']!=manifest_sha or
        plan['kind']!=('science' if scope=='scientific' else 'prelaunch_rehearsal')):
        raise ValueError('factorial profile queue or scope differs')
    provenance={'profile_manifest_sha256':manifest_sha,'fitting_manifest_sha256':fit_sha,
        'profile_manifest':str(manifest),'profile_queue':str(queue),
        'fitting_manifest':str(fit_manifest),'fitting_queue':str(fit_queue)}
    return fits,plan,status,provenance


def collect(manifest,queue,assignment,scope,fit_manifest=None,fit_queue=None):
    manifest,queue,assignment=map(inside,(manifest,queue,assignment))
    fits,plan,status,provenance=source_queues(manifest,queue,scope,fit_manifest,fit_queue)
    assigned=read(assignment)
    if set(assigned)!={'fits'}:raise ValueError('factorial source assignment changed')
    mapping={(r['family'],r['recipe'],r['seed']):r for r in assigned['fits']}
    if len(mapping)!=len(assigned['fits']) or set(mapping)!={(r['family'],r['recipe'],r['seed']) for r in fits}:
        raise ValueError('each actual fit requires its explicit basic profiles')
    rows=[]
    for fit in fits:
        key=(fit['family'],fit['recipe'],fit['seed']);sources=mapping[key]
        if fit['status']!='COMPLETE':rows.append(fit);continue
        choice,cr=complete_job(plan,queue,status,sources['choice_job'],'runners.stage9.choice_analysis')
        calibration,pr=complete_job(plan,queue,status,sources['calibration_job'],'runners.stage9.calibration_check')
        generations={};receipts={'choice':cr,'calibration':pr}
        if set(sources['generation_jobs'])!={'original','expanded'}:raise ValueError('both declared generation populations required')
        for population,job in sources['generation_jobs'].items():
            path,receipt=complete_job(plan,queue,status,job,'runners.stage9.neural_operations')
            receipts[population]=receipt
            if path is not None:
                ni=read(path/'IDENTITY.json');profile=read(path/'GENERATION.json')
                if ni['operation']!='broad_'+population or ni['adapter_sha256']!=fit['adapter_sha256'] or ni['scope']!=scope:
                    raise ValueError('generation used a different fit or population')
                if profile['expected_attempts']!=(96 if scope=='scientific' else 2):raise ValueError('basic generation sample incomplete')
                generations[population]=profile
        failed=[k for k,r in receipts.items() if r['status']!='COMPLETE']
        if failed:
            rows.append(fit|{'status':'NOT_RUN','reason':'required basic profiles unavailable: '+','.join(failed),'profile_receipts':receipts});continue
        ci=read(choice/'IDENTITY.json');cp=read(choice/'PROFILE.json');paired=read(choice/'PAIRED_ROWS.json')
        ni=read(Path(ci['inputs']['neural']['path'])/'IDENTITY.json');decision=read(calibration/'DECISION.json')
        pi=read(calibration/'IDENTITY.json')
        if (ni['adapter_sha256']!=fit['adapter_sha256'] or ni['family']!=fit['family'] or ni['scope']!=scope
            or ni['operation']!='genuine_choice' or cp['role']!=('discovery' if scope=='scientific' else 'pilot')
            or cp['selection_only'] is not False or cp['assigned_units']!=(192 if scope=='scientific' else 2)
            or ci['package']!=pi['package']):raise ValueError('factorial requires the complete actual held-out basic choice package')
        rows.append(fit|{'choice_rows':paired,'instrument_accepted':decision['instrument_accepted'],
            'generation':generations,'profile_receipts':receipts})
    return rows,provenance


def run(directory,manifest,queue,assignment,scope,fit_manifest=None,fit_queue=None):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    prefix='factorial-analysis-pilots' if scope=='pilot' else 'scientific-factorial-analysis'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('factorial scope differs')
    rows,provenance=collect(manifest,queue,assignment,scope,fit_manifest,fit_queue)
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'complete-seed-factorial-analysis-v1','scope':scope,'source':source,
        'source_queues':provenance,'assignment_sha256':file_hash(inside(assignment)),'rows_sha256':digest(rows)}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed factorial analysis changed')
            return done
        freeze(directory/'FACTORIAL.json',score_json(summarize(rows,scope)));freeze(directory/'FIT_ROWS.json',rows)
        verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/p for p in ('IDENTITY.json','FACTORIAL.json','FIT_ROWS.json')]),'scientific_admission':False}
        freeze(directory/'COMPLETE.json',done);return done


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('output','manifest','queue','assignment'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('fitting-manifest','fitting-queue'):p.add_argument('--'+name,type=Path)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    a=p.parse_args();run(a.output,a.manifest,a.queue,a.assignment,a.scope,a.fitting_manifest,a.fitting_queue)
