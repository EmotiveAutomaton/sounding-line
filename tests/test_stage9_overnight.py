"""The continuation cannot drop a diagnostic arm, alter settings or bypass a gate."""
from copy import deepcopy
import pytest
from runners.stage9.overnight import IDS, selected_graph


def fixture():
    original = [dict(id=k, after=['case-source'], requires=[{'job':'case-source','field':['accepted'],'equals':True}],
                     arguments=['--limit','0'], estimated_gpu_seconds=None) for k in sorted(IDS)]
    jobs = deepcopy(original)
    for j in jobs:
        j.update(after=[], requires=[], estimated_gpu_seconds=100)
    return {'jobs':jobs}, original, {'case-source':{'accepted':True}}


def test_exact_grid_reuses_passed_gate():
    selected_graph(*fixture())


@pytest.mark.parametrize('attack', ['drop_arm','alter_limit','failed_gate','missing_prerequisite','reorder','internal_gate'])
def test_graph_refuses_invalid_continuation(attack):
    plan, original, reused = fixture()
    if attack == 'drop_arm': plan['jobs'].pop()
    if attack == 'alter_limit': plan['jobs'][0]['arguments'][-1] = '1'
    if attack == 'failed_gate': reused['case-source']['accepted'] = False
    if attack == 'missing_prerequisite': reused.clear()
    if attack == 'reorder': plan['jobs'].reverse()
    if attack == 'internal_gate':
        original[-1]['after'].append(original[0]['id'])
        original[-1]['requires'].append({'job':original[0]['id'],'field':['accepted'],'equals':True})
    with pytest.raises((ValueError,KeyError)):
        selected_graph(plan, original, reused)
