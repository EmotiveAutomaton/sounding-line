import json
import pytest
from runners.drive.cards import week3_tr4_analysis as a


def test_actual_consumer_replays_and_refuses_tamper(tmp_path):
    a.execute(tmp_path,{},a.CONFIGS['constructed'])
    first=(tmp_path/'RESULTS.json').read_bytes()
    assert a.verify(tmp_path,{},a.CONFIGS['constructed'])['complete_input_replay']
    assert (tmp_path/'RESULTS.json').read_bytes()==first
    value=json.loads(first);value['cases']['change']['primary']['estimate']=0
    (tmp_path/'RESULTS.json').write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError,match='independent replay'):a.verify(tmp_path,{},a.CONFIGS['constructed'])


def test_full_controls_and_verification_are_in_cost_projection():
    t=dict(forecasts=1,profiles=2,outcome=3,labels=4,uncertainty=5)
    p=a.projection(t)
    assert p['execute_and_fresh_verify_cpu_seconds']==3*(1+2+100*3+500*4+50000*5)
    assert p['full_config']==a.CONFIGS['main']


def test_main_refuses_unlanded_cost(tmp_path):
    with pytest.raises(ValueError,match='bindings'):a.execute(tmp_path,{},a.CONFIGS['main'])
