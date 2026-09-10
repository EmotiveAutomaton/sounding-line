"""Compiled source, fitting, prediction and analysis for stated code-change purpose.

DESIGN CHECK: H06/X01/X02/X03/X05/X06/X12; LESSONS 2--5. NULL: surface
correspondence can defeat a learned reader; missing calls never improve a score.
ALTERNATIVE: a fixed new repository menu favors changed-code features beyond the
strongest independently selected ordinary rival. Every target/distractor repository
belongs to one menu and one partition. Fewer than60 independent menus are descriptive;
larger scoped discovery uses the fixed .05-nat criterion. No maker-ID accumulation,
full generator admission, latent historical intention or automatic confirmation.
"""
import argparse,math,time
from pathlib import Path
from . import commit_cases,commit_models,commit_runtime
from .commit_features import predict as forecast
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .artifact_comparisons import audit_execution,checkpoint_call
from .queue import inside,writer
from .revision_predictions import sources,completed,reentry,finish
from .training_jobs import cell_identity
from .scoring import log_score,paired_extended,classify,score_json

ARMS={'all','surface','description_only','uniform','lexical_overlap','filename_overlap'}
CHEAP=sorted(ARMS-{'all'})


def output_root(directory,scope,kind):
    directory=inside(directory);prefix='commit-'+kind+'-pilots' if scope=='pilot' else 'scientific-commit-'+kind
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('code-change output scope differs')
    return directory


def prepare(directory,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'case')
    rows,metadata=commit_cases.inputs(scope)
    identity={'cell_identity':cell_identity(),'operation':'commit-cases-v1','scope':scope,'source':sources(),**metadata,'rows_sha256':digest(rows)}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        freeze(directory/'CASES.json',rows)
        return finish(directory,identity,start,cpu,['CASES.json'],counts=metadata['counts'],reserved_payload_parsed=False)


def cases(directory,scope):
    identity,done=completed(directory,'commit-cases-v1',scope);rows=read(directory/'CASES.json')
    if set(rows)!={'train','development','evaluation'} or digest(rows)!=identity['rows_sha256']:raise ValueError('source cases or partitions differ')
    used=set();wording=set()
    for lane in ('evaluation','development','train'):
        own=rows[lane];groups=[g for r in own for g in r['candidate_units']]
        text={commit_cases.wording(m) for r in own for m in r['evidence']['candidate_descriptions']}
        if not own or len({r['key'] for r in own})!=len(own) or len(groups)!=4*len(own) or len(groups)!=len(set(groups)):
            raise ValueError('repeated menu or target/distractor repository')
        if set(groups)&used or text&wording:raise ValueError('source or candidate wording crosses partitions')
        if len(own)!=identity['counts'][lane]['menus']:raise ValueError('source menu count differs')
        for row in own:
            if row['unit'] not in row['candidate_units'] or row['truth'] not in ('0','1','2','3') or any(identity['allocation'][g]!=lane for g in row['candidate_units']):
                raise ValueError('canonical source allocation or target differs')
        used.update(groups);wording.update(text)
    return rows,identity


