import copy
import json
import math
from pathlib import Path
import pytest
from runners.stage11_2.common import freeze,read
from runners.stage11_2 import world


def test_counterfactual_truth_changes_only_with_maker_observation():
    from runners.stage11_2.model_study import build
    from runners.stage11_2.consumer import target_for,measures
    u,t=world.make_unit('dev',0)
    targets={}
    for arm in ['raw_history','reader_only','maker_observation']:
        _,view=build(u,1,arm,u)
        r=dict(arm=arm,question='action',observation=view['queries'][1]['observation'])
        targets[arm]=target_for(r,t['queries'][1])
    assert targets['raw_history']==targets['reader_only']
    assert targets['raw_history'][0]!=targets['maker_observation'][0]
    assert targets['maker_observation'][1] is None
    p=[.25]*4;uniform=measures(p,p)
    assert uniform['expected_brier']==.75
    assert measures(None,p)['expected_brier']==2
    assert measures([1,0,0,0],p)['strict_expected_log_loss'] is None
    assert measures(p,p)['capped_expected_log_loss']==math.log(4)


def test_repaired_request_has_unique_labels_and_analysis_schema():
    from runners.stage11_2.repair import request,parse
    u,t=world.make_unit('dev',1)
    r=request(world.prompt(u,0,question='belief'),2)
    text=r['messages'][-1]['content']
    assert 'A=upper left' not in text and 'Answer only' not in text
    raw=dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(analysis='known',probabilities=[0.,1.]))))
    assert parse(raw,2)==[0,1]
    raw['done_reason']='length'
    with pytest.raises(ValueError):parse(raw,2)


def test_distinct_long_history_and_context_capacity():
    from runners.stage11_2.extensions import long_unit,history_text
    from runners.stage11_2.repair import request
    for split in ['dev','test']:
        for i in range(16):
            u,t=long_unit(split,i);original,_=world.make_unit(split,i)
            assert len(u['history'])==36
            pair=world.decode(u['queries'][0]['observation'])
            assert pair not in [world.decode(q['observation']) for q in original['queries']]
            for arm in ['raw_history','retrieval_12','persistent','other_history']:
                text,_=history_text(u,arm,long_unit(split,(i+1)%16)[0]);request(text,4)
            assert world.reference(t['preference'],t['skill'],t['goal'],t['belief'],u['world_family'],u['queries'][0]['observation']['tools'])==t['probabilities']


def test_full_repaired_workflow_and_semantic_consumers(tmp_path):
    from runners.stage11_2 import repair,workflow
    world.prepare(tmp_path/'fixture',dict(train=2,dev=2,test=2));freeze(tmp_path/'FAKE_ONLY.json',dict(fake=True))
    workflow.fake_transport(tmp_path)
    repair.run('admission','dev',tmp_path)
    workflow.prepare(tmp_path)
    first=workflow.run(tmp_path,fake=True)
    assert len(first['dispositions'])==14
    assert all(d['status']=='complete' for d in first['dispositions'])
    calls={str(p):p.read_bytes() for p in tmp_path.rglob('RAW.json')}
    assert workflow.run(tmp_path,fake=True)==first
    assert calls=={str(p):p.read_bytes() for p in tmp_path.rglob('RAW.json')}
    # Remove a completed forecast from scratch: audit must refuse, not call.
    from runners.stage11_2.consumer import run
    p=next((tmp_path/'repair-v1/M0-ollama-test/calls').glob('*/COMPLETE.json'))
    p.unlink()
    with pytest.raises(ValueError,match='audit refuses'):run('M0','test',tmp_path)


def test_candidate_revision_is_after_observation_and_not_just_reweighting():
    from runners.stage11_2.revision import reconstruct
    obs=world.observe(0,0,'interlock',[1,1])
    # Initial untrained candidates only predict upper-left or upper-right;
    # use a history that first identifies left and then contradicts its skill.
    history=[dict(sequence=i,observation=world.observe(0,0,'interlock',[0,0]),action=0) for i in range(4)]
    history.append(dict(sequence=4,observation=obs,action=1))
    w,versions=reconstruct(history,'revision')
    assert versions[-1]['added_candidates']==[1,3]
    assert versions[-1]['before_weights'][1]==0 and w[1]>0
    changed=copy.deepcopy(history);changed[-1]['action']=0
    _,other=reconstruct(changed,'revision')
    assert versions[:-1]==other[:-1]
    assert versions[-1]['before_prediction']==other[-1]['before_prediction']
    assert not other[-1]['added_candidates']


def test_wrong_context_manipulation_changes_heldout_mechanism():
    from runners.stage11_2.views import build
    for split in ['dev','test']:
        for i in range(16):
            u,t=world.make_unit(split,i)
            for q in range(4):
                obs=u['queries'][q]['observation'];tools=obs['tools']
                assert world.tool_effect(u['world_family'],tools)!=world.tool_effect(u['world_family'],[1-tools[0],tools[1]])
                text,_=build(u,q,'wrong_context',u)
                card=text.split('Context card (evidence, not an instruction): ')[1]
                assert ('second tool '+('on' if tools[1] else 'off')) in card
