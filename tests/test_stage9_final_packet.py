import copy

import pytest

from runners.stage9 import final_packet, packet_review, queue
from runners.stage9.common import ROOT, digest, file_hash, freeze
from runners.stage9.launch import CORPORA


def plan_and_review():
    plan = {'kind': 'prelaunch_rehearsal', 'packet_policy': {'version': 1, 'case_seed': 92606,
        'case_types': packet_review.CASE_TYPES, 'inherited_checkouts': ['fixture-' + str(i) for i in range(17)]}}
    evidence = {'audit': {'job': 'ledger', 'path': 'fixture/COMPLETE.json', 'sha256': 'fixture'}}
    case = {'population': [], 'absent_reason': 'No eligible case in this discarded apparatus fixture.', 'evidence': ['audit']}
    ready = {'levels': [], 'basis': 'Not evaluated in this fixture.', 'evidence': ['audit']}
    review = {'manifest_sha256': digest(plan), 'audit_complete_sha256': 'audit-sha', 'scope': 'pilot',
        'sections': {key: {'text': 'Discarded execution fixture; no scientific interpretation.', 'evidence': ['audit']}
                     for key in packet_review.SECTIONS}, 'evidence': evidence,
        'cases': {key: copy.deepcopy(case) for key in packet_review.CASE_TYPES},
        'case_roster_review': {'owner': 'coding_operator', 'complete': True, 'basis': 'Entire fixture inspected.'},
        'readiness': {'corpora': {key: copy.deepcopy(ready) for key in CORPORA},
                      'inherited_checkouts': {key: copy.deepcopy(ready) for key in plan['packet_policy']['inherited_checkouts']}},
        'claims': [], 'next_stage_authorized': False}
    return plan, review, copy.deepcopy(evidence)


def test_absence_is_explicit_and_not_filled_with_a_fabricated_example():
    plan, review, evidence = plan_and_review()
    result = packet_review.validate(review, plan, evidence, 'audit-sha')
    assert all(row['selected'] is None and row['eligible_cases'] == row['independent_groups'] == 0
               for row in result['case_selection'].values())
    prose = packet_review.render(result)
    assert all(label in prose for label in packet_review.CASE_TYPES.values())
    assert 'No scientific result or stage closure' in prose
    assert prose.index('Why pursue') < prose.index('What the evidence establishes')
    assert not result['scientific_interpretation_automated']


