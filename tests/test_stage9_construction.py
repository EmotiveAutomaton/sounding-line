import copy

import pytest

from runners.stage7.constructor import worlds as W
from runners.stage7.reader import law as LAW
from runners.stage8.constructor import population as POP
from runners.stage9.construction import Replay, register


def test_actual_expert_prefix_state_and_policy_match_existing_executor():
    register()
    for domain in POP.DOMAINS:
        for i in range(20):
            world = POP.sample_world(POP.pop_lid(i, domain, 9930000))
            prefix = world['trajectory']['steps'][:min(5, len(world['trajectory']['steps']))]
            replay = Replay(world, prefix)
            expected = W._state_at(world['state'], world['trajectory'], len(prefix), world['inventory'])
            assert replay.snapshot() == expected
            if prefix:
                prediction = W._predictive(expected, expected['pending'], list(replay.sections),
                                          prefix[-1]['type'], len(prefix), len(replay.done), len(world['inventory']))
                joint = replay.probabilities()
                if any(prediction['next_action'].values()):
                    assert joint['stop'] == pytest.approx(prediction['p_stop'], abs=1e-12)
                    for aid, p in prediction['next_action'].items():
                        assert joint.get(aid, 0) == pytest.approx((1 - prediction['p_stop']) * p, abs=1e-12)


def test_zero_teacher_probability_action_still_creates_a_real_state():
    world = POP.sample_world(POP.pop_lid(90, 'essay', 9930000))
    world['state']['expertise_law'] = copy.deepcopy(W.LAWS['novice'])
    replay = Replay(world)
    action = next(a for a in world['inventory'] if a['type'] == 'restructure')
    assert replay.probabilities().get(LAW.action_id(action), 0) == 0
    replay.apply(action, verify_outcome=False)
    assert len(replay.steps) == 1
    assert replay.last_type == 'restructure'
    assert LAW.action_id(action) in replay.done
    tail, stopped = replay.continue_teacher(11, max_events=8)
    assert all(e['i'] >= 1 for e in tail)
    assert len(replay.steps) <= 8


def test_extension_is_recorded_and_invalid_attempt_does_not_mutate():
    world = POP.sample_world(POP.pop_lid(91, 'essay', 9930000))
    replay = Replay(world, extend_visible=True)
    original = {LAW.action_id(a) for a in world['inventory']}
    action = next(a for a in replay.legal_actions() if LAW.action_id(a) not in original)
    replay.apply(action)
    assert len(replay.extensions) == 1
    prior = replay.snapshot()
    with pytest.raises(ValueError):
        replay.apply({'type': 'write', 'section': 'nonexistent', 'slot': 's999'})
    assert replay.snapshot() == prior


def test_explicit_empty_change_schedule_stays_empty():
    world = POP.sample_world(POP.pop_lid(92, 'essay', 9930000))
    world['trajectory']['changes'] = []
    world['trajectory']['change_step'] = 1
    world['state']['external_context']['scheduled_change'] = 'deadline_imposed'
    world['state']['external_context']['deadline'] = 'loose'
    replay = Replay(world)
    action = next(a for a in world['inventory'] if a['type'] == 'write')
    replay.apply(action, verify_outcome=False)
    assert replay.c_ext['deadline'] == 'loose'
