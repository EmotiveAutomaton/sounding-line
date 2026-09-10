"""Actual B-roll fitting, restricted forecasting and grouped selection analyses.

DESIGN CHECK: H03/X01--X06/X11; LESSONS 2--5. NULL: identical forecasts give
zero paired gain; failed attempts cannot vanish or choose their own baseline.
ALTERNATIVE: a selected personal forecast beats an independently selected cheap
rival on the same word opportunities and earlier-script budget. People and scripts
remain separate dependence axes. No historical imagery or maker-values claim.
"""
import argparse,math,time
from pathlib import Path
from . import broll_cases,broll_fitting,broll_reader,broll_runtime
from .artifact_comparisons import checkpoint_call,audit_execution
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .queue import inside,writer
from .revision_predictions import completed,finish,reentry,sources
from .scoring import brier,paired_interval
from .training_jobs import cell_identity


def output(directory,scope,kind):
    directory=inside(directory);prefix='broll-'+kind+'-pilots' if scope=='pilot' else 'scientific-broll-'+kind
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('explicit B-roll output scope required')
    return directory


def identity(operation,scope,**extra):
    return {'cell_identity':cell_identity(),'operation':'broll-'+operation+'-v1','scope':scope,'source':sources(),**extra}


def case_inputs(path,scope):
    path=inside(path);ident,done=completed(path,'broll-cases-v1',scope);rows=read(path/'CASES.json')
    metadata=read(path/'METADATA.json')
    if digest(metadata)!=ident['metadata_sha256'] or set(rows)!={'train','development','evaluation'}:raise ValueError('B-roll case closure differs')
    for lane,own in rows.items():
        if len(own)!=metadata['counts'][lane] or not own:raise ValueError('B-roll assigned case count differs')
    return rows,metadata,ident