def fit(directory,cases_path,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'fit');cases_path=inside(cases_path)
    rows,ci=cases(cases_path,scope)
    identity={'cell_identity':cell_identity(),'operation':'commit-fit-v1','scope':scope,'source':sources(),
        'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),'training_rows_sha256':digest(rows['train'])}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        fitted=commit_models.all_models(rows['train']);freeze(directory/'MODELS.json',fitted)
        return finish(directory,identity,start,cpu,['MODELS.json'],training_only=True,menus=len(rows['train']))


def unit(row,models,call):
    evidence=row['evidence'];task={'operation':'commit_description_models','information_sha256':digest(evidence),
        'parameters':models,'parameters_sha256':digest(models)}
    result=call(evidence,task)
    return {k:row[k] for k in ('key','unit','source_group','language','candidate_units','truth')}|{
        'valid':result['accepted'],'probabilities':result['prediction']['probabilities'] if result['accepted'] else None,
        'public_input_sha256':digest(evidence),'model_sha256':digest(models),'call':result}


def predict(directory,cases_path,fit_path,lane,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'prediction')
    if lane not in ('development','evaluation'):raise ValueError('explicit prediction partition required')
    cases_path,fit_path=map(inside,(cases_path,fit_path));rows,_=cases(cases_path,scope);fi,_=completed(fit_path,'commit-fit-v1',scope)
    if fi['cases_complete_sha256']!=file_hash(cases_path/'COMPLETE.json'):raise ValueError('fit used another case population')
    models=read(fit_path/'MODELS.json')
    if set(models)!=ARMS:raise ValueError('missing declared code-change rival')
    identity={'cell_identity':cell_identity(),'operation':'commit-predict-v1','scope':scope,'source':sources(),
        'lane':lane,'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),
        'fit':str(fit_path),'fit_complete_sha256':file_hash(fit_path/'COMPLETE.json'),'assigned_rows_sha256':digest(rows[lane]),'models_sha256':digest(models)}
    with writer(directory):
        units=Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        predictions=[]
        for row in rows[lane]:
            def call(evidence,task):
                result=checkpoint_call(directory/'calls'/(row['key']+'.json'),{'evidence':evidence,'task':task},
                    lambda:commit_runtime.execute(evidence,task=task,root=directory/'capsules'))
                audit_execution(result);return result
            result=unit(row,models,call);old=units.get(row['key'])
            if old is not None and old!=result:raise ValueError('code-change prediction differs on resume')
            units.put(row['key'],result);predictions.append(result)
        freeze(directory/'PREDICTIONS.json',predictions)
        return finish(directory,identity,start,cpu,['units','calls','capsules','PREDICTIONS.json'],
            assigned_calls=len(predictions),invalid_calls=sum(not r['valid'] for r in predictions),scored=False)


def verified_predictions(directory,lane,scope):
    identity,done=completed(directory,'commit-predict-v1',scope)
    if identity['lane']!=lane:raise ValueError('wrong code-change prediction partition')
    rows,_=cases(inside(identity['cases']),scope);fit_path=inside(identity['fit']);fi,_=completed(fit_path,'commit-fit-v1',scope)
    if file_hash(fit_path/'COMPLETE.json')!=identity['fit_complete_sha256'] or fi['cases_complete_sha256']!=identity['cases_complete_sha256']:
        raise ValueError('prediction fit or cases changed')
    models=read(fit_path/'MODELS.json');saved=read(directory/'PREDICTIONS.json');rebuilt=[]
    for row in rows[lane]:
        def call(evidence,task):
            result=checkpoint_call(directory/'calls'/(row['key']+'.json'),{'evidence':evidence,'task':task},None,resume_only=True)
            audit_execution(result)
            if result['accepted'] and result['prediction']['probabilities']!={k:forecast(evidence,m) for k,m in models.items()}:
                raise ValueError('actual copied code-change forecasts differ from exported models')
            return result
        rebuilt.append(unit(row,models,call))
    if rebuilt!=saved or len(saved)!=done['assigned_calls']:raise ValueError('missing, changed or duplicated saved code-change prediction')
    return saved,identity


def validate_rows(rows):
    if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('complete unique description questions required')
    groups=[g for r in rows for g in r['candidate_units']]
    if len(groups)!=4*len(rows) or len(groups)!=len(set(groups)):raise ValueError('dependent candidate repositories counted as separate questions')
    if any(r['valid'] and set(r['probabilities'])!=ARMS for r in rows):raise ValueError('missing description rival')


def select(rows):
    validate_rows(rows)
    base={'assigned':len(rows),'source_units':sorted({g for r in rows for g in r['candidate_units']}),'excluded':0}
    if any(not r['valid'] for r in rows):return base|{'accepted':False,'disposition':'IMPLEMENTATION INVALID','selected':None}
    means={k:math.fsum(log_score(r['probabilities'][k],r['truth']) for r in rows)/len(rows) for k in CHEAP}
    finite=[k for k in CHEAP if math.isfinite(means[k])]
    return base|{'accepted':bool(finite),'selected':min(finite,key=lambda k:(-means[k],k)) if finite else None,'means':means,'eligible':CHEAP,
        'rule':'highest development mean per independent disjoint repository menu; fixed lexical tie break'}


def evaluate(rows,selection,scope,draws=4000):
    validate_rows(rows)
    if set(selection['source_units'])&{g for r in rows for g in r['candidate_units']}:raise ValueError('selection reused target or distractor repository')
    base={'assigned':len(rows),'excluded':0,'independent_unit':'one disjoint four-repository menu',
        'source_repositories':4*len(rows),'language_counts':dict(__import__('collections').Counter(r['language'] for r in rows)),
        'scientific_admission':False,'confirmation_eligible':False,'scope':'stated-description correspondence, no person identity or private intention'}
    if any(not r['valid'] for r in rows):return base|{'disposition':'IMPLEMENTATION INVALID','invalid':[r['key'] for r in rows if not r['valid']],'scored':0}
    if not selection['accepted']:return base|{'disposition':'NOT RUN WITH REASON','reason':'independent strongest-rival selection unavailable','scored':0}
    contrasts={}
    for label,right in [('selected_rival',selection['selected']),('lexical_overlap','lexical_overlap'),('surface','surface'),('description_only','description_only'),('filename_overlap','filename_overlap')]:
        paired=[]
        for row in rows:
            a,b=(log_score(row['probabilities'][k],row['truth']) for k in ('all',right))
            paired.append({'unit':row['unit'],'language':row['language'],'difference':None if a==b==-math.inf else a-b})
        overall=paired_extended(paired,draws=draws,seed=902109)
        contrasts[label]={'right':right,'estimate':overall,'disposition':classify(overall,threshold=.05,descriptive=scope=='pilot' or len(rows)<60),
            'by_language':{k:paired_extended([r for r in paired if r['language']==k],draws=draws,seed=902109) for k in sorted({r['language'] for r in paired})},
            'leave_language_out':{k:paired_extended([r for r in paired if r['language']!=k],draws=draws,seed=902109) for k in sorted({r['language'] for r in paired}) if any(r['language']!=k for r in paired)}}
    return base|{'scored':len(rows),'contrasts':contrasts,'practical_effect_nats':.05,'promotion_scope':'local predictive correspondence only, after complete source and shared-attack closure'}


def analyze(directory,predictions,scope,operation,selection_path=None):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'analysis');predictions=inside(predictions)
    lane='development' if operation=='select' else 'evaluation' if operation=='evaluate' else None
    if lane is None:raise ValueError('unknown code-change analysis operation')
    rows,pi=verified_predictions(predictions,lane,scope);selected=None
    if operation=='evaluate':
        if selection_path is None:raise ValueError('independent complete selection required')
        selection_path=inside(selection_path);si,_=completed(selection_path,'commit-analysis-select-v1',scope)
        if si['fit_complete_sha256']!=pi['fit_complete_sha256'] or si['cases_complete_sha256']!=pi['cases_complete_sha256']:raise ValueError('selection used another model or source')
        dev,_=verified_predictions(inside(si['predictions']),'development',scope);selected=select(dev)
        if score_json(selected)!=read(selection_path/'SELECTION.json'):raise ValueError('selection no longer reconstructs')
    elif selection_path is not None:raise ValueError('selection cannot read evaluation output')
    identity={'cell_identity':cell_identity(),'operation':'commit-analysis-'+operation+'-v1','scope':scope,'source':sources(),
        'predictions':str(predictions),'predictions_complete_sha256':file_hash(predictions/'COMPLETE.json'),
        'fit_complete_sha256':pi['fit_complete_sha256'],'cases_complete_sha256':pi['cases_complete_sha256'],
        'selection_complete_sha256':file_hash(selection_path/'COMPLETE.json') if selection_path else None}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        result=select(rows) if operation=='select' else evaluate(rows,selected,scope);name='SELECTION.json' if operation=='select' else 'PROFILE.json'
        freeze(directory/name,score_json(result));return finish(directory,identity,start,cpu,[name],confirmation_eligible=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('prepare','fit','predict','select','evaluate'))
    p.add_argument('--output',type=Path,required=True);p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    for k in ('cases','fit','predictions','selection'):p.add_argument('--'+k,type=Path)
    p.add_argument('--lane',choices=('development','evaluation'));a=p.parse_args()
    if a.operation=='prepare':prepare(a.output,a.scope)
    elif a.operation=='fit':fit(a.output,a.cases,a.scope)
    elif a.operation=='predict':predict(a.output,a.cases,a.fit,a.lane,a.scope)
    else:analyze(a.output,a.predictions,a.scope,a.operation,a.selection)
