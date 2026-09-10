import copy
import pytest
from runners.stage9.compact_matched_pilot import first_two
from runners.stage9.matching import match_budget,target_positions


def test_compaction_retains_complete_correct_targets_and_never_labels_learner_context():
    row={'kind':'learner_visited','key':'a','lineages':['a'],'input_ids':[99,11,12,98,21,22,97,31,32,96,41,42],
         'labels':[-100,11,-100,-100,21,-100,-100,31,-100,-100,41,-100],
         'spans':[{'context':[i,i+1],'correct_target':[i+1,i+3]} for i in (0,3,6,9)],
         'complete_continuations_retained':4,'complete_continuations_excluded':0}
    before=copy.deepcopy(row);compact=first_two(row)
    assert row==before
    assert compact['input_ids']==[99,11,12,98,21,22]
    assert compact['labels']==[-100,11,12,-100,21,22]
    assert compact['complete_continuations_excluded']==2
    matched=match_budget([compact],3)[0]
    assert len(target_positions(matched))==3
    assert matched['labels'][0]==matched['labels'][3]==-100


def test_compact_capacity_shortfall_does_not_invent_targets():
    row={'kind':'original_replay','key':'a','lineages':['a'],'input_ids':[1,2,3],'labels':[1,2,3]}
    assert first_two(row)==row
    with pytest.raises(ValueError):match_budget([row],3)
