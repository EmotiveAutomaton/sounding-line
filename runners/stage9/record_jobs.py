"""Compiled prospective writing pipeline; present artifacts and prior records differ.

DESIGN CHECK: H07/H08/X01/X02/X03/X05/X06/X12; LESSONS 2--5. NULL: future
labels, mixed source groups, incomplete views or failed calls cannot improve a
reader's score. ALTERNATIVE: fixed prospective forecasts beat an independently
selected strong baseline on complete paired targets. Historical data and small
source/stimulus support stay descriptive; no hidden intention or confirmation.
"""
import argparse,math,time
from collections import Counter
from pathlib import Path
from . import record_models,record_runtime
from .record_features import SUPPORT,predict as forecast
from .common import REPO,ROOT,Units,digest,file_hash,freeze,read
from .artifact_comparisons import audit_execution,checkpoint_call
from .queue import inside,writer
from .revision_predictions import sources,completed,reentry,finish
from .training_jobs import cell_identity
from .scoring import log_score,paired_extended,score_json


def contract(dataset):
    if dataset=='coauthor':return {'coauthor':list(SUPPORT['coauthor'])}
    if dataset=='scholawrite':return {k:list(SUPPORT[k]) for k in ('schola_category','schola_location')}
    raise ValueError('unsupported compiled prospective corpus')


def output_root(directory,scope,kind):
    directory=inside(directory);prefix='record-'+kind+'-pilots' if scope=='pilot' else 'scientific-record-'+kind
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('prospective output scope differs')
    return directory


def prepare(directory,scope,dataset,fold=None):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'case');classes=contract(dataset)
    if dataset=='coauthor':
        if fold is not None:raise ValueError('CoAuthor has no project rotation')
        from .coauthor_cases import inputs
        rows,metadata=inputs(scope)
        metadata=metadata|{'allocation':metadata['writer_component_allocation'],'crossed_stimulus':True}
    else:
        from .schola_cases import inputs
        rows,metadata=inputs(scope,fold)
    if metadata['classes']!=classes:raise ValueError('native prospective support differs')
    identity={'cell_identity':cell_identity(),'operation':'record-cases-v1','scope':scope,'source':sources(),
        **metadata,'dataset':dataset,'classes':classes,'rows_sha256':digest(rows)}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        freeze(directory/'CASES.json',rows)
        return finish(directory,identity,start,cpu,['CASES.json'],counts=metadata['counts'],reserve_payload_parsed=False)


def cases(directory,scope):
    identity,done=completed(directory,'record-cases-v1',scope);rows=read(directory/'CASES.json')
    if identity['classes']!=contract(identity['dataset']) or set(rows)!={'train','development','evaluation'} or digest(rows)!=identity['rows_sha256']:
        raise ValueError('canonical prospective support or source cases changed')
    groups=set();stimuli=set()
    for lane,own in rows.items():
        if not own or len({r['key'] for r in own})!=len(own) or len(own)!=identity['counts'][lane]['records']:raise ValueError('prospective cases missing or repeated')
        own_groups={r['unit'] for r in own};own_stimuli={r['stimulus'] for r in own}
        if groups&own_groups or identity['crossed_stimulus'] and stimuli&own_stimuli:raise ValueError('prospective source or stimulus leakage')
        if {r['kind'] for r in own}!=set(identity['classes']):raise ValueError('prospective target kind unavailable')
        for row in own:
            if row['truth'] not in identity['classes'][row['kind']] or set(row['views'])!={'artifact','record'} or identity['allocation'][row['unit']]!=lane:
                raise ValueError('prospective label/view/allocation differs')
        groups.update(own_groups);stimuli.update(own_stimuli)
    return rows,identity


