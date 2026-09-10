"""Matched familiarity and expectedness with private entry-point purchases.

DESIGN CHECK: T02/S02/X01/X02/X05/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: changing old unseen outcomes cannot change an offer or target; familiarity
labels alone never enter the public reader input. ALTERNATIVE: actual different
makers can leave different first-action previews under the same public conditions.
The current prefix and subsequent target reproduce the existing familiarity cross.
Three earlier works each supply one executed-action preview and one private next
decision. Every condition pays for all previews; stop and failure outcomes remain.
Expectedness is a balanced conditional first-choice stress, not natural-frequency
calibration. This evaluator-only construction does not presume that a reader knows
whether the current maker and archive maker coincide. Source realization is not
reader competence, and the complete acquisition consumer remains a separate gate.
"""
import math
import argparse
import time
from pathlib import Path

from .artifact_preparation import work
from .artifact_view import support
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .constraint_cases import initial_world
from .construction import LAW,Replay,register
from .familiarity_cases import ARCHIVE_WORKS,CONDITIONS,choice_strata,draw
from .matched_controls import construct as other_maker
from .selection_reader import purchased_symbol
from .artifact_comparisons import validate_cases
from .queue import inside,writer
from .revision_predictions import sources,reentry,finish
from .training_jobs import cell_identity


def construct(case,role='pilot'):
    register()
    if len(case['source_worlds'])<ARCHIVE_WORKS+1:
        raise ValueError('entry selection needs a current and three earlier works')
    current=initial_world(case['source_worlds'][0])
    old=case['source_worlds'][1:ARCHIVE_WORKS+1]
    key=digest({'familiarity_other_maker_v1':[w['lid'] for w in old]})
    alternative=other_maker(old,role,key)
    archives={f:[initial_world(w) for w in worlds] for f,worlds in
              (('familiar',old),('unfamiliar',alternative['worlds']))}
    def template(w):return digest({k:w[k] for k in ('domain','doc','inventory','state','shape')})
    templates={f:[template(w) for w in worlds] for f,worlds in archives.items()}
    if any(len(set(ids))!=ARCHIVE_WORKS or template(current) in ids for ids in templates.values()):
        raise ValueError('entry archive repeats a source or the current work')
    for a,b in zip(archives['familiar'],archives['unfamiliar']):
        if (work(a,[],'artifact')!=work(b,[],'artifact') or a['inventory']!=b['inventory']
                or a['goal_name']!=b['goal_name']):
            raise ValueError('entry familiarity changes matched conditions or purpose')
    previews,purchases={},{}
    for familiarity,worlds in archives.items():
        previews[familiarity],purchases[familiarity]=[],[]
        for w in worlds:
            seed=int(digest({'familiarity_entry_preview_v1':w['lid']})[:16],16)
            events,stopped=Replay(w).continue_teacher(seed,max_events=1)
            if stopped or len(events)!=1:raise ValueError('missing executed-action preview')
            previews[familiarity].append({'events':events,'seed':seed})
            seed=int(digest({'familiarity_entry_purchase_v1':w['lid']})[:16],16)
            future,stopped=Replay(w,events).continue_teacher(seed,max_events=2)
            if (stopped and future) or (not stopped and len(future)!=1):
                raise ValueError('purchase is not exactly one next decision')
            purchases[familiarity].append({'events':events+future,'observed_stop':True if stopped else None,'seed':seed})
    initial=Replay(current).probabilities();strata,threshold=choice_strata(initial)
    prefixes={}
    for stratum,choices in strata.items():
        seed=int(digest({'familiarity_choice_v1':current['lid'],'stratum':stratum})[:16],16)
        chosen=draw(choices,seed);replay=Replay(current)
        action=next(a for a in replay.legal_actions() if LAW.action_id(a)==chosen)
        prefixes[stratum]={'events':[replay.apply(action)],'seed':seed,'action':chosen,
            'source_action_probability_given_execution':initial[chosen]/(1-initial['stop']),
            'stratum_mass_given_execution':math.fsum(choices.values())/(1-initial['stop'])}
    # All permitted offers and both current prefixes are fixed before future draw.
    outcomes={}
    for stratum,prefix in prefixes.items():
        replay=Replay(current,prefix['events']);oracle=replay.probabilities()
        seed=int(digest({'familiarity_future_v1':current['lid'],'stratum':stratum})[:16],16)
        events,stopped=replay.continue_teacher(seed,max_events=2)
        outcomes[stratum]={'target':'stop' if stopped else LAW.action_id(events[0]),
            'future_event':events,'future_stopped':stopped,'oracle':oracle,'seed':seed}
    conditions={}
    for condition in CONDITIONS:
        familiarity,stratum=condition.split('|');public={};private={};symbols={}
        for view in ('artifact','process_record'):
            pool={'o'+str(i):work(w,p['events'],view) for i,(w,p) in
                  enumerate(zip(archives[familiarity],previews[familiarity]))}
            public[view]={'view':view,'current':work(current,prefixes[stratum]['events'],view),'pool':pool}
            private[view]={'o'+str(i):work(w,p['events'],view,p['observed_stop']) for i,(w,p) in
                           enumerate(zip(archives[familiarity],purchases[familiarity]))}
            symbols[view]={n:purchased_symbol(pool[n],p,view) for n,p in private[view].items()}
            if outcomes[stratum]['target'] not in support(public[view]['current'],view):
                raise ValueError('entry target outside public support')
        conditions[condition]={'public':public,'purchases':private,'symbols':symbols,
            'target':outcomes[stratum]['target'],'recognition_target':'same' if familiarity=='familiar' else 'different'}
    return {'conditions':conditions,'prefixes':prefixes,'outcomes':outcomes,
        'preview_draws':previews,'purchase_draws':purchases,'choice_strata':strata,'choice_threshold':threshold,
        'other_maker_plan':alternative['plan'],'source_templates':{'current':template(current),**templates},
        'archive_work_count':ARCHIVE_WORKS,'preview_actions':1,'purchase_decisions':1,
        'scope':'matched familiar/unfamiliar entry; common preview cost; expectedness conditional before own future'}


