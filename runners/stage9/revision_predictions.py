"""Separate fitting and restricted prediction handlers for canonical revisions.

DESIGN CHECK: H01/H02/X01/X02/X06; LESSONS 3--5. NULL: evaluation labels,
changed fit/case identities, lost attempts or changed permitted views refuse.
ALTERNATIVE: the full ordinary-rival grid executes using only public text and
training-derived coefficients. Forecasts are committed before evaluation; an
invalid call stays in the assigned grid. Historical ArgRewrite is descriptive,
never a freshly reserved population or a test of maker intention.
"""
import argparse
from pathlib import Path
import time
from . import revision_models,revision_runtime
from .artifact_comparisons import audit_execution,checkpoint_call
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .queue import inside,verify_sources,writer
from .training_jobs import cell_identity


def sources():
    return closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/run_arg_replication.py',
        REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])


def completed(directory,operation,scope):
    directory=inside(directory);identity=read(directory/'IDENTITY.json');done=read(directory/'COMPLETE.json')
    if (done.get('execution_complete') is not True or identity['operation']!=operation or identity['scope']!=scope or
        done['identity_sha256']!=digest(identity) or done['cell_identity']!=identity['cell_identity']):
        raise ValueError('revision producer completion or scope differs')
    if closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:raise ValueError('revision source outputs changed')
    return identity,done


ARG_CASES='argrewrite-actual-revision-cases-v1'
ITERA_CASES='iterater-actual-revision-cases-v1'


def case_contract(operation):
    if operation==ARG_CASES:
        from .argrewrite import CLASSES
        return {'classes':list(CLASSES),'views':{'retrospective':{'artifact','pair','record'},'future':{'artifact','record'}},
            'pairs':{'retrospective':[('pair','artifact'),('record','pair')],'future':[('record','artifact')]},
            'scope':'historically exposed ArgRewrite; no untouched reserve',
            'unit':'essay/student lineage; within-record mean over canonical annotations'}
    if operation==ITERA_CASES:
        from .data import INTENTS
        return {'classes':list(INTENTS),'views':{'retrospective':{'artifact','pair'},'future':{'artifact','record'}},
            'pairs':{'retrospective':[('pair','artifact')],'future':[('record','artifact')]},
            'scope':'discarded IteraTeR HUMAN execution pilot from exposed training/development; no fresh confirmation',
            'unit':'connected document/revision lineage; within-record mean over canonical edit major intents'}
    raise ValueError('unsupported canonical revision source operation')


def active_contract(identity):
    contract=case_contract(identity['operation']);active=identity.get('active_tasks',list(contract['views']))
    if not active or len(active)!=len(set(active)) or not set(active)<=set(contract['views']):
        raise ValueError('explicit nonempty canonical task set required')
    if identity['operation']==ITERA_CASES and 'active_tasks' in identity:
        tasks=identity['task_dispositions']
        if set(tasks)!=set(contract['views']):raise ValueError('missing task disposition')
        for task in contract['views']:
            expected='READY' if task in active else 'NOT RUN WITH REASON'
            if tasks[task]['disposition']!=expected or expected!='READY' and not tasks[task]['reason']:
                raise ValueError('task availability lacks a recorded disposition')
    contract['views']={k:v for k,v in contract['views'].items() if k in active}
    contract['pairs']={k:v for k,v in contract['pairs'].items() if k in active}
    return contract


def cases(directory,scope):
    directory=inside(directory);operation=read(directory/'IDENTITY.json')['operation'];contract=case_contract(operation)
    identity,done=completed(directory,operation,scope)
    if identity['classes']!=contract['classes']:raise ValueError('canonical class support differs')
    contract=active_contract(identity)
    if operation==ITERA_CASES and scope=='scientific' and 'active_tasks' not in identity:
        raise ValueError('scientific HUMAN task allocation is absent')
    rows=read(directory/'CASES.json')
    if set(rows)!={'train','development','evaluation'}:raise ValueError('complete revision partitions required')
    for lane,own in rows.items():
        if not own or len({r['key'] for r in own})!=len(own):raise ValueError('missing or duplicated revision cases')
        for task in contract['views']:
            if sum(r['task']==task for r in own)==0 or sum(r['task']==task for r in own)!=done['counts'][lane][task]:raise ValueError('revision task counts changed')
        for row in own:
            if row['task'] not in contract['views'] or set(row['views'])!=contract['views'][row['task']]:raise ValueError('canonical permitted views differ')
            if not row['labels'] or any(k not in identity['classes'] for k in row['labels']):raise ValueError('missing canonical target labels')
            if identity['allocation'][row['unit']]!=lane:raise ValueError('case moved across its original allocation')
    for a,b in [('train','development'),('train','evaluation'),('development','evaluation')]:
        if {r['unit'] for r in rows[a]}&{r['unit'] for r in rows[b]}:raise ValueError('revision source leakage')
    return rows,identity


def finish(directory,identity,start,cpu,files,**extra):
    verify_sources(identity['source'])
    done={'cell_identity':identity['cell_identity'],'identity_sha256':digest(identity),'execution_complete':True,
        'scope':identity['scope'],'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
        'outputs':closure([directory/p for p in ('IDENTITY.json',*files)]),'scientific_admission':False,**extra}
    freeze(directory/'COMPLETE.json',done);return done


