"""Final saved reconstruction of ordinary baselines and maker comparisons.

DESIGN CHECK: B03/C01/M01/M02/M04/X01/X02/X04/X05/X06/X11/X12;
LESSONS 3--5, CONTROLS 6--7. NULL: changed source/fitting/control selection,
request, unit, export or omitted failed call refuses. ALTERNATIVE: original
shared input constructors and unchanged forecast functions reproduce every
assigned output from saved runtime requests. No reader, fitting, writer or new
reserve opening occurs. Failure/quality decisions remain original; full B03,
scientific capability and public-claim acceptance remain separate.
"""
from pathlib import Path

from . import artifact_comparisons, baseline_predictions, baseline_controls
from .common import REPO, closure, digest, file_hash, read
from .live_status import read as read_status
from .queue import inside, verify_committed, verify_disposition
from .closure_purpose import SavedRequests
from .saved_replay import replaying

MODULES = {m.__name__:m for m in (artifact_comparisons,baseline_predictions,baseline_controls)}


def identity_source(source, artifact):
    """The dispatchers' original source scopes differ from the queue's superset."""
    extra = {'runners/__init__.py','runners/readout_repair.py'}
    if not artifact:
        extra |= {'runners/s3_lib.py','runners/s4_lib.py','runners/s5_lib.py'}
    files = {p:sha for p,sha in source['files'].items() if p in extra or
             p.startswith(('runners/stage9/','runners/stage7/','runners/stage8/','soundingline/'))}
    return {'files':files,'sha256':digest(files)}


def inputs(job, plan):
    module = MODULES.get(job['module'])
    if module is None:raise ValueError('comparator audit requires its original dispatcher')
    args = module.argument_parser().parse_args(job['arguments'])
    artifact = module is artifact_comparisons
    directory = inside(REPO / (args.root if artifact else args.output))
    if (REPO/job['produces']).resolve()!=directory/'COMPLETE.json':
        raise ValueError('comparator original output path differs')
    cases_path,models_path = inside(REPO/args.cases),inside(REPO/args.models)
    cell = digest({'manifest_sha256':digest(plan),'job':job})
    source = identity_source(plan['sources'],artifact)
    if artifact:
        identity,cases,models,controls = module.context(directory,cases_path,models_path,cell=cell,source=source,
            role=args.role,doses=tuple(args.doses),pilot_units=args.pilot_units,
            controls_path=inside(REPO/args.controls) if args.controls else None,views=args.views)
    elif module is baseline_controls:
        identity,cases,models,controls = module.context(directory,cases_path,models_path,inside(REPO/args.controls),
            args.scope,tuple(args.doses),cell=cell,source=source)
    else:
        identity,cases,models = module.context(directory,cases_path,models_path,args.scope,tuple(args.doses),cell=cell,source=source)
        controls = {}
    return module,args,directory,identity,cases,models,controls


def reconstruct(module,args,directory,cases,models,controls):
    """Use unchanged original forecast functions and real runtime constructors."""
    rows = []
    for case in cases:
        if module is artifact_comparisons:
            key = {'unit':case['unit']}
            row = module.forecast_unit(case,models,directory/'calls'/digest(key)[:12],
                doses=tuple(args.doses),control=controls.get(case['unit']),resume_only=True,views=args.views)
        else:
            key = case['unit']
            def call(bundle,label):
                return module.checkpoint_call(directory/'calls'/case['unit'][:16]/(label+'.json'),bundle,
                    lambda:module.baseline_matrix_runtime.execute(bundle,root=directory/'capsules'),resume_only=True)
            if module is baseline_controls:
                row = module.unit_result(case,controls[key],models,call,tuple(args.doses))
            else:
                row = module.unit_result(case,models,call,tuple(args.doses))
        rows.append((key,row))
    return rows


def inspect_completed(job, plan, queue_path):
    verify_committed(queue_path,job,plan,digest(plan))
    module,args,directory,identity,cases,models,controls = inputs(job,plan)
    before = closure([directory])
    if read(directory/'IDENTITY.json')!=identity:
        raise ValueError('comparator original source, fitting, matching or selected cases differ')
    done = read(directory/'COMPLETE.json');artifact = module is artifact_comparisons
    requests = SavedRequests(directory,plan['sources'],storage='calls' if artifact else 'capsules')
    with replaying(requests):
        rebuilt = reconstruct(module,args,directory,cases,models,controls)
    requests.verify_inventory()
    rows = []; units = set()
    for key,row in rebuilt:
        path = directory/'units'/(digest(key)+'.json');saved = read(path)
        if (path in units or saved.get('complete') is not True
                or saved!={'identity':digest(identity),'key':key,'complete':True,'row':row}):
            raise ValueError('comparator unit differs from complete saved-request reconstruction')
        units.add(path);rows.append(row)
    if (not rows or not requests.calls or read(directory/'PREDICTIONS.json')!=rows
            or {p.resolve() for p in (directory/'units').rglob('*.json')}!=units):
        raise ValueError('comparator predictions have missing, extra or altered units')
    names = ['PREDICTIONS.json','units','calls']
    if not artifact:names += ['IDENTITY.json','capsules']
    exports = {}
    if module is baseline_predictions:
        exports['FORECASTS.json']=module.discovery_forecasts(cases,rows,models,tuple(args.doses))
        names += list(exports)
    for name,value in exports.items():
        if read(directory/name)!=value:raise ValueError('comparator final forecast export changed')
    if done['identity_sha256']!=digest(identity) or done['outputs']!=closure([directory/n for n in names]):
        raise ValueError('comparator completion identity or output inventory differs')
    expected = {'cell_identity':identity['cell_identity'],'role':identity['role'],'execution_complete':True,
        'assigned_units':len(cases),'completed_units':len(rows),'scores_computed':False}
    if artifact:
        expected.update(source=identity['source'],launch_accepted=False,gpu_seconds=0,
            cpu_scope='parent excludes reader capsules')
    else:
        expected['scientific_admission']=False
        if module is baseline_predictions:
            expected.update(source=identity['source'],cpu_scope='parent only; each child capsule has a separate wall receipt')
    if any(type(done.get(k)) is not type(v) or done[k]!=v for k,v in expected.items()):
        raise ValueError('comparator completion loses assigned work or promotes execution')
    if closure([directory])!=before:raise ValueError('read-only comparator reconstruction changed original outputs')
    return {'status':'RECONSTRUCTED','operation':identity['operation'],'units':len(rows),'calls':len(requests.calls),
        'invalid_calls_retained':sum(not r['accepted'] for r in requests.calls.values()),
        'complete_sha256':file_hash(directory/'COMPLETE.json'),'predictions_sha256':digest(rows),
        'exports':{name:digest(value) for name,value in exports.items()},
        'new_reader_calls':0,'new_reserve_openings':0,'scientific_admission':False}


def queue_audits(plan,queue_path,prior):
    state=read_status(queue_path/'STATUS.json');result={}
    for key,job in prior.items():
        if job['module'] not in MODULES:continue
        own=state['jobs'][key]
        if own['status']=='COMPLETE':result[key]=inspect_completed(job,plan,queue_path)
        elif own['status'] in ('FAILED','NOT_RUN'):
            verify_disposition(queue_path,job,own)
            result[key]={k:own[k] for k in ('status','reason','disposition_sha256')}
        else:raise ValueError('comparator audit requires terminal predictions')
    return {'jobs':result,'scientific_admission':False,
        'scope':'Original ordinary-baseline and artifact-comparison saved requests, fitting/controls and complete units; no reader execution'}