def fit(directory,cases_path,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'fit');cases_path=inside(cases_path)
    rows,ci=cases(cases_path,scope)
    identity={'cell_identity':cell_identity(),'operation':'record-fit-v1','scope':scope,'source':sources(),
        'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),'training_rows_sha256':digest(rows['train'])}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        models={}
        for kind in ci['classes']:
            models[kind]={}
            for view in ('artifact','record'):
                training=[{k:r[k] for k in ('key','unit','truth')}|{'evidence':r['views'][view]} for r in rows['train'] if r['kind']==kind]
                models[kind][view]=record_models.all_models(training,kind,view=='record')
        freeze(directory/'MODELS.json',models)
        return finish(directory,identity,start,cpu,['MODELS.json'],training_only=True,assigned_training_records=len(rows['train']))


def unit(row,view,models,call):
    evidence=row['views'][view];task={'operation':'prospective_record_models','parameters':models,'parameters_sha256':digest(models),
        'information_sha256':digest(evidence),'kind':row['kind'],'record':view=='record'}
    result=call(evidence,task)
    return {k:row[k] for k in ('key','unit','stimulus','kind','truth','source_group')}|{'view':view,'valid':result['accepted'],
        'probabilities':result['prediction']['probabilities'] if result['accepted'] else None,'model_sha256':digest(models),
        'public_input_sha256':digest(evidence),'call':result}


def predict(directory,cases_path,fit_path,lane,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'prediction')
    if lane not in ('development','evaluation'):raise ValueError('explicit prospective prediction partition required')
    cases_path,fit_path=map(inside,(cases_path,fit_path));rows,ci=cases(cases_path,scope);fi,_=completed(fit_path,'record-fit-v1',scope)
    if fi['cases_complete_sha256']!=file_hash(cases_path/'COMPLETE.json'):raise ValueError('prospective fit used different source cases')
    models=read(fit_path/'MODELS.json')
    identity={'cell_identity':cell_identity(),'operation':'record-predict-v1','scope':scope,'source':sources(),'lane':lane,
        'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),'fit':str(fit_path),
        'fit_complete_sha256':file_hash(fit_path/'COMPLETE.json'),'assigned_rows_sha256':digest(rows[lane]),'models_sha256':digest(models)}
    with writer(directory):
        units=Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        predictions=[]
        for row in rows[lane]:
            for view in ('artifact','record'):
                key={'case':row['key'],'view':view};name=digest(key)
                def call(evidence,task):
                    result=checkpoint_call(directory/'calls'/(name+'.json'),{'evidence':evidence,'task':task},
                        lambda:record_runtime.execute(evidence,task=task,root=directory/'capsules'))
                    audit_execution(result);return result
                result=unit(row,view,models[row['kind']][view],call);old=units.get(key)
                if old is not None and old!=result:raise ValueError('prospective prediction differs on resume')
                units.put(key,result);predictions.append(result)
        freeze(directory/'PREDICTIONS.json',predictions)
        return finish(directory,identity,start,cpu,['units','calls','capsules','PREDICTIONS.json'],assigned_calls=len(predictions),
            invalid_calls=sum(not r['valid'] for r in predictions),scored=False)


def verified_predictions(directory,lane,scope):
    pi,done=completed(directory,'record-predict-v1',scope)
    if pi['lane']!=lane:raise ValueError('wrong prospective prediction partition')
    case_path=inside(pi['cases']);rows,ci=cases(case_path,scope);fit_path=inside(pi['fit']);fi,_=completed(fit_path,'record-fit-v1',scope)
    if file_hash(case_path/'COMPLETE.json')!=pi['cases_complete_sha256'] or file_hash(fit_path/'COMPLETE.json')!=pi['fit_complete_sha256'] or fi['cases_complete_sha256']!=pi['cases_complete_sha256']:
        raise ValueError('prospective fit or source population changed')
    models=read(fit_path/'MODELS.json');saved=read(directory/'PREDICTIONS.json');rebuilt=[]
    for row in rows[lane]:
        for view in ('artifact','record'):
            name=digest({'case':row['key'],'view':view});parameters=models[row['kind']][view]
            def call(evidence,task):
                result=checkpoint_call(directory/'calls'/(name+'.json'),{'evidence':evidence,'task':task},None,resume_only=True)
                audit_execution(result)
                if result['accepted'] and result['prediction']['probabilities']!={k:forecast(evidence,m) for k,m in parameters.items()}:raise ValueError('copied prospective forecast does not reproduce')
                return result
            rebuilt.append(unit(row,view,parameters,call))
    if rebuilt!=saved or len(saved)!=done['assigned_calls']:raise ValueError('missing, changed or repeated prospective calls')
    return saved,pi,ci


def validate_rows(rows):
    if not rows or len({(r['key'],r['kind'],r['view']) for r in rows})!=len(rows):raise ValueError('nonempty complete prospective rows required')
    for kind in {r['kind'] for r in rows}:
        views={v:[r for r in rows if r['kind']==kind and r['view']==v] for v in ('artifact','record')}
        if not views['artifact'] or {r['key'] for r in views['artifact']}!={r['key'] for r in views['record']}:raise ValueError('prospective view omitted an assigned target')
    for r in rows:
        expected={'lexical','surface','class_prior','majority'}|({'previous_transition','persistence'} if r['view']=='record' else set())
        if r['kind'] not in SUPPORT or r['view'] not in ('artifact','record') or r['truth'] not in SUPPORT[r['kind']]:raise ValueError('unknown prospective target or view')
        if r['valid'] and set(r['probabilities'])!=expected:raise ValueError('missing prospective rival')


def mean(rows,model):
    units={}
    for row in rows:units.setdefault(row['unit'],[]).append(log_score(row['probabilities'][model],row['truth']))
    return math.fsum(math.fsum(x)/len(x) for x in units.values())/len(units)


def select(rows):
    validate_rows(rows);output={}
    for kind in sorted({r['kind'] for r in rows}):
        output[kind]={}
        for view in ('artifact','record'):
            own=[r for r in rows if (r['kind'],r['view'])==(kind,view)]
            base={'assigned':len(own),'excluded':0,'source_units':sorted({r['unit'] for r in own}),'stimuli':sorted({r['stimulus'] for r in own})}
            if any(not r['valid'] for r in own):output[kind][view]=base|{'accepted':False,'selected':None,'disposition':'IMPLEMENTATION INVALID'};continue
            eligible=sorted(set(own[0]['probabilities'])-{'lexical'});means={m:mean(own,m) for m in eligible};finite=[k for k,v in means.items() if math.isfinite(v)]
            output[kind][view]=base|{'accepted':bool(finite),'selected':min(finite,key=lambda k:(-means[k],k)) if finite else None,'eligible':eligible,'means':means}
    return output


def comparison(rows,kind,left_view,left_model,right_view,right_model,crossed,draws):
    a={r['key']:r for r in rows if (r['kind'],r['view'])==(kind,left_view)};b={r['key']:r for r in rows if (r['kind'],r['view'])==(kind,right_view)}
    if not a or set(a)!=set(b):raise ValueError('missing paired prospective target')
    paired=[];invalid=[]
    for key,left in a.items():
        right=b[key]
        if any(left[k]!=right[k] for k in ('unit','stimulus','truth')):raise ValueError('prospective target/source differs across views')
        if not left['valid'] or not right['valid']:invalid.append(key);continue
        x,y=(log_score(r['probabilities'][m],r['truth']) for r,m in ((left,left_model),(right,right_model)))
        paired.append({'unit':left['unit'],'stimulus':left['stimulus'],'difference':None if x==y==-math.inf else x-y})
    base={'kind':kind,'left':{'view':left_view,'model':left_model},'right':{'view':right_view,'model':right_model},
        'assigned':len(a),'source_units':len({r['unit'] for r in a.values()}),'stimuli':len({r['stimulus'] for r in a.values()}),
        'classes':dict(Counter(r['truth'] for r in a.values())),'excluded':0,'scientific_admission':False}
    if invalid:return base|{'disposition':'IMPLEMENTATION INVALID','invalid':invalid,'scored':0}
    return base|{'estimate':paired_extended(paired,draws=draws,seed=902107,**({'second_cluster':'stimulus'} if crossed else {})),
        'scored':len(paired),'disposition':'DESCRIPTIVE','scope':'historically exposed corpus; limited source and stimulus counts; no fresh confirmation'}


def evaluate(rows,selection,crossed=True,draws=4000):
    validate_rows(rows)
    if set(selection)!={r['kind'] for r in rows}:raise ValueError('selection and evaluation target kinds differ')
    contrasts=[]
    for kind in sorted(selection):
        for view in ('artifact','record'):
            own=[r for r in rows if (r['kind'],r['view'])==(kind,view)];selected=selection[kind][view]
            if set(selected['source_units'])&{r['unit'] for r in own} or crossed and set(selected['stimuli'])&{r['stimulus'] for r in own}:raise ValueError('selection reused prospective source or stimulus')
            if selected['accepted']:contrasts.append(comparison(rows,kind,view,'lexical',view,selected['selected'],crossed,draws))
            else:contrasts.append({'kind':kind,'view':view,'disposition':'NOT RUN WITH REASON','reason':'independent rival selection unavailable','assigned':len(own),'excluded':0})
        contrasts.append(comparison(rows,kind,'record','lexical','artifact','lexical',crossed,draws))
    return {'contrasts':contrasts,'scientific_admission':False,'confirmation_eligible':False,
        'crossed_source_stimulus':crossed,'scope':'complete prospective source-native targets; record assistance separate, no maker-intention claim'}


def analyze(directory,predictions,scope,operation,selection_path=None):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'analysis');predictions=inside(predictions)
    lane='development' if operation=='select' else 'evaluation' if operation=='evaluate' else None
    if lane is None:raise ValueError('unknown prospective analysis operation')
    rows,pi,ci=verified_predictions(predictions,lane,scope);selected=None
    if operation=='evaluate':
        if selection_path is None:raise ValueError('independent prospective selection required')
        selection_path=inside(selection_path);si,_=completed(selection_path,'record-analysis-select-v1',scope)
        if si['fit_complete_sha256']!=pi['fit_complete_sha256'] or si['cases_complete_sha256']!=pi['cases_complete_sha256']:raise ValueError('selection model/source differs')
        dev,_,_=verified_predictions(inside(si['predictions']),'development',scope);selected=select(dev)
        if score_json(selected)!=read(selection_path/'SELECTION.json'):raise ValueError('prospective selection does not reconstruct')
    elif selection_path is not None:raise ValueError('selection cannot read evaluation decisions')
    identity={'cell_identity':cell_identity(),'operation':'record-analysis-'+operation+'-v1','scope':scope,'source':sources(),
        'predictions':str(predictions),'predictions_complete_sha256':file_hash(predictions/'COMPLETE.json'),
        'fit_complete_sha256':pi['fit_complete_sha256'],'cases_complete_sha256':pi['cases_complete_sha256'],
        'selection':str(selection_path) if selection_path else None,
        'selection_complete_sha256':file_hash(selection_path/'COMPLETE.json') if selection_path else None}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        result=select(rows) if operation=='select' else evaluate(rows,selected,ci['crossed_stimulus']);name='SELECTION.json' if operation=='select' else 'PROFILE.json'
        freeze(directory/name,score_json(result));return finish(directory,identity,start,cpu,[name],confirmation_eligible=False)


