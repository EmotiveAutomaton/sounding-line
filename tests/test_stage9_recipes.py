from runners.stage8.constructor import population as POP
from runners.stage8.reader import logfmt as LF
from runners.stage9.construction import Replay
from runners.stage9.learner import collect_one
from runners.stage9.recipes import training_record, sampled_world, parameter_partition, combination


def test_narrow_recipe_exactly_replays_original_rendering_and_metadata():
    for domain in POP.DOMAINS:
        for i in range(16):
            actual, _ = training_record(i, domain, 9950000, 'original')
            assert actual == POP.training_example(i, domain, 9950000)


def test_broader_law_variants_share_heldout_combinations():
    changed = 0
    for i in range(30):
        lid = POP.pop_lid(i, 'essay', 9950000)
        narrow, broad = sampled_world(lid), sampled_world(lid, 'both')
        assert combination(narrow) == combination(broad)
        assert parameter_partition(narrow) == parameter_partition(broad)
        assert narrow['doc'] == broad['doc']
        if broad['state']['names']['law'].endswith('2'):
            changed += 1
    assert 0 < changed < 30


def test_invalid_generated_action_cannot_become_a_learner_visit():
    world = sampled_world(POP.pop_lid(2, 'essay', 9950000))
    def invalid(evidence, turn):
        assert set(evidence) == {'prefix', 'options'} and not evidence['options']
        return {'accepted': True, 'prediction': {'text': 'A plausible explanation without an action'}}
    result = collect_one(world, invalid)
    assert result['learner_actions_applied'] == 0
    assert len(result['attempts']) == 1 and result['attempts'][0]['failure']
    assert all(e['learner_actions_applied'] == 0 for e in result['examples'])


def test_teacher_targets_continue_actual_applied_action_clock():
    world = sampled_world(POP.pop_lid(4, 'essay', 9950000))
    replay = Replay(world, world['trajectory']['steps'][:2], extend_visible=True)
    action = replay.legal_actions()[0]
    def execute_fixture(evidence, turn):
        return {'accepted': True, 'prediction': {'text': LF.event_line(len(replay.steps), action['type'], action['section'], action['slot'], action['outcome'])}}
    result = collect_one(world, execute_fixture, maximum_actions=1)
    assert result['learner_actions_applied'] == 1
    first, second = result['examples']
    assert second['teacher_clock'] == first['teacher_clock'] + 1
    assert second['actual_prefix'][-1]['type'] == action['type']
    for target in second['targets']:
        assert LF.parse_line(target['target'].splitlines()[0])['i'] == second['teacher_clock']
