"""Native exact-capacity and fixed-cohort audit fixture; no probabilities fit."""
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from . import week5_at_history_support as card
from .timing_census import read
from .timing_p6 import write_equal


def bank():
    records=[];rows=defaultdict(list);roster={'writers':{}}
    for writer in ['a','b','c','d','e','f']:
        # a's own history precedes every other writer; no other-writer history
        # can support its first target. Later writers have real earlier donors.
        offset=0 if writer=='a' else 100
        for i in range(4):
            sid=writer+str(i)
            records.append(dict(session=sid,writer=writer,prompt='p'+str(i),genre='argument',timestamp=offset+i*10,end_at=offset+i*10+1,training_sequences=[['x']*10]))
        rows[writer]=[dict(session=writer+'3')];roster['writers'][writer]=dict(supported_sessions=dict(calibration=[writer+'2']))
    by=defaultdict(list)
    for record in records:by[record['writer']].append(record)
    return SimpleNamespace(records={r['session']:r for r in records},rows=rows,roster=roster,by_writer=by,writers=sorted(rows))


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed-only metadata fixture')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);source=root/'CONSTRUCTED.json';write_equal(source,dict(fixture_only=True))
    old=card.original.load;card.original.load=lambda *_:bank()
    try:(card.verify if verifying else card.execute)(root/'audit',dict(fixture=str(source)),{})
    finally:card.original.load=old
    result=read(root/'audit/SUMMARY.json')
    if result['writers_with_impossible_union']!=1 or result['necessary_capacity_writers_by_k']['1']!=5 or result['necessary_capacity_writers_by_k']['20']!=0:
        raise ValueError('Known chronological capacity answer differs')
    receipt=dict(fixture_only=True,complete_actual_metadata_handler=True,early_recipient_impossible=True,
                 later_single_donor_feasible=True,k_larger_than_pool_refused=True,no_scientific_fit=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Support fixture differs')
    else:write_equal(root/'FIXTURE.json',receipt)
    return dict(verified=True) if verifying else dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
