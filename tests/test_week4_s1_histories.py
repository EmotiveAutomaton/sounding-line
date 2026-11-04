from collections import defaultdict
from copy import deepcopy
import pytest
from runners.drive.cards import week4_s1_histories as h

def test_exact_counts_no_future_and_no_source_mutation():
    records,_=h.fixture();by=defaultdict(list)
    for r in records:by[r['writer']].append(r)
    before=deepcopy(by);proof,donor=h.match(by,records[2])
    assert proof['donor_sessions']==['b0'] and proof['own_tokens']==proof['donor_tokens']==4
    assert by==before and donor[0]['training_sequences']==[['a']*4]
    proof,donor=h.match(by,records[0]);assert not proof['supported'] and donor is None

def test_insufficient_capacity_remains_unsupported():
    records,_=h.fixture();records[1]['training_sequences']=[['a']*3];by=defaultdict(list)
    for r in records:by[r['writer']].append(r)
    proof,donor=h.match(by,records[2]);assert not proof['supported'] and donor is None

def test_actual_native_interface_replays_and_refuses_mutation(tmp_path):
    c=h.configuration('constructed');h.execute(tmp_path,{},c)
    assert h.verify(tmp_path,{},c)['complete_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='differs'):h.verify(tmp_path,{},c)
