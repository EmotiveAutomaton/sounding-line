import pytest
from runners.drive.cards.week4_cursor_texture import configuration,execute,verify,GRID
from runners.drive.cards.week4_cursor import motion,near_edit

def test_frozen_threshold_boundaries_and_followup():
    assert motion(0,40,[],[],20)=='jump'
    assert motion(0,40,[],[],80)=='other'
    landing=dict(ordinal=1,time=0,near_start=0,near_end=10)
    edit=dict(ordinal=2,time=45,ops=[{'insert':'x'}],user=True)
    assert not near_edit(landing,[edit],30) and near_edit(landing,[edit],60)
    with pytest.raises(ValueError):configuration(15,60)

@pytest.mark.parametrize('jump,window',GRID)
def test_complete_fixture_replay_and_mutation_refusal(tmp_path,jump,window):
    config=configuration(jump,window,True);execute(tmp_path,{},config)
    assert verify(tmp_path,{},config)['complete_statistical_replay']
    p=tmp_path/'SUMMARY.json';p.write_text('{}')
    with pytest.raises(ValueError,match='mismatch'):verify(tmp_path,{},config)