def reentry(directory,identity):
    if not (directory/'COMPLETE.json').exists():return None
    done=read(directory/'COMPLETE.json')
    if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
        raise ValueError('completed revision operation changed')
    return done


def output_root(directory,scope,kind):
    directory=inside(directory)
    prefix='revision-'+kind+'-pilots' if scope=='pilot' else 'scientific-revision-'+kind
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('revision output scope differs')
    return directory


def fit(directory,cases_path,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=output_root(directory,scope,'fit')
    cases_path=inside(cases_path);rows,source_case=cases(cases_path,scope)
    identity={'cell_identity':cell,'operation':'ordinary-revision-fitting-v1','scope':scope,'source':sources(),
        'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),
        'training_rows_sha256':digest(rows['train']),'classes':source_case['classes'],
        'role':'training only; no development or evaluation label contributes to fitted parameters'}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        fitted={}
        for task in active_contract(source_case)['views']:
            own=[r for r in rows['train'] if r['task']==task];views=set(own[0]['views'])
            if any(set(r['views'])!=views for r in own):raise ValueError('training views are incomplete')
            fitted[task]={}
            for view in sorted(views):
                training=[{'key':r['key'],'unit':r['unit'],'labels':r['labels'],'evidence':r['views'][view]} for r in own]
                fitted[task][view]=revision_models.all_models(training,identity['classes'],earlier_labels=view=='record')
        freeze(directory/'MODELS.json',fitted)
        return finish(directory,identity,start,cpu,['MODELS.json'],training_only=True,
            fitted_views=sum(len(v) for v in fitted.values()))


def unit(row,view,models,call):
    evidence=row['views'][view]
    task={'operation':'revision_models','parameters':models,'parameters_sha256':digest(models),
        'information_sha256':digest(evidence)}
    result=call(evidence,task)
    return {'key':row['key'],'unit':row['unit'],'task':row['task'],'view':view,'cycle':row['cycle'],
        'source_group':row['source_group'],'labels':row['labels'],'valid':result['accepted'],
        'probabilities':result['prediction']['probabilities'] if result['accepted'] else None,
        'public_input_sha256':digest(evidence),'model_sha256':digest(models),'call':result}


def predict(directory,cases_path,fit_path,lane,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=output_root(directory,scope,'prediction')
    if lane not in ('development','evaluation'):raise ValueError('explicit preallocated prediction partition required')
    cases_path,fit_path=map(inside,(cases_path,fit_path));rows,source_case=cases(cases_path,scope)
    fitted,fdone=completed(fit_path,'ordinary-revision-fitting-v1',scope)
    if fitted['cases_complete_sha256']!=file_hash(cases_path/'COMPLETE.json'):raise ValueError('fitting used different cases or allocation')
    models=read(fit_path/'MODELS.json');selected=rows[lane]
    identity={'cell_identity':cell,'operation':'ordinary-revision-predictions-v1','scope':scope,'source':sources(),
        'lane':lane,'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),
        'fit':str(fit_path),'fit_complete_sha256':file_hash(fit_path/'COMPLETE.json'),
        'assigned_rows_sha256':digest(selected),'models_sha256':digest(models),'classes':source_case['classes'],
        'exposure':source_case.get('data_scope',case_contract(source_case['operation'])['scope'])}
    with writer(directory):
        units=Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        predictions=[]
        for row in selected:
            if set(row['views'])!=set(models[row['task']]):raise ValueError('reader view differs from fitted view')
            for view in sorted(row['views']):
                key={'case':row['key'],'view':view};name=digest(key)
                def call(evidence,task):
                    result=checkpoint_call(directory/'calls'/(name+'.json'),{'evidence':evidence,'task':task},
                        lambda:revision_runtime.execute(evidence,task=task,root=directory/'capsules'))
                    audit_execution(result);return result
                result=unit(row,view,models[row['task']][view],call)
                saved=units.get(key)
                if saved is not None and saved!=result:raise ValueError('revision prediction changed on reentry')
                units.put(key,result);predictions.append(result)
        freeze(directory/'PREDICTIONS.json',predictions)
        return finish(directory,identity,start,cpu,['units','calls','capsules','PREDICTIONS.json'],
            lane=lane,assigned_records=len(selected),assigned_calls=len(predictions),
            invalid_calls=sum(not r['valid'] for r in predictions),scored=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('fit','predict'))
    for key in ('output','cases'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--fit',type=Path);p.add_argument('--lane',choices=('development','evaluation'))
    p.add_argument('--scope',choices=('pilot','scientific'),required=True);a=p.parse_args()
    if a.operation=='fit':
        if a.fit is not None or a.lane is not None:p.error('fit does not consume predictions or select a test lane')
        fit(a.output,a.cases,a.scope)
    else:
        if a.fit is None or a.lane is None:p.error('predict requires the completed fit and explicit lane')
        predict(a.output,a.cases,a.fit,a.lane,a.scope)
