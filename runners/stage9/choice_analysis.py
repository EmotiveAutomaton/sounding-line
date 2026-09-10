"""Complete offered-choice profiles against a single development-selected rival.

DESIGN CHECK: C01/C05/C07/C08/X01/X02/X06/X11; LESSONS 3--5, CONTROLS 6.
NULL: equal forecasts have zero gain, bad seeds stay in the profile, and a stronger
cheap rival defeats a reader. ALTERNATIVE: complete prospective gain exceeds .05
nats with a positive paired interval in each separately reported domain. Identical
public questions form one analysis cluster, not additional independent questions.
This is a component profile: actual package calibration and final card controls
remain necessary for admission. No model selection or reserve access occurs here.
"""
import argparse
from pathlib import Path
import time
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.artifact_analysis import load_complete,select
from runners.stage9.artifact_comparisons import checkpoint_call,model_inputs
from runners.stage9.baseline_predictions import unit_result as baseline_unit
from runners.stage9.neural_operations import case_inputs,unit_result as neural_unit,validate_complete
from runners.stage9.prospective_choice import choice_input
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.scoring import log_score,paired_extended,classify,score_json
from runners.stage9.training_jobs import cell_identity

VIEWS={'genuine_choice':'process_record','process_choice':'process_record','artifact_choice':'artifact'}


def baseline_inputs(directory,scope):
    directory=inside(directory);identity=read(directory/'IDENTITY.json')
    if identity['operation']!='independent-baseline-predictions-v1' or identity['scope']!=scope:
        raise ValueError('independent complete baseline handler required')
    rows,expected,identity,done=load_complete(directory,identity['role'])
    cases,role,sha=case_inputs(Path(identity['cases']),scope,2 if scope=='pilot' else 0)
    package=model_inputs(Path(identity['models']),role)
    if sha!=identity['cases_complete_sha256'] or package['completion_sha256']!=identity['model_completion_sha256']:
        raise ValueError('baseline cases or fitted models changed')
    units=Units(directory,identity)
    rebuilt=[]
    for case in cases:
        def call(bundle,view):
            return checkpoint_call(directory/'calls'/case['unit'][:16]/(view+'.json'),bundle,None,resume_only=True)
        row=baseline_unit(case,package,call,tuple(identity['doses']))
        if row!=units.get(case['unit']):raise ValueError('baseline unit no longer reconstructs')
        rebuilt.append(row)
    if rows!=rebuilt or expected!=[c['unit'] for c in cases]:raise ValueError('baseline saved row order or allocation changed')
    return rows,cases,identity,done


