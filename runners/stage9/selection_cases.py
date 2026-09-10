"""Private two-step observation offers with no hidden outcome in the public pool.

DESIGN CHECK: S02/S03/S04/X01/X02/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: old unseen trajectories cannot select a new preview, offered purchase or
target. ALTERNATIVE: existing constructor decisions provide prospective information.
Seven same-maker earlier works supply one observed-action preview and one privately
drawn next decision each. The current work has a separate actual future. Failed
actions and stopped continuations are retained; no source is selected on a future.
This module is evaluator-owned and never enters a reader capsule. The source owner
must deliver a purchase only after the reader has selected its canonical preview.
"""
import argparse
import time
from pathlib import Path
from .artifact_preparation import work
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .constraint_cases import initial_world
from .construction import LAW,Replay,register
from .selection_reader import purchased_symbol
from .artifact_comparisons import validate_cases
from .queue import inside,writer
from .revision_predictions import sources,reentry,finish
from .training_jobs import cell_identity


def construct(case):
    register()
    if len(case['source_worlds'])!=8:raise ValueError('selection requires one target and seven earlier works')
    worlds=[initial_world(w) for w in case['source_worlds']]
    templates=[digest({k:w[k] for k in ('domain','doc','inventory','state','shape')}) for w in worlds]
    if len(set(templates))!=8:raise ValueError('selection source repeats an initial work')
    prefixes=[]
    for world in worlds:
        seed=int(digest({'selection_preview_v1':world['lid']})[:16],16)
        events,stopped=Replay(world).continue_teacher(seed,max_events=1)
        if stopped or len(events)!=1:raise ValueError('source cannot provide its first executed-action preview')
        prefixes.append({'events':events,'seed':seed})
    offers=[]
    for world,prefix in zip(worlds[1:],prefixes[1:]):
        seed=int(digest({'selection_purchase_v1':world['lid']})[:16],16)
        events,stopped=Replay(world,prefix['events']).continue_teacher(seed,max_events=2)
        if (stopped and events) or (not stopped and len(events)!=1):raise ValueError('source purchase does not reveal exactly one decision')
        offers.append({'events':prefix['events']+events,'observed_stop':True if stopped else None,'seed':seed})
    public={};private_purchases={};symbols={}
    for view in ('artifact','process_record'):
        pool={'o'+str(i):work(w,p['events'],view) for i,(w,p) in enumerate(zip(worlds[1:],prefixes[1:]))}
        public[view]={'view':view,'current':work(worlds[0],prefixes[0]['events'],view),'pool':pool}
        private_purchases[view]={'o'+str(i):work(w,p['events'],view,p['observed_stop'])
                                for i,(w,p) in enumerate(zip(worlds[1:],offers))}
        symbols[view]={name:purchased_symbol(pool[name],value,view) for name,value in private_purchases[view].items()}
    # Source construction and all observation opportunities are fixed first.
    replay=Replay(worlds[0],prefixes[0]['events']);oracle=replay.probabilities()
    seed=int(digest({'selection_target_v1':worlds[0]['lid']})[:16],16)
    events,stopped=replay.continue_teacher(seed,max_events=2)
    target='stop' if stopped else LAW.action_id(events[0])
    return {'public':public,'purchases':private_purchases,'symbols':symbols,'preview_draws':prefixes,
        'purchase_draws':offers,'target':target,'oracle':oracle,'future_seed':seed,'future_events':events,
        'future_stopped':stopped,'source_template_sha256':digest(templates),
        'scope':'all seven first-action previews have a common cost; next decision is private until purchased'}


def prepare(directory,source,role,pilot_offset=0):
    start,cpu=time.monotonic(),time.process_time();register()
    directory,source=inside(directory),inside(source)
    namespace=ROOT/'private'/('selection-case-pilots' if role=='pilot' else 'scientific-selection-cases')
    if (role not in ('pilot','development','discovery') or not directory.is_relative_to(namespace)
            or pilot_offset not in (0,1) or role!='pilot' and pilot_offset):
        raise ValueError('undeclared selection source scope')
    done,own=read(source/'COMPLETE.json'),read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role']!=role
            or done['identity_sha256']!=digest(own)
            or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('ordinary source pool incomplete, changed or failed realization')
    cases=read(source/'CASES.json');validate_cases(cases,role)
    if role!='pilot' and (own['per_cohort']!=2 or len(cases)!=192):
        raise ValueError('selection needs its full fixed 192-series scientific pool')
    groups={}
    for case in sorted(cases,key=lambda c:digest({'selection_assignment_v1':c['source_worlds'][0]['lid']})):
        group=case['private_factors']['domain'] if role=='pilot' else case['private_factors']['domain']+'|'+case['private_factors']['purpose']
        groups.setdefault(group,[]).append(case)
    expected_groups,per_group=(2,1) if role=='pilot' else (8,24)
    assigned=[c for group in sorted(groups) for c in groups[group][pilot_offset:pilot_offset+per_group]]
    selected,realization=[],[]
    for case in assigned:
        try:cf=construct(case)
        except ValueError as exc:realization.append({'unit':case['unit'],'realized':False,'reason':str(exc)})
        else:
            selected.append({**case,'selection':cf});realization.append({'unit':case['unit'],'realized':True})
    templates=[c['selection']['source_template_sha256'] for c in selected]
    accepted=(len(groups)==expected_groups and len(assigned)==expected_groups*per_group
              and len(selected)==len(assigned) and len(set(templates))==len(templates))
    identity={'cell_identity':cell_identity(),'operation':'selection-cases-v1','role':role,
        'scope':'pilot' if role=='pilot' else 'scientific','source':sources(),'source_pool':str(source),
        'source_complete_sha256':file_hash(source/'COMPLETE.json'),'pilot_offset':pilot_offset,
        'per_group':per_group,'expected_groups':expected_groups,'assigned_units':[c['unit'] for c in assigned],
        'selected_units':[c['unit'] for c in selected],'preview_actions':1,'purchase_decisions':1,
        'archive_work_count':7,'selection_uses_future':False,'selection_uses_realized_length':False}
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
