"""Full C01/C02/C04/C06/C08 diagnostics on immutable operation executions.

DESIGN CHECK: LESSONS 3--5, CONTROLS 6, X01/X06/X08/X10/X11.
NULL: stories, invalid calls, constant binary answers, early STOP and missing
matched states cannot masquerade as sustained or distinguishing competence.
ALTERNATIVE: exact constructor/rule execution has known correct consequences;
realized paired views are compared on the same sources and every attempt remains.
Rates and conditional matched-state contrasts are diagnostics, not broad admission.
Finite projections are the independent units, never their source-world aliases.
"""
import argparse
from collections import Counter
from functools import partial
from pathlib import Path
import time
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.artifact_comparisons import checkpoint_call
from runners.stage9.competence import rate
from runners.stage9.finite_queries import group_cases
from runners.stage9.neural_operations import case_inputs,unit_result,validate_complete,request_task
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.scoring import log_score,paired_extended,score_json
from runners.stage9.series_cases import recorded_target
from runners.stage9.training_jobs import cell_identity

ROLLOUTS=('offered','environment_outcome','self_outcome','reset_environment','artifact_environment')
HORIZONS=(1,4,8,16)


def exact_binary(call):
    if call.get('accepted') is not True:return None
    p=call['prediction']['probs']
    if set(p)!={'yes','no'}:raise ValueError('complete binary future support required')
    # A tied or uniform reader earns no distinguishing success.
    log_score(p,'yes')
    if p['yes']==p['no']:return None
    return max(p,key=p.get)


def finite_profile(rows):
    if not rows or len({r['result']['projection_identity'] for r in rows})!=len(rows):
        raise ValueError('one representative per independent finite projection required')
    results=[]
    for row in rows:
        result=row['result'];queries=result['queries'];by_condition={};marginals=Counter()
        for item in queries:
            query=item['query'];key=digest(query['sequence']);condition=query['condition']
            if key in by_condition.setdefault(condition,{}):raise ValueError('repeated finite query')
            answer=exact_binary(item['call']);marginals[query['truth']]+=1
            by_condition[condition][key]={'truth':query['truth'],'answer':answer,
                'valid':item['call'].get('accepted') is True,'length':len(query['sequence']),
                'proper_log_score':log_score(item['call']['prediction']['probs'],query['truth']) if item['call'].get('accepted') is True else None}
        required={'distinction_left','distinction_right','compression_left','compression_right'}
        if set(by_condition)!=required or len({tuple(sorted(q)) for q in by_condition.values()})!=1:
            raise ValueError('complete matched finite query grid required')
        compression=[];distinction=[];longer=[]
        for key,left in by_condition['compression_left'].items():
            right=by_condition['compression_right'][key]
            if left['truth']!=right['truth']:raise ValueError('compression truth is not equivalent')
            compression.append(left['answer']==right['answer']==left['truth'])
        for key,left in by_condition['distinction_left'].items():
            right=by_condition['distinction_right'][key]
            if left['truth']!=right['truth']:
                correct=left['answer']==left['truth'] and right['answer']==right['truth']
                distinction.append(correct)
                if left['length']>1:longer.append(correct)
        if not longer or not distinction:raise ValueError('no actual longer distinction in finite battery')
        flat=[r for condition in by_condition.values() for r in condition.values()]
        results.append({'unit':result['projection_identity'],'query_count':len(flat),'truth_counts':dict(marginals),
            'valid_calls':sum(r['valid'] for r in flat),'correct_answers':sum(r['answer']==r['truth'] for r in flat),
            'compression_correct':all(compression),'distinction_correct':all(distinction),'longer_distinction_correct':all(longer),
            'all_answers_correct':all(r['answer']==r['truth'] for r in flat),'queries':by_condition})
    return {'units':results,'independent_projections':len(results),
        'exact_supported_battery_pass':all(r['all_answers_correct'] for r in results),
        'compression':rate(sum(r['compression_correct'] for r in results),len(results)),
        'distinction':rate(sum(r['distinction_correct'] for r in results),len(results)),
        'longer_distinction':rate(sum(r['longer_distinction_correct'] for r in results),len(results)),
        'disposition':'DESCRIPTIVE','scientific_admission':False,
        'limit':'finite supplied-rule diagnostic; small distinct-projection count and source aliases disclosed, no stochastic-world or paper replication claim'}


