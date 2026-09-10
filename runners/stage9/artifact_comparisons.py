"""Checkpointed prospective artifact forecasts; no scoring before completion.

DESIGN CHECK: M01/M04/C08/X01/X02/X05/X06/X07/X11/X12; LESSONS 3--5,
CONTROLS 2/6. NULL: repeated evidence gives the single-work forecast, invalid
program calculations cannot earn a score, and independent baselines remain usable.
ALTERNATIVE: distinct works change complete forecasts within the fixed precision
envelope. Every assigned unit is retained; validity is per required comparator.
This produces predictions, not a scientific verdict or broad model admission.
Evidence views are explicitly frozen before execution. A process-record-only
assignment cannot execute an unrequested artifact estimator or inherit its claim.
"""
import argparse
import copy
from datetime import datetime,timezone
import os
from pathlib import Path
import time

from . import baseline_matrix_runtime,comparison_runtime
from .artifact_preparation import evidence as project_evidence
from .artifact_view import validate
from .artifact_models import validate_prepared,validate_library,validate_choice
from .common import REPO,Units,closure,digest,distribution,file_hash,freeze,read,write
from .construction import register
from .likelihood_table import approximation_comparison
from .queue import inside,verify_sources,writer
from .recipes import parameter_partition,sampled_world
from .scoring import score_json
from .series_cases import content_identity,dose_view,recorded_target,prepare_case,TERMINAL

VIEWS=('artifact','process_record')
DOSES=(0,1,3,7)
ROUTES=('program_mixture','differentiated_maker')


def selected_views(views):
    if (not isinstance(views,(tuple,list)) or not views or
            any(view not in VIEWS for view in views) or len(set(views))!=len(views)):
        raise ValueError('explicit distinct supported evidence views required')
    return tuple(view for view in VIEWS if view in views)


def model_inputs(directory,role):
    directory=inside(directory);done=read(directory/'COMPLETE.json')
    if done.get('accepted') is not True or done.get('training_only') is not True:
        raise ValueError('numerical training package is incomplete or failed')
    if role!='pilot' and done['role']!='training':
        raise ValueError('discarded pilot parameters cannot enter scientific prediction')
    if closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
        raise ValueError('numerical training package outputs changed')
    library=read(directory/'LIBRARY.json')
    fitting_identity=read(directory/'IDENTITY.json')
    prepared={view:read(directory/(view+'-PREPARED.json')) for view in VIEWS}
    for view,data in prepared.items():
        validate_prepared(data,band=fitting_identity['band'],per_domain=fitting_identity['per_domain'],view=view)
    validate_library(library,read(directory/'LIBRARY_FIT.json'),prepared['artifact']['records'],
        {u['unit'] for u in prepared['artifact']['units']},minimum_units=2*fitting_identity['per_domain'])
    models={view:{} for view in VIEWS}
    for key,item in done['models'].items():
        parameters,audit=read(REPO/item['parameters']),read(REPO/item['fit'])
        records=[{k:r[k] for k in ('unit','evidence','target')} for r in prepared[item['view']]['records']]
        validate_choice(parameters,audit,records,item['l2'])
        if audit['converged'] is not True or digest(parameters)!=audit['parameters_sha256'] or parameters['individual'] is not False:
            raise ValueError('failed or mismatched population fit')
        models[item['view']][key]=parameters
    if any(len(v)!=2 for v in models.values()) or len(library['candidates'])!=48:
        raise ValueError('declared numerical candidate grid is incomplete')
    types={view:read(directory/(view+'-TYPE_PRIOR.json')) for view in VIEWS}
    return {'library':library,'models':models,'types':types,'completion_sha256':file_hash(directory/'COMPLETE.json')}


def validate_cases(cases,role):
    register()  # Saved worlds do not trigger construction-time registration.
    if not cases or len({c['unit'] for c in cases})!=len(cases):
        raise ValueError('nonempty unique independent series required')
    source_set=set()
    for case in cases:
        if case.get('realized') is not True or case['role']!=role:
            raise ValueError('unrealized or wrong-partition case')
        worlds=case['source_worlds'];expected='training' if role=='pilot' else role
        hashes=[content_identity(w) for w in worlds]
        if (hashes!=case['sources'] or any(h in source_set for h in hashes) or len(hashes)!=len(set(hashes)) or
            any(parameter_partition(w)!=expected for w in worlds) or
            case['unit']!=digest({'stage9_series_content_v1':hashes})):
            raise ValueError('source identity, independence or parameter partition mismatch')
        source_set.update(hashes)
        rebuilt_case=prepare_case(worlds[0],worlds[1:],case['requested_boundary'],role)
        if any(rebuilt_case.get(k)!=case.get(k) for k in ('realized','unit','target','oracle','private_factors','parameter_partition')):
            raise ValueError('case factors, prospective truth or oracle differ from actual sources')
        target,reason=recorded_target(worlds[0]['trajectory'],case['requested_boundary'])
        if reason or target!=case['target']:raise ValueError('prospective target differs from source')
        previous=[(w,w['trajectory']['steps'],w['trajectory']['stop_kind'] in TERMINAL) for w in worlds[1:]]
        for view in VIEWS:
            rebuilt=project_evidence(worlds[0],worlds[0]['trajectory']['steps'][:case['requested_boundary']],view,previous)
            if rebuilt!=case['views'][view]:raise ValueError('visible input differs from recorded source projection')
    return source_set


