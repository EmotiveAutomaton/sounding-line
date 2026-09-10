"""Local genetic-edition correspondence with frozen copied-text and neural readers.

DESIGN CHECK: H04/X01/X02/X03/X06/X07/X11/X12; LESSONS 2--5. NULL: copied
text, length preferences, missing calls or prior target exposure cannot license
historical reconstruction. ALTERNATIVE: complete offered-replacement predictions
beat separately retained copied-text/uniform/length rivals on verified local changes.
One famous work remains qualitative even with many pages; no admission or population
interval. Predictions are committed before outcome-dependent analysis.
"""
import argparse,math,time,uuid
from pathlib import Path
from .common import REPO,ROOT,Units,digest,file_hash,freeze,read
from .queue import inside,writer
from .revision_predictions import sources,completed,reentry,finish
from .training_jobs import cell_identity
from .artifact_comparisons import audit_execution,checkpoint_call
from .runtime import execute
from .features import copy_probabilities
from .scoring import log_score,paired_extended,score_json
from .genetic_cases import inputs,validate


def output_root(directory,scope,kind):
    directory=inside(directory);prefix='genetic-'+kind+'-pilots' if scope=='pilot' else 'scientific-genetic-'+kind
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('genetic output scope differs')
    return directory


def prepare(directory,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'case');rows,metadata=inputs(scope)
    identity={'cell_identity':cell_identity(),'operation':'genetic-cases-v1','source':sources(),**metadata,'rows_sha256':digest(rows)}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        freeze(directory/'CASES.json',rows);return finish(directory,identity,start,cpu,['CASES.json'],assigned=len(rows))


def cases(directory,scope):
    ci,done=completed(directory,'genetic-cases-v1',scope);rows=read(directory/'CASES.json');validate(rows)
    if digest(rows)!=ci['rows_sha256'] or len(rows)!=done['assigned'] or ci['selected_keys']!=[r['key'] for r in rows]:raise ValueError('genetic source allocation changed')
    return rows,ci


def controls(before,options,copied):
    if set(copied)!=set(options) or copied!=copy_probabilities(before,options):raise ValueError('copied-text prediction does not reconstruct')
    logits={k:-abs(len(before.split())-len(text.split())) for k,text in options.items()};maximum=max(logits.values())
    weights={k:math.exp(v-maximum) for k,v in logits.items()};total=math.fsum(weights.values())
    return {'copied_text':copied,'uniform':{k:1/len(options) for k in options},
            'length':{k:.99*v/total+.01/len(options) for k,v in weights.items()}}


def unit(case,result,kind):
    probabilities=None
    if result['accepted']:
        p=result['prediction']['probs']
        if set(p)!=set(case['evidence']['options']):raise ValueError('genetic prediction omitted a candidate')
        probabilities=controls(case['case']['local_before'],case['evidence']['options'],p) if kind=='controls' else {'neural':p}
    return {k:case[k] for k in ('key','unit','truth')}|{'valid':result['accepted'],'probabilities':probabilities,'call':result,
        'public_input_sha256':digest(case['evidence']),'hand_status':case['case']['hand_status'],'hands':case['case']['hands']}


def prediction_context(directory,cases_path,scope,kind,*,cell,source=None,family=None,training=None,package_kind='fitted'):
    """Shared original input/package identity; no writer or reader execution."""
    directory=output_root(directory,scope,'prediction');cases_path=inside(cases_path);rows,_=cases(cases_path,scope)
    source=sources() if source is None else source
    if kind=='controls':
        return {'cell_identity':cell,'operation':'genetic-controls-v1','scope':scope,'source':source,
            'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),
            'rivals':['copied_text','uniform','length']},rows,None
    if kind!='neural':raise ValueError('genetic prediction context requires controls or neural')
    from .neural_operations import training_package
    from .reader_packages import reference_package
    from .generation_policy import GREEDY
    if package_kind=='fitted':
        if training is None:raise ValueError('actual fitted package required')
        adapter,adapter_sha,fit_sha=training_package(training,family,scope)
    else:
        if training is not None:raise ValueError('reference package cannot name a fit')
        adapter,adapter_sha,fit_sha=reference_package(family,package_kind)
    identity={'cell_identity':cell,'operation':'genetic-neural-v1','scope':scope,'source':source,
        'cases':str(cases_path),'cases_complete_sha256':file_hash(cases_path/'COMPLETE.json'),'family':family,
        'package_kind':package_kind,'training':str(training) if training else None,'fit_sha256':fit_sha,'adapter_sha256':adapter_sha,
        'precision':'float16','max_context':4096,'max_support':128,'generation':GREEDY,'max_new_tokens':32}
    return identity,rows,adapter


