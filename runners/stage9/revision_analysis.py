"""Complete human-revision forecasts, separate rival selection and evaluation.

DESIGN CHECK: H01/X01/X06/X11; LESSONS 3--5. NULL: equal forecasts give zero,
the strongest cheap rival may defeat lexical reading, and a failed call cannot
vanish. ALTERNATIVE: held-out annotation log scores improve at the declared view.
All canonical annotations contribute; bootstrap units are essay/student lineages.
ArgRewrite's historical exposure forces descriptive dispositions, with no fresh
confirmation, broad process competence, maker-intention or values inference.
"""
import argparse,math
from collections import Counter,defaultdict
from pathlib import Path
import time
from .artifact_comparisons import audit_execution,checkpoint_call
from .common import REPO,Units,digest,file_hash,freeze,read
from .queue import inside,writer
from .revision_predictions import cases,completed,finish,output_root,reentry,sources,unit,case_contract,active_contract,ARG_CASES
from .scoring import log_score,paired_extended,score_json


def verified_predictions(directory,lane,scope):
    directory=inside(directory);identity,done=completed(directory,'ordinary-revision-predictions-v1',scope)
    if identity['lane']!=lane:raise ValueError('revision selection/evaluation lane differs')
    case_path,fit_path=map(inside,(identity['cases'],identity['fit']))
    rows,ci=cases(case_path,scope);fi,_=completed(fit_path,'ordinary-revision-fitting-v1',scope)
    if (identity['cases_complete_sha256']!=file_hash(case_path/'COMPLETE.json') or
        identity['fit_complete_sha256']!=file_hash(fit_path/'COMPLETE.json') or
        fi['cases_complete_sha256']!=identity['cases_complete_sha256']):raise ValueError('revision fit/case identity changed')
    models=read(fit_path/'MODELS.json');selected=rows[lane]
    if digest(models)!=identity['models_sha256'] or digest(selected)!=identity['assigned_rows_sha256']:raise ValueError('assigned forecasts changed')
    saved=read(directory/'PREDICTIONS.json');expected=[]
    for row in selected:
        for view in sorted(row['views']):
            key={'case':row['key'],'view':view};name=digest(key)
            def call(evidence,task):
                result=checkpoint_call(directory/'calls'/(name+'.json'),{'evidence':evidence,'task':task},None,resume_only=True)
                audit_execution(result);return result
            expected.append(unit(row,view,models[row['task']][view],call))
    if expected!=saved or len(saved)!=done['assigned_calls']:raise ValueError('saved human forecasts fail actual-call reconstruction')
    return saved,identity


def scores(row,model):
    if not row['valid']:raise ValueError('invalid prediction has no score')
    labels=row['labels']
    if not labels:raise ValueError('empty canonical annotation set')
    p=row['probabilities'][model]
    return math.fsum(log_score(p,k) for k in labels)/len(labels)


def grouped_mean(rows,model):
    groups=defaultdict(list)
    for row in rows:groups[row['unit']].append(scores(row,model))
    return math.fsum(math.fsum(values)/len(values) for values in groups.values())/len(groups)


def select(rows):
    if not rows or len({(r['task'],r['view'],r['key']) for r in rows})!=len(rows):raise ValueError('missing or repeated human forecast records')
    result={}
    for task in sorted({r['task'] for r in rows}):
        result[task]={}
        for view in sorted({r['view'] for r in rows if r['task']==task}):
            own=[r for r in rows if (r['task'],r['view'])==(task,view)]
            if any(not r['valid'] for r in own):
                result[task][view]={'accepted':False,'disposition':'IMPLEMENTATION INVALID','assigned_records':len(own),'excluded_records':0};continue
            eligible=['surface_delta','class_prior','majority']+(['previous_cycle'] if view=='record' else [])
            if any(set(r['probabilities'])!=set(['lexical_delta',*eligible]) for r in own):raise ValueError('missing or extra declared human rival')
            means={k:grouped_mean(own,k) for k in eligible}
            finite=[k for k in eligible if math.isfinite(means[k])]
            selected=min(finite,key=lambda k:(-means[k],k)) if finite else None
            result[task][view]={'accepted':selected is not None,'selected':selected,'means':means,'eligible':eligible,
                'source_units':sorted({r['unit'] for r in own}),'records':[r['key'] for r in own],
                'assigned_records':len(own),'excluded_records':0,
                'reason':'highest equal-source mean development log score; fixed lexical tie break' if finite else 'no finite development rival'}
    return result


