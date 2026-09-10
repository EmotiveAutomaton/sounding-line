"""Final-only local capability calibration and complete paired evaluation jobs.

DESIGN CHECK: C03/X01/X02/X09/X11/X12; LESSONS 3--5, CONTROLS 6.
NULL: a completed file without valid contents, changed comparator selection,
training/development reuse or mismatched reader information invalidates admission.
ALTERNATIVE: independent known-answer calibration and complete actual forecasts
reconstruct before the unchanged domain/view-specific gate runs. Every result is
written privately once complete; no unfinished per-artifact scoring is emitted.
"""
import argparse
from functools import partial
from pathlib import Path
import time
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .queue import inside,verify_sources,writer
from .training_jobs import cell_identity
from .repair_jobs import (VIEWS,inputs,records,model_inputs,complete,sources,public_task,
    unit_result as baseline_unit_result)
from .repair_fit import select
from .repair_analysis import calibrate,evaluate
from .scoring import score_json
from .artifact_comparisons import checkpoint_call,audit_execution
from .neural_operations import case_inputs,validate_complete,unit_result as neural_unit_result


def namespace(directory,scope):
    directory=inside(directory);name='repair-admission-pilots' if scope=='pilot' else 'scientific-repair-admission'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/name):
        raise ValueError('repair admission output scope mismatch')
    return directory


def selection_inputs(directory,scope):
    directory=inside(directory);identity=read(directory/'IDENTITY.json');done=complete(directory,identity)
    if identity['operation']!='select' or identity['scope']!=scope or done.get('development_only') is not True:
        raise ValueError('consequence comparator lacks independent development selection')
    prediction_path=Path(identity['predictions']);pi=read(prediction_path/'IDENTITY.json');pd=complete(prediction_path,pi)
    if file_hash(prediction_path/'COMPLETE.json')!=identity['predictions_complete_sha256']:
        raise ValueError('selected comparator prediction source changed')
    if pi['scope']!=scope or pi['role']!=('pilot' if scope=='pilot' else 'development'):
        raise ValueError('comparator selection reused evaluation or discarded predictions')
    models,training,fit_sha=model_inputs(Path(pi['models']),scope)
    cases,role,case_sha=inputs(Path(pi['cases']),scope)
    if scope=='pilot':cases=[next(c for c in cases if c['private_factors']['domain']==d) for d in ('essay','workshop_doc')]
    if (pi['models_complete_sha256']!=fit_sha or pi['cases_complete_sha256']!=case_sha
        or pi['units']!=[c['unit'] for c in cases] or pd['completed_units']!=len(cases)):
        raise ValueError('consequence development sample or fitting package changed')
    units=Units(prediction_path,pi)
    for case in cases:
        def call(bundle,view):
            task={'operation':'repair_baselines','information_sha256':digest(bundle)}
            return checkpoint_call(prediction_path/'calls'/case['unit'][:16]/(view+'.json'),
                {'evidence':bundle,'task':task},None,resume_only=True)
        if baseline_unit_result(case,models,call)!=units.get(case['unit']):
            raise ValueError('selected comparator development forecasts do not reconstruct')
    development=records(cases);selection={v:select(models[v],training[v],development[v]) for v in VIEWS}
    if score_json(selection)!=read(directory/'SELECTION.json'):raise ValueError('selected comparator cannot reproduce')
    return models,selection,training,development,file_hash(directory/'COMPLETE.json')


def disjoint(cases,training,development):
    rows=records(cases)
    for view in VIEWS:
        if len({digest(r['evidence']) for r in rows[view]})!=len(rows[view]):
            raise ValueError('repair evaluation repeats a public task within its own cohort')
        previous=[*training[view],*development[view]]
        if {r['unit'] for r in rows[view]}&{r['unit'] for r in previous}:
            raise ValueError('repair evaluation reuses fitting or development source')
        if {digest(r['evidence']) for r in rows[view]}&{digest(r['evidence']) for r in previous}:
            raise ValueError('repair evaluation repeats an exposed public task')


def run_calibrate(directory,cases_path,selection_path,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=namespace(directory,scope)
    models,selection,training,development,selected_sha=selection_inputs(selection_path,scope)
    cases,_,case_sha=inputs(cases_path,'pilot');disjoint(cases,training,development)
    source=sources();identity={'cell_identity':cell,'operation':'calibrate','scope':scope,'sources':source,
        'cases':str(inside(cases_path)),'cases_complete_sha256':case_sha,'selection':str(inside(selection_path)),
        'selection_complete_sha256':selected_sha}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():return complete(directory,identity)
        instrument,rows=calibrate(cases,models,selection)
        freeze(directory/'INSTRUMENT.json',instrument);freeze(directory/'CONTROL_ROWS.json',rows);verify_sources(source)
        result={'cell_identity':cell,'identity_sha256':digest(identity),'accepted':True,'instrument_only':True,
            'instrument_accepted':instrument['all_groups_accepted'],'source_units':len(cases),
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'INSTRUMENT.json',directory/'CONTROL_ROWS.json']),'scientific_admission':False}
        freeze(directory/'COMPLETE.json',result);return result


def checked_instrument(directory,scope,models,selection):
    directory=inside(directory);identity=read(directory/'IDENTITY.json');done=complete(directory,identity)
    if identity['operation']!='calibrate' or identity['scope']!=scope or done.get('instrument_only') is not True:
        raise ValueError('missing operation-specific calibration')
    cases,_,sha=inputs(Path(identity['cases']),'pilot')
    if sha!=identity['cases_complete_sha256']:raise ValueError('calibration source changed')
    rebuilt,rows=calibrate(cases,models,selection)
    if rebuilt!=read(directory/'INSTRUMENT.json') or rows!=read(directory/'CONTROL_ROWS.json'):
        raise ValueError('local calibration cannot reproduce')
    return rebuilt,file_hash(directory/'COMPLETE.json')


