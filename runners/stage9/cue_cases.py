"""Paired global/local future states constructed before source reports are scored.

DESIGN CHECK: T04/X01/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: an already tight deadline, unchanged hazard, absent local check or missing
known mark fails conditional eligibility. ALTERNATIVE: existing state interventions
change global stopping pressure versus only one section's check availability, with
goal, expertise, habit and history fixed. All original realization gates remain.
Scientific source selection requires one fixed 2304-series pool per role, then 24
eligible units per domain/purpose; shortfall refuses without replacement-seed search.
The cue reliability is a stipulated reader assumption; balanced true/false stress
arms are not claimed to be a naturally calibrated reporter sample.
"""
import argparse
import copy
import time
from pathlib import Path
from .common import REPO, ROOT, Units, digest, file_hash, freeze, read, closure
from .construction import Replay, LAW, register
from .queue import inside, writer
from .revision_predictions import sources, reentry, finish
from .artifact_comparisons import validate_cases
from .training_jobs import cell_identity


def eligibility(case):
    world=case['source_worlds'][0]
    replay=Replay(world,world['trajectory']['steps'][:case['requested_boundary']])
    old=replay.snapshot();p=replay.probabilities()
    global_change=copy.deepcopy(replay)
    global_change.c_ext,global_change.belief=LAW.apply_change(global_change.c_ext,global_change.belief,'deadline_imposed')
    gp=global_change.probabilities()
    sections=sorted({a['section'] for a in replay.pending if a['type']=='check' and p.get(LAW.action_id(a),0)>0})
    section=sections[0] if sections else None
    local_change=copy.deepcopy(replay)
    if section is not None:
        local_change.belief['believed_checked']=sorted(set(local_change.belief['believed_checked'])|{section})
    lp=local_change.probabilities();local=local_change.snapshot()
    removed=set(old['subjective_action_space'])-set(local['subjective_action_space'])
    only_local=bool(removed) and all(a['type']=='check' and a['section']==section
                                   for a in replay.pending if LAW.action_id(a) in removed)
    if set(local['subjective_action_space'])-set(old['subjective_action_space']):
        raise ValueError('local context unexpectedly creates new subjective actions')
    conditions={'global_deadline_was_loose':old['external_context']['deadline']=='loose' and old['maker_context']['perceived_deadline']=='loose',
                'global_hazard_changes':gp.get('stop',0)>p.get('stop',0),
                'local_removes_only_one_sections_checks':only_local,'local_policy_changes':lp!=p,
                'known_past_mark_for_redundant_cue':bool(case['views']['process_record']['current']['marks'])}
    for changed in (global_change,local_change):
        state=changed.snapshot()
        if any(state[k]!=old[k] for k in ('proximal_goal','expertise_law','history_residue')) or changed.steps!=replay.steps:
            raise ValueError('context intervention changes goal, skill, habit or recorded past')
    return {'eligible':all(conditions.values()),'conditions':conditions,'section':section},global_change,local_change


def counterfactual(case,condition):
    if condition not in ('global','local'):
        raise ValueError('unknown context-reach condition')
    check,global_change,local_change=eligibility(case)
    if not check['eligible']:
        raise ValueError('source cannot realize both context interventions and redundancy control')
    replay=global_change if condition=='global' else local_change
    oracle=replay.probabilities()
    seed=int(digest({'context_cue_future_v1':case['source_worlds'][0]['lid'],'boundary':case['requested_boundary']})[:16],16)
    events,stopped=replay.continue_teacher(seed,max_events=case['requested_boundary']+1)
    if len(events)!=int(not stopped):
        raise ValueError('context future did not execute exactly one opportunity')
    target='stop' if stopped else LAW.action_id(events[0]);support=case['views']['process_record']['support']
    if target not in support or set(oracle)-set(support) or oracle.get(target,0)<=0:
        raise ValueError('context future outside the complete offered support')
    if condition=='global':
        true={'kind':'deadline','value':'tight','section':None,'reliability':.9}
        false={**true,'value':'loose'}
    else:
        true={'kind':'section_checked','value':True,'section':check['section'],'reliability':.9}
        false={**true,'value':False}
    redundant={'kind':'past_mark','value':sorted(case['views']['process_record']['current']['marks'])[0],
               'section':None,'reliability':.9}
    return {'eligibility':check,'condition':condition,'target':target,'oracle':oracle,
            'cues':{'true':true,'false':false,'redundant':redundant},'seed':seed,'executed_events':events,'stopped':stopped,
            'meaning':'global deadline pressure or local check belief; report truth labels and actual future are evaluator-only'}


