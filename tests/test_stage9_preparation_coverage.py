"""Preparation evidence cannot invent execution or hide unfinished obligations."""
import copy

import pytest

from runners.stage9 import closure_coverage as subject, launch
from runners.stage9.common import closure, digest, file_hash
from tests.test_stage9_closure_coverage import fixture


def prepared(tmp_path, monkeypatch, *, science=False, unresolved=False):
    plan, queue, prior, states, seal = fixture(tmp_path, monkeypatch, science=science)
    # Deliberately not JSON: validation must hash evidence without opening payloads.
    path = tmp_path / 'original-evidence.bin'; path.write_bytes(b'original\xff\x00bytes')
    review = plan['final_coverage']; review['version'] = 2
    review['cards']['I04'] = []
    requirements = {name: {'status': 'verified', 'basis': 'Independently reviewed fixture, within its original scope.',
        'evidence': [{'path': path.name, 'sha256': file_hash(path)}]}
        for name in subject.PREPARATION_REQUIREMENTS['I04']}
    if unresolved:
        requirements['attribution_scope_and_lineage'].update(status='unresolved',
            basis='The distribution fixture does not establish the attribution instrument.')
    review['preparations'] = {'I04': {'source_sha256': plan['sources']['sha256'],
        'jobs_sha256': digest(plan['jobs']), 'requirements': requirements,
        'limitations': 'Constructed preparation evidence, no scientific execution or human result.'}}
    seal()
    return plan, queue, prior, states, seal, path


def test_preparation_is_visible_without_becoming_a_completed_cell(tmp_path, monkeypatch):
    plan, queue, prior, *_ = prepared(tmp_path, monkeypatch, science=True)
    before = closure([tmp_path]); result = subject.inspect(plan, queue, prior)
    assert closure([tmp_path]) == before
    assert result['scheduled_cells'] == 5 and result['terminal_cells'] == 3
    row = result['cards']['I04']
    assert row['jobs'] == {} and row['terminal_counts'] == {} and row['closure_tail'] == []
    assert row['explicit_not_run_studies'] == 0
    assert len(row['preparation']['verified_requirements']) == 4
    assert not row['preparation']['unresolved_requirements']
    assert not row['preparation']['scientific_execution'] and not result['scientific_admission']
    assert result['cards']['I01']['terminal_counts'] == {'COMPLETE': 1, 'FAILED': 1, 'NOT_RUN': 1}


def test_rehearsal_retains_preparation_gap_and_science_refuses_it(tmp_path, monkeypatch):
    plan, queue, prior, *_ = prepared(tmp_path, monkeypatch, unresolved=True)
    result = subject.inspect(plan, queue, prior)
    assert result['cards']['I04']['preparation']['unresolved_requirements'] == ['attribution_scope_and_lineage']
    plan['kind'] = 'science'
    # Supply the complete scientific map so inventory omissions cannot mask the gap.
    plan['final_coverage']['cards'].update({card: ['work'] for card in subject.CARDS - set(plan['final_coverage']['cards'])})
    plan['final_coverage']['attacks'].update({key: {'jobs': [], 'null_expected': 'fixture',
        'alternative_expected': 'fixture', 'not_applicable_reason': 'No applicable condition in this unit fixture.'}
        for key in subject.ATTACKS - set(plan['final_coverage']['attacks'])})
    with pytest.raises(ValueError, match='scientific preparation remains unresolved: I04'):
        subject.validate_mapping(plan)


def test_launch_reaches_the_unresolved_preparation_guard_before_acceptance(tmp_path, monkeypatch):
    from runners.stage9 import queue as scheduler, closure_raw
    plan, *_ = prepared(tmp_path, monkeypatch, science=True, unresolved=True)
    monkeypatch.setattr(scheduler, 'validate_manifest', lambda p: None)
    monkeypatch.setattr(scheduler, 'verify_sources', lambda p: None)
    monkeypatch.setattr(closure_raw, 'validate_scientific_reviews', lambda *a: None)
    monkeypatch.setattr(launch, 'checked', lambda p: p)
    evidence = {key: {} for key in launch.REQUIRED}
    evidence['manual_review'] = {'manifest_sha256': digest(plan),
        'jobs': {j['id']: {} for j in plan['jobs']}, 'cards': plan['final_coverage']['cards']}
    with pytest.raises(ValueError, match='scientific preparation remains unresolved: I04'):
        launch.validate(plan, evidence)


