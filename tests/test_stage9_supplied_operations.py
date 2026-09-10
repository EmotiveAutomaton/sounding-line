import copy
import json
import pytest
from runners.stage9 import supplied_operations as supplied
from runners.stage9.common import digest
from runners.stage9.construction import POP, Replay
from runners.stage9.recipes import sampled_world
from runners.stage9.kernel_runtime import execute
from runners.stage9.neural_operations import request_task, unit_result


def case():
    world = sampled_world(POP.pop_lid(3, 'essay', 9950000), 'both')
    oracle = Replay(world).probabilities()
    return {'source_worlds': [world], 'requested_boundary': 0, 'unit': 'fixture',
            'role': 'pilot', 'target': max(oracle, key=oracle.get), 'oracle': oracle}


def test_full_input_contains_actual_executable_semantics_and_no_future():
    c = case()
    actual = supplied.inputs(c)
    code = actual['full']['prefix'].split('\n', 1)[1].split('\nINPUT\n')[0]
    scope = {}
    exec(compile(code, '<supplied-operative-source>', 'exec'), scope)
    program = actual['bundle']['programs'][0]
    assert scope['probabilities'](program) == c['oracle']
    encoded = actual['full']['prefix'].split('\nINPUT\n')[1].split('\nNEXT ACTION\n')[0]
    assert json.loads(encoded) == actual['bundle']
    assert actual['full']['options'] == actual['parameters_only']['options']
    assert encoded in actual['parameters_only']['prefix'] and code not in actual['parameters_only']['prefix']
    changed = copy.deepcopy(c)
    changed['target'] = 'hidden-target'
    changed['oracle'] = {'hidden-target': 1.}
    changed['source_worlds'][0]['trajectory'] = {'steps': [], 'stop_kind': 'different-future'}
    assert supplied.inputs(changed) == actual


def test_actual_kernel_capsule_crosses_complete_grid_and_refuses_wrong_semantics(tmp_path):
    c = case()
    invocations = []
    def call(evidence, arguments, index):
        invocations.append(index)
        if index == 'explicit-kernel':
            return execute(evidence, request_task(evidence, arguments, {}), root=tmp_path/'caps')
        # Deterministic known-answer transport fixture, not a model-performance claim.
        return {'accepted': True, 'prediction': {'probs': {k: c['oracle'].get(k, 0.) for k in evidence['options']}}}
    row = unit_result(c, 'supplied_kernel', call)
    assert invocations == ['explicit-kernel', 'full', 'parameters_only']
    result = supplied.profile([row], draws=100)
    for name in ('execution_vs_direct', 'operative_code_added'):
        assert result['comparisons']['all'][name]['estimate']['mean'] == 0.
    bad = copy.deepcopy(row)
    bad['result']['calls']['full']['accepted'] = False
    assert supplied.profile([bad])['comparisons']['all']['execution_vs_direct']['disposition'] == 'IMPLEMENTATION INVALID'
    kernel = row['result']['calls']['explicit']
    wrong = copy.deepcopy(kernel)
    wrong['copied_sources']['files']['reader/kernel.py'] = '0'*64
    with pytest.raises(ValueError, match='operative semantics'):
        supplied.evaluate_unit(c, lambda *args: wrong)
    with pytest.raises(ValueError, match='distinct assigned'):
        supplied.profile([row, row])
    bad = copy.deepcopy(c)
    bad['oracle'] = {'stop': 1.}
    with pytest.raises(ValueError, match='constructor consequences'):
        supplied.evaluate_unit(bad, lambda *args: pytest.fail('bad oracle reached reader'))