def comparison(rows,task,left_view,left_model,right_view,right_model,draws=4000,reason='historically exposed single-topic student essays; corpus-specific annotation agreement'):
    a={r['key']:r for r in rows if (r['task'],r['view'])==(task,left_view)}
    b={r['key']:r for r in rows if (r['task'],r['view'])==(task,right_view)}
    if (not a or set(a)!=set(b) or len(a)!=sum((r['task'],r['view'])==(task,left_view) for r in rows)
        or len(b)!=sum((r['task'],r['view'])==(task,right_view) for r in rows)):
        raise ValueError('revision evidence views omit or duplicate paired canonical records')
    paired=[];invalid=[]
    for key,left in a.items():
        right=b[key]
        if left['labels']!=right['labels'] or left['unit']!=right['unit']:raise ValueError('revision target or source changed between views')
        if not left['valid'] or not right['valid']:invalid.append(key);continue
        x,y=scores(left,left_model),scores(right,right_model)
        paired.append({'unit':left['unit'],'difference':None if x==y==-math.inf else x-y})
    result={'task':task,'left':{'view':left_view,'model':left_model},'right':{'view':right_view,'model':right_model},
        'assigned_records':len(a),'assigned_source_units':len({r['unit'] for r in a.values()}),'excluded_records':0,
        'target_annotations':sum(len(r['labels']) for r in a.values()),
        'class_counts':dict(Counter(k for r in a.values() for k in r['labels'])),'scientific_admission':False}
    if invalid:return {**result,'disposition':'IMPLEMENTATION INVALID','invalid_records':invalid,'scored_records':0}
    return {**result,'estimate':paired_extended(paired,draws=draws,seed=902109),'scored_records':len(paired),
        'disposition':'DESCRIPTIVE','reason':reason}


def evaluate(rows,selection,draws=4000,case_operation=ARG_CASES,case_identity=None):
    if case_identity is not None and case_identity['operation']!=case_operation:raise ValueError('analysis source operation differs')
    contract=case_contract(case_operation) if case_identity is None else active_contract(case_identity)
    if case_identity is not None:contract['scope']=case_identity['data_scope']
    if set(selection)!=set(contract['views']):raise ValueError('canonical revision task inventory differs')
    if {r['task'] for r in rows}!=set(selection):raise ValueError('development/evaluation task inventory differs')
    output=[]
    for task,views in selection.items():
        actual={r['view'] for r in rows if r['task']==task}
        if actual!=set(views) or actual!=contract['views'][task]:raise ValueError('development/evaluation views differ')
        for view,item in views.items():
            own=[r for r in rows if (r['task'],r['view'])==(task,view)]
            if set(item.get('source_units',()))&{r['unit'] for r in own}:raise ValueError('selection reused evaluation source groups')
            if item['accepted']:
                output.append(comparison(rows,task,view,'lexical_delta',view,item['selected'],draws,contract['scope']))
            else:
                output.append({'task':task,'view':view,'disposition':'NOT RUN WITH REASON',
                    'reason':'required independent development rival selection unavailable','assigned_records':len(own),'excluded_records':0})
        pairs=contract['pairs'][task]
        for left,right in pairs:output.append(comparison(rows,task,left,'lexical_delta',right,'lexical_delta',draws,contract['scope']))
    return {'contrasts':output,'source_scope':contract['scope'],
        'independent_unit':contract['unit'],
        'original_class_support_retained':True,'future_target':'all canonical next-cycle labels under one earlier whole-draft forecast',
        'earlier_annotation_assistance':'explicit record view only','scientific_admission':False,'confirmation_eligible':False,
        **({'task_dispositions':case_identity['task_dispositions']} if case_identity is not None and 'task_dispositions' in case_identity else {})}


def run(directory,predictions,scope,operation,selection_path=None):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'analysis')
    from .training_jobs import cell_identity
    cell=cell_identity();predictions=inside(predictions)
    lane='development' if operation=='select' else 'evaluation' if operation=='evaluate' else None
    if lane is None:raise ValueError('undeclared human analysis operation')
    rows,pi=verified_predictions(predictions,lane,scope)
    _,case_identity=cases(inside(pi['cases']),scope)
    selected=None
    if operation=='evaluate':
        if selection_path is None:raise ValueError('separate complete development selection required')
        selection_path=inside(selection_path);si,_=completed(selection_path,'revision-analysis-select-v1',scope)
        if si['fit_complete_sha256']!=pi['fit_complete_sha256'] or si['cases_complete_sha256']!=pi['cases_complete_sha256']:
            raise ValueError('revision selection used another fit/case population')
        dev,_=verified_predictions(inside(si['predictions']),'development',scope)
        selected=select(dev)
        if score_json(selected)!=read(selection_path/'SELECTION.json'):raise ValueError('live development selection does not reproduce')
    elif selection_path is not None:raise ValueError('development selection cannot consume evaluation decisions')
    identity={'cell_identity':cell,'operation':'revision-analysis-'+operation+'-v1','scope':scope,'source':sources(),
        'predictions':str(predictions),'predictions_complete_sha256':file_hash(predictions/'COMPLETE.json'),
        'fit_complete_sha256':pi['fit_complete_sha256'],'cases_complete_sha256':pi['cases_complete_sha256'],
        'selection_complete_sha256':file_hash(selection_path/'COMPLETE.json') if selection_path else None}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        result=select(rows) if operation=='select' else evaluate(rows,selected,case_operation=case_identity['operation'],case_identity=case_identity)
        filename='SELECTION.json' if operation=='select' else 'PROFILE.json'
        freeze(directory/filename,score_json(result))
        return finish(directory,identity,start,cpu,[filename],descriptive_only=True,confirmation_eligible=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('select','evaluate'))
    for key in ('output','predictions'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--selection',type=Path);p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    a=p.parse_args();run(a.output,a.predictions,a.scope,a.operation,a.selection)
