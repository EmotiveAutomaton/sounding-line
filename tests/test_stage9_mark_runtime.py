import copy

import pytest

from runners.stage9.artifact_view import TYPES
from runners.stage9.erased_inference import infer
from runners.stage9.mark_runtime import execute
from runners.stage9.program_inference import Budget
from runners.stage9.program_proposals import propose
from tests.test_stage9_erased_inference import A, B, evidence, marked, program


def bundle():
    return {'evidence': evidence(marked([], 'future'), [marked([A], 'past')]),
            'candidates': {'a': program(.75), 'b': program(.25)}, 'prior': {'a': .5, 'b': .5},
            'shared_groups': {'a': 'same', 'b': 'same'},
            'population': {'version': 's9-conditional-choice-v1', 'weights': {}, 'individual': False, 'uniform_mixture': .01},
            'population_types': {t: 1/len(TYPES) for t in TYPES}}


def test_four_actual_capsule_routes_keep_complete_support_and_declared_assistance(tmp_path):
    value = bundle()
    outputs = {}
    for route in ('population', 'cheap_individual', 'program_mixture', 'differentiated_maker'):
        result = execute(value, route, root=tmp_path/'caps')
        assert result['accepted'], result
        outputs[route] = result['prediction']
        assert set(result['prediction']['prediction']) == set(value['evidence']['support'])
        assert result['inputs_and_sources_unchanged']
        names = result['copied_sources']['files']
        assert not any('constructor' in key or 'preparation' in key or 'fit' in key for key in names)
    assert outputs['program_mixture']['prediction'][A] == pytest.approx(15/32)
    # The same persistent group has independent purposes across works, so the
    # past updates neither current purpose nor the only persistent group.
    assert outputs['differentiated_maker']['prediction'][A] == pytest.approx(3/8)
    assert outputs['cheap_individual']['prediction'][A] > outputs['population']['prediction'][A]


def test_actual_capsule_retains_contradicted_candidate_and_refuses_invalid_bundle(tmp_path):
    value = bundle()
    value['candidates']['b']['available_types'] = ['check']
    accepted = execute(value, 'program_mixture', root=tmp_path/'caps')
    assert accepted['accepted'], accepted
    assert accepted['prediction']['weights']['b'] == 0
    assert accepted['prediction']['likelihood_receipts']['b'][0]['log_mass'] == {'extended_real': 'negative_infinity'}
    bad = copy.deepcopy(value)
    bad['truth'] = 'forbidden'
    refused = execute(bad, 'program_mixture', root=tmp_path/'caps')
    assert not refused['accepted'] and refused['prediction'] is None
    refused = execute(value, 'program_mixture', budget=1, root=tmp_path/'caps')
    assert not refused['accepted'] and refused['prediction'] is None


def test_actual_comparator_capsule_cannot_open_existing_truth(tmp_path):
    hidden = tmp_path/'private-truth.json'
    hidden.write_text('untouched truth')
    result = execute(None, task={'probe': True, 'forbidden_paths': [str(hidden)], 'other_port': 65534}, root=tmp_path/'caps')
    assert result['accepted'], result
    assert hidden.read_text() == 'untouched truth'


def test_numerical_proposal_replenishment_opens_missing_support_without_exact_claim(tmp_path):
    value = bundle()
    value['evidence'] = evidence(marked([B]))
    old = program()
    old['available_types'] = ['write']
    proposals = propose(value['evidence'], [old, old], Budget(100), maximum=4, expand=True)
    assert proposals['distinct_library_candidates'] == 1
    assert proposals['selected_candidates'] == 2
    assert not proposals['fixed_complete_catalogue'] and not proposals['proposal_density_known']
    result = infer(value['evidence'], proposals['candidates'], proposals['prior'], Budget(100))
    assert sum(w > 0 for w in result['weights'].values()) == 1
    # The actual worker runs the same proposal operation; it does not quietly
    # substitute a population prediction when the initial library contradicts.
    value['candidates'] = {'old': old}
    value['prior'] = {'old': 1.}
    value['shared_groups'] = {'old': 'same'}
    actual = execute(value, 'numerical_proposals', maximum_candidates=4, expand=True, root=tmp_path/'caps')
    assert actual['accepted'], actual
    assert actual['prediction']['candidates'] == proposals['candidates']
    assert actual['prediction']['language_model_calls'] == 0


def test_fixed_proposals_and_repeated_evidence_do_not_create_candidates():
    value = bundle()
    original = propose(value['evidence'], list(value['candidates'].values()), Budget(100), maximum=8)
    value['evidence']['earlier'] *= 3
    repeated = propose(value['evidence'], list(value['candidates'].values())*2, Budget(100), maximum=8)
    assert original['candidates'] == repeated['candidates']
    assert repeated['fixed_complete_catalogue']
    assert original['prior'] == repeated['prior']
