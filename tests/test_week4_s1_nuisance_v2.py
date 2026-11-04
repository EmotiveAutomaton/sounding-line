import pytest
from runners.drive.cards import week4_s1_nuisance_v2 as n

def test_explicit_source_clock_units():
    assert all(n.known_check().values())

def test_native_interface_replays_and_refuses_mutation(tmp_path):
    c=n.configuration('constructed');n.execute(tmp_path,{},c)
    assert n.verify(tmp_path,{},c)['complete_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='summary'):n.verify(tmp_path,{},c)
