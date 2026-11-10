"""Input-only AT1 donor-history capacity audit; no fits or replacement cohort.

DESIGN CHECK: LESSONS 2--5, 2026-11-07. Earlier, prompt-excluded histories,
genre pools and exact session/token budgets are the frozen primary rules.
Impossible union capacity proves lack of support even before random donor
draws. Passing necessary bounds does not prove support or nonconstant calibrated
surprise. No writer, target, failed draw or calendar rule is removed.
"""
from collections import Counter
from pathlib import Path
import time

from runners.stage9.common import digest
from . import week5_at_history as original
from .timing_d33_match import earlier,token_count
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress


def capacity(pool,own):
    count=len(own);budget=sum(map(token_count,own));sizes=sorted(map(token_count,pool),reverse=True)
    maximum=sum(sizes[:count])
    return dict(required_sessions=count,required_tokens=budget,available_sessions=len(pool),
                maximum_tokens_at_exact_session_count=maximum,
                supported=bool(count and budget and len(pool)>=count and maximum>=budget))


def inspect_writer(bank,writer):
    calibration=bank.roster['writers'][writer]['supported_sessions']['calibration']
    evaluation=sorted({row['session'] for row in bank.rows[writer]})
    targets=list(dict.fromkeys(calibration+evaluation));rows=[]
    for sid in targets:
        target=bank.records[sid];genre=target['genre'];own=earlier(bank.by_writer[writer],target,True)
        pool={w:[s for s in earlier(records,target,True) if s['genre']==genre]
              for w,records in sorted(bank.by_writer.items()) if w!=writer and any(s['genre']==genre for s in records)}
        all_sessions=[s for sessions in pool.values() for s in sessions]
        bound=capacity(all_sessions,own);individual={w:capacity(sessions,own) for w,sessions in pool.items()}
        variants={}
        for k in (1,3,5,20):
            # Summing each donor's largest n sessions is an upper bound: it
            # may count more than n sessions overall, so only failure proves
            # impossibility. Union top-n adds the common exact-count bound.
            donor_max=sorted((r['maximum_tokens_at_exact_session_count'] for r in individual.values()),reverse=True)
            sessions_max=sorted((r['available_sessions'] for r in individual.values()),reverse=True)
            upper=min(bound['maximum_tokens_at_exact_session_count'],sum(donor_max[:k]))
            possible=bool(len(pool)>=k and bound['supported'] and upper>=bound['required_tokens'] and sum(sessions_max[:k])>=bound['required_sessions'])
            variants[str(k)]=dict(necessary_capacity_pass=possible,donor_pool_writers=len(pool),token_upper_bound=upper)
        rows.append(dict(session=sid,role='calibration' if sid in calibration else 'evaluation',genre=genre,
                         union=bound,per_donor=individual,variants=variants))
    same_donor_by_genre={}
    for genre in sorted({row['genre'] for row in rows}):
        groups=[{w for w,value in row['per_donor'].items() if value['supported']} for row in rows if row['genre']==genre]
        same_donor_by_genre[genre]=sorted(set.intersection(*groups)) if groups else []
    possible={str(k):all(row['variants'][str(k)]['necessary_capacity_pass'] for row in rows) for k in (1,3,5,20)}
    # k=1 additionally has an exact same-donor condition across a genre's targets.
    possible['1']=possible['1'] and all(same_donor_by_genre.values())
    return dict(writer=writer,targets=rows,own_history_absent=sum(not row['union']['required_tokens'] for row in rows),
                impossible_even_with_all_donors=sum(not row['union']['supported'] for row in rows),
                necessary_capacity_by_k=possible,k1_exact_metadata_donors=same_donor_by_genre,
                caveat='No calibrated probabilities fitted; passing capacity does not prove nonconstant donor surprise or stochastic bank support')


def run(output,inputs,config,verifying=False):
    if config!={}:raise ValueError('Frozen primary metadata audit only')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    paused=lambda:(root/'YIELD_REQUEST.json').exists() or (root.parent/'STOP').exists() or time.monotonic()-start>=1200
    if paused():return dict(status='yielded',operation='AT1-support-audit',scientific_admission=False)
    bank=original.load(inputs,{})
    binding=dict(inputs={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v) for k,v in inputs.items()},revision='AT1-input-support-v1')
    if verifying:
        if read(root/'BINDING.json')!=binding:raise ValueError('Support source changed')
    else:write_equal(root/'BINDING.json',binding)
    records=[]
    for n,writer in enumerate(bank.writers):
        path=root/f'writer-{n:04d}.json';seal=root/f'writer-{n:04d}.seal.json'
        unit=dict(binding=digest(binding),writer=writer)
        if seal.exists():
            stamp=read(seal)
            if stamp.get('unit')!=unit or stamp.get('sha256')!=filehash(path):raise ValueError('Audit checkpoint changed')
            saved=read(path)
        else:saved=None
        if verifying or saved is None:
            value=inspect_writer(bank,writer)
            if verifying:
                if value!=saved:raise ValueError('Complete input-support audit replay differs')
            else:write_equal(path,value);write_equal(seal,dict(unit=unit,sha256=filehash(path)))
        else:value=saved
        records.append(value);progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'metadata',writers=n+1,total=len(bank.writers)))
        if paused():return dict(status='yielded',operation='AT1-support-audit',writers=n+1,scientific_admission=False)
    summary=dict(card='AT1-support-audit',writers=len(records),writers_with_impossible_union=sum(bool(r['impossible_even_with_all_donors']) for r in records),
                 necessary_capacity_writers_by_k={str(k):sum(r['necessary_capacity_by_k'][str(k)] for r in records) for k in (1,3,5,20)},
                 outcomes_or_calibrated_scores_used=False,scientific_admission=False,
                 disposition='Input-only audit; preserve original undefined point. No donor replacement, unsupported-writer deletion or automatic descendant admission.')
    if verifying:
        if read(root/'SUMMARY.json')!=summary:raise ValueError('Support audit reduction differs')
    else:write_equal(root/'SUMMARY.json',summary)
    return dict(verified=True,complete_metadata_replay=True) if verifying else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