def prepare(directory,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output(directory,scope,'case')
    rows,metadata=broll_cases.inputs(scope);ident=identity('cases',scope,metadata_sha256=digest(metadata))
    with writer(directory):
        Units(directory,ident);prior=reentry(directory,ident)
        if prior is not None:return prior
        freeze(directory/'CASES.json',rows);freeze(directory/'METADATA.json',metadata)
        return finish(directory,ident,start,cpu,['CASES.json','METADATA.json'],case_counts=metadata['counts'])


def fit(directory,cases_path,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output(directory,scope,'fit');cases_path=inside(cases_path)
    rows,metadata,ci=case_inputs(cases_path,scope)
    ident=identity('fit',scope,cases=str(cases_path),cases_complete_sha256=file_hash(cases_path/'COMPLETE.json'),training_rows_sha256=digest(rows['train']))
    with writer(directory):
        Units(directory,ident);prior=reentry(directory,ident)
        if prior is not None:return prior
        model=broll_fitting.fit(rows['train']);freeze(directory/'MODEL.json',model)
        return finish(directory,ident,start,cpu,['MODEL.json'],training_only=True)


def unit(row,view,model,call):
    evidence=row['views'][view];task={'operation':'broll_selection_models','parameters':model,
        'parameters_sha256':digest(model),'information_sha256':digest(evidence)}
    result=call(evidence,task)
    return {k:row[k] for k in ('key','unit','script','goal','trial','earlier_trial_count','labels')}|{
        'view':view,'valid':result['accepted'],'probabilities':result['prediction']['probabilities'] if result['accepted'] else None,
        'public_input_sha256':digest(evidence),'model_sha256':digest(model),'call':result}


def predict(directory,cases_path,fit_path,lane,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output(directory,scope,'prediction')
    if lane not in ('development','evaluation'):raise ValueError('declared forecast partition required')
    cases_path,fit_path=map(inside,(cases_path,fit_path));rows,metadata,ci=case_inputs(cases_path,scope)
    fi,_=completed(fit_path,'broll-fit-v1',scope)
    if fi['cases_complete_sha256']!=file_hash(cases_path/'COMPLETE.json'):raise ValueError('fit used different participant/script allocation')
    model=read(fit_path/'MODEL.json');broll_reader.validate_model(model)
    ident=identity('predict',scope,cases=str(cases_path),fit=str(fit_path),lane=lane,
        cases_complete_sha256=file_hash(cases_path/'COMPLETE.json'),fit_complete_sha256=file_hash(fit_path/'COMPLETE.json'),
        assigned_rows_sha256=digest(rows[lane]),model_sha256=digest(model))
    with writer(directory):
        units=Units(directory,ident);prior=reentry(directory,ident)
        if prior is not None:return prior
        predictions=[]
        for row in rows[lane]:
            if set(row['views'])!={'same_person','other_person'}:raise ValueError('required matched context missing')
            for view in ('same_person','other_person'):
                key={'case':row['key'],'view':view};name=digest(key)
                def call(evidence,task):
                    result=checkpoint_call(directory/'calls'/(name+'.json'),{'evidence':evidence,'task':task},
                        lambda:broll_runtime.execute(evidence,task=task,root=directory/'capsules'))
                    audit_execution(result);return result
                result=unit(row,view,model,call);saved=units.get(key)
                if saved is not None and saved!=result:raise ValueError('saved B-roll forecast differs')
                units.put(key,result);predictions.append(result)
        freeze(directory/'PREDICTIONS.json',predictions)
        return finish(directory,ident,start,cpu,['units','calls','capsules','PREDICTIONS.json'],
            assigned_calls=len(predictions),invalid_calls=sum(not r['valid'] for r in predictions),scored=False)


def verified_predictions(path,lane,scope):
    path=inside(path);ident,done=completed(path,'broll-predict-v1',scope)
    if ident['lane']!=lane:raise ValueError('B-roll prediction lane differs')
    cases_path,fit_path=map(inside,(ident['cases'],ident['fit']));rows,metadata,ci=case_inputs(cases_path,scope)
    fi,_=completed(fit_path,'broll-fit-v1',scope);model=read(fit_path/'MODEL.json')
    if (fi['cases_complete_sha256']!=ident['cases_complete_sha256'] or ident['cases_complete_sha256']!=file_hash(cases_path/'COMPLETE.json')
        or ident['fit_complete_sha256']!=file_hash(fit_path/'COMPLETE.json') or ident['model_sha256']!=digest(model)
        or ident['assigned_rows_sha256']!=digest(rows[lane])):raise ValueError('fitting, allocation or assigned targets changed')
    expected=[]
    for row in rows[lane]:
        for view in ('same_person','other_person'):
            name=digest({'case':row['key'],'view':view})
            def call(evidence,task):
                result=checkpoint_call(path/'calls'/(name+'.json'),{'evidence':evidence,'task':task},None,resume_only=True)
                audit_execution(result);return result
            expected.append(unit(row,view,model,call))
    if expected!=read(path/'PREDICTIONS.json') or len(expected)!=done['assigned_calls']:raise ValueError('actual B-roll forecast reconstruction differs')
    return expected,ident,metadata


def mean_brier(rows,arm):
    by_person={}
    for row in rows:
        if not row['valid']:raise ValueError('invalid forecast has no selection score')
        if set(row['probabilities'])!=set(broll_reader.ARMS):raise ValueError('ordinary selection rival missing')
        by_person.setdefault(row['unit'],[]).append(brier(row['probabilities'][arm],row['labels']))
    if not by_person:raise ValueError('no independent selection sources')
    return math.fsum(math.fsum(v)/len(v) for v in by_person.values())/len(by_person)


def select(rows):
    if not rows or len({(r['key'],r['view']) for r in rows})!=len(rows):raise ValueError('nonempty unique development forecasts required')
    same=[r for r in rows if r['view']=='same_person']
    if len(same)*2!=len(rows) or {r['key'] for r in same}!={r['key'] for r in rows if r['view']=='other_person'}:
        raise ValueError('development context grid differs')
    if any(not r['valid'] for r in rows):return {'accepted':False,'reason':'invalid assigned development forecast','excluded_records':0}
    personal=('person_pos','person_word');cheap=tuple(k for k in broll_reader.ARMS if k not in personal)
    means={k:mean_brier(same,k) for k in broll_reader.ARMS}
    return {'accepted':True,'personal':min(personal,key=lambda k:(means[k],k)),'cheap':min(cheap,key=lambda k:(means[k],k)),
        'mean_brier':means,'source_units':sorted({r['unit'] for r in same}),
        'rule':'lowest equal-participant development mean Brier error; fixed lexical tie break','excluded_records':0}


def threshold():
    # Known-answer balanced Bernoulli calibration: the proposal's .05-nat gain
    # over a .5 population forecast maps to this expected squared-error benefit.
    lo,hi=.5,1.
    for _ in range(60):
        p=(lo+hi)/2;gain=p*math.log(2*p)+(1-p)*math.log(2*(1-p))
        if gain<.05:lo=p
        else:hi=p
    p=(lo+hi)/2
    return {'brier_gain':(p-.5)**2,'known_truth_probability':p,'reference_probability':.5,
        'expected_log_gain_nats':p*math.log(2*p)+(1-p)*math.log(2*(1-p)),
        'null_identical_forecasts_gain':0.,'scope':'fixed balanced-Bernoulli known-answer scale anchor; no universal score conversion'}


def compare(rows,left_view,left_arm,right_view,right_arm,draws=4000):
    a={r['key']:r for r in rows if r['view']==left_view};b={r['key']:r for r in rows if r['view']==right_view}
    if not a or set(a)!=set(b) or any(sum((r['view'],r['key'])==(view,key) for r in rows)!=1 for view,keys in ((left_view,a),(right_view,b)) for key in keys):
        raise ValueError('complete paired B-roll view grid required')
    if any(any(a[k][f]!=b[k][f] for f in ('unit','script','goal','labels')) for k in a):raise ValueError('paired B-roll targets differ')
    result={'left':{'view':left_view,'arm':left_arm},'right':{'view':right_view,'arm':right_arm},
        'assigned_records':len(a),'participants':len({r['unit'] for r in a.values()}),'scripts':len({r['script'] for r in a.values()}),'excluded_records':0}
    if any(not r['valid'] for r in (*a.values(),*b.values())):return result|{'disposition':'IMPLEMENTATION INVALID','scored_records':0}
    cells=[{'unit':a[k]['unit'],'script':a[k]['script'],'dose':a[k]['earlier_trial_count'],
        'difference':brier(b[k]['probabilities'][right_arm],b[k]['labels'])-brier(a[k]['probabilities'][left_arm],a[k]['labels'])} for k in a]
    groups=sorted({r['script'] for r in cells})
    return result|{'disposition':'DESCRIPTIVE','scored_records':len(cells),
        'estimate':paired_interval(cells,second_cluster='script',draws=draws),
        'per_script':{s:paired_interval([r for r in cells if r['script']==s],draws=draws) for s in groups},
        'leave_one_script_out':{s:paired_interval([r for r in cells if r['script']!=s],draws=draws) for s in groups if len(groups)>1},
        'earlier_trial_counts':{str(d):sum(r['dose']==d for r in cells) for d in sorted({r['dose'] for r in cells})}}


def evaluate(rows,selection,draws=4000):
    if not selection['accepted']:return {'disposition':'NOT RUN WITH REASON','reason':selection['reason'],'excluded_records':0}
    if set(selection['source_units'])&{r['unit'] for r in rows}:raise ValueError('selection reused evaluation participants')
    personal,cheap=selection['personal'],selection['cheap']
    if personal not in ('person_pos','person_word') or cheap not in set(broll_reader.ARMS)-{'person_pos','person_word'}:raise ValueError('undeclared selected rival')
    comparisons=[compare(rows,'same_person',personal,'same_person',cheap,draws),
        compare(rows,'same_person',personal,'other_person',personal,draws),
        compare(rows,'same_person','budget_only','same_person','commission',draws)]
    overlaps={}
    for arm in broll_reader.ARMS:
        values=[]
        for row in rows:
            if row['view']!='same_person':continue
            if not row['valid']:
                values.append({'unit':row['unit'],'key':row['key'],'valid':False,'reason':'invalid assigned forecast','scored':False});continue
            prediction={i for i,p in enumerate(row['probabilities'][arm]) if p>=.5};truth={i for i,y in enumerate(row['labels']) if y}
            values.append({'unit':row['unit'],'key':row['key'],'valid':True,'intersection':len(prediction&truth),'union':len(prediction|truth),
                'jaccard':len(prediction&truth)/len(prediction|truth) if prediction|truth else 1.})
        overlaps[arm]=values
    return {'contrasts':comparisons,'selection_overlap':overlaps,'selection_overlap_rule':'fixed .5 Bernoulli threshold; empty/empty overlap is one; separate from proper score',
        'practical_effect_calibration':threshold(),'independent_unit':'participant with crossed script dependence',
        'claim_scope':'recorded concept selections; limited held-out scripts, no imagery or values inference',
        'scientific_admission':False,'confirmation_eligible':False}


def analyze(directory,predictions,scope,operation,selection_path=None):
    start,cpu=time.monotonic(),time.process_time();directory=output(directory,scope,'analysis');predictions=inside(predictions)
    lane='development' if operation=='select' else 'evaluation' if operation=='evaluate' else None
    if lane is None:raise ValueError('undeclared B-roll analysis')
    rows,pi,metadata=verified_predictions(predictions,lane,scope);selection=None
    if operation=='evaluate':
        if selection_path is None:raise ValueError('independent selection required')
        selection_path=inside(selection_path);si,_=completed(selection_path,'broll-select-v1',scope)
        if (si['cases_complete_sha256'],si['fit_complete_sha256'])!=(pi['cases_complete_sha256'],pi['fit_complete_sha256']):raise ValueError('B-roll selection population differs')
        dev,_,_=verified_predictions(inside(si['predictions']),'development',scope);selection=select(dev)
        if selection!=read(selection_path/'SELECTION.json'):raise ValueError('B-roll development selection changed')
    elif selection_path is not None:raise ValueError('development selection cannot inspect evaluation')
    ident=identity(operation,scope,predictions=str(predictions),predictions_complete_sha256=file_hash(predictions/'COMPLETE.json'),
        cases_complete_sha256=pi['cases_complete_sha256'],fit_complete_sha256=pi['fit_complete_sha256'],
        selection_complete_sha256=file_hash(selection_path/'COMPLETE.json') if selection_path else None,
        practical_effect_calibration=threshold())
    with writer(directory):
        Units(directory,ident);prior=reentry(directory,ident)
        if prior is not None:return prior
        result=select(rows) if operation=='select' else evaluate(rows,selection)
        name='SELECTION.json' if operation=='select' else 'PROFILE.json';freeze(directory/name,result)
        return finish(directory,ident,start,cpu,[name],source_scope=metadata['scope'],descriptive_only=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('prepare','fit','predict','select','evaluate'))
    p.add_argument('--output',type=Path,required=True);p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    for key in ('cases','fit','predictions','selection'):p.add_argument('--'+key,type=Path)
    p.add_argument('--lane',choices=('development','evaluation'));a=p.parse_args()
    if a.operation=='prepare':prepare(a.output,a.scope)
    elif a.operation=='fit':fit(a.output,a.cases,a.scope)
    elif a.operation=='predict':predict(a.output,a.cases,a.fit,a.lane,a.scope)
    else:analyze(a.output,a.predictions,a.scope,a.operation,a.selection)