def prefix_profile(cases,rows,draws=4000):
    if len(cases)!=len(rows) or {r['unit'] for r in rows}!={c['unit'] for c in cases}:raise ValueError('complete prefix allocation required')
    lookup={r['unit']:r['result'] for r in rows};attempts=[]
    for case in cases:
        row=lookup[case['unit']];item={'unit':case['unit'],'domain':case['private_factors']['domain'],
            'realized':row['realized'],'generated_matched':row['matched_generated_state'],'valid':False}
        if not row['realized']:
            attempts.append(item|{'reason':row['reason']});continue
        truth,reason=recorded_target(case['source_worlds'][0]['trajectory'],row['boundary'])
        if reason:raise ValueError('matched prefix lacks a genuine prospective target')
        scores={};supports=[]
        item['source_unit']=item['unit']
        item['unit']=digest({name:row['predictions'][name]['copied_sources']['evidence_sha256'] for name in ('genuine','altered')})
        for name,call in row['predictions'].items():
            if call.get('accepted') is True:
                p=call['prediction']['probs'];scores[name]=log_score(p,truth);supports.append(set(p))
            else:scores[name]=None
        if supports and any(s!=supports[0] for s in supports):raise ValueError('matched prefix supports differ')
        if ('generated' in scores)!=row['matched_generated_state']:raise ValueError('unrealized generated state was scored')
        item.update(scores=scores,valid=all(v is not None for v in scores.values()),truth=truth)
        attempts.append(item)
    groups={}
    for domain in sorted({r['domain'] for r in attempts}):
        own=[r for r in attempts if r['domain']==domain];realized=[r for r in own if r['realized']]
        contrasts={}
        for name in ('altered','generated'):
            selected=[r for r in realized if name in r['scores']]
            valid=bool(selected) and all(r['valid'] for r in selected)
            pairs=[{'unit':r['unit'],'difference':None if r['scores'][name]==r['scores']['genuine']==float('-inf')
                else r['scores'][name]-r['scores']['genuine']} for r in selected] if valid else []
            accepted_construction=len(realized)/len(own)>=.75
            contrasts[name]={'assigned':len(own),'realized_source_pairs':len(realized),'scored_matched_pairs':len(selected),
                'source_realization_pass':accepted_construction,
                'contrast':paired_extended(pairs,draws=draws,seed=9031) if valid and accepted_construction else None,
                'disposition':('IMPLEMENTATION INVALID' if not accepted_construction or selected and not valid
                    else 'DESCRIPTIVE' if valid else 'NOT RUN WITH REASON'),
                'reason':None if selected else 'no assigned generated history reached the declared exact matched state',
                'scope':'conditional on exact realized state; generated match is reader-dependent, not a population causal effect'}
        groups[domain]={'realization':rate(len(realized),len(own)),'contrasts':contrasts}
    return {'attempts':attempts,'domains':groups,'scientific_admission':False,
        'all_assignments_retained':True,'limit':'state-match failures retain reasons; a conditional comparison cannot identify performance where generation never reached that state'}


def rollout_profile(cases,operations,draws=4000):
    expected={c['unit'] for c in cases}
    if not expected or set(operations)!=set(ROLLOUTS):raise ValueError('all five declared rollout assistance conditions required')
    if any(len(rows)!=len(expected) or {r['unit'] for r in rows}!=expected for rows in operations.values()):
        raise ValueError('rollout conditions do not share the complete assigned source cohort')
    lookups={k:{r['unit']:r for r in rows} for k,rows in operations.items()};groups={}
    clusters={c['unit']:digest({op:lookups[op][c['unit']]['result']['attempts'][0]['evidence_sha256']
        for op in ROLLOUTS}) for c in cases}
    def cluster_rate(values,own):
        pairs=[{'unit':clusters[c['unit']],'difference':float(v)} for c,v in zip(own,values)]
        return {'successes':sum(values),'assigned_worlds':len(own),'raw_rate':sum(values)/len(own),
            'equal_public_question_cluster_mean':paired_extended(pairs,draws=draws,seed=9041)}
    pairs=(('environment_outcome','offered'),('self_outcome','environment_outcome'),
        ('reset_environment','environment_outcome'),('artifact_environment','environment_outcome'))
    for domain in sorted({c['private_factors']['domain'] for c in cases}):
        own=[c for c in cases if c['private_factors']['domain']==domain];conditions={}
        for operation,lookup in lookups.items():
            rows=[lookup[c['unit']]['result'] for c in own]
            conditions[operation]={'assigned_worlds':len(own),'assistance':rows[0]['assistance'],
                'distinct_initial_public_questions':len({clusters[c['unit']] for c in own}),
                'stop_rate':cluster_rate([r['stopped'] for r in rows],own),
                'any_invalid_call':cluster_rate([any(a['valid_execution'] is not True for a in r['attempts']) for r in rows],own),
                'failure_reasons':dict(Counter(r['failure'] for r in rows if r['failure'])),
                'horizons':{str(h):{
                    key:cluster_rate([bool(r['horizons'][str(h)][key]) for r in rows],own)
                    for key in ('reached_action_horizon','all_observed_actions_legal','stopped','reset_realized')}
                    for h in HORIZONS}}
        contrasts={}
        for left,right in pairs:
            contrasts[left+'-vs-'+right]={}
            for horizon in HORIZONS:
                paired=[]
                for case in own:
                    a=lookups[left][case['unit']]['result']['horizons'][str(horizon)]
                    b=lookups[right][case['unit']]['result']['horizons'][str(horizon)]
                    paired.append({'unit':clusters[case['unit']],'difference':float(a['reached_action_horizon'])-float(b['reached_action_horizon'])})
                contrasts[left+'-vs-'+right][str(horizon)]={'contrast':paired_extended(paired,draws=draws,seed=9041),
                    'disposition':'DESCRIPTIVE','meaning':'paired rate of reaching the stated number of legal executed actions; STOP is shown separately, not credited as sustained action'}
        groups[domain]={'conditions':conditions,'contrasts':contrasts}
    return {'domains':groups,'scientific_admission':False,'independent_unit':'source world; nested action horizons are not independent replicates',
        'limit':'action, outcome and reset-assistance diagnostic; no policy-quality or correct-stopping verdict from legality or length alone'}


