"""Known acceptance/refusal cases for the adopted execution-scope boundary."""
import copy
import time

import pytest

from runners.stage9 import common, launch, tranche, closure_coverage, packet_review
from runners.stage9 import queue


@pytest.fixture
def complete_branch(tmp_path, monkeypatch):
    # These constructed receipts test validation, not execution or scientific eligibility.
    for module in (common, launch, tranche, closure_coverage, queue):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(launch, 'ROOT', tmp_path)
    monkeypatch.setattr(tranche, 'ROOT', tmp_path)
    def save(name, value):
        path = tmp_path / name; common.write(path, value)
        return {'path': name, 'sha256': common.file_hash(path)}
    paths = []
    for module in ('series_jobs', 'closure_probe', 'closure_ledger', 'final_packet',
                   'source_bootstrap', 'common', 'process_identity'):
        path = tmp_path / ('runners/stage9/' + module + '.py')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text('# known fixture\n')
        paths.append(path)
    source = common.closure(paths)
    now = time.time(); start = now - 100; horizon = now + 3600
    def job(key, module, after=(), args=()):
        return {'id': key, 'module': 'runners.stage9.' + module, 'arguments': list(args),
                'after': list(after), 'requires': [], 'resource': 'cpu', 'role': 'work',
                'produces': str((tmp_path / ('produces/' + key + '.json')).relative_to(common.REPO)),
                'estimated_gpu_seconds': 0.}
    probe = job('probe', 'closure_probe', args=['--runtime', 'kernel'])
    work = job('work', 'series_jobs', ['probe'], ['--per-cohort', '2'])
    work['requires'] = [{'job': 'probe', 'field': ['isolation_probe_verified'], 'equals': True}]
    other = job('unrelated', 'series_jobs')
    audit = job('audit', 'closure_ledger', ['probe', 'work', 'unrelated'])
    packet = job('packet', 'final_packet', ['probe', 'work', 'unrelated', 'audit'],
                 ['--review', 'review.json'])
    for j in (audit, packet): j.update(role='closure', allow_failed_dependencies=True)
    original = [probe, work, other, audit, packet]
    chosen = copy.deepcopy([probe, work, audit, packet])
    chosen[2]['after'].remove('unrelated'); chosen[3]['after'].remove('unrelated')
    roster = {'I06': ['work'], 'C01': ['unrelated'], 'B03': ['probe', 'audit'], 'B04': ['packet']}
    adoption = {'policy': tranche.POLICY, 'adopted': True, 'authority': 'curator',
                'adopted_at': 'fixture', 'gpu_cap_hours': 92, 'horizon_extended': False,
                'campaign_start': start, 'horizon_epoch': horizon,
                'addendum': save('addendum.json', {'fixture': True})}
    cards = {}
    for card in launch.CARDS:
        old = roster.get(card, []); keep = [k for k in old if k != 'unrelated']; deferred = [k for k in old if k == 'unrelated']
        status = 'selected' if keep else 'deferred'
        if card in ('I01', 'I05'): status = 'preparation'
        cards[card] = {'selected': keep, 'deferred': deferred, 'status': status,
                       'reason': 'known fixture scope', 'deferral_kind': 'budget' if status == 'deferred' else None}
    scope = {'policy': tranche.POLICY, 'adoption': save('adoption.json', adoption),
             'original_jobs': save('original.json', original), 'original_cards': save('cards.json', roster),
             'selected_jobs': [j['id'] for j in chosen], 'deferred_jobs': ['unrelated'], 'cards': cards,
             'manifest_path': 'plan.json', 'queue_root': 'queue', 'review_path': 'review.json',
             'required_split_roles': ['pilot', 'development', 'discovery'],
             'package_kinds': {}, 'source_corpora': [],
             'permitted_claims': {'comparison': {'scope': 'package_specific_discovery',
                                               'ceiling': 'constructed validation only', 'jobs': ['work']}}}
    plan = {'kind': 'science', 'campaign_start': start, 'horizon_epoch': horizon,
            'sources': source, 'jobs': chosen, 'execution_scope': scope,
            'packet_policy': {'version': 1, 'case_seed': 9, 'case_types': packet_review.CASE_TYPES,
                              'inherited_checkouts': ['checkout-' + str(i) for i in range(17)]}}
    checked_input = save('known-input.json', {'known_positive': 1, 'known_negative': 0})
    preparations = {}
    for card in ('I01', 'I05'):
        preparations[card] = {'source_sha256': source['sha256'], 'jobs_sha256': common.digest(chosen),
                             'limitations': 'constructed validation only',
                             'requirements': {k: {'status': 'verified', 'basis': 'known fixture', 'evidence': [checked_input]}
                                              for k in closure_coverage.PREPARATION_REQUIREMENTS[card]}}
    plan['final_coverage'] = {'version': 2, 'cards': {c: r['selected'] for c, r in cards.items()},
                              'preparations': preparations,
                              'attacks': {f'X{i:02d}': {'jobs': ['work'], 'null_expected': 'refuse',
                                  'alternative_expected': 'accept', 'not_applicable_reason': None} for i in range(1, 13)}}
    old_plan = {k: v for k, v in plan.items() if k not in ('execution_scope', 'final_coverage')}
    old_plan['kind'] = 'prelaunch_rehearsal'
    old_pointer = save('rehearsal.json', old_plan)
    save('rehearsal-queue/MANIFEST.json', old_plan)
    save('rehearsal-queue/COMPLETE.json', {'jobs': {j['id']: {'status': 'COMPLETE'} for j in chosen}})
    mapping = {}
    for j in chosen:
        cell = common.digest({'manifest_sha256': common.digest(old_plan), 'job': j})
        output = save(j['produces'], {'known_fixture': True})
        execution = save('rehearsal-queue/' + j['id'] + '-execution.json', {
            'cell_identity': cell, 'returncode': 0, 'error': None, 'loaded_project_sources': source['files']})
        save('rehearsal-queue/commits/' + j['id'] + '.json', {'manifest_sha256': common.digest(old_plan),
            'cell_identity': cell, 'produce_sha256': output['sha256'],
            'execution_path': j['id'] + '-execution.json', 'execution_sha256': execution['sha256']})
        mapping[j['id']] = {'plan': old_pointer, 'job': j['id'], 'queue_root': 'rehearsal-queue',
                             'compatibility': {'changes': {}, 'checks': [], 'basis': 'identical fixture source'}}
    save('CAMPAIGN.json', {'started_epoch': start, 'horizon_epoch': horizon})
    design = {k: 'explicit known-fixture expectation' for k in ('hypothesis', 'method', 'null_expectation',
        'alternative_expectation', 'failure_direction', 'independent_unit', 'evidence_view', 'strongest_rival', 'exhaustive_bands')}
    seconds = save('timing.json', {'seconds': 1.})
    forecasts = {j['id']: {'measured_seconds': 1., 'measured_units': 1, 'planned_units': 1,
        'overhead_seconds': 0., 'multiplier': 1., 'forecast_seconds': 1., 'pilot': seconds,
        'measured_field': ['seconds']} for j in chosen}
    checks = {k: True for k in ('all_actual_loaded_sources_match', 'all_prior_unit_bytes_unchanged',
        'campaign_clock_unchanged', 'competing_writer_refused', 'complete_192_units', 'native_kill_observed',
        'same_cell_identity', 'same_manifest', 'source_omission_rejected')}
    objects = {
        'manual_review': {'manifest_sha256': common.digest(plan), 'jobs': {j['id']: design | {
            'read_source_sha256': source['files'][j['module'].replace('.', '/') + '.py']} for j in chosen},
            'cards': plan['final_coverage']['cards'], 'training_fits': [], 'owner_session_id': 'fixture-owner'},
        'sources': {'corpora': {}, 'inherited_checkouts': plan['packet_policy']['inherited_checkouts']},
        'fixtures': {'positive_cases': ['positive'], 'negative_cases': ['negative'], 'all_expected_answers': True,
                     'attacks': {f'X{i:02d}': {'null_expected': 'refuse', 'alternative_expected': 'accept',
                                                'executed_receipts': [checked_input]} for i in range(1, 13)}},
        'packages': {'families': {}},
        'splits': {'assignments': [{'role': r, 'group': r, 'content_sha256': common.digest(r)}
                                   for r in ('pilot', 'development', 'discovery')],
                   'cross_source_checks': [checked_input], 'reserve_truth_opened': False},
        'wake': {'probe_id': 'S9-WAKE-20260906-01', 'delivered': True, 'recorded_at': 'fixture',
                  'owner_session_id': 'fixture-owner'},
        'interruption': {'checks': checks, 'preserved_completed_units': 1, 'source': save('source.json', source),
                         'compatibility': {'changes': {}, 'checks': [], 'basis': 'identical fixture source'}},
        'dress_rehearsal': {'job_mapping': mapping},
        'forecast': {'jobs': forecasts, 'preparation_gpu_reserved_seconds': 85 * 3600,
                     'scheduling': 'serial', 'remaining_wall_seconds': 100., 'forecast_at': now,
                     'initial_queue_seconds': 4., 'underfill_reason': 'complete bounded fixture'}}
    def evidence(): return {k: save('evidence-' + k + '.json', v) for k, v in objects.items()}
    return plan, objects, evidence, save


