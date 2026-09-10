"""Exact conditional three-mark histories with partial future-context separation.

DESIGN CHECK: M05/X01/X02/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: unequal artifacts, hidden failure paths, absent histories or no partial future
separation fail construction before sampling any history or outcome. ALTERNATIVE:
all six orders of two writes and one consultation produce the same marks, with one
old predictive class and more than one but fewer than six classes after tool arrival.
The true history is drawn from the actual conditional source likelihood, never
chosen to favor a reader. Numeric source law and oracle history odds stay private.
This is a declared finite offered-history diagnostic, not unrestricted recovery.
"""
import copy
import itertools
import math
import random
import argparse
import time
from pathlib import Path
from .common import digest,distribution
from .construction import Replay,LAW,register
from .artifact_preparation import evidence


def inspect(case):
    original=case['source_worlds'][0]
    world={k:copy.deepcopy(original[k]) for k in ('lid','domain','doc','inventory','state','shape','goal_name')}
    world['trajectory']={'changes':[]}
    world['state']['external_context'],world['state']['belief_state']=LAW.apply_change(
        world['state']['external_context'],world['state']['belief_state'],'library_withdrawn')
    initial=Replay(world);p=initial.probabilities()
    writes=sorted([a for a in initial.pending if a['type']=='write' and p.get(LAW.action_id(a),0)>0],key=LAW.action_id)
    consults=sorted([a for a in initial.pending if a['type']=='consult' and p.get(LAW.action_id(a),0)>0],key=LAW.action_id)
    if (len(writes)<2 or not consults or not initial.c_ext['tools']['source_access']
            or not initial.belief['believed_tools']['source_access']):
        return {'eligible':False,'reason':'missing two writes or objectively and subjectively available consultation'},None
    histories={};artifacts=[]
    actions=sorted([*writes[:2],consults[0]],key=LAW.action_id)
    for index,order in enumerate(itertools.permutations(actions)):
        replay=Replay(world);log_mass=0.
        for action in order:
            probability=replay.probabilities().get(LAW.action_id(action),0.)
            if probability<=0:raise ValueError('offered history has zero constructor probability')
            log_mass+=math.log(probability)
            if replay.apply(action,verify_outcome=False)['outcome']!='done':
                raise ValueError('offered successful history fails actual execution')
        old=replay.probabilities();changed=copy.deepcopy(replay)
        changed.c_ext,changed.belief=LAW.apply_change(changed.c_ext,changed.belief,'library_arrives')
        future=changed.probabilities();visible=evidence(world,replay.steps,'artifact',[])
        artifacts.append(visible)
        histories['h'+str(index)]={'events':replay.steps,'log_mass':log_mass,'old':old,'changed':future,
                                  'old_class':digest(old),'changed_class':digest(future)}
    if len({digest(a) for a in artifacts})!=1:
        raise ValueError('offered histories do not produce identical public artifacts')
    # With both subjective tools correctly available/unavailable, every offered
    # source action succeeds. There are no unobserved failed-action self-loops.
    no_failures=all(a['outcome']=='done' for a in initial.legal_actions()
                    if LAW.action_id(a) in initial.snapshot()['subjective_action_space'])
    old_classes=len({h['old_class'] for h in histories.values()})
    changed_classes=len({h['changed_class'] for h in histories.values()})
    check={'eligible':no_failures and old_classes==1 and 1<changed_classes<6,
           'no_hidden_failure_paths':no_failures,'old_predictive_classes':old_classes,
           'changed_predictive_classes':changed_classes,'completed_histories':len(histories)}
    return check,{'world':world,'histories':histories,'artifact':artifacts[0]}


def _draw(probabilities,seed):
    distribution(probabilities);u=random.Random(seed).random()
    for key,p in sorted(probabilities.items()):
        u-=p
        if u<=0:return key
    return sorted(probabilities)[-1]