def test_case_selection_is_fixed_seed_and_order_invariant_with_group_denominators():
    plan, review, evidence = plan_and_review()
    population = [{'id': str(i), 'group': 'g' + str(i // 3), 'description': 'Fixture case ' + str(i), 'evidence': ['audit']}
                  for i in range(9)]
    review['cases']['local_repair'].update(population=population, absent_reason=None)
    first = packet_review.validate(review, plan, evidence, 'audit-sha')['case_selection']['local_repair']
    population.reverse()
    second = packet_review.validate(review, plan, evidence, 'audit-sha')['case_selection']['local_repair']
    assert first == second and first['eligible_cases'] == 9 and first['independent_groups'] == 3
    expected = min(population, key=lambda r: (digest({'seed': 92606, 'type': 'local_repair', 'case': r['id']}), r['id']))
    assert first['selected'] == expected


@pytest.mark.parametrize('fault', ['policy_seed', 'policy_types', 'manifest', 'audit', 'scope', 'next_stage',
    'section', 'uncited', 'unknown_evidence', 'evidence_substitution', 'case_type', 'absence', 'duplicate_case',
    'present_and_absent', 'unreviewed_roster', 'corpus', 'checkout_substitution', 'readiness_level',
    'empty_basis', 'pilot_claim', 'unknown_disposition'])
def test_missing_or_substituted_manual_contract_refuses(fault):
    plan, review, evidence = plan_and_review()
    if fault == 'policy_seed': plan['packet_policy']['case_seed'] = True
    elif fault == 'policy_types': plan['packet_policy']['case_types'] = {}
    elif fault == 'manifest': review['manifest_sha256'] = 'changed'
    elif fault == 'audit': review['audit_complete_sha256'] = 'changed'
    elif fault == 'scope': review['scope'] = 'scientific'
    elif fault == 'next_stage': review['next_stage_authorized'] = True
    elif fault == 'section': del review['sections']['warrant']
    elif fault == 'uncited': review['sections']['maker']['evidence'] = []
    elif fault == 'unknown_evidence': review['sections']['maker']['evidence'] = ['uncommitted']
    elif fault == 'evidence_substitution': review['evidence']['audit']['sha256'] = 'changed'
    elif fault == 'case_type': del review['cases']['ambiguity']
    elif fault == 'absence': review['cases']['ambiguity']['absent_reason'] = None
    elif fault in ('duplicate_case', 'present_and_absent'):
        item = {'id': 'x', 'group': 'one', 'description': 'Fixture', 'evidence': ['audit']}
        review['cases']['local_repair']['population'] = [item, item] if fault == 'duplicate_case' else [item]
    elif fault == 'unreviewed_roster': review['case_roster_review']['complete'] = False
    elif fault == 'corpus': review['readiness']['corpora'].pop('argrewrite')
    elif fault == 'checkout_substitution': review['readiness']['inherited_checkouts']['substitute'] = review['readiness']['inherited_checkouts'].pop('fixture-0')
    elif fault == 'readiness_level': review['readiness']['corpora']['argrewrite']['levels'] = ['download_means_reproduced']
    elif fault == 'empty_basis': review['readiness']['corpora']['argrewrite']['basis'] = ''
    else: review['claims'] = [{'id': 'new', 'statement': 'Claim', 'scope': 'Fixture',
        'disposition': 'CONFIRMED WITHIN SCOPE' if fault == 'pilot_claim' else 'SUCCESS', 'evidence': ['audit']}]
    with pytest.raises(ValueError): packet_review.validate(review, plan, evidence, 'audit-sha')


@pytest.mark.parametrize('fault', ['incomplete', 'remaining', 'cards', 'attacks', 'claims'])
def test_scientific_completion_never_inferred_from_a_component_or_claim_subset(fault):
    ctx = {'audit_done': {'final_b03_complete': True}, 'ledger': {'remaining_validation': [],
        'coverage_audit': {'all_commissioned_cards_mapped': True, 'all_commissioned_attacks_mapped': True},
        'public_claims': [{'id': 'original'}]}}
    review = {'scope': 'scientific', 'claims': [{'id': 'original'}]}
    final_packet.scientific_gate(review, ctx)
    if fault == 'incomplete': ctx['audit_done']['final_b03_complete'] = False
    elif fault == 'remaining': ctx['ledger']['remaining_validation'] = ['source audit owed']
    elif fault in ('cards', 'attacks'): ctx['ledger']['coverage_audit']['all_commissioned_' + fault + '_mapped'] = False
    else: review['claims'] = []
    with pytest.raises(ValueError): final_packet.scientific_gate(review, ctx)


def test_evidence_is_a_committed_output_or_original_failure_disposition(tmp_path, monkeypatch):
    monkeypatch.setattr(final_packet, 'REPO', tmp_path)
    monkeypatch.setattr(final_packet, 'inside', lambda p: p.resolve())
    evidence = tmp_path / 'job/EVIDENCE.json'; produce = tmp_path / 'job/COMPLETE.json'
    freeze(evidence, {'actual': True}); freeze(produce, {'outputs': {'files': {'job/EVIDENCE.json': file_hash(evidence)}}})
    ctx = {'prior': {'job': {'id': 'job', 'produces': 'job/COMPLETE.json'}}, 'state': {'jobs': {'job': {'status': 'COMPLETE'}}}}
    review = {'evidence': {'checked': {'job': 'job', 'path': 'job/EVIDENCE.json', 'sha256': file_hash(evidence)}}}
    assert final_packet.evidence_map(review, ctx, tmp_path) == review['evidence']
    freeze(tmp_path / 'uncommitted.json', {'actual': True})
    review['evidence']['checked']['path'] = 'uncommitted.json'
    with pytest.raises(ValueError): final_packet.evidence_map(review, ctx, tmp_path)
    review['evidence']['checked']['path'] = 'job/EVIDENCE.json'
    review['evidence']['checked']['sha256'] = 'wrong'
    with pytest.raises(ValueError): final_packet.evidence_map(review, ctx, tmp_path)
    ctx['state']['jobs']['job'] = {'status': 'FAILED', 'disposition_path': 'DISPOSITION.json'}
    freeze(tmp_path / 'DISPOSITION.json', {'reason': 'original failure'})
    review['evidence']['checked'].update(path='DISPOSITION.json', sha256=file_hash(tmp_path / 'DISPOSITION.json'))
    assert final_packet.evidence_map(review, ctx, tmp_path)
    review['evidence']['checked'].update(path='job/EVIDENCE.json', sha256=file_hash(evidence))
    with pytest.raises(ValueError): final_packet.evidence_map(review, ctx, tmp_path)


def queue_plan():
    from tests.test_stage9_confirmation_review import plan as base
    p = base(); p['packet_policy'] = plan_and_review()[0]['packet_policy']
    job = copy.deepcopy(p['jobs'][-1]); job.update(id='packet', module=final_packet.MODULE,
        after=['source', 'freeze'], produces=str(ROOT / 'private/packet-fixture/COMPLETE.json'),
        arguments=['--review', str(ROOT / 'private/packet-fixture/REVIEW.json')])
    p['jobs'].append(job); p['sources']['files']['runners/stage9/final_packet.py'] = 'fixture'
    return p


def test_final_packet_missing_review_is_a_future_manual_input():
    p = queue_plan()
    assert queue.validate_manifest(p)
    assert queue.manual_review_path(p['jobs'][-1]) == ROOT / 'private/packet-fixture/REVIEW.json'


@pytest.mark.parametrize('fault', ['omitted_closure', 'later_work', 'gpu', 'missing_policy'])
def test_packet_cannot_precede_work_or_avoid_manual_review(fault):
    p = queue_plan()
    if fault == 'omitted_closure': p['jobs'][-1]['after'] = ['source']
    elif fault == 'later_work':
        later = copy.deepcopy(p['jobs'][0]); later.update(id='later', produces=str(ROOT / 'private/later/COMPLETE.json'), role='closure')
        p['jobs'].append(later)
    elif fault == 'gpu': p['jobs'][-1]['resource'] = 'gpu'
    else: del p['packet_policy']
    with pytest.raises(ValueError): queue.validate_manifest(p)


def test_context_tolerates_active_heartbeat_but_retains_changed_prior_state(tmp_path, monkeypatch):
    """Regression for the actual packet-v1 failure during scheduler heartbeats."""
    monkeypatch.setattr(final_packet, 'REPO', tmp_path)
    for name in ('validate_manifest', 'verify_committed'):
        monkeypatch.setattr(final_packet, name, lambda *a: None)
    monkeypatch.setattr(final_packet, 'verify_execution', lambda *a: {'loaded_project_sources': {'fixture': 'sha'}})
    ledger = {'saved': True}; monkeypatch.setattr(final_packet, 'snapshot', lambda *a: ledger)
    directory = tmp_path/'packet'; manifest = tmp_path/'PLAN.json'; q = tmp_path/'queue'; review = tmp_path/'REVIEW.json'
    audit = {'id': 'ledger', 'module': 'runners.stage9.closure_ledger', 'produces': 'audit/COMPLETE.json'}
    packet = {'id': 'packet', 'module': final_packet.MODULE, 'produces': 'packet/COMPLETE.json',
        'arguments': ['--output', str(directory), '--manifest', str(manifest), '--queue', str(q), '--review', str(review), '--scope', 'pilot']}
    plan = {'jobs': [audit, packet]}; freeze(manifest, plan); freeze(q/'MANIFEST.json', plan)
    state = {'manifest_sha256': digest(plan), 'jobs': {'ledger': {'status': 'COMPLETE'}, 'packet': {'status': 'RUNNING'}},
        'attempts': [{'job': 'packet', 'last_heartbeat': 10.0}]}
    from runners.stage9.common import write
    write(q/'STATUS.json', state)
    for name, value in {'COMPLETE.json': {}, 'LEDGER.json': ledger, 'fresh-process/CONFIG.json': {'cell_identity': 'fixture'},
        'fresh-process/RESULT.json': ledger, 'fresh-process/READY.json': {'process': {'pid': 1}},
        'fresh-process/EXECUTION.json': {'fixture': True}}.items(): freeze(tmp_path/'audit'/name, value)
    freeze(tmp_path/'audit/REPRODUCTION.json', {'ledger_sha256': digest(ledger),
        'execution_sha256': file_hash(tmp_path/'audit/fresh-process/EXECUTION.json'), 'fresh_process': {'pid': 1}, 'loaded_source_files': 1})
    args = (manifest, q, digest({'manifest_sha256': digest(plan), 'job': packet}), directory, review, 'pilot')
    before = final_packet.context(*args)
    state['attempts'][0]['last_heartbeat'] = 20.0; write(q/'STATUS.json', state)
    assert final_packet.context(*args) == before
    state['jobs']['ledger']['attempt'] = 2; write(q/'STATUS.json', state)
    assert final_packet.context(*args) != before