def prepare(directory,source,role,pilot_offset=0):
    start,cpu=time.monotonic(),time.process_time();register()
    directory,source=inside(directory),inside(source)
    namespace=ROOT/'private'/('familiarity-entry-case-pilots' if role=='pilot' else 'scientific-familiarity-entry-cases')
    if (role not in ('pilot','development','discovery') or not directory.is_relative_to(namespace)
            or pilot_offset not in (0,1) or role!='pilot' and pilot_offset):
        raise ValueError('undeclared familiarity entry source scope')
    done,own=read(source/'COMPLETE.json'),read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role']!=role
            or done['identity_sha256']!=digest(own)
            or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('ordinary source pool incomplete, changed or failed realization')
    cases=read(source/'CASES.json');validate_cases(cases,role)
    if role!='pilot' and (own['per_cohort']!=2 or len(cases)!=192):
        raise ValueError('familiarity entry needs its fixed 192-series scientific pool')
    groups={}
    for case in sorted(cases,key=lambda c:digest({'familiarity_selection_v1':c['source_worlds'][0]['lid']})):
        group=case['private_factors']['domain'] if role=='pilot' else case['private_factors']['domain']+'|'+case['private_factors']['purpose']
        groups.setdefault(group,[]).append(case)
    expected_groups,per_group=(2,1) if role=='pilot' else (8,24)
    assigned=[c for group in sorted(groups) for c in groups[group][pilot_offset:pilot_offset+per_group]]
    selected,realization=[],[]
    for case in assigned:
        try:cf=construct(case,role)
        except ValueError as exc:realization.append({'unit':case['unit'],'realized':False,'reason':str(exc)})
        else:
            selected.append({**case,'familiarity_entry':cf});realization.append({'unit':case['unit'],'realized':True})
    templates=[digest(c['familiarity_entry']['source_templates']) for c in selected]
    accepted=(len(groups)==expected_groups and len(assigned)==expected_groups*per_group
              and len(selected)==len(assigned) and len(set(templates))==len(templates))
    identity={'cell_identity':cell_identity(),'operation':'familiarity-entry-cases-v1','role':role,
        'scope':'pilot' if role=='pilot' else 'scientific','source':sources(),'source_pool':str(source),
        'source_complete_sha256':file_hash(source/'COMPLETE.json'),'pilot_offset':pilot_offset,
        'per_group':per_group,'expected_groups':expected_groups,'assigned_units':[c['unit'] for c in assigned],
        'selected_units':[c['unit'] for c in selected],'preview_actions':1,'purchase_decisions':1,
        'archive_work_count':ARCHIVE_WORKS,'selection_uses_future':False,'selection_uses_realized_length':False}
    with writer(directory):
        Units(directory,identity);previous=reentry(directory,identity)
        if previous is not None:return previous
        freeze(directory/'CASES.json',selected);freeze(directory/'REALIZATION.json',realization)
        return finish(directory,identity,start,cpu,['CASES.json','REALIZATION.json'],accepted=accepted,
            role=role,construction_only=True,selected_series=len(selected),assigned_series=len(assigned),
            requested_series=expected_groups*per_group,scientific_admission=False,
            disposition='DESCRIPTIVE' if accepted else 'IMPLEMENTATION INVALID')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('output','source'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--role',choices=('pilot','development','discovery'),required=True)
    p.add_argument('--pilot-offset',type=int,default=0)
    a=p.parse_args();prepare(a.output,a.source,a.role,a.pilot_offset)