def reconstructed(path,cases_path,scope):
    path=inside(path);identity=read(path/'IDENTITY.json');validate_complete(path,identity)
    cases,role,sha=case_inputs(cases_path,scope,2 if scope=='pilot' else 0)
    if identity['scope']!=scope or identity['cases_complete_sha256']!=sha or identity['role']!=role:
        raise ValueError('operation analysis source identity differs')
    selected,groups=group_cases(cases) if identity['operation']=='finite_queries' else (cases,None)
    if identity['units']!=[c['unit'] for c in selected] or identity.get('projection_groups')!=groups:
        raise ValueError('operation analysis source aliases or allocation changed')
    package=read(path/'PACKAGE.json');rows=[]
    for case in selected:
        def call(evidence,arguments,index):
            task=request_task(evidence,arguments,package)
            return checkpoint_call(path/'calls'/case['unit'][:16]/('call-'+digest(index)[:16]+'.json'),
                {'evidence':evidence,'task':task},None,resume_only=True)
        row=unit_result(case,identity['operation'],call)
        saved=read(path/'units'/(digest(case['unit'])+'.json'))
        expected={'identity':digest(identity),'key':case['unit'],'complete':True,'row':row}
        if digest(saved)!=digest(expected):raise ValueError('operation unit does not reconstruct')
        rows.append(row)
    return cases,rows,identity,package


def context(directory,cases_path,plan_path,scope,*,cell,source=None):
    """Read original inputs without acquiring a writer or executing a reader."""
    directory=inside(directory)
    prefix='operation-analysis-pilots' if scope=='pilot' else 'scientific-operation-analysis'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('operation analysis scope differs')
    plan=read(inside(plan_path));kind=plan['operation'];sources={};rows={};packages={};cases=None
    expected=(ROLLOUTS if kind=='rollouts' else ('finite_queries',) if kind=='finite' else
              ('prefix_match',) if kind=='prefix' else ('supplied_kernel',) if kind=='supplied' else ())
    if not expected or set(plan['inputs'])!=set(expected):raise ValueError('explicit complete operation comparison required')
    for name,path in plan['inputs'].items():
        own,data,identity,package=reconstructed(inside(path),inside(cases_path),scope)
        if identity['operation']!=name or cases is not None and cases!=own:raise ValueError('operation comparison changed assigned cases')
        if packages and package!=next(iter(packages.values())):raise ValueError('operation comparison uses different actual packages')
        cases=own;rows[name]=data;packages[name]=package;sources[name]=file_hash(inside(path)/'COMPLETE.json')
    if source is None:
        source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
            REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    else:
        # Preserve the original dispatcher's scope, including older queue sources.
        files={p:sha for p,sha in source['files'].items() if p.startswith(
            ('runners/stage9/','runners/stage7/','runners/stage8/','soundingline/')) or p in
            {'runners/__init__.py','runners/readout_repair.py','runners/s3_lib.py','runners/s4_lib.py','runners/s5_lib.py'}}
        source={'files':files,'sha256':digest(files)}
    identity={'cell_identity':cell,'operation':'complete-operation-analysis-v1','kind':kind,'scope':scope,'source':source,
        'plan_sha256':file_hash(inside(plan_path)),'inputs':sources,'packages':packages,
        'cases_complete_sha256':file_hash(inside(cases_path)/'COMPLETE.json')}
    return identity,cases,rows


def summarize(kind,cases,rows):
    """The unchanged diagnostic calculations, shared by execution and final audit."""
    if kind=='supplied':
        from runners.stage9.supplied_operations import profile
        return profile(rows['supplied_kernel'])
    if kind not in ('rollouts','finite','prefix'):raise ValueError('undeclared diagnostic profile')
    return (rollout_profile(cases,rows) if kind=='rollouts' else finite_profile(rows['finite_queries']) if kind=='finite'
        else prefix_profile(cases,rows['prefix_match']))


def run(directory,cases_path,plan_path,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    identity,cases,rows=context(directory,cases_path,plan_path,scope,cell=cell)
    source=identity['source']
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('complete operation analysis changed')
            return done
        result=summarize(identity['kind'],cases,rows)
        freeze(directory/'PROFILE.json',score_json(result));verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'scientific_admission':False,
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'IDENTITY.json',directory/'PROFILE.json'])}
        freeze(directory/'COMPLETE.json',done);return done


def argument_parser():
    p=argparse.ArgumentParser()
    for name in ('output','cases','plan'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    return p


if __name__=='__main__':
    a=argument_parser().parse_args();run(a.output,a.cases,a.plan,a.scope)