def fold_summary(folds,draws=4000):
    """Each project contributes one outer evaluation, with its own dev-selected rival.

    Overlapping fitting sets and only five projects license descriptive sensitivity,
    never a fresh-reserve or independent-training replicate claim.
    """
    if len(folds)!=5 or {f['fold'] for f in folds}!=set(range(5)):
        raise ValueError('all five distinct outer folds required')
    held={f['held_project'] for f in folds}
    if len(held)!=5:raise ValueError('repeated outer evaluation project')
    combined=[];profiles=[];roster=[];selection_failed=set();keys=set()
    for fold in sorted(folds,key=lambda f:f['fold']):
        allocation=fold['allocation'];rows=fold['predictions'];selection=fold['selection']
        expected={p:'evaluation' if p==fold['held_project'] else 'development' if p==fold['selection_project'] else 'train' for p in held}
        if allocation!=expected or fold['selection_project']==fold['held_project'] or fold['selection_project'] not in held:
            raise ValueError('whole-project fitting/selection/evaluation roles differ')
        if {r['unit'] for r in rows}!={fold['held_project']} or {r['kind'] for r in rows}!=set(contract('scholawrite')):
            raise ValueError('outer predictions have wrong project or native targets')
        validate_rows(rows)
        own_keys={(r['key'],r['view']) for r in rows}
        if keys&own_keys:raise ValueError('outer evaluation repeats a target')
        keys.update(own_keys)
        for kind in selection:
            for view in ('artifact','record'):
                decision=selection[kind][view]
                if set(decision['source_units'])!={fold['selection_project']}:
                    raise ValueError('outer rival was not selected on its assigned project')
                if not decision['accepted']:selection_failed.add((kind,view))
                roster.append({'fold':fold['fold'],'kind':kind,'view':view,'decision':decision})
        profiles.append({'fold':fold['fold'],'held_project':fold['held_project'],'profile':evaluate(rows,selection,False,draws)})
        for row in rows:
            decision=selection[row['kind']][row['view']]
            probabilities=None if not row['valid'] else dict(row['probabilities'])
            if row['valid'] and decision['accepted']:probabilities['fold_selected']=probabilities[decision['selected']]
            combined.append(row|{'probabilities':probabilities})
    contrasts=[]
    for kind in contract('scholawrite'):
        for label,lv,lm,rv,rm in (('artifact_rival','artifact','lexical','artifact','fold_selected'),
                                ('record_rival','record','lexical','record','fold_selected'),
                                ('record_gain','record','lexical','artifact','lexical')):
            own=[r for r in combined if r['kind']==kind]
            if rm=='fold_selected' and (kind,rv) in selection_failed:
                result={'kind':kind,'disposition':'NOT RUN WITH REASON','reason':'a required outer-fold rival selection failed',
                    'assigned':len(own)//2,'excluded':0,'scientific_admission':False}
                sensitivity=[]
            else:
                result=comparison(own,kind,lv,lm,rv,rm,False,draws)
                sensitivity=[{'omitted_project':p,'profile':comparison([r for r in own if r['unit']!=p],kind,lv,lm,rv,rm,False,draws)} for p in sorted(held)]
            contrasts.append({'comparison':label,'profile':result,'leave_one_project_out':sensitivity})
    return {'folds':profiles,'contrasts':contrasts,'selected_rivals':roster,'projects':5,
        'scientific_admission':False,'confirmation_eligible':False,
        'scope':'historically exposed five-project outer cross-validation; equal project weighting; overlapping fitting sets; descriptive sensitivity only'}


def collect(directory,evaluations,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'analysis')
    evaluations=list(map(inside,evaluations));folds=[];inputs=[]
    for path in evaluations:
        ei,_=completed(path,'record-analysis-evaluate-v1',scope)
        rows,pi,ci=verified_predictions(inside(ei['predictions']),'evaluation',scope)
        if ci['dataset']!='scholawrite' or ci['crossed_stimulus']:raise ValueError('outer collector requires actual ScholaWrite outputs')
        selection_path=inside(ei['selection']);si,_=completed(selection_path,'record-analysis-select-v1',scope)
        if any(ei[k]!=pi[k] or si[k]!=pi[k] for k in ('cases_complete_sha256','fit_complete_sha256')):
            raise ValueError('outer analysis differs from actual fit/source')
        if ei['predictions_complete_sha256']!=file_hash(inside(ei['predictions'])/'COMPLETE.json') or ei['selection_complete_sha256']!=file_hash(selection_path/'COMPLETE.json'):
            raise ValueError('outer predictions or selection changed')
        dev,dpi,dci=verified_predictions(inside(si['predictions']),'development',scope)
        if dci!=ci or any(dpi[k]!=pi[k] for k in ('cases_complete_sha256','fit_complete_sha256')) or si['predictions_complete_sha256']!=file_hash(inside(si['predictions'])/'COMPLETE.json'):
            raise ValueError('outer development fit/source differs')
        selection=select(dev)
        if score_json(selection)!=read(selection_path/'SELECTION.json') or score_json(evaluate(rows,selection,False))!=read(path/'PROFILE.json'):
            raise ValueError('outer selection or profile does not reconstruct')
        folds.append({k:ci[k] for k in ('fold','held_project','selection_project','allocation')}|{'predictions':rows,'selection':selection})
        inputs.append({'path':str(path),'complete_sha256':file_hash(path/'COMPLETE.json')})
    identity={'cell_identity':cell_identity(),'operation':'record-outer-collect-v1','scope':scope,'source':sources(),'evaluations':inputs}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        profile=fold_summary(folds);freeze(directory/'PROFILE.json',score_json(profile))
        return finish(directory,identity,start,cpu,['PROFILE.json'],outer_projects=5,confirmation_eligible=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('prepare','fit','predict','select','evaluate','collect'))
    p.add_argument('--output',type=Path,required=True);p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    p.add_argument('--dataset',choices=('coauthor','scholawrite'));p.add_argument('--fold',type=int)
    p.add_argument('--evaluations',type=Path,nargs='+')
    for k in ('cases','fit','predictions','selection'):p.add_argument('--'+k,type=Path)
    p.add_argument('--lane',choices=('development','evaluation'));a=p.parse_args()
    if a.operation=='prepare':prepare(a.output,a.scope,a.dataset,a.fold)
    elif a.operation=='collect':collect(a.output,a.evaluations or [],a.scope)
    elif a.operation=='fit':fit(a.output,a.cases,a.scope)
    elif a.operation=='predict':predict(a.output,a.cases,a.fit,a.lane,a.scope)
    else:analyze(a.output,a.predictions,a.scope,a.operation,a.selection)
