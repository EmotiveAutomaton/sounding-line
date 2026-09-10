import copy

import pytest

from runners.stage9.artifact_preparation import evidence
from runners.stage9.artifact_view import action_id, validate
from runners.stage9.common import canonical
from runners.stage9.recipes import POP, sampled_world


def test_actual_constructor_actions_are_in_complete_public_support_at_every_boundary():
    for domain in POP.DOMAINS:
        for i in range(8):
            world = sampled_world(POP.pop_lid(i, domain, 9988100), 'both')
            events = world['trajectory']['steps']
            for boundary in range(len(events)+1):
                primary = evidence(world, events[:boundary])
                diagnostic = evidence(world, events[:boundary], 'process_record')
                assert primary['support'] == diagnostic['support']
                assert 'stop' in primary['support']
                if boundary < len(events):
                    assert action_id(events[boundary]) in primary['support']
                assert 'events' not in primary['current']
                assert 'observed_stop' not in primary['current']


def test_hidden_state_inventory_future_and_identifiers_have_no_visible_bytes():
    world = sampled_world(POP.pop_lid(9, 'essay', 9988100), 'both')
    prefix = world['trajectory']['steps'][:2]
    original = evidence(world, prefix)
    changed = copy.deepcopy(world)
    changed['lid'] = 'CANARY_ID'
    changed['goal_name'] = 'CANARY_PURPOSE'
    changed['inventory'] = 'CANARY_INVENTORY'
    changed['trajectory'] = 'CANARY_FUTURE'
    context = copy.deepcopy(changed['state']['external_context'])
    context['brief_sections'] = ['CANARY_REQUIRED_PURPOSE_PROXY']
    context['scheduled_change'] = 'CANARY_CHANGE'
    changed['state'] = {'external_context': context, 'belief_state': 'CANARY_BELIEF',
                        'expertise_law': 'CANARY_LAW', 'history_residue': 'CANARY_HISTORY'}
    assert evidence(changed, prefix) == original
    assert 'CANARY' not in canonical(evidence(changed, prefix))


def test_order_and_failed_attempt_are_erased_only_in_artifact_view():
    world = sampled_world(POP.pop_lid(10, 'essay', 9988100), 'both')
    slots = world['doc']['sections'][0]
    a = {'i': 0, 'type': 'write', 'section': slots['name'], 'slot': slots['slots'][0], 'outcome': 'done'}
    b = {'i': 1, 'type': 'check', 'section': slots['name'], 'slot': slots['slots'][0], 'outcome': 'done'}
    failure = {'i': 2, 'type': 'cite', 'section': slots['name'], 'slot': 'ref', 'outcome': 'failed'}
    ordered = [a, b, failure]
    swapped = [dict(b, i=0), dict(a, i=1)]
    assert evidence(world, ordered) == evidence(world, swapped)
    assert evidence(world, ordered, 'process_record') != evidence(world, swapped, 'process_record')


def test_undeclared_fields_partial_support_and_current_stop_truth_are_rejected():
    world = sampled_world(POP.pop_lid(11, 'essay', 9988100), 'both')
    visible = evidence(world, [], 'process_record')
    invalid = copy.deepcopy(visible)
    invalid['current']['context']['purpose'] = 'teach'
    with pytest.raises(ValueError, match='undeclared context'):
        validate(invalid)
    invalid = copy.deepcopy(visible)
    invalid['support'].pop()
    with pytest.raises(ValueError, match='support omits'):
        validate(invalid)
    invalid = copy.deepcopy(visible)
    invalid['current']['observed_stop'] = False
    with pytest.raises(ValueError, match='queried stop'):
        validate(invalid)
