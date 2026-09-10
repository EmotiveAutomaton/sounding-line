"""Timing-only two-continuation packing of the same completed learner-state pilot.

DESIGN CHECK: C05/X12. Four correct continuations per state created costly repeated
contexts. Prespecify the first two, keeping source assignment and state unchanged;
rematch exactly the same target budget. All four original targets remain preserved.
NULL: insufficient capacity refuses the variant; no extra source or model label.
ALTERNATIVE: unchanged expert rows and a smaller measured context with equal targets.
"""
import argparse
import copy
from pathlib import Path
import time
from runners.stage9.common import REPO,ROOT,closure,digest,freeze,read
from runners.stage9.matching import audit,match_budget,target_positions
from runners.stage9.train import train


def first_two(row):
    row=copy.deepcopy(row)
    if row['kind']!='learner_visited':
        return row
    spans=row['spans'][:2]
    if len(spans)!=2:
        raise ValueError('the fixed two-continuation variant requires two complete correct targets')
    end=spans[-1]['correct_target'][1]
    ids=row['input_ids'][:end]
    labels=[-100]*len(ids)
    for span in spans:
        start,stop=span['correct_target']
        labels[start:stop]=ids[start:stop]
    row.update(input_ids=ids,labels=labels,spans=spans,complete_continuations_retained=2,
               complete_continuations_excluded=row['complete_continuations_excluded']+row['complete_continuations_retained']-2)
    return row


def prepare(family):
    started=time.time();source=ROOT/'private/pilot-matched'/family
    expert,mixed=read(source/'expert.json'),read(source/'mixed.json')
    budget=sum(len(target_positions(r)) for r in expert['examples'])
    candidates=[first_two(r) for r in mixed['examples']]
    fixed={r['key'] for r in mixed['examples'] if r['kind']!='learner_visited'}
    rows=match_budget(candidates,budget,fixed_keys=fixed)
    comparison=audit({'expert':expert['examples'],'mixed_two':rows})
    output=ROOT/'private/pilot-matched-two'/family
    identity={'family':family,'scope':'discarded compact-context timing only',
              'parent_corpora_sha256':{'expert':digest(expert),'mixed':digest(mixed)},
              'sources':closure([REPO/'runners/stage9'/n for n in ('compact_matched_pilot.py','matching.py')]),
              'matching':comparison,'selection':'first two independently correct continuations at the unchanged preassigned actual state; no performance selection'}
    freeze(output/'mixed.json',{'split':'pilot','identity':identity,'examples':rows,
                              'validation':expert['validation'],'validation_choices':expert['validation_choices']})
    receipt={'family':family,'comparison':comparison,'preparation_seconds':time.time()-started,
             'training_timing_complete':False,'scientific_training_accepted':False}
    freeze(output/'PREPARATION.json',receipt)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['prepare','train'])
    parser.add_argument('--family',required=True,choices=['qwen','smollm'])
    args=parser.parse_args()
    if args.operation=='prepare':
        print(prepare(args.family))
    else:
        root=ROOT/'private/pilot-matched-two'/args.family
        train(root/'mixed.json',root/'training-v1',args.family,seed=994901,epochs=1,max_length=1024,checkpoint_every=8)