def test_complete_branch_accepts_with_unrelated_branch_deferred(complete_branch):
    plan, _, evidence, _ = complete_branch
    result = launch.validate(plan, evidence())
    assert result['acceptance_scope'] == 'tranche' and result['full_stage_accepted'] is False
    cert = result | {'version': 2, 'accepted': True}
    assert launch.verify_certificate(plan, cert)
    for key, value in (('full_stage_accepted', True), ('acceptance_scope', 'full'), ('permitted_claims', {})):
        with pytest.raises(ValueError, match='scope or claims'):
            launch.verify_certificate(plan, cert | {key: value})


def test_discovery_closure_explicitly_omits_unselected_confirmation(complete_branch, tmp_path):
    from runners.stage9.closure_ledger import calculations
    plan, _, _, _ = complete_branch
    plan['final_calculations'] = []
    assert calculations(plan, tmp_path, {}) == {}
    plan['execution_scope']['permitted_claims']['comparison']['scope'] = 'confirmation'
    with pytest.raises(ValueError, match='claim ceiling'):
        calculations(plan, tmp_path, {})


@pytest.mark.parametrize('defect', ['leakage', 'source', 'prerequisite', 'recovery', 'reserve', 'preparation', 'sample', 'deferred'])
def test_selected_observation_still_refuses_missing_safeguards(complete_branch, defect):
    plan, objects, evidence, _ = complete_branch
    if defect == 'leakage': objects['fixtures']['attacks']['X02'] = {'status': 'inapplicable', 'reason': 'deferred'}
    elif defect == 'source': plan['sources']['files'][next(iter(plan['sources']['files']))] = '0' * 64
    elif defect == 'prerequisite': plan['jobs'][1]['requires'] = []
    elif defect == 'recovery': objects['interruption']['checks']['competing_writer_refused'] = False
    elif defect == 'reserve': objects['splits']['reserve_truth_opened'] = True
    elif defect == 'preparation': plan['execution_scope']['cards']['I01'].update(status='deferred', deferral_kind='budget')
    elif defect == 'sample': plan['jobs'][1]['arguments'] = ['--per-cohort', '1']
    else: plan['execution_scope']['deferred_jobs'] = []
    objects['manual_review']['manifest_sha256'] = common.digest(plan)
    with pytest.raises(ValueError): launch.validate(plan, evidence())