def selection_inputs(directory,scope):
    directory=inside(directory);identity=read(directory/'IDENTITY.json');done=read(directory/'COMPLETE.json')
    role='pilot' if scope=='pilot' else 'development'
    if (identity['operation']!='select' or identity['role']!=role or done.get('execution_complete') is not True
        or done['identity_sha256']!=digest(identity)
        or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('development selection incomplete or changed')
    receipt=read(directory/'SELECTION.json')
    # The selection identity fixes hashes; the explicit provenance paths below
    # are provided by this handler's caller, then verified against those hashes.
    return identity,receipt


def summarize(cases,operation,predictions,baseline_rows,selection,*,scope,draws=4000):
    if operation not in VIEWS or scope not in ('pilot','scientific'):raise ValueError('undeclared prediction profile')
    count=2 if scope=='pilot' else 192
    expected=[c['unit'] for c in cases]
    if (len(cases)!=count or len(set(expected))!=count or set(predictions)!=set(expected)
        or len(baseline_rows)!=count or {r['unit'] for r in baseline_rows}!=set(expected)):
        raise ValueError('complete offered-choice and paired baseline allocation required')
    query=VIEWS[operation]+'|dose0';chosen=selection[query]
    if chosen.get('accepted') is not True:raise ValueError('required cheap-rival selection invalid')
    selected=chosen['selection']['selected']
    if set(expected)&set(chosen['selection']['units']):raise ValueError('development unit entered prediction profile')
    lookup={r['unit']:r for r in baseline_rows};rows=[]
    for case in cases:
        evidence=choice_input(case,operation);base=lookup[case['unit']]
        item=base['rows'][query];pred=predictions[case['unit']]
        if base['truth']!=case['target'] or set(item['support'])!=set(evidence['options']):
            raise ValueError('neural and baseline target or support differ')
        valid=pred.get('accepted') is True and item['validity'].get(selected) is True
        difference=None;left=right=None
        if valid:
            probabilities=pred['prediction']['probs'];rival=item['predictions'][selected]
            if set(probabilities)!=set(evidence['options']) or set(rival)!=set(evidence['options']):
                raise ValueError('prediction component omitted support')
            left=log_score(probabilities,case['target']);right=log_score(rival,case['target'])
            difference=None if left==right==float('-inf') else left-right
        rows.append({'unit':digest(evidence),'source_unit':case['unit'],'domain':case['private_factors']['domain'],
            'law':case['private_factors']['law'],'purpose':case['private_factors']['purpose'],
            'target_type':case['target'].split(':')[0],'valid':valid,'difference':difference,
            'reader_log_score':left,'rival_log_score':right})
    groups={}
    for field in ('domain','law','purpose','target_type'):
        groups[field]={}
        for name in sorted({r[field] for r in rows}):
            subset=[r for r in rows if r[field]==name];valid=all(r['valid'] for r in subset)
            summary=paired_extended(subset,draws=draws,seed=9011) if valid else None
            groups[field][name]={'assigned':len(subset),'invalid':sum(not r['valid'] for r in subset),
                'distinct_questions':len({r['unit'] for r in subset}),'contrast':summary,
                'disposition':classify(summary,threshold=.05,descriptive=scope=='pilot') if valid else 'IMPLEMENTATION INVALID',
                'component_criterion_pass':bool(scope=='scientific' and valid and summary['finite_estimate']
                    and summary['mean']>=.05 and summary['ci'] is not None and summary['ci'][0]>0)}
    return {'operation':operation,'scope':scope,'selected_rival':selected,'query':query,'groups':groups,
        'assigned_units':count,'distinct_public_questions':len({r['unit'] for r in rows}),
        'practical_effect_nats':.05,'scientific_admission':False,
        'admission_limit':'separate actual package precision and full card controls required; no historical full-generator admission'},rows


def run(directory,neural_path,baseline_path,development_path,selection_path,scope):
    started,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    prefix='choice-analysis-pilots' if scope=='pilot' else 'scientific-choice-analysis'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('choice analysis output scope differs')
    rows,cases,bi,bd=baseline_inputs(baseline_path,scope)
    development,dev_cases,di,dd=baseline_inputs(development_path,scope)
    if bi['role'] not in (('pilot',) if scope=='pilot' else ('development','discovery')) or di['role']!=('pilot' if scope=='pilot' else 'development'):
        raise ValueError('choice selection/evaluation role differs')
    si,selection=selection_inputs(selection_path,scope)
    if (bi['model_completion_sha256']!=di['model_completion_sha256']
        or si['prediction_completion_sha256']!=file_hash(inside(development_path)/'COMPLETE.json')
        or selection['package_sha256']!=di['model_completion_sha256']):raise ValueError('choice selection package or development prediction differs')
    queries=selection['selections'];eligible={k:v['selection']['eligible'] for k,v in queries.items() if v['accepted']}
    if set(eligible)!=set(queries) or select(development,[c['unit'] for c in dev_cases],eligible,selection['package_sha256'])!=queries:
        raise ValueError('selected cheap comparator does not reproduce')
    neural_path=inside(neural_path);ni=read(neural_path/'IDENTITY.json');nd=validate_complete(neural_path,ni)
    if (ni['operation'] not in VIEWS or ni['scope']!=scope or ni['role']!=bi['role']
        or ni['cases_complete_sha256']!=bi['cases_complete_sha256'] or ni['units']!=bi['selected_units']):
        raise ValueError('complete matched neural operation required')
    dev_public={digest(choice_input(c,ni['operation'])) for c in dev_cases}
    if any(digest(choice_input(c,ni['operation'])) in dev_public for c in cases):
        raise ValueError('development public question entered evaluation')
    units=Units(neural_path,ni);package=read(neural_path/'PACKAGE.json');predictions={}
    for case in cases:
        def call(evidence,arguments,index):
            task={**arguments,'identity':{**package,'information_sha256':digest(evidence)}}
            return checkpoint_call(neural_path/'calls'/case['unit'][:16]/('call-'+digest(index)[:16]+'.json'),
                {'evidence':evidence,'task':task},None,resume_only=True)
        row=neural_unit(case,ni['operation'],call)
        if row!=units.get(case['unit']):raise ValueError('complete neural choice unit does not reconstruct')
        predictions[case['unit']]=row['result']['call']
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'choice-profile-v1','scope':scope,'source':source,'package':package,
        'inputs':{name:{'path':str(inside(path)),'complete_sha256':file_hash(inside(path)/'COMPLETE.json')}
                  for name,path in [('neural',neural_path),('baseline',baseline_path),('development',development_path),('selection',selection_path)]}}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed choice profile changed')
            return done
        profile,paired=summarize(cases,ni['operation'],predictions,rows,queries,scope=scope)
        profile['role']=bi['role']
        profile['selection_only']=bi['role']=='development'
        freeze(directory/'PROFILE.json',score_json(profile));freeze(directory/'PAIRED_ROWS.json',score_json(paired));verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'scope':scope,
            'wall_seconds':time.monotonic()-started,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/p for p in ('IDENTITY.json','PROFILE.json','PAIRED_ROWS.json')]),'scientific_admission':False}
        freeze(directory/'COMPLETE.json',done);return done


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('output','neural','baseline','development','selection'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    a=p.parse_args();run(a.output,a.neural,a.baseline,a.development,a.selection,a.scope)