def predict_controls(directory,cases_path,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'prediction')
    identity,rows,_=prediction_context(directory,cases_path,scope,'controls',cell=cell_identity())
    with writer(directory):
        units=Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        predictions=[]
        for case in rows:
            task={'operation':'copy_baseline','copy_source':case['case']['local_before']};evidence=case['evidence']
            result=checkpoint_call(directory/'calls'/(case['key']+'.json'),{'evidence':evidence,'task':task},
                lambda:execute(evidence,task,root=directory/'capsules'));audit_execution(result)
            row=unit(case,result,'controls');old=units.get(case['key'])
            if old is not None and old!=row:raise ValueError('genetic control resume changed')
            units.put(case['key'],row);predictions.append(row)
        freeze(directory/'PREDICTIONS.json',predictions)
        return finish(directory,identity,start,cpu,['units','calls','capsules','PREDICTIONS.json'],assigned=len(rows),invalid=sum(not r['valid'] for r in predictions),scored=False)


def predict_neural(directory,cases_path,scope,family,training=None,package_kind='fitted'):
    from .service_owner import resident
    from .generation_policy import GREEDY
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'prediction')
    identity,rows,adapter=prediction_context(directory,cases_path,scope,'neural',cell=cell_identity(),
        family=family,training=training,package_kind=package_kind)
    adapter_sha=identity['adapter_sha256']
    with writer(directory):
        units=Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        config={'family':family,'adapter':str(adapter) if adapter else None,'adapter_sha256':adapter_sha,'precision':'float16',
            'device':'cuda','batch_size':4,'max_context':4096,'max_support':128,'generation':GREEDY,'max_new_tokens':32}
        predictions=[]
        with resident(directory/'services'/uuid.uuid4().hex[:12],config) as (ready,token):
            freeze(directory/'PACKAGE.json',ready['identity'])
            for case in rows:
                evidence=case['evidence'];task={'operation':'choice','identity':ready['identity']|{'information_sha256':digest(evidence)}}
                result=checkpoint_call(directory/'calls'/(case['key']+'.json'),{'evidence':evidence,'task':task},
                    lambda:execute(evidence,task,ready['endpoint'],token,root=directory/'capsules'));audit_execution(result)
                row=unit(case,result,'neural');old=units.get(case['key'])
                if old is not None and old!=row:raise ValueError('genetic neural resume changed')
                units.put(case['key'],row);predictions.append(row)
        freeze(directory/'PREDICTIONS.json',predictions)
        return finish(directory,identity,start,cpu,['units','calls','capsules','services','PACKAGE.json','PREDICTIONS.json'],assigned=len(rows),invalid=sum(not r['valid'] for r in predictions),scored=False)


def verified_predictions(directory,scope,kind):
    from runners.readout_repair import readout
    identity,done=completed(directory,'genetic-'+kind+'-v1',scope);cases_path=inside(identity['cases']);rows,ci=cases(cases_path,scope)
    if file_hash(cases_path/'COMPLETE.json')!=identity['cases_complete_sha256']:raise ValueError('genetic prediction source changed')
    package=read(directory/'PACKAGE.json') if kind=='neural' else None;rebuilt=[]
    for case in rows:
        evidence=case['evidence'];task=({'operation':'choice','identity':package|{'information_sha256':digest(evidence)}} if kind=='neural' else
            {'operation':'copy_baseline','copy_source':case['case']['local_before']})
        result=checkpoint_call(directory/'calls'/(case['key']+'.json'),{'evidence':evidence,'task':task},None,resume_only=True);audit_execution(result)
        if kind=='neural' and result['accepted'] and readout(evidence['prefix'],evidence['options'],lambda p,o:result['prediction']['components'],task['identity'])!=result['prediction']:
            raise ValueError('genetic saved sequence readout does not reconstruct')
        rebuilt.append(unit(case,result,kind))
    if rebuilt!=read(directory/'PREDICTIONS.json') or len(rebuilt)!=done['assigned']:raise ValueError('genetic forecasts missing or changed')
    return rebuilt,identity,ci


