from copy import deepcopy
import pytest
from runners.drive.cards import week4_t4_menus as m

def test_canonical_choice_dismissal_and_ignore_remain_distinct():
    sessions=m.fixture();menus=sessions[0]['menus']
    assert menus[0]['choice']==1 and menus[0]['original_option_ids']==[7,3]
    assert menus[1]['choice']==menus[1]['dismissal_index']==2
    assert menus[2]['choice'] is None
    assert menus[0]['preceding_visible_sentence']=='Last sentence.'

def test_past_state_clock_units_and_session_halves():
    ss=m.past_state(m.fixture());target=ss[1]['menus'][1]
    assert target['previous_five_acceptance']==.4 and target['seconds_since_last_acceptance']==1.5
    assert ss[0]['half']=='train' and ss[1]['half']=='test'
    assert not ss[0]['menus'][0]['state_supported']

def test_unresolved_and_future_resolution_never_enter_state():
    ss=m.fixture();ss[0]['menus'][3]['resolved_at']=9000
    m.past_state(ss);target=ss[1]['menus'][1]
    assert target['previous_five_count']==4 and not target['state_supported']
    assert target['seconds_since_last_acceptance']==4.5

def test_actual_interface_replay_and_tamper_refusal(tmp_path):
    c=m.configuration('constructed');m.execute(tmp_path,{},c)
    assert m.verify(tmp_path,{},c)['complete_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='aggregate'):m.verify(tmp_path,{},c)