def queries(case,view,doses=DOSES):
    if not doses or any(d not in DOSES for d in doses) or len(doses)!=len(set(doses)):
        raise ValueError('explicit distinct supported doses required')
    result={'dose'+str(d):dose_view(case,d,view) for d in doses}
    if 1 in doses:result['repeat7']=dose_view(case,7,view,repeat=True)
    for query in result.values():validate(query)
    return result


def checkpoint_call(path,inputs,call,*,resume_only=False):
    from .saved_replay import active
    replay = active()
    if replay is not None:
        return replay.checkpoint(path, inputs, call, resume_only=resume_only)
    signature=digest(inputs)
    if path.exists():
        saved=read(path)
        if saved['input_sha256']!=signature:raise ValueError('completed capsule call inputs changed')
        audit_execution(saved['result'])
        return saved['result']
    if resume_only:raise ValueError('completed unit is missing an immutable capsule call')
    result=call()
    audit_execution(result)
    freeze(path,{'input_sha256':signature,'result':result})
    return result


def audit_execution(result):
    cap=Path(result['capsule']).resolve();copied=result['copied_sources']
    if not cap.is_relative_to(REPO):raise ValueError('capsule escapes repository')
    if copied['sha256']!=digest(copied['files']) or any(file_hash(cap/p)!=sha for p,sha in copied['files'].items()):
        raise ValueError('copied execution source changed')
    if digest(read(cap/'task.json'))!=copied['task_sha256'] or digest(read(cap/'evidence.json'))!=copied['evidence_sha256']:
        raise ValueError('copied execution input changed')
    for name in ('prediction','receipt'):
        path=cap/'out'/(name+'.json')
        if path.exists() and read(path)!=result.get(name):raise ValueError('saved capsule result differs from actual output')
    if result['accepted']:
        expected={('reader' if p=='reader/__init__.py' else p[:-3].replace('/','.')):sha
                  for p,sha in copied['files'].items() if p.startswith('reader/')}
        if result['rc']!=0 or result['receipt']['loaded_sources']!=expected or result['prediction']['valid'] is not True:
            raise ValueError('accepted execution lacks matching loaded-source output')
    return True


