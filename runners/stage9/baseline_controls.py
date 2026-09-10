"""Ordinary maker-dosage comparisons with independent wrong-maker controls.

DESIGN CHECK: M01/M04/X01/X03/X04/X05/X06/X11; LESSONS 3--5, CONTROLS 2/6.
NULL: duplicate evidence reproduces one work, zero dose cannot depend on another
maker, and changed current tasks invalidate matching. ALTERNATIVE: distinct prior
works can alter cheap adaptation while every comparison retains the same current
task and support. Wrong-maker conditions match public causes, not outcome length.
No neural or approximate program gate is required for these ordinary baselines.
"""
import argparse
import copy
from pathlib import Path
import time
from runners.stage9 import baseline_matrix_runtime
from runners.stage9.artifact_comparisons import model_inputs,checkpoint_call
from runners.stage9.baseline_predictions import unit_result as plain_unit,VIEWS
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.matched_controls import validate as validate_control
from runners.stage9.neural_operations import case_inputs
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.recipes import sampled_world
from runners.stage9.series_cases import content_identity
from runners.stage9.training_jobs import cell_identity


def control_inputs(directory,cases_path,scope):
    directory,cases_path=map(inside,(directory,cases_path));identity=read(directory/'IDENTITY.json');done=read(directory/'COMPLETE.json')
    cases,role,sha=case_inputs(cases_path,scope,2 if scope=='pilot' else 0)
    if (done.get('accepted') is not True or done.get('execution_complete') is not True or done['role']!=role
        or done['identity_sha256']!=digest(identity) or identity['case_completion_sha256']!=sha
        or identity['case_sha256']!=file_hash(cases_path/'CASES.json')
        or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('complete matched-control source differs')
    rows=read(directory/'CONTROLS.json');lookup={r['unit']:r['control'] for r in rows}
    all_cases=read(cases_path/'CASES.json')
    if len(lookup)!=len(rows) or set(lookup)!={c['unit'] for c in all_cases}:raise ValueError('matched control cohort incomplete')
    return cases,role,sha,lookup


def unit_result(case,control,models,call,doses):
    validate_control(case['source_worlds'][1:],control,case['role'],control['plan']['key'])
    changed=copy.deepcopy(case)
    for view in VIEWS:changed['views'][view]['earlier']=copy.deepcopy(control['views'][view])
    same=plain_unit(case,models,lambda bundle,view:call(bundle,'same-'+view),doses)
    other=plain_unit(changed,models,lambda bundle,view:call(bundle,'other-'+view),doses)
    for key,row in other['rows'].items():
        view,query=key.split('|');same['rows'][view+'|other-'+query]=row
        if query=='dose0' and row!=same['rows'][key]:raise ValueError('wrong-maker control changed zero-dose evidence or prediction')
    for view in VIEWS:
        if 1 in doses:
            for label in ('','other-'):
                a=same['rows'][view+'|'+label+'dose1'];b=same['rows'][view+'|'+label+'repeat7']
                if a['predictions']!=b['predictions'] or a['validity']!=b['validity']:
                    raise ValueError('duplicate evidence changed ordinary individual support')
    same['costs']=[{**row,'context_condition':label} for label,source in [('same',same),('other',other)] for row in source['costs']]
    same['control_sha256']=digest(control)
    same['matching']='same public conditions and per-work purpose, different persistent maker; resulting text lengths are outcomes, not matched'
    return same


def context(directory,cases_path,models_path,controls_path,scope,doses,*,cell,source=None):
    """Original matching and fitting checks; no writer or capsule execution."""
    directory=inside(directory)
    prefix='baseline-control-pilots' if scope=='pilot' else 'scientific-baseline-controls'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('controlled baseline scope differs')
    cases,role,case_sha,controls=control_inputs(controls_path,cases_path,scope);models=model_inputs(models_path,role)
    training=read(inside(models_path)/'artifact-PREPARED.json')
    used={content_identity(sampled_world(u['lineage'],'both')) for u in training['units']}
    for case in cases:
        case_sources=case['sources']+controls[case['unit']]['sources']
        if len(set(case_sources))!=len(case_sources) or used.intersection(case_sources):raise ValueError('control source overlaps fitting, target or earlier works')
        used.update(case_sources)
    source=source if source is not None else closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'independent-controlled-baseline-v1','scope':scope,'role':role,'source':source,
        'cases':str(inside(cases_path)),'models':str(inside(models_path)),'controls':str(inside(controls_path)),
        'cases_complete_sha256':case_sha,'model_completion_sha256':models['completion_sha256'],
        'controls_complete_sha256':file_hash(inside(controls_path)/'COMPLETE.json'),
        'selected_units':[c['unit'] for c in cases],'doses':list(doses)}
    return identity,cases,models,controls


def run(directory,cases_path,models_path,controls_path,scope,doses):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    identity,cases,models,controls=context(directory,cases_path,models_path,controls_path,scope,doses,cell=cell)
    source=identity['source'];role=identity['role']
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed controlled baseline changed')
            return done
        rows=[]
        for case in cases:
            old=units.get(case['unit'])
            def call(bundle,key):
                return checkpoint_call(directory/'calls'/case['unit'][:16]/(key+'.json'),bundle,
                    lambda:baseline_matrix_runtime.execute(bundle,root=directory/'capsules'),resume_only=old is not None)
            row=unit_result(case,controls[case['unit']],models,call,doses)
            if old is not None and old!=row:raise ValueError('controlled baseline unit changed')
            units.put(case['unit'],row);rows.append(row)
        freeze(directory/'PREDICTIONS.json',rows);verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'role':role,
            'assigned_units':len(cases),'completed_units':len(units.all()),'wall_seconds':time.monotonic()-start,
            'parent_cpu_seconds':time.process_time()-cpu,'outputs':closure([directory/p for p in ('IDENTITY.json','PREDICTIONS.json','units','calls','capsules')]),
            'scientific_admission':False,'scores_computed':False}
        if done['completed_units']!=len(cases):raise ValueError('controlled baseline unit allocation differs')
        freeze(directory/'COMPLETE.json',done);return done


def argument_parser():
    p=argparse.ArgumentParser()
    for name in ('output','cases','models','controls'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    p.add_argument('--doses',type=int,nargs='+',default=[0,1,3,7])
    return p


if __name__=='__main__':
    a=argument_parser().parse_args();run(a.output,a.cases,a.models,a.controls,a.scope,tuple(a.doses))