def summarize(neural,rivals):
    a={r['key']:r for r in neural};b={r['key']:r for r in rivals}
    if not a or len(a)!=len(neural) or len(b)!=len(rivals) or set(a)!=set(b):raise ValueError('complete paired genetic predictions required')
    contrasts=[]
    for model in ('copied_text','uniform','length'):
        pairs=[];invalid=[]
        for key,row in a.items():
            other=b[key]
            if any(row[k]!=other[k] for k in ('unit','truth','public_input_sha256')):raise ValueError('genetic comparison changes task or work')
            if not row['valid'] or not other['valid']:invalid.append(key);continue
            if set(row['probabilities'])!={'neural'} or set(other['probabilities'])!={'copied_text','uniform','length'}:raise ValueError('genetic model roster differs')
            left=row['probabilities']['neural'];right=other['probabilities'][model]
            if set(left)!=set(right):raise ValueError('genetic comparison changes offered support')
            x,y=log_score(left,row['truth']),log_score(right,row['truth'])
            pairs.append({'unit':row['unit'],'difference':None if x==y==-math.inf else x-y})
        base={'rival':model,'assigned':len(a),'independent_works':len({r['unit'] for r in a.values()}),'excluded':0}
        if invalid:contrasts.append(base|{'disposition':'IMPLEMENTATION INVALID','invalid':invalid,'scored':0})
        else:
            estimate=paired_extended(pairs,draws=100)
            if estimate.get('ci') is not None:raise ValueError('qualitative genetic branch unexpectedly contains independent works')
            contrasts.append(base|{'estimate':estimate,'disposition':'DESCRIPTIVE','scored':len(pairs)})
    return {'contrasts':contrasts,'scientific_admission':False,'confirmation_eligible':False,
        'scope':'offered local replacement correspondence in one famous work; local editorial hand/chronology uncertainty retained; memorization unresolved; no population or historical-intention claim'}


def analyze(directory,neural_path,controls_path,scope):
    start,cpu=time.monotonic(),time.process_time();directory=output_root(directory,scope,'analysis');neural_path,controls_path=map(inside,(neural_path,controls_path))
    neural,ni,nc=verified_predictions(neural_path,scope,'neural');rivals,bi,bc=verified_predictions(controls_path,scope,'controls')
    if nc!=bc or ni['cases_complete_sha256']!=bi['cases_complete_sha256']:raise ValueError('genetic comparison source differs')
    identity={'cell_identity':cell_identity(),'operation':'genetic-analysis-v1','scope':scope,'source':sources(),
        'inputs':{name:{'path':str(path),'complete_sha256':file_hash(path/'COMPLETE.json')} for name,path in [('neural',neural_path),('controls',controls_path)]}}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        freeze(directory/'PROFILE.json',score_json(summarize(neural,rivals)))
        return finish(directory,identity,start,cpu,['PROFILE.json'],confirmation_eligible=False)


def argument_parser():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('prepare','controls','neural','evaluate'));p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    for k in ('output','cases','training','neural','controls'):p.add_argument('--'+k,type=Path,required=k=='output')
    p.add_argument('--family',choices=('qwen','smollm'));p.add_argument('--package-kind',choices=('fitted','base','archive'),default='fitted')
    return p


if __name__=='__main__':
    a=argument_parser().parse_args()
    if a.operation=='prepare':prepare(a.output,a.scope)
    elif a.operation=='controls':predict_controls(a.output,a.cases,a.scope)
    elif a.operation=='neural':predict_neural(a.output,a.cases,a.scope,a.family,a.training,a.package_kind)
    else:analyze(a.output,a.neural,a.controls,a.scope)
