from runners.stage9.construction import Replay, POP
from runners.stage9.recipes import sampled_world
from runners.stage9.kernel import probabilities, action_id
from runners.stage9.kernel_preparation import supplied_program
from runners.stage9.kernel_runtime import execute


def test_actual_kernel_capsule_executes_complete_information_and_rejects_missing_support(tmp_path):
    world = sampled_world(POP.pop_lid(3, 'essay', 9950000), 'both')
    program = supplied_program(Replay(world))
    evidence = {'programs': [program], 'weights': [1.], 'support': ['stop'] + [action_id(a) for a in program['pending']]}
    result = execute(evidence, root=tmp_path / 'caps')
    assert result['accepted'], result
    expected = probabilities(program)
    assert result['prediction']['probs'] == {k: expected.get(k, 0.) for k in evidence['support']}
    evidence['support'].remove('stop')
    failed = execute(evidence, root=tmp_path / 'caps')
    assert not failed['accepted'] and failed['prediction'] is None
    assert 'missing or spurious' in failed['error']['traceback']


def test_actual_kernel_capsule_cannot_read_or_write_existing_outside_truth(tmp_path):
    hidden = tmp_path / 'hidden.json'
    hidden.write_text('preserve hidden truth')
    result = execute(None, {'probe': True, 'forbidden_paths': [str(hidden)], 'other_port': 65534}, root=tmp_path / 'caps')
    assert result['accepted'], result
    assert hidden.read_text() == 'preserve hidden truth'