def forecast_unit(case,package,directory,*,doses=DOSES,draws=1024,budget=8000000,control=None,resume_only=False,views=VIEWS):
    """Every route gets the same query; truths stay in this evaluator process."""
    views=selected_views(views)
    if control is not None:
        from .matched_controls import validate as validate_control
        validate_control(case['source_worlds'][1:],control,case['role'],control['plan']['key'])
        changed=copy.deepcopy(case)
        for view in VIEWS:
            changed['views'][view]['earlier']=copy.deepcopy(control['views'][view])
            assert changed['views'][view]['current']==case['views'][view]['current']
            assert changed['views'][view]['support']==case['views'][view]['support']
        same=forecast_unit(case,package,Path(directory)/'same',doses=doses,draws=draws,budget=budget,resume_only=resume_only,views=views)
        other=forecast_unit(changed,package,Path(directory)/'other',doses=doses,draws=draws,budget=budget,resume_only=resume_only,views=views)
        for key,value in other['rows'].items():
            view,name=key.split('|');same['rows'][view+'|other-'+name]=value
        same['costs']=[{**c,'context_condition':condition} for condition,data in [('same',same),('other',other)] for c in data['costs']]
        same['control_sha256']=digest(control)
        same['matching']='identical public conditions and per-work purpose; different persistent maker; lengths unmatched'
        return same
    directory=Path(directory);rows={};costs=[]
    for view in views:
        query_set=queries(case,view,doses)
        baseline_bundle={'evidences':query_set,'models':package['models'][view],'population_types':package['types'][view]}
        baseline=checkpoint_call(directory/(view+'-baselines.json'),baseline_bundle,
            lambda:baseline_matrix_runtime.execute(baseline_bundle,root=directory/'caps-baseline'),resume_only=resume_only)
        costs.append({'operation':'baselines','view':view,'accepted':baseline['accepted'],
                      'wall_seconds':baseline['wall_s'],
                      'capsule':baseline.get('capsule')})
        library=package['library']
        program_bundle={'evidences':query_set,**library,'population':next(iter(package['models'][view].values())),
                        'population_types':package['types'][view]}
        if set(program_bundle)!={'evidences','candidates','prior','shared_groups','population','population_types'}:
            raise ValueError('undeclared library fields enter the reader')
        results=[]
        # Two independent artifact estimators; process likelihood is exact and
        # gets only one pass. The first artifact seed remains the declared forecast.
        for seed in ((90617,90618) if view=='artifact' else (90617,)):
            setting={'bundle':program_bundle,'seed':seed,'draws':draws,'budget':budget,'exact_states':4096}
            result=checkpoint_call(directory/(view+'-'+str(seed)+'.json'),setting,
                lambda:comparison_runtime.execute(program_bundle,seed=seed,estimator='grouped',draws=draws,
                    exact_states=4096,budget=budget,root=directory/'caps-program'),resume_only=resume_only)
            results.append(result)
            costs.append({'operation':'programs','view':view,'seed':seed,'accepted':result['accepted'],
                'wall_seconds':result['wall_s'],'capsule':result.get('capsule')})
        for name,query in query_set.items():
            predictions={};validity={};quality={}
            for model in package['models'][view]:
                for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0'):
                    key=model+'|'+route
                    valid=baseline['accepted']
                    validity[key]=valid
                    if valid:predictions[key]=baseline['prediction']['predictions'][name][key]
            for route in ROUTES:
                valid=all(result['accepted'] for result in results)
                if valid:
                    forecasts=[result['prediction']['predictions'][name][route] for result in results]
                    quality[route]=(approximation_comparison(*forecasts) if len(forecasts)==2 else
                        {'accepted':forecasts[0]['exact_within_declared_model'],'meaning':'exact process likelihood'})
                    valid=quality[route]['accepted']
                    # Failed precision forecasts stay in immutable capsule files;
                    # they never become a scoreable prediction in this row.
                    if valid:predictions[route]=forecasts[0]['prediction']
                validity[route]=valid
            for prediction in predictions.values():
                distribution(prediction)
                if set(prediction)!=set(query['support']):raise ValueError('prediction omitted public support')
            rows[view+'|'+name]={'predictions':predictions,'validity':validity,'quality':score_json(quality),
                'evidence_sha256':digest(query),'support':query['support'],'unique_prior_works':len({digest(w) for w in query['earlier']})}
    return {'unit':case['unit'],'role':case['role'],'rows':rows,'costs':costs,
        'truth':case['target'],'domain':case['private_factors']['domain'],'purpose':case['private_factors']['purpose'],
        'assistance':'numerical models fitted on training; no unaided neural competence claim'}


def contrast_rows(rows,query,required):
    """Validity belongs to the contrast's required components, never other routes."""
    result=[]
    for row in rows:
        cell=row['rows'][query]
        result.append({'unit':row['unit'],'truth':row['truth'],'domain':row['domain'],'purpose':row['purpose'],
            'valid':all(cell['validity'].get(key) is True for key in required),
            'predictions':{key:cell['predictions'][key] for key in required if key in cell['predictions']}})
    return result


