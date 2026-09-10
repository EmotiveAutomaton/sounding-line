"""Allocate distinct unexposed local questions before any reader execution.

DESIGN CHECK: C03/X01/X02/X05/X11; LESSONS 3--5, CONTROLS 6.
NULL: renamed sources or private truth cannot make duplicate visible questions
independent. ALTERNATIVE: the same fixed constructor cohorts yield distinct local
tasks in each view, excluding prior fitting/selection questions using only public
inputs. Retain all attempts, source exclusions and both total and eligible yields;
require >=.75 realization in every domain/purpose group on BOTH denominators.
This is explicitly the unexposed distinct-local-task population, not the original
unfiltered distribution. No future consequence or model output selects a case.
"""
import argparse
from collections import Counter
from pathlib import Path
import time
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .queue import inside,verify_sources,writer
from .training_jobs import cell_identity
from .artifact_comparisons import validate_cases
from .local_repair import task_case
from .repair_jobs import VIEWS,public_task,sources
from .series_cases import COHORTS,construct_attempt


def public_keys(case):
    if case.get('realized') is not True:raise ValueError('no local question at an unrealized boundary')
    return {view:digest(public_task(task_case(case,view))) for view in VIEWS}


def exclusion_inputs(paths):
    excluded={view:set() for view in VIEWS};references=[]
    for path in paths:
        path=inside(path);done=read(path/'COMPLETE.json')
        if (done.get('accepted') is not True or done.get('construction_only') is not True
            or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
            raise ValueError('invalid source-exclusion preparation')
        cases=read(path/'CASES.json');validate_cases(cases,done['role'])
        if len(cases)!=done['selected_series']:raise ValueError('source-exclusion cohort incomplete')
        for case in cases:
            for view,key in public_keys(case).items():excluded[view].add(key)
        references.append({'path':str(path),'completion_sha256':file_hash(path/'COMPLETE.json'),'role':done['role'],'source_units':len(cases)})
    return excluded,references


def eligibility(case,excluded,seen):
    if not case['realized']:return False,case['reason'],None
    keys=public_keys(case)
    if any(key in excluded[view] for view,key in keys.items()):return False,'exposed_public_local_task',keys
    if any(key in seen[view] for view,key in keys.items()):return False,'repeated_public_local_task',keys
    return True,None,keys


def prepare(directory,*,role,key,exclude=(),per_cohort=2,attempts_per_cohort=40):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    if role not in ('pilot','training','development','discovery') or not isinstance(key,str) or not key:
        raise ValueError('explicit unsealed role and source namespace required')
    if type(per_cohort) is not int or per_cohort<2 or type(attempts_per_cohort) is not int or attempts_per_cohort<per_cohort:
        raise ValueError('complete local-task cohort and bounded construction budget required')
    expected_root=ROOT/'private'/('repair-case-pilots' if role=='pilot' else 'scientific-repair-cases')
    if not directory.is_relative_to(expected_root):raise ValueError('local task preparation namespace differs from role')
    excluded,references=exclusion_inputs(exclude);source=sources()
    identity={'cell_identity':cell,'operation':'unique-local-repair-cases-v1','role':role,'key':key,'source':source,
        'per_cohort':per_cohort,'dose':0,'attempts_per_cohort':attempts_per_cohort,'references':references,
        'excluded_public_keys':{view:sorted(values) for view,values in excluded.items()},'cohorts':[list(c) for c in COHORTS],
        'selection':'first realized unexposed task distinct in both public views within fixed cohorts; no future target selection',
        'realization_gate':{'grouping':['domain','purpose'],'all_attempt_minimum':.75,'eligible_attempt_minimum':.75}}
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed local source preparation changed')
            return done
        seen={view:set() for view in VIEWS};source_seen=set();selected=[];attempts=[];groups={}
        for cohort in COHORTS:
            accepted=0
            for attempt in range(attempts_per_cohort):
                attempt_key={'cohort':list(cohort),'attempt':attempt};row=units.get(attempt_key)
                if row is None:
                    case=construct_attempt(key=digest({'namespace':key,**attempt_key}),cohort=cohort,role=role,dose=0)
                    row={**attempt_key,'case':case};units.put(attempt_key,row)
                case=row['case'];eligible,reason,keys=eligibility(case,excluded,seen)
                projected_exclusion=reason in ('exposed_public_local_task','repeated_public_local_task')
                group=groups.setdefault(cohort[0]+'|'+cohort[3],{'attempted':0,'eligible_attempted':0,'selected':0})
                group['attempted']+=1;group['eligible_attempted']+=not projected_exclusion;group['selected']+=eligible
                attempts.append({**attempt_key,'constructor_realized':case['realized'],'selected':eligible,
                    'reason':reason,'public_keys':keys,'parameter_draws':case.get('parameter_draws',0)})
                if eligible:
                    if source_seen&set(case['sources']):raise ValueError('duplicate whole source reached local selection')
                    selected.append(case);source_seen.update(case['sources'])
                    for view,value in keys.items():seen[view].add(value)
                    accepted+=1
                if accepted==per_cohort:break
        for group in groups.values():
            group['all_attempt_yield']=group['selected']/group['attempted']
            group['eligible_yield']=group['selected']/group['eligible_attempted'] if group['eligible_attempted'] else 0.
        requested=len(COHORTS)*per_cohort
        qualified=len(selected)==requested and all(g['all_attempt_yield']>=.75 and g['eligible_yield']>=.75 for g in groups.values())
        assert all(len(values)==len(selected) and not values&excluded[view] for view,values in seen.items())
        validate_cases(selected,role)
        freeze(directory/'CASES.json',selected);freeze(directory/'ATTEMPTS.json',attempts)
        freeze(directory/'PUBLIC_TASKS.json',{c['unit']:public_keys(c) for c in selected});verify_sources(source)
        result={'cell_identity':cell,'identity_sha256':digest(identity),'role':role,'source':source,'construction_only':True,
            'accepted':qualified,'selected_series':len(selected),'requested_series':requested,'attempted_series':len(attempts),
            'distinct_public_tasks':{v:len(s) for v,s in seen.items()},'groups':groups,'exclusions':dict(Counter(r['reason'] for r in attempts if not r['selected'])),
            'wall_seconds':time.monotonic()-start,'cpu_seconds':time.process_time()-cpu,
            'disposition':'DESCRIPTIVE' if qualified else 'IMPLEMENTATION INVALID','scientific_admission':False,
            'outputs':closure([directory/'CASES.json',directory/'ATTEMPTS.json',directory/'PUBLIC_TASKS.json',directory/'units'])}
        freeze(directory/'COMPLETE.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--role',required=True,choices=('pilot','training','development','discovery'));p.add_argument('--key',required=True)
    p.add_argument('--exclude',action='append',type=Path,default=[]);p.add_argument('--per-cohort',type=int,default=2)
    p.add_argument('--attempts-per-cohort',type=int,default=40);a=p.parse_args()
    result=prepare(a.output,role=a.role,key=a.key,exclude=a.exclude,per_cohort=a.per_cohort,attempts_per_cohort=a.attempts_per_cohort)
    print('Local source preparation complete; accepted='+str(result['accepted'])+'; no reader evaluated.',flush=True)
