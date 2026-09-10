import copy
import pytest
from runners.stage7.constructor import worlds as W
from runners.stage8.reader import logfmt as LF
from runners.stage9.construction import Replay,register
from runners.stage9.recipes import POP,sampled_world
from runners.stage9.rollout_operations import (execute_action,matched_altered_prefix,
    public_input,rollout,state_identity)


def worlds(count=8):
    register()
    return [sampled_world(POP.pop_lid(i,domain,9994000),'both')
            for domain in POP.DOMAINS for i in range(count)]


def response(line):
    return {'accepted':True,'prediction':{'text':line}}


def line(event):
    return LF.event_line(event['i'],event['type'],event['section'],event['slot'],event['outcome'])


def test_actual_constructor_actions_validate_both_execution_interfaces():
    count=0
    for world in worlds():
        actual=world['trajectory']['steps']
        if not actual:continue
        def oracle(evidence,arguments,index):
            return response(line(actual[index]) if index<len(actual) else LF.stop_line(index))
        for mode in ('self_outcome','environment_outcome'):
            result=rollout(world,oracle,mode=mode,horizon=4)
            assert result['failure'] is None
            expected=actual[:4]
            assert len(result['events'])==len(expected)
            for observed,wanted in zip(result['events'],expected):
                assert {k:observed[k] for k in ('i','type','section','slot','outcome')}=={
                    k:wanted[k] for k in ('i','type','section','slot','outcome')}
            source_state=W._state_at(world['state'],world['trajectory'],len(expected),world['inventory'])
            assert Replay(world,result['events']).snapshot()==source_state
            count+=1
    assert count>=24


def test_environment_supplies_outcome_but_never_repairs_an_illegal_action():
    world=next(w for w in worlds(1) if w['trajectory']['steps'])
    actual=world['trajectory']['steps'][0];wrong=copy.deepcopy(actual)
    wrong['outcome']='failed' if actual['outcome']=='done' else 'done'
    supplied=Replay(world,extend_visible=True)
    accepted=execute_action(supplied,response(line(wrong)),'environment_outcome',{})
    assert accepted['legal'] and accepted['actual_event']['outcome']==actual['outcome']
    unaided=Replay(world,extend_visible=True);before=state_identity(unaided)
    refused=execute_action(unaided,response(line(wrong)),'self_outcome',{})
    assert not refused['legal'] and 'objective execution' in refused['failure']
    assert state_identity(unaided)==before
    illegal=response('00 write nonexistent s999 done')
    refused=execute_action(unaided,illegal,'environment_outcome',{})
    assert not refused['legal'] and state_identity(unaided)==before


def test_story_wrong_clock_and_early_stop_are_not_sustained_success():
    world=worlds(1)[0]
    for text in ('The maker should improve the argument.','99 write sec1 s1.1 done'):
        result=rollout(world,lambda *args:response(text),mode='environment_outcome',horizon=16)
        assert len(result['attempts'])==1 and not result['attempts'][0]['legal']
        assert not result['horizons']['16']['reached_action_horizon']
    stopped=rollout(world,lambda *args:response('00 stop'),mode='environment_outcome',horizon=16)
    assert stopped['stopped'] and stopped['failure'] is None
    assert all(not row['reached_action_horizon'] for row in stopped['horizons'].values())
    assert all(row['legal_interactions']==1 for row in stopped['horizons'].values())


def test_genuine_reset_replaces_an_actual_learner_history_and_is_visible():
    world=next(w for w in worlds(16) if len(w['trajectory']['steps'])>=8)
    reference=world['trajectory']['steps'];independent=Replay(world,extend_visible=True)
    seen=[]
    def proposal(evidence,arguments,index):
        seen.append(evidence)
        if index==4:
            assert evidence['prefix']==public_input(world,reference[:4])['prefix']
            return response('04 stop')
        candidates=[a for a in independent.legal_actions() if a['outcome']=='done']
        action=next(a for a in reversed(candidates) if (a['type'],a['section'],a['slot'])!=
                    tuple(reference[index][k] for k in ('type','section','slot')))
        actual=independent.apply(action,verify_outcome=False)
        return response(line(actual))
    result=rollout(world,proposal,mode='environment_outcome',horizon=8,reset_every=4)
    assert len(seen)==5 and result['stopped']
    assert result['resets'][0]['replaced_state']!=result['resets'][0]['genuine_state']
    assert result['resets'][0]['genuine_state']==state_identity(Replay(world,reference[:4],extend_visible=True))
    assert result['assistance']['genuine_state_reset_every']==4
    assert result['horizons']['4']['reset_boundaries']==[]
    assert result['horizons']['8']['reset_boundaries']==[4]


def test_matched_history_is_legal_and_preserves_full_state_not_just_marks():
    matched=[]
    for world in worlds(12):
        result=matched_altered_prefix(world,3)
        if not result['realized']:continue
        genuine=Replay(world,result['genuine']);altered=Replay(world,result['altered'])
        assert genuine.steps!=altered.steps
        assert genuine.snapshot()==altered.snapshot()
        assert genuine.last_type==altered.last_type and len(genuine.steps)==len(altered.steps)==3
        assert result['state_sha256']==state_identity(genuine)==state_identity(altered)
        matched.append(result)
    assert matched


def test_artifact_rendering_uses_only_visible_projection_and_offers_full_support():
    world=worlds(1)[0];steps=world['trajectory']['steps'][:2]
    public=public_input(world,steps,'artifact',offered=True)
    changed=copy.deepcopy(world)
    changed['state']['persistent_tendency']={'private_canary':'DO_NOT_SHOW'}
    changed['trajectory']['changes']=[(30,'library_arrives')]
    assert public==public_input(changed,steps,'artifact',offered=True)
    assert 'DO_NOT_SHOW' not in public['prefix'] and 'stop' in public['options']
    assert public['options']['stop']==LF.stop_line(len(steps))