@pytest.mark.parametrize('defect', ['cap', 'horizon', 'clock', 'overlap', 'stale'])
def test_adoption_never_extends_resources(complete_branch, defect):
    plan, objects, evidence, _ = complete_branch
    if defect == 'cap': objects['forecast']['preparation_gpu_reserved_seconds'] = 92 * 3600 + 1
    elif defect == 'horizon': objects['forecast']['remaining_wall_seconds'] = 7200
    elif defect == 'clock': plan['campaign_start'] -= 3600
    elif defect == 'overlap': objects['forecast']['scheduling'] = 'overlapped'
    else: objects['forecast']['forecast_at'] = time.time() + 86400
    objects['manual_review']['manifest_sha256'] = common.digest(plan)
    with pytest.raises(ValueError): launch.validate(plan, evidence())


def test_full_stage_retains_full_grid_requirement(complete_branch):
    plan, objects, evidence, _ = complete_branch
    plan.pop('execution_scope'); objects['manual_review']['manifest_sha256'] = common.digest(plan)
    with pytest.raises(ValueError): launch.validate(plan, evidence())


def test_packet_cannot_promote_tranche_or_omit_its_comparator(complete_branch):
    plan, _, _, _ = complete_branch
    review = {'scope': 'scientific_tranche', 'full_stage_complete': False,
              'execution_scope_sha256': common.digest(plan['execution_scope']), 'claims': [],
              'evidence': {'work': {'job': 'work'}}}
    tranche.packet_claims(review, plan)
    for changed in (review | {'full_stage_complete': True}, review | {'scope': 'scientific'},
                    review | {'claims': [{'id': 'factorial', 'scope': 'package_specific_discovery', 'evidence': ['work']}]},
                    review | {'claims': [{'id': 'comparison', 'scope': 'package_specific_discovery', 'evidence': []}]}):
        with pytest.raises(ValueError): tranche.packet_claims(changed, plan)