def context(directory,cases_path,models_path,*,role,cell,source=None,doses=DOSES,pilot_units=None,controls_path=None,views=VIEWS):
    """Original prospective source/package selection without output creation."""
    views=selected_views(views)
    if role not in ('pilot','development','discovery'):raise ValueError('reserve requires separate confirmation handler')
    cell_identity=cell
    if role!='pilot' and (not cell_identity or len(cell_identity)!=64):raise ValueError('scientific prediction requires source-checked queue')
    directory=inside(directory);cases_path=inside(cases_path);models_path=inside(models_path)
    source=source if source is not None else closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
                    REPO/'runners/__init__.py',REPO/'runners/readout_repair.py'])
    prepared=read(cases_path.parent/'COMPLETE.json')
    if prepared.get('accepted') is not True or prepared['role']!=role:raise ValueError('source preparation failed or wrong role')
    if closure([REPO/p for p in prepared['outputs']['files']])!=prepared['outputs']:raise ValueError('prepared source output changed')
    cases=read(cases_path)
    control_lookup={};control_completion=None
    if controls_path is not None:
        controls_path=inside(controls_path)
        control_done=read(controls_path.parent/'COMPLETE.json');control_identity=read(controls_path.parent/'IDENTITY.json')
        control_rows=read(controls_path)
        if (control_done.get('accepted') is not True or control_done.get('execution_complete') is not True or
            control_done['role']!=role or control_done['identity_sha256']!=digest(control_identity) or
            control_identity['case_sha256']!=file_hash(cases_path) or
            control_identity['case_completion_sha256']!=file_hash(cases_path.parent/'COMPLETE.json') or
            len(control_rows)!=len(cases) or {r['unit'] for r in control_rows}!={c['unit'] for c in cases} or
            closure([REPO/p for p in control_done['outputs']['files']])!=control_done['outputs']):
            raise ValueError('matched-control preparation incomplete, mismatched or changed')
        control_lookup={r['unit']:r['control'] for r in control_rows}
        control_completion=file_hash(controls_path.parent/'COMPLETE.json')
    if pilot_units is not None:
        if role!='pilot' or type(pilot_units) is not int or not 1<=pilot_units<=len(cases):raise ValueError('only discarded rehearsal can use a subset')
        cases=sorted(cases,key=lambda c:digest({'pilot_unit_order':c['unit']}))[:pilot_units]
    case_sources=validate_cases(cases,role);package=model_inputs(models_path,role)
    training=read(models_path/'artifact-PREPARED.json')
    training_sources={content_identity(sampled_world(u['lineage'],'both')) for u in training['units']}
    if any(content_identity(w) in training_sources for case in cases for w in case['source_worlds']):
        raise ValueError('fit world reused in prospective comparison')
    if control_lookup:
        from .matched_controls import validate as validate_control
        used=case_sources|training_sources
        for case in cases:
            control=control_lookup[case['unit']]
            validate_control(case['source_worlds'][1:],control,role,control['plan']['key'])
            if used.intersection(control['sources']):raise ValueError('control source reused across independent units or fitting')
            used.update(control['sources'])
    identity={'operation':'artifact-comparisons-v1','cell_identity':cell_identity,'role':role,'source':source,
        'cases_sha256':file_hash(cases_path),'selected_units':[c['unit'] for c in cases],
        'model_completion_sha256':package['completion_sha256'],'doses':list(doses),'views':list(views),
        'control_completion_sha256':control_completion,'control_sha256':file_hash(controls_path) if controls_path else None,
        'draws':1024,'budget':8000000,'exact_states':4096,'quality_tv':.01,'quality_maximum_option_log_nats':.01}
    return identity,cases,package,control_lookup


def run(directory,cases_path,models_path,*,role,doses=DOSES,pilot_units=None,controls_path=None,views=VIEWS):
    started,cpu=time.monotonic(),time.process_time();cell_identity=os.environ.get('S9_CELL_IDENTITY')
    directory=inside(directory);views=selected_views(views)
    identity,cases,package,control_lookup=context(directory,cases_path,models_path,role=role,cell=cell_identity,
        doses=doses,pilot_units=pilot_units,controls_path=controls_path,views=views)
    source=identity['source']
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            complete=read(directory/'COMPLETE.json')
            if complete['identity_sha256']!=digest(identity) or closure([REPO/p for p in complete['outputs']['files']])!=complete['outputs']:
                raise ValueError('completed prediction closure changed')
            return complete
        rows=[]
        for case in cases:
            key={'unit':case['unit']};row=units.get(key)
            reconstructed=forecast_unit(case,package,directory/'calls'/digest(key)[:12],doses=doses,
                control=control_lookup.get(case['unit']),resume_only=row is not None,views=views)
            if row is not None and row!=reconstructed:raise ValueError('completed prediction unit differs from actual capsule reconstruction')
            if row is None:row=reconstructed;units.put(key,row)
            rows.append(row)
        freeze(directory/'PREDICTIONS.json',rows);verify_sources(source)
        complete={'at':datetime.now(timezone.utc).isoformat(),'identity_sha256':digest(identity),'cell_identity':cell_identity,
            'source':source,'role':role,'execution_complete':True,'assigned_units':len(cases),'completed_units':len(rows),
            'scores_computed':False,'launch_accepted':False,'wall_seconds':time.monotonic()-started,
            'cpu_seconds':time.process_time()-cpu,'gpu_seconds':0,'cpu_scope':'parent excludes reader capsules',
            'cost_scope':'this invocation; all capsule receipts retained, hard-kill gap belongs to parent queue attempt',
            'outputs':closure([directory/'PREDICTIONS.json',directory/'units',directory/'calls'])}
        freeze(directory/'COMPLETE.json',complete);return complete


def argument_parser():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','cases','models','role'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--pilot-units',type=int)
    parser.add_argument('--controls')
    parser.add_argument('--doses',type=int,nargs='+',default=list(DOSES))
    parser.add_argument('--views',choices=VIEWS,nargs='+',default=list(VIEWS))
    return parser


def main():
    args=argument_parser().parse_args()
    run(Path(args.root),Path(args.cases),Path(args.models),role=args.role,doses=tuple(args.doses),pilot_units=args.pilot_units,
        controls_path=Path(args.controls) if args.controls else None,views=args.views)
    print('Complete assigned prediction grid retained; scientific scoring and disposition remain separate.',flush=True)


if __name__=='__main__':main()
