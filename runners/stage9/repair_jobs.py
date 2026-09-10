"""Resumable source-checked training and inference for local consequence rivals.

DESIGN CHECK: C03/X01/X02/X11/X12; LESSONS 3--5, CONTROLS 6.
NULL: reused pilot sources, wrong roles, partial inputs, changed weights and hidden
information refuse acceptance. ALTERNATIVE: complete training-only cohorts fit all
six rivals per view; every inference runs through the public-only capsule and
every resumed unit reconstructs from its actual saved calls. No capability gate
is granted by completing training or computing development predictions.
"""
import argparse
from pathlib import Path
import time
from .artifact_comparisons import audit_execution,checkpoint_call,validate_cases
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .local_repair import task_case,consequence
from .queue import inside,verify_sources,writer
from .repair_features import validate
from .repair_fit import fit,select
from .repair_runtime import execute
from .scoring import score_json
from .training_jobs import cell_identity

VIEWS=('artifact','process_record')


def public_task(task):
    return validate({k:task[k] for k in ('view','current','requested_mark','proposed_edit')})


def sources():
    return closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])


def inputs(directory,scope,training=False):
    directory=inside(directory);done=read(directory/'COMPLETE.json')
    expected=('pilot',) if scope=='pilot' else (('training',) if training else ('development','discovery'))
    if scope not in ('pilot','scientific') or done.get('role') not in expected:
        raise ValueError('local comparator source role or scope mismatch')
    if (done.get('accepted') is not True or done.get('construction_only') is not True
        or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('local comparator construction incomplete or changed')
    cases=read(directory/'CASES.json');validate_cases(cases,done['role'])
    if len(cases)!=done['selected_series'] or len(cases)<(96 if scope=='pilot' else 192):
        raise ValueError('local comparator declared source cohort incomplete')
    return cases,done['role'],file_hash(directory/'COMPLETE.json')


def records(cases):
    rows={view:[] for view in VIEWS}
    for case in cases:
        for view in VIEWS:
            task=task_case(case,view)
            if task.get('realized') is not True:raise ValueError('local comparator task not realized')
            rows[view].append({'unit':case['unit'],'evidence':public_task(task),'target':consequence(task)})
    return rows


def namespace(directory,scope):
    directory=inside(directory)
    root=ROOT/'private'/('repair-baseline-pilots' if scope=='pilot' else 'scientific-repair-baselines')
    if scope not in ('pilot','scientific') or not directory.is_relative_to(root):
        raise ValueError('local comparator output scope mismatch')
    return directory


def complete(directory,identity):
    done=read(directory/'COMPLETE.json')
    if (done.get('cell_identity')!=identity['cell_identity'] or done.get('identity_sha256')!=digest(identity)
        or done.get('accepted') is not True or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('local comparator completion changed or invalid')
    return done


def model_inputs(directory,scope):
    directory=inside(directory);identity=read(directory/'IDENTITY.json');done=complete(directory,identity)
    if identity['operation']!='fit' or identity['scope']!=scope:raise ValueError('wrong consequence fitting package')
    cases,role,sha=inputs(Path(identity['cases']),scope,training=True)
    if sha!=identity['cases_complete_sha256']:raise ValueError('fitting source changed')
    rebuilt=records(cases)
    if rebuilt!=read(directory/'TRAINING_ROWS.json'):raise ValueError('consequence training rows differ from actual source')
    models=read(directory/'MODELS.json');fitting=read(directory/'FIT.json')
    for view in VIEWS:
        if (len(models[view])!=6 or fitting[view]['parameters_sha256']!=digest(models[view])
            or fitting[view]['training_records_sha256']!=digest(rebuilt[view])
            or any(row['converged'] is not True for row in fitting[view]['optimizers'].values())):
            raise ValueError('incomplete or invalid fitted consequence grid')
    return models,rebuilt,file_hash(directory/'COMPLETE.json')


def run_fit(directory,cases_path,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=namespace(directory,scope)
    cases,role,sha=inputs(cases_path,scope,training=True);rows=records(cases)
    source=sources();identity={'cell_identity':cell,'operation':'fit','scope':scope,'role':role,'sources':source,
        'cases':str(inside(cases_path)),'cases_complete_sha256':sha,'training_rows_sha256':digest(rows)}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():return complete(directory,identity)
        freeze(directory/'TRAINING_ROWS.json',rows);models={};fitting={}
        for view in VIEWS:models[view],fitting[view]=fit(rows[view])
        freeze(directory/'MODELS.json',models);freeze(directory/'FIT.json',fitting);verify_sources(source)
        result={'cell_identity':cell,'identity_sha256':digest(identity),'accepted':True,'training_only':True,
            'source_units':len(cases),'models':12,'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'TRAINING_ROWS.json',directory/'MODELS.json',directory/'FIT.json']),
            'scientific_admission':False}
        freeze(directory/'COMPLETE.json',result);return result


def unit_result(case,models,call):
    result={}
    for view in VIEWS:
        task=task_case(case,view)
        if not task['realized']:raise ValueError('declared local task not realized')
        evidence=public_task(task);bundle={'evidence':evidence,'models':models[view]}
        prediction=call(bundle,view)
        if prediction.get('accepted') is not True:raise ValueError('local baseline capsule failed')
        result[view]={'public_task_sha256':digest(evidence),'truth':consequence(task),'call':prediction}
    return {'unit':case['unit'],'results':result}


def run_predict(directory,models_path,cases_path,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=namespace(directory,scope)
    models,training,fit_sha=model_inputs(models_path,scope);cases,role,case_sha=inputs(cases_path,scope)
    # The bounded rehearsal exercises the same unit path on two actual domains.
    if scope=='pilot':cases=[next(c for c in cases if c['private_factors']['domain']==d) for d in ('essay','workshop_doc')]
    queried=records(cases)
    train_sources={r['unit'] for r in training['artifact']}
    if train_sources&{c['unit'] for c in cases}:raise ValueError('local forecast reuses fitting source units')
    for view in VIEWS:
        if {digest(r['evidence']) for r in training[view]}&{digest(r['evidence']) for r in queried[view]}:
            raise ValueError('local forecast contains exact training task copies')
    source=sources();identity={'cell_identity':cell,'operation':'predict','scope':scope,'role':role,'sources':source,
        'models':str(inside(models_path)),'models_complete_sha256':fit_sha,'cases':str(inside(cases_path)),
        'cases_complete_sha256':case_sha,'units':[c['unit'] for c in cases]}
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():return complete(directory,identity)
        def call(case,bundle,view,resume_only=False):
            task={'operation':'repair_baselines','information_sha256':digest(bundle)}
            path=directory/'calls'/case['unit'][:16]/(view+'.json')
            return checkpoint_call(path,{'evidence':bundle,'task':task},lambda:execute(bundle,root=directory/'capsules'),resume_only=resume_only)
        for case in cases:
            old=units.get(case['unit']);row=unit_result(case,models,lambda bundle,view:call(case,bundle,view,old is not None))
            if old is not None and old!=row:raise ValueError('resumed baseline unit differs')
            units.put(case['unit'],row)
        for case in cases:
            if unit_result(case,models,lambda bundle,view:call(case,bundle,view,True))!=units.get(case['unit']):
                raise ValueError('completed baseline unit cannot reconstruct')
        verify_sources(source)
        result={'cell_identity':cell,'identity_sha256':digest(identity),'accepted':True,'expected_units':len(cases),
            'completed_units':len(cases),'calls':2*len(cases),'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'units',directory/'calls',directory/'capsules']),
            'scientific_admission':False}
        freeze(directory/'COMPLETE.json',result);return result


def run_select(directory,predictions_path,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=namespace(directory,scope)
    predictions_path=inside(predictions_path);pi=read(predictions_path/'IDENTITY.json');pd=complete(predictions_path,pi)
    if pi['operation']!='predict' or pi['scope']!=scope or pi['role']!=('pilot' if scope=='pilot' else 'development'):
        raise ValueError('consequence selection requires separate complete development predictions')
    models,training,fit_sha=model_inputs(Path(pi['models']),scope)
    cases,role,case_sha=inputs(Path(pi['cases']),scope)
    if scope=='pilot':cases=[next(c for c in cases if c['private_factors']['domain']==d) for d in ('essay','workshop_doc')]
    if case_sha!=pi['cases_complete_sha256'] or fit_sha!=pi['models_complete_sha256']:
        raise ValueError('consequence selection inputs changed')
    development=records(cases);source=sources()
    identity={'cell_identity':cell,'operation':'select','scope':scope,'sources':source,
        'predictions':str(predictions_path),'predictions_complete_sha256':file_hash(predictions_path/'COMPLETE.json')}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():return complete(directory,identity)
        selection={view:select(models[view],training[view],development[view]) for view in VIEWS}
        # Independently match every prediction used for selecting the rival to the
        # real capsule output. Selection cannot run solely on refabricated logits.
        from .repair_features import predict
        units=Units(predictions_path,pi)
        for case in cases:
            row=units.get(case['unit'])
            if row is None:raise ValueError('missing development unit')
            for view in VIEWS:
                saved=row['results'][view];audit_execution(saved['call']);visible=public_task(task_case(case,view))
                if saved['public_task_sha256']!=digest(visible) or saved['truth']!=consequence(task_case(case,view)):
                    raise ValueError('development prediction task or truth differs')
                if saved['call']['prediction']['predictions']!={k:predict(visible,v) for k,v in models[view].items()}:
                    raise ValueError('development capsule differs from rebuilt probabilities')
        freeze(directory/'SELECTION.json',score_json(selection));verify_sources(source)
        result={'cell_identity':cell,'identity_sha256':digest(identity),'accepted':True,'development_only':True,
            'units':len(cases),'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'SELECTION.json']),'scientific_admission':False}
        freeze(directory/'COMPLETE.json',result);return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('fit','predict','select'))
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--scope',required=True,choices=('pilot','scientific'))
    parser.add_argument('--cases',type=Path);parser.add_argument('--models',type=Path);parser.add_argument('--predictions',type=Path)
    args=parser.parse_args()
    if args.operation=='fit':
        if args.cases is None or args.models is not None or args.predictions is not None:parser.error('fit requires only --cases')
        run_fit(args.output,args.cases,args.scope)
    elif args.operation=='predict':
        if args.cases is None or args.models is None or args.predictions is not None:parser.error('predict requires --cases and --models')
        run_predict(args.output,args.models,args.cases,args.scope)
    else:
        if args.predictions is None or args.cases is not None or args.models is not None:parser.error('select requires only --predictions')
        run_select(args.output,args.predictions,args.scope)
    print('Complete local baseline '+args.operation+'; no scientific capability admitted.',flush=True)


if __name__=='__main__':main()