def test_recipe_consumers_cannot_use_partial_grid(complete_branch):
    plan, _, _, save = complete_branch
    original = common.read(tranche.pointer(plan['execution_scope']['original_jobs']))
    original[1]['module'] = 'runners.stage9.recipe_selection'
    plan['jobs'][1]['module'] = original[1]['module']
    plan['execution_scope']['original_jobs'] = save('recipe-original.json', original)
    with pytest.raises(ValueError, match='recipe selection'): tranche.scope(plan)


def test_reused_receipt_needs_exact_changed_source_review(complete_branch):
    plan, objects, evidence, _ = complete_branch
    objects['dress_rehearsal']['job_mapping']['work']['compatibility']['changes'] = {'invented.py': {'old': 'a', 'current': 'b'}}
    with pytest.raises(ValueError, match='source difference'): launch.validate(plan, evidence())


def test_current_writer_preserves_completed_bytes_and_refuses_competitor(tmp_path):
    directory = tmp_path / 'one-writer'
    with queue.writer(directory):
        common.freeze(directory / 'COMPLETE.json', {'unit': 192, 'complete': True})
        original = (directory / 'COMPLETE.json').read_bytes()
        with pytest.raises(RuntimeError, match='another writer'):
            with queue.writer(directory):
                pytest.fail('competing writer entered')
    with queue.writer(directory):
        common.freeze(directory / 'COMPLETE.json', {'unit': 192, 'complete': True})
    assert (directory / 'COMPLETE.json').read_bytes() == original


def test_tranche_final_integrity_retains_missing_capsule_or_service_failure(complete_branch):
    plan, _, _, _ = complete_branch
    ledger = {'coverage_audit': {'status': 'RECONCILED',
        'execution_scope_sha256': common.digest(plan['execution_scope']),
        'all_commissioned_cards_mapped': True, 'all_commissioned_attacks_mapped': True},
        'capsule_audits': {'jobs': {}}, 'resident_service_audits': {'jobs': {}}}
    assert tranche.final_integrity(plan, ledger)['full_stage_complete'] is False
    missing = copy.deepcopy(ledger)
    missing['capsule_audits']['jobs']['work'] = {'status': 'INSPECTED',
        'storage': {'uncached_capsules': ['unresolved']}, 'calls': []}
    with pytest.raises(ValueError, match='capsule provenance'): tranche.final_integrity(plan, missing)
    missing = copy.deepcopy(ledger)
    missing['resident_service_audits']['jobs']['work'] = {'all_recorded_services_reconciled': False}
    with pytest.raises(ValueError, match='service provenance'): tranche.final_integrity(plan, missing)
