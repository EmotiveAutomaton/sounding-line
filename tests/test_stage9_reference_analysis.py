"""Known-answer paired means, complete seed retention and producer binding guards."""
import copy
import pytest
from runners.stage9 import common, reference_analysis as subject
from runners.stage9.common import closure, digest, file_hash, read, write
from runners.stage9.training_jobs import FITS


def fixture(effect=0.):
    def rows(delta):
        return [{'unit': str(i), 'source_unit': str(i), 'domain': 'essay' if i < 96 else 'workshop_doc',
                 'law': 'original' if i % 2 else 'expanded', 'purpose': 'teach', 'target_type': 'write',
                 'rival_log_score': -4., 'reader_log_score': -3. + delta, 'valid': True} for i in range(192)]
    fits = [{'family': f, 'recipe': r, 'seed': s, 'status': 'COMPLETE', 'instrument_accepted': True,
             'choice_rows': rows(effect if f == 'qwen' else -effect), 'comparison_contract': {'same': True}}
            for f, r, s in FITS]
    refs = [{'family': f, 'package_kind': k, 'status': 'COMPLETE', 'instrument_accepted': True,
             'choice_rows': rows(0.), 'comparison_contract': {'same': True}} for f, k in subject.REFERENCES]
    return fits, refs


def overall(result, family='qwen', comparison='both_mixed-vs-base'):
    return result['families'][family]['comparisons'][comparison]['groups']['overall']


def test_equal_forecasts_and_opposite_family_effects():
    null = subject.summarize(*fixture(), 'scientific', draws=100)
    for family in null['families'].values():
        for result in family['comparisons'].values():
            assert result['groups']['overall']['estimate']['mean'] == 0
            assert result['reference_package_count'] == 1 and result['seed_count'] == 3
    fits, refs = fixture(.2)
    result = subject.summarize(fits, refs, 'scientific', draws=100)
    assert overall(result)['estimate']['mean'] == pytest.approx(.2)
    assert overall(result, 'smollm')['estimate']['mean'] == pytest.approx(-.2)
    assert subject.summarize(list(reversed(fits)), list(reversed(refs)), 'scientific', draws=100)['families'] == result['families']
    assert not result['scientific_admission']


def test_one_lucky_seed_and_single_fixed_reference():
    fits, refs = fixture()
    for f in fits:
        if f['family'] == 'qwen' and f['recipe'] == 'both_mixed':
            for row in f['choice_rows']:
                row['reader_log_score'] += 1. if f['seed'] == 9001 else -.5
    result = overall(subject.summarize(fits, refs, 'scientific', draws=100))
    assert result['estimate']['mean'] == 0 and result['estimate']['second_groups'] == 3
    assert result['per_seed']['9001']['mean'] == 1. and result['per_seed']['9002']['mean'] == -.5
    assert result['assigned'] == 576


@pytest.mark.parametrize('side', ['fit', 'reference'])
def test_failed_source_stays_and_other_comparisons_continue(side):
    fits, refs = fixture(.2)
    target = fits[0] if side == 'fit' else refs[0]
    target.update(status='FAILED', reason='retained original failure')
    result = subject.summarize(fits, refs, 'scientific', draws=100)
    affected = fits[0]['recipe'] + '-vs-base'
    assert result['families']['qwen']['comparisons'][affected]['disposition'] == 'NOT RUN WITH REASON'
    assert overall(result, 'smollm')['estimate']['mean'] == pytest.approx(-.2)
    assert len(result['fits']) == 24 and len(result['references']) == 4


@pytest.mark.parametrize('mutation', ['missing_fit', 'missing_reference', 'repeated_reference', 'fake_reference_seed',
                                     'running', 'different_units', 'duplicate_units', 'question', 'rival', 'contract'])
def test_incomplete_or_mismatched_comparison_refuses(mutation):
    fits, refs = fixture()
    if mutation == 'missing_fit': fits.pop()
    elif mutation == 'missing_reference': refs.pop()
    elif mutation == 'repeated_reference': refs[-1] = copy.deepcopy(refs[0])
    elif mutation == 'fake_reference_seed': refs[0]['seed'] = 9001
    elif mutation == 'running': fits[0]['status'] = 'RUNNING'
    elif mutation == 'different_units': refs[0]['choice_rows'][0]['source_unit'] = 'other'
    elif mutation == 'duplicate_units': refs[0]['choice_rows'][1]['source_unit'] = '0'
    elif mutation == 'question': refs[0]['choice_rows'][0]['unit'] = 'other'
    elif mutation == 'rival': refs[0]['choice_rows'][0]['rival_log_score'] = -9.
    elif mutation == 'contract': refs[0]['comparison_contract'] = {'same': False}
    with pytest.raises(ValueError): subject.summarize(fits, refs, 'scientific', draws=100)