def prepare(directory,source,role,condition,pilot_offset=0):
    start,cpu=time.monotonic(),time.process_time();register()
    directory,source=inside(directory),inside(source)
    namespace=ROOT/'private'/('cue-case-pilots' if role=='pilot' else 'scientific-cue-cases')
    if (role not in ('pilot','development','discovery') or condition not in ('global','local')
            or not directory.is_relative_to(namespace) or pilot_offset not in (0,1)
            or role!='pilot' and pilot_offset!=0):
        raise ValueError('undeclared context-cue source scope or subset')
    done,source_identity=read(source/'COMPLETE.json'),read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role']!=role
            or done['identity_sha256']!=digest(source_identity)
            or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('ordinary source pool incomplete, changed or failed realization')
    candidates=read(source/'CASES.json');validate_cases(candidates,role)
    if role!='pilot' and (source_identity['per_cohort']!=24 or len(candidates)!=2304):
        raise ValueError('context cue requires its one declared complete 2304-series pool')
    screened,groups=[],{}
    ordered=sorted(candidates,key=lambda c:digest({'context_cue_selection_v1':c['source_worlds'][0]['lid'],'boundary':c['requested_boundary']}))
    for case in ordered:
        check,_,_=eligibility(case)
        group=case['private_factors']['domain'] if role=='pilot' else case['private_factors']['domain']+'|'+case['private_factors']['purpose']
        screened.append({'unit':case['unit'],'group':group,**check});groups.setdefault(group,[])
        if check['eligible']:groups[group].append(case)
    expected_groups,per_group=(2,1) if role=='pilot' else (8,24)
    selected=[case for group in sorted(groups) for case in groups[group][pilot_offset:pilot_offset+per_group]]
    accepted=len(groups)==expected_groups and len(selected)==expected_groups*per_group
    selected=[{**case,'context_cue':counterfactual(case,condition)} for case in selected]
    identity={'cell_identity':cell_identity(),'operation':'context-cue-cases-v1','role':role,
              'scope':'pilot' if role=='pilot' else 'scientific','condition':condition,'source':sources(),
              'source_pool':str(source),'source_complete_sha256':file_hash(source/'COMPLETE.json'),
              'pilot_offset':pilot_offset,'per_group':per_group,'expected_groups':expected_groups,
              'selected_units':[c['unit'] for c in selected],'selection_uses_future':False}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        freeze(directory/'CASES.json',selected);freeze(directory/'ELIGIBILITY.json',screened)
        return finish(directory,identity,start,cpu,['CASES.json','ELIGIBILITY.json'],accepted=accepted,role=role,
                      construction_only=True,selected_series=len(selected),requested_series=expected_groups*per_group,
                      source_candidates=len(candidates),eligible_counts={k:len(v) for k,v in groups.items()},condition=condition,
                      scientific_admission=False,disposition='DESCRIPTIVE' if accepted else 'IMPLEMENTATION INVALID')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('output','source'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--role',choices=('pilot','development','discovery'),required=True)
    p.add_argument('--condition',choices=('global','local'),required=True)
    p.add_argument('--pilot-offset',type=int,default=0)
    a=p.parse_args();prepare(a.output,a.source,a.role,a.condition,a.pilot_offset)