@pytest.mark.parametrize('fault', ['source', 'jobs', 'missing_requirement', 'extra_requirement', 'status',
    'basis', 'limits', 'empty_evidence', 'changed_evidence', 'duplicate_evidence', 'missing_file',
    'checksum', 'unknown_pointer_field', 'unknown_review_field', 'scheduled_produce',
    'absolute_path', 'parent_path', 'empty_preparations', 'unsupported_card', 'unmapped_cell', 'closure_substitute'])
def test_unbound_missing_or_false_preparation_coverage_refuses(tmp_path, monkeypatch, fault):
    plan, *_rest, path = prepared(tmp_path, monkeypatch, science=True)
    review = plan['final_coverage']; row = review['preparations']['I04']
    req = row['requirements']['attribution_scope_and_lineage']; pointer = req['evidence'][0]
    if fault == 'source': row['source_sha256'] = '0' * 64
    elif fault == 'jobs': row['jobs_sha256'] = '0' * 64
    elif fault == 'missing_requirement': row['requirements'].pop('attribution_scope_and_lineage')
    elif fault == 'extra_requirement': row['requirements']['invented'] = copy.deepcopy(req)
    elif fault == 'status': req['status'] = 'accepted'
    elif fault == 'basis': req['basis'] = ' '
    elif fault == 'limits': row['limitations'] = ''
    elif fault == 'empty_evidence': req['evidence'] = []
    elif fault == 'changed_evidence': path.write_bytes(b'changed')
    elif fault == 'duplicate_evidence': req['evidence'].append(dict(pointer))
    elif fault == 'missing_file': pointer['path'] = 'absent.bin'
    elif fault == 'checksum': pointer['sha256'] = True
    elif fault == 'unknown_pointer_field': pointer['accepted'] = True
    elif fault == 'unknown_review_field': row['accepted'] = True
    elif fault == 'scheduled_produce':
        pointer.update(path='work/COMPLETE.json', sha256=file_hash(tmp_path / 'work/COMPLETE.json'))
    elif fault == 'absolute_path': pointer['path'] = str(path)
    elif fault == 'parent_path': pointer['path'] = 'a/../' + path.name
    elif fault == 'empty_preparations': review['preparations'] = {}
    elif fault == 'unsupported_card': review['preparations'] = {'C01': row}
    elif fault == 'unmapped_cell': review['cards']['I01'].remove('failed')
    elif fault == 'closure_substitute': review['cards']['I04'] = ['audit']
    with pytest.raises(ValueError): subject.validate_mapping(plan)


def test_final_inspection_rechecks_preparation_bytes_after_mapping_validation(tmp_path, monkeypatch):
    plan, queue, prior, *_, path = prepared(tmp_path, monkeypatch)
    subject.validate_mapping(plan)
    path.write_bytes(b'changed after initial validation')
    with pytest.raises(ValueError, match='changed'):
        subject.inspect(plan, queue, prior)


def test_preparation_cannot_be_smuggled_into_historical_version(tmp_path, monkeypatch):
    plan, *_ = prepared(tmp_path, monkeypatch)
    plan['final_coverage']['version'] = 1
    with pytest.raises(ValueError, match='explicit final coverage map'):
        subject.validate_mapping(plan)


def test_aliases_cannot_count_one_evidence_file_twice_in_an_obligation(tmp_path, monkeypatch):
    plan, *_rest, path = prepared(tmp_path, monkeypatch)
    req = plan['final_coverage']['preparations']['I04']['requirements']['attribution_scope_and_lineage']
    req['evidence'].append({'path': './' + path.name, 'sha256': file_hash(path)})
    with pytest.raises(ValueError, match='duplicated'):
        subject.validate_mapping(plan)
