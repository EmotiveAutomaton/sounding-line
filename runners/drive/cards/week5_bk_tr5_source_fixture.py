"""Native TR5 history/matching replay with R1 semantic and physical cases."""
import copy
from pathlib import Path
from . import week5_bk_tr5_source as card
from . import week3_trust_inputs as old
from . import week4_shared_spans_h1 as r1
from .week3_insertion_provenance_h1 import fixture as insertion
from runners.stage9.coauthor import replay
from .timing_census import read
from .timing_p6 import write_equal,gzread
from tests.test_week3_trust_inputs import fixture,session


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed-only TR5 source fixture')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);rows=fixture()+[session('later','later',later_delete=True)]
    single=session('single','single')
    for event in single['canonical']['events']:event['options']=event['options'][:1]
    rows.append(single);source=root/'CONSTRUCTED.json';write_equal(source,rows)
    cfg=dict(card='TR5-inputs',mode='constructed',max_wall_seconds=1200)
    (card.verify if verifying else card.execute)(root/'source',dict(fixture=str(source)),cfg)
    data=gzread(root/'source/EVENTS.json.gz')
    for n in range(5):
        expected=old.prepare_session(**rows[n]);actual=data['sessions'][n]
        # Additional R1 audit/provenance fields cannot change old matched clocks.
        if any(actual[k]!=expected[k] for k in ('menu','clocks','requests','failures','legacy_failure_candidates')):raise ValueError('Original TR5 windows/anchors changed')
        for before,after in zip(expected['spans'],actual['spans']):
            if any(before[k]!=after[k] for k in before):raise ValueError('Original anchor-time retention changed')
    first=data['sessions'][4]['spans'][0];failed=next(s for s in data['sessions'][4]['spans'] if s['failure_removed']==8)
    if not old.kept(first,failed['failure_ordinal']) or old.kept(first,len(rows[4]['events'])-1):raise ValueError('Future deletion contaminated old run')
    if not data['sessions'][5]['failures']:raise ValueError('Single-option failure history disappeared')
    cases=[]
    for kind in ('plain','newline','rewrite','repeated','unmatched','edited','deleted'):
        events,timeline=insertion(kind);canonical=replay(events);proof=r1.spans(events,timeline,canonical)
        value=card.history(events,timeline,canonical,proof)
        if len(value)!=len(proof) or len({row['physical_origin'] for row in value.values()})!=len(proof):raise ValueError('Physical insertion collision')
        if kind=='repeated' and (len(value)!=2 or any(row['canonical'] for row in value.values())):raise ValueError('Repeated menu received invented canonical identity')
        cases.append(dict(case=kind,physical_insertions=len(value)))
    receipt=dict(fixture_only=True,actual_tr5_source_handler=True,original_window_match_and_history_equivalence=True,
                 future_deletion_does_not_change_run=True,single_option_history_kept=True,physical_cases=cases)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('TR5 source fixture differs')
    else:write_equal(root/'FIXTURE.json',receipt)
    return dict(verified=True,complete_tr5_source_replay=True) if verifying else dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