def test_calibration_invalidity_nonfinite_scores_and_repeated_questions():
    fits, refs = fixture(.2); refs[0]['instrument_accepted'] = False
    result = overall(subject.summarize(fits, refs, 'scientific', draws=100))
    assert result['estimate'] is None and result['invalid'] == 576 and result['disposition'] == 'IMPLEMENTATION INVALID'
    fits, refs = fixture(.2); refs[0]['choice_rows'][0]['reader_log_score'] = {'extended_real': 'negative_infinity'}
    result = overall(subject.summarize(fits, refs, 'scientific', draws=100))
    assert result['estimate']['finite_estimate'] is False and result['estimate']['excluded_targets'] == 0
    assert result['estimate']['n_targets'] == 576
    fits, refs = fixture(.2)
    for member in fits + refs:
        for row in member['choice_rows']: row['unit'] = 'same-public-question'
    result = overall(subject.summarize(fits, refs, 'scientific', draws=100))
    assert result['estimate']['n_units'] == 1 and result['estimate']['ci'] is None


def profile_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(common, 'REPO', tmp_path); monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'inside', lambda p: tmp_path / p)
    neural, choice, calibration = [tmp_path / name for name in ('neural', 'choice', 'calibration')]
    package = {'actual': 'package'}
    ni = {'family': 'qwen', 'package_kind': 'base', 'adapter_sha256': 'base-no-adapter',
          'operation': 'genuine_choice', 'scope': 'pilot', 'training_complete_sha256': 'reference', 'cases_complete_sha256': 'cases'}
    write(neural / 'IDENTITY.json', ni); write(neural / 'PACKAGE.json', package)
    nd = {'identity_sha256': digest(ni), 'execution_complete': True, 'outputs': closure([neural / 'IDENTITY.json', neural / 'PACKAGE.json'])}
    write(neural / 'COMPLETE.json', nd)
    ci = {'operation': 'choice-profile-v1', 'scope': 'pilot', 'package': package,
          'inputs': {'neural': {'path': str(neural), 'complete_sha256': file_hash(neural / 'COMPLETE.json')},
                     'baseline': {'same': 'baseline'}, 'development': {'same': 'development'}, 'selection': {'same': 'selection'}}}
    write(choice / 'IDENTITY.json', ci)
    write(choice / 'PROFILE.json', {'role': 'pilot', 'selection_only': False, 'assigned_units': 2})
    write(choice / 'PAIRED_ROWS.json', [{'saved': True}])
    write(calibration / 'IDENTITY.json', {'operation': 'actual-package-calibration-consumer-v1', 'scope': 'pilot', 'package': package})
    write(calibration / 'DECISION.json', {'instrument_accepted': True})
    seen = []
    def completed(plan, queue, status, key, module):
        seen.append((key, module))
        return {'choice': choice, 'calibration': calibration}[key], {'status': 'COMPLETE'}
    monkeypatch.setattr(subject, 'complete_job', completed)
    expected = {k: ni[k] for k in ('family', 'package_kind', 'adapter_sha256', 'training_complete_sha256')}
    assignment = {'choice_job': 'choice', 'calibration_job': 'calibration'}
    return neural, choice, calibration, expected, assignment, seen


def test_profile_uses_choice_and_own_calibration_without_broad_dependency(tmp_path, monkeypatch):
    neural, choice, calibration, expected, assignment, seen = profile_fixture(tmp_path, monkeypatch)
    result = subject.profile({}, tmp_path, {}, assignment, 'pilot', expected)
    assert result['choice_rows'] == [{'saved': True}] and result['instrument_accepted']
    assert [key for key, _ in seen] == ['choice', 'calibration']


@pytest.mark.parametrize('mutation', ['family', 'package_kind', 'adapter_sha256', 'training_complete_sha256',
                                     'neural_bytes', 'calibration_package', 'calibration_scope', 'development_role', 'choice_scope'])
def test_profile_rejects_wrong_package_or_changed_producer(tmp_path, monkeypatch, mutation):
    neural, choice, calibration, expected, assignment, seen = profile_fixture(tmp_path, monkeypatch)
    if mutation in expected: expected[mutation] = 'different'
    elif mutation == 'neural_bytes': write(neural / 'PACKAGE.json', {'changed': True})
    elif mutation in ('calibration_package', 'calibration_scope'):
        p = calibration / 'IDENTITY.json'; value = read(p)
        value['package' if mutation == 'calibration_package' else 'scope'] = 'changed'; write(p, value)
    elif mutation == 'choice_scope':
        p = choice / 'IDENTITY.json'; value = read(p); value['scope'] = 'scientific'; write(p, value)
    else: write(choice / 'PROFILE.json', {'role': 'development', 'selection_only': True, 'assigned_units': 2})
    with pytest.raises(ValueError): subject.profile({}, tmp_path, {}, assignment, 'pilot', expected)