def run_evaluate(directory,neural_path,baseline_path,selection_path,instrument_path,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=namespace(directory,scope)
    models,selection,training,development,selected_sha=selection_inputs(selection_path,scope)
    instrument,instrument_sha=checked_instrument(instrument_path,scope,models,selection)
    neural_path=inside(neural_path);ni=read(neural_path/'IDENTITY.json');nd=validate_complete(neural_path,ni)
    if ni['scope']!=scope or ni['operation'] not in ('local_repair_artifact','local_repair_process'):
        raise ValueError('reader operation cannot borrow local repair admission')
    view='artifact' if ni['operation']=='local_repair_artifact' else 'process_record'
    baseline_path=inside(baseline_path);bi=read(baseline_path/'IDENTITY.json');bd=complete(baseline_path,bi)
    if bi['operation']!='predict' or bi['scope']!=scope or bi['role']!=('pilot' if scope=='pilot' else 'discovery'):
        raise ValueError('complete separate evaluation baseline predictions required')
    cases,role,case_sha=case_inputs(Path(bi['cases']),scope,2 if scope=='pilot' else 0);disjoint(cases,training,development)
    _,_,fit_sha=model_inputs(Path(bi['models']),scope)
    if (ni['cases_complete_sha256']!=case_sha or bi['cases_complete_sha256']!=case_sha or ni['role']!=role
        or ni['units']!=bi['units'] or ni['units']!=[c['unit'] for c in cases]
        or bd['completed_units']!=len(cases) or nd['completed_units']!=len(cases)
        or bi['models_complete_sha256']!=fit_sha):raise ValueError('reader and baseline evaluation inputs differ')
    expected_models,_,_=model_inputs(Path(bi['models']),scope)
    if expected_models!=models:raise ValueError('selected and evaluated cheap-rival parameters differ')
    package=read(neural_path/'PACKAGE.json');nu=Units(neural_path,ni);bu=Units(baseline_path,bi)
    neural_rows=[];baseline_rows=[]
    for case in cases:
        def neural_call(evidence,arguments,index):
            task={**arguments,'identity':{**package,'information_sha256':digest(evidence)}}
            return checkpoint_call(neural_path/'calls'/case['unit'][:16]/('call-'+digest(index)[:16]+'.json'),
                {'evidence':evidence,'task':task},None,resume_only=True)
        n=neural_unit_result(case,ni['operation'],neural_call)
        if n!=nu.get(case['unit']):raise ValueError('actual neural repair unit cannot reproduce')
        def base_call(bundle,view):
            task={'operation':'repair_baselines','information_sha256':digest(bundle)}
            return checkpoint_call(baseline_path/'calls'/case['unit'][:16]/(view+'.json'),
                {'evidence':bundle,'task':task},None,resume_only=True)
        b=baseline_unit_result(case,models,base_call)
        if b!=bu.get(case['unit']):raise ValueError('actual baseline repair unit cannot reproduce')
        neural_rows.append(n);baseline_rows.append(b)
    source=sources();identity={'cell_identity':cell,'operation':'evaluate','scope':scope,'sources':source,'view':view,
        'neural':str(neural_path),'neural_complete_sha256':file_hash(neural_path/'COMPLETE.json'),
        'baseline':str(baseline_path),'baseline_complete_sha256':file_hash(baseline_path/'COMPLETE.json'),
        'selection':str(inside(selection_path)),'selection_complete_sha256':selected_sha,
        'instrument':str(inside(instrument_path)),'instrument_complete_sha256':instrument_sha,'units':[c['unit'] for c in cases]}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():return complete(directory,identity)
        result,rows=evaluate(cases,view,package,ni['sources'],neural_rows,baseline_rows,models,selection,instrument)
        freeze(directory/'CAPABILITIES.json',result);freeze(directory/'PAIRED_ROWS.json',rows);verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'accepted':True,'source_units':len(cases),
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'CAPABILITIES.json',directory/'PAIRED_ROWS.json']),
            'scientific_evaluation':scope=='scientific','scientific_admission':False,
            'scope':'each exact package/domain/view has its own capability status; completion alone admits none'}
        freeze(directory/'COMPLETE.json',done);return done


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('calibrate','evaluate'))
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--scope',choices=('pilot','scientific'),required=True)
    parser.add_argument('--selection',type=Path,required=True);parser.add_argument('--cases',type=Path)
    parser.add_argument('--neural',type=Path);parser.add_argument('--baseline',type=Path);parser.add_argument('--instrument',type=Path)
    args=parser.parse_args()
    if args.operation=='calibrate':
        if args.cases is None or any(x is not None for x in (args.neural,args.baseline,args.instrument)):parser.error('calibrate requires only --cases and --selection')
        run_calibrate(args.output,args.cases,args.selection,args.scope)
    else:
        if args.cases is not None or any(x is None for x in (args.neural,args.baseline,args.instrument)):parser.error('evaluate requires --neural --baseline --selection --instrument')
        run_evaluate(args.output,args.neural,args.baseline,args.selection,args.instrument,args.scope)
    print('Complete local repair '+args.operation+'; inspect final scoped capability contents.',flush=True)


if __name__=='__main__':main()
