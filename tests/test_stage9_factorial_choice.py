from pathlib import Path

import pytest

from runners.stage9 import factorial_choice as subject
from runners.stage9.common import write
from runners.stage9.training_jobs import FITS
from tests.test_stage9_factorial_analysis import fixture, estimate


def test_known_answer_estimand_is_unchanged_without_generation():
    rows = fixture(.2, .1, .3, True)
    for row in rows: del row['generation']
    result = subject.summarize(rows, 'scientific', draws=100)
    for family, sign in [('qwen', 1), ('smollm', -1)]:
        assert estimate(result, family, 'breadth_expert')['mean'] == pytest.approx(sign * .2)
        assert estimate(result, family, 'exposure_original')['mean'] == pytest.approx(sign * .1)
        assert estimate(result, family, 'interaction')['mean'] == pytest.approx(sign * .3)
        assert len(result['families'][family]['all_seed_profiles']) == 12
        assert result['families'][family]['seed_count'] == 3
    assert result['scientific_admission'] is False


def test_null_failed_fit_and_bad_calibration_keep_original_bands():
    rows = fixture()
    for row in rows: del row['generation']
    assert estimate(subject.summarize(rows, 'scientific', draws=100), 'qwen', 'breadth_expert')['mean'] == 0
    rows[0]['instrument_accepted'] = False
    result = subject.summarize(rows, 'scientific', draws=100)
    assert result['families'][rows[0]['family']]['effects']['breadth_expert']['groups']['overall']['disposition'] == 'IMPLEMENTATION INVALID'
    rows[0].update(status='FAILED', reason='original failed fit')
    result = subject.summarize(rows, 'scientific', draws=100)
    assert len(result['families'][rows[0]['family']]['all_seed_profiles']) == 12
    assert result['families'][rows[0]['family']]['effects']['breadth_expert']['disposition'] == 'NOT RUN WITH REASON'


def test_generation_is_not_silently_reinterpreted_as_choice():
    with pytest.raises(ValueError, match='generation profile'): subject.summarize(fixture(), 'scientific', draws=100)


@pytest.fixture
def collector(tmp_path, monkeypatch):
    monkeypatch.setattr(subject, 'inside', lambda p: Path(p).resolve())
    fits = [{'family': f, 'recipe': r, 'seed': s, 'status': 'COMPLETE',
             'adapter_sha256': f + r + str(s), 'complete_sha256': 'fit-' + f + r + str(s)} for f, r, s in FITS]
    assigned = {'fits': [{'family': f, 'recipe': r, 'seed': s, 'choice_job': f'{f}-{r}-{s}-choice',
                         'calibration_job': f'{f}-{r}-{s}-calibration'} for f, r, s in FITS]}
    path = tmp_path / 'ASSIGNMENT.json'; write(path, assigned); seen = []
    monkeypatch.setattr(subject, 'source_queues', lambda *args: (fits, {}, {}, {'original': 'queues'}))
    def profile(plan, queue, status, row, scope, expected):
        assert set(row) == {'family', 'recipe', 'seed', 'choice_job', 'calibration_job'}
        assert expected == {'family': row['family'], 'package_kind': 'fitted',
                            'adapter_sha256': row['family'] + row['recipe'] + str(row['seed']),
                            'training_complete_sha256': 'fit-' + row['family'] + row['recipe'] + str(row['seed'])}
        seen.append(row)
        return {'status': 'COMPLETE', 'choice_rows': [], 'instrument_accepted': True,
                'comparison_contract': {'cases': 'same', 'selected_comparator': 'same'}}
    monkeypatch.setattr(subject, 'profile', profile)
    return path, assigned, fits, seen


def collect(fixture):
    return subject.collect(fixture[0].parent / 'PLAN.json', fixture[0].parent / 'queue', fixture[0], 'scientific')


def test_collector_has_only_choice_and_own_calibration_dependencies(collector):
    rows, provenance = collect(collector)
    assert len(rows) == len(collector[3]) == 24
    assert all('generation' not in r for r in rows)
    assert provenance == {'original': 'queues'}


@pytest.mark.parametrize('attack', ['missing', 'duplicate', 'extra_generation', 'wrong_seed', 'extra_top_field'])
def test_incomplete_or_generation_coupled_assignment_refuses(collector, attack):
    path, assigned, _, _ = collector
    if attack == 'missing': assigned['fits'].pop()
    elif attack == 'duplicate': assigned['fits'][-1] = assigned['fits'][0]
    elif attack == 'extra_generation': assigned['fits'][0]['generation_jobs'] = {}
    elif attack == 'wrong_seed': assigned['fits'][0]['seed'] = True
    else: assigned['generation'] = 'required'
    write(path, assigned)
    with pytest.raises(ValueError): collect(collector)


def test_failed_seed_is_retained_without_opening_its_consumers(collector):
    collector[2][0].update(status='FAILED', reason='retained failure')
    rows, _ = collect(collector)
    assert len(rows) == 24 and len(collector[3]) == 23 and rows[0]['reason'] == 'retained failure'


def test_different_selected_comparators_refuse_even_with_matching_row_ids(collector, monkeypatch):
    original = subject.profile
    def changed(*args):
        result = original(*args)
        if args[-1]['adapter_sha256'] == 'qwenboth_mixed9001': result['comparison_contract'] = {'different': 'comparator'}
        return result
    monkeypatch.setattr(subject, 'profile', changed)
    with pytest.raises(ValueError, match='comparator differs'): collect(collector)
