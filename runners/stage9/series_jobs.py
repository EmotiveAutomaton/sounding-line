"""Resumable, explicitly sized maker-series preparation, without reader scoring.

DESIGN CHECK: M01/M04/X01/X12; LESSONS 3--5. NULL: absent targets, duplicate
whole sources, changed sources or incomplete cohorts cannot become accepted cases.
ALTERNATIVE: complete selected cohorts retain every attempt, complete support and
fixed whole-series identity under restart. Bands: complete with >=.75 realization
in each domain/purpose cell, otherwise IMPLEMENTATION INVALID; no predictive verdict.
Reserve preparation requires the later frozen confirmation handler, not this CLI.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path
import time

from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read, write
from .queue import inside, verify_sources, writer
from .series_cases import COHORTS, construct_attempt


def prepare(directory, *, role, key, per_cohort=2, dose=7, attempts_per_cohort=20, allocation=None):
    cell=os.environ.get('S9_CELL_IDENTITY')
    if role!='pilot' and (not cell or len(cell)!=64 or any(c not in '0123456789abcdef' for c in cell)):
        raise ValueError('scientific series preparation requires the source-checked queue cell identity')
    directory = inside(directory)
    if role not in ('pilot','training','development','discovery') or not isinstance(key,str) or not key:
        raise ValueError('explicit nonreserve source role and seed namespace required')
    if type(per_cohort) is not int or per_cohort < 1 or type(attempts_per_cohort) is not int or attempts_per_cohort < per_cohort:
        raise ValueError('invalid fixed cohort/sample budget')
    if type(dose) is not int or not 0 <= dose <= 7:
        raise ValueError('invalid earlier-work dose')
    quotas=[per_cohort]*len(COHORTS)
    if allocation is not None:
        from .development_allocation import load
        allocation=inside(allocation)
        quotas=load(allocation,role,per_cohort)
        if max(quotas)>attempts_per_cohort:raise ValueError('attempt budget cannot fill declared development allocation')
    sources = closure([REPO/'runners/stage9', REPO/'runners/stage7', REPO/'runners/stage8', REPO/'soundingline',
                       REPO/'runners/__init__.py', REPO/'runners/readout_repair.py'])
    identity = {'operation':'series-preparation-v1','cell_identity':cell,'role':role,'key':key,'cohorts':[list(c) for c in COHORTS],
        'per_cohort':per_cohort,'dose':dose,'attempts_per_cohort':attempts_per_cohort,
        'source':sources,'selection':'first realized within each fixed cohort; independent preconstruction geometric cut',
        'realization_gate':{'grouping':['domain','purpose'],'minimum':.75}}
    if allocation is not None:
        identity['allocation']={'path':allocation.relative_to(REPO).as_posix(),'sha256':file_hash(allocation),
            'cohort_counts':quotas,'scope':'development finite-support repair; unavailable joint cohorts explicitly retained'}
    with writer(directory):
        units = Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            complete = read(directory/'COMPLETE.json')
            if complete['identity_sha256'] != digest(identity):
                raise ValueError('completed series identity mismatch')
            if closure([REPO/p for p in complete['outputs']['files']]) != complete['outputs']:
                raise ValueError('completed series outputs changed')
            return complete
        started, cpu = time.monotonic(), time.process_time()
        selected, attempts, source_set = [], [], set()
        try:
            for cohort,quota in zip(COHORTS,quotas):
                if quota==0:continue
                accepted = 0
                for attempt in range(attempts_per_cohort):
                    unit_key = {'cohort':list(cohort),'attempt':attempt}
                    row = units.get(unit_key)
                    if row is None:
                        case = construct_attempt(key=digest({'namespace':key,**unit_key}),cohort=cohort,role=role,dose=dose)
                        row = {'cohort':list(cohort),'attempt':attempt,'case':case}
                        units.put(unit_key,row)
                    case = row['case']
                    attempts.append({'cohort':list(cohort),'attempt':attempt,'realized':case['realized'],
                                     'reason':case.get('reason'),'parameter_draws':case.get('parameter_draws',0)})
                    if case['realized']:
                        if any(sha in source_set for sha in case['sources']):
                            raise ValueError('whole world content repeated across independent series')
                        source_set.update(case['sources'])
                        selected.append(case)
                        accepted += 1
                    if accepted == quota:
                        break
            requested = sum(quotas)
            groups = {}
            for row in attempts:
                domain,law,residue,purpose = row['cohort']
                group = groups.setdefault(domain+'|'+purpose,{'attempted':0,'realized':0})
                group['attempted'] += 1
                group['realized'] += row['realized']
            for group in groups.values():
                group['yield'] = group['realized']/group['attempted']
            complete_grid = len(selected) == requested
            qualified = complete_grid and all(g['yield']>=.75 for g in groups.values())
            write(directory/'CASES.json',selected)
            write(directory/'ATTEMPTS.json',attempts)
            verify_sources(sources)
            complete = {'at':datetime.now(timezone.utc).isoformat(),'identity_sha256':digest(identity),'cell_identity':cell,
                'role':role,'source':sources,'accepted':qualified,'construction_only':True,
                'disposition':'DESCRIPTIVE' if qualified else 'IMPLEMENTATION INVALID',
                'requested_series':requested,'selected_series':len(selected),'attempted_series':len(attempts),
                'complete_cohorts':complete_grid,'groups':groups,
                'exclusions':dict(Counter(r['reason'] for r in attempts if not r['realized'])),
                'selected_target_counts':dict(Counter(c['target'].split(':')[0] for c in selected)),
                'independent_source_worlds':len(source_set),
                'maximum_support':max((len(c['views']['artifact']['support']) for c in selected),default=0),
                'maximum_earlier_marks':max((len(w['marks']) for c in selected for w in c['views']['artifact']['earlier']),default=0),
                'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu,'gpu_seconds':0,
                'cost_scope':'this invocation; earlier interrupted attempts retain their own RUN receipts',
                'heldout_predictions_scored':False,'launch_accepted':False,
                'outputs':closure([directory/'CASES.json',directory/'ATTEMPTS.json',directory/'units'])}
            if allocation is not None:
                if file_hash(allocation)!=identity['allocation']['sha256']:raise ValueError('development allocation changed during preparation')
                complete['allocation']=identity['allocation']
                complete['unavailable_cohorts']=[list(c) for c,n in zip(COHORTS,quotas) if n==0]
            write(directory/'COMPLETE.json',complete)
            return complete
        finally:
            # Each invocation gets its own immutable receipt, including interrupted exceptions.
            runs = directory/'runs'
            runs.mkdir(exist_ok=True)
            stamp = time.time_ns()
            freeze(runs/(str(stamp)+'.json'),{'identity_sha256':digest(identity),
                'at':datetime.now(timezone.utc).isoformat(),'wall_seconds':time.monotonic()-started,
                'cpu_seconds':time.process_time()-cpu,'gpu_seconds':0,
                'completion_present':(directory/'COMPLETE.json').exists()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--role',required=True,choices=('pilot','training','development','discovery'))
    parser.add_argument('--key',required=True)
    parser.add_argument('--per-cohort',type=int,default=2)
    parser.add_argument('--dose',type=int,default=7)
    parser.add_argument('--attempts-per-cohort',type=int,default=20)
    parser.add_argument('--cohort-allocation',type=Path)
    args = parser.parse_args()
    result = prepare(Path(args.root),role=args.role,key=args.key,per_cohort=args.per_cohort,
                     dose=args.dose,attempts_per_cohort=args.attempts_per_cohort,allocation=args.cohort_allocation)
    print('Series preparation complete; construction accepted='+str(result['accepted'])+
          '; no held-out prediction evaluated.',flush=True)


if __name__ == '__main__':
    main()