def construct(case):
    check,prepared=inspect(case)
    if not check['eligible']:raise ValueError('source cannot realize declared partial history ambiguity')
    histories=prepared['histories'];peak=max(h['log_mass'] for h in histories.values())
    weights={k:math.exp(h['log_mass']-peak) for k,h in histories.items()};total=math.fsum(weights.values())
    posterior=distribution({k:w/total for k,w in weights.items()})
    world=prepared['world']
    history_seed=int(digest({'ambiguity_history_v1':world['lid']})[:16],16)
    selected=_draw(posterior,history_seed)
    future_seed=int(digest({'ambiguity_future_v1':world['lid']})[:16],16)
    outcomes={}
    for condition in ('old','changed'):
        replay=Replay(world,histories[selected]['events'])
        if condition=='changed':
            replay.c_ext,replay.belief=LAW.apply_change(replay.c_ext,replay.belief,'library_arrives')
        oracle=replay.probabilities()
        if oracle!=histories[selected][condition]:raise ValueError('sampled historical state differs from its enumerated future')
        events,stopped=replay.continue_teacher(future_seed,max_events=4)
        if len(events)!=int(not stopped):raise ValueError('ambiguity future is not one actual opportunity')
        target='stop' if stopped else LAW.action_id(events[0])
        if target not in prepared['artifact']['support'] or oracle.get(target,0)<=0:
            raise ValueError('ambiguity target absent from the common offered support')
        outcomes[condition]={'target':target,'event':events[0] if events else None,'stopped':stopped,'oracle_given_history':oracle}
    observed=outcomes['changed']['target']
    updated={h:posterior[h]*histories[h]['changed'].get(observed,0.) for h in histories}
    normalizer=math.fsum(updated.values());assert normalizer>0
    after=distribution({h:p/normalizer for h,p in updated.items()})
    for a,b in itertools.combinations(histories,2):
        if histories[a]['changed_class']==histories[b]['changed_class']:
            if abs(after[a]*posterior[b]-after[b]*posterior[a])>1e-12:
                raise ValueError('future observation spuriously distinguishes equivalent histories')
    offered={h:[{k:e[k] for k in ('i','type','section','slot','outcome')} for e in item['events']]
             for h,item in histories.items()}
    template={k:world[k] for k in ('domain','doc','inventory','state','shape')}
    return {'eligibility':check,'artifact':prepared['artifact'],'offered_histories':offered,
            'true_history':selected,'history_posterior_oracle':posterior,'history_posterior_after_oracle':after,
            'outcomes':outcomes,'history_future_oracles':{h:{c:row[c] for c in ('old','changed')} for h,row in histories.items()},
            'history_classes':{h:{c:row[c+'_class'] for c in ('old','changed')} for h,row in histories.items()},
            'history_seed':history_seed,'future_seed':future_seed,'content_sha256':digest(template),
            'scope':'three-successful-mark conditional source; complete six-history support offered, numeric law and selected history private'}


def prepare(directory,source,role,pilot_offset=0):
    """One fixed source pool, with no selection on sampled history or future."""
    from .common import REPO,ROOT,Units,read,freeze,closure,file_hash
    from .queue import inside,writer
    from .revision_predictions import sources,reentry,finish
    from .artifact_comparisons import validate_cases
    from .training_jobs import cell_identity
    started,cpu=time.monotonic(),time.process_time();register()
    directory,source=inside(directory),inside(source)
    namespace=ROOT/'private'/('ambiguity-case-pilots' if role=='pilot' else 'scientific-ambiguity-cases')
    if (role not in ('pilot','development','discovery') or not directory.is_relative_to(namespace)
            or pilot_offset not in (0,1) or role!='pilot' and pilot_offset):
        raise ValueError('undeclared ambiguity source scope or subset')
    done,parent=read(source/'COMPLETE.json'),read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role']!=role
            or done['identity_sha256']!=digest(parent)
            or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('ordinary ambiguity source pool is incomplete or changed')
    candidates=read(source/'CASES.json');validate_cases(candidates,role)
    if role!='pilot' and (parent['per_cohort']!=24 or len(candidates)!=2304):
        raise ValueError('ambiguity requires its complete fixed 2304-series source pool')
    ordered=sorted(candidates,key=lambda c:digest({'ambiguity_selection_v1':c['source_worlds'][0]['lid']}))
    screened,groups,seen=[],{},set()
    for case in ordered:
        check,prepared=inspect(case)
        group=case['private_factors']['domain']
        if role!='pilot':group+='|'+case['private_factors']['purpose']
        groups.setdefault(group,[])
        content=None
        if check['eligible']:
            content=digest({k:prepared['world'][k] for k in ('domain','doc','inventory','state','shape')})
            if content not in seen:groups[group].append(case)
        screened.append({'unit':case['unit'],'group':group,**check,'content_sha256':content,
                         'duplicate_template':content is not None and content in seen})
        if content is not None:seen.add(content)
    expected,per_group=(2,1) if role=='pilot' else (8,24)
    selected=[c for group in sorted(groups) for c in groups[group][pilot_offset:pilot_offset+per_group]]
    accepted=len(groups)==expected and len(selected)==expected*per_group
    selected=[{**c,'ambiguity':construct(c)} for c in selected]
    identity={'cell_identity':cell_identity(),'operation':'ambiguity-cases-v1','role':role,
        'scope':'pilot' if role=='pilot' else 'scientific','source':sources(),'source_pool':str(source),
        'source_complete_sha256':file_hash(source/'COMPLETE.json'),'pilot_offset':pilot_offset,
        'per_group':per_group,'expected_groups':expected,'selected_units':[c['unit'] for c in selected],
        'selection_uses_future':False,'duplicate_policy':'first eligible distinct initial template in fixed hash order'}
    with writer(directory):
        Units(directory,identity);prior=reentry(directory,identity)
        if prior is not None:return prior
        freeze(directory/'CASES.json',selected);freeze(directory/'ELIGIBILITY.json',screened)
        return finish(directory,identity,started,cpu,['CASES.json','ELIGIBILITY.json'],accepted=accepted,role=role,
            construction_only=True,selected_series=len(selected),requested_series=expected*per_group,
            source_candidates=len(candidates),eligible_counts={k:len(v) for k,v in groups.items()},
            scientific_admission=False,disposition='DESCRIPTIVE' if accepted else 'IMPLEMENTATION INVALID')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('output','source'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--role',choices=('pilot','development','discovery'),required=True)
    p.add_argument('--pilot-offset',type=int,default=0)
    a=p.parse_args();prepare(a.output,a.source,a.role,a.pilot_offset)
