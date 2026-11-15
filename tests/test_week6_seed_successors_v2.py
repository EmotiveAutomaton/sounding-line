"""Bounded seed/allocation and conditional-review checks; no full bank or fit."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from runners.drive.cards import week6_la6_v1 as old_la
from runners.drive.cards import week6_la6_v2 as la
from runners.drive.cards import week6_la6_runner_v2 as la_run
from runners.drive.cards import week6_dc1_v1 as old_dc
from runners.drive.cards import week6_dc1_v2 as dc
from runners.drive.cards import week6_dc1_runner_v2 as dc_run


@pytest.mark.parametrize('old,new', [(old_la, la), (old_dc, dc)])
def test_math_ast_changes_only_the_inherited_seed(old, new):
    def without_seed(module):
        tree = ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SEED' for t in n.targets))]
        return ast.dump(tree, include_attributes=False)
    assert old.SEED == 20261115 and new.SEED == 20261107
    assert without_seed(old) == without_seed(new)


@pytest.mark.parametrize('ordinal', [0, 17, 1999])
def test_LA6_seed_selects_exact_whole_meeting_multiplicities(ordinal, monkeypatch):
    rows = [{'meeting': f'm{i}', 'label': y, 'act_type': 'a'} for i in range(6) for y in (0, 1)]
    arm = {'predictions': [.25, .75] * 6, 'categories': ['a']}; base = {'True': arm, 'False': arm}
    seen = []
    def fitted(rows, include, weights):
        seen.append(np.asarray(weights).copy())
        return SimpleNamespace(coef_=np.zeros((1, 9 if include else 8))), None
    monkeypatch.setattr(la, 'fitted', fitted)
    first = la_run.one_draw(rows, base, ordinal); second = la_run.one_draw(rows, base, ordinal)
    expected = np.bincount(np.random.default_rng(np.random.SeedSequence([20261107, ordinal, 6])).integers(6, size=6), minlength=6)
    assert first == second and len(seen) == 4
    assert all(np.array_equal(w, np.repeat(expected, 2)) for w in seen)


@pytest.mark.parametrize('ordinal', [0, 17, 1999])
def test_DC1_seed_selects_exact_whole_person_multiplicities(ordinal, monkeypatch):
    monkeypatch.setattr(dc, 'from_statistics', lambda stats, weights: {'weights': weights.tolist()})
    stats = {'keys': np.arange(7)}
    expected = np.bincount(np.random.default_rng(np.random.SeedSequence([20261107, ordinal, 1])).integers(7, size=7), minlength=7)
    assert dc.bootstrap_draw(stats, ordinal) == dc.bootstrap_draw(stats, ordinal) == {'weights': expected.tolist()}


def test_successor_reviews_bind_new_math_and_conditional_scope():
    assert la_run.math is la and dc_run.math is dc
    review = dc_run.review_contract('constructed-completion')
    assert review['first_play_primary'] and review['fixed_prospective_TR1_RR3_intersection']
    assert review['identical_primary_rating_choice_occasions'] and review['history_through_completed_k_only']
    assert not review['causal_claim'] and not review['deployable_rating_time_forecast']
    assert set(review['offer_controls']) == set(dc.TERMS[:3])
    assert all(v['rating_time_visibility'] == 'not asserted' for v in review['offer_controls'].values())
    assert 'future-offer nuisance adjustment' in dc_run.CONDITIONAL_SCOPE


def conditional_source(tmp_path, monkeypatch):
    root = tmp_path / 'prepared'; output = root / 'output'; output.mkdir(parents=True)
    dc_run.io.write_json(root / 'COMPLETE.json', {'constructed_only': True})
    row = {'person': 1, 'attempt': 1, 'stored_rating_trial': 3, 'next_choice_trial': 4,
           'history_last_trial': 3, 'controls_requiring_timing_review': list(dc.TERMS[:3]),
           'x': [0.] * 9, 'rating': 1., 'choice': 0}
    table = {'timing': 'post_trial_k_to_next_choice_k_plus_1', 'terms': list(dc.TERMS),
             'source_identity': dict(dc_run.PARENT_PINS), 'rows': [row],
             'person_source_arrays': [{'person': 1}], 'roster': {'common_people': 1}}
    def write(value):
        dc_run.io.write_json(output / 'TABLE.json', value)
        dc_run.io.write_json(output / 'RESULT.json', {'complete_preparation': True, 'table_sha256': dc_run.io.sha(output / 'TABLE.json')})
    write(table); review_path = tmp_path / 'review.json'
    dc_run.io.write_json(review_path, dc_run.review_contract(dc_run.io.sha(root / 'COMPLETE.json')))
    monkeypatch.setattr(dc_run.seal, 'complete', lambda path, module: (root, {}, {}))
    return {'prepared_run': str(root), 'owner_review': str(review_path)}, table, write


def test_conditional_review_accepts_original_future_offer_mapping(tmp_path, monkeypatch):
    inputs, table, _ = conditional_source(tmp_path, monkeypatch)
    loaded, identity = dc_run.load(inputs)
    assert loaded == table and not identity['owner_review']['deployable_rating_time_forecast']


@pytest.mark.parametrize('mutation', ['repeat', 'future_history', 'missing_person', 'wrong_parent'])
def test_conditional_review_refuses_changed_fixed_source_or_occasions(tmp_path, monkeypatch, mutation):
    inputs, table, write = conditional_source(tmp_path, monkeypatch); table = copy.deepcopy(table)
    if mutation == 'repeat': table['rows'][0]['attempt'] = 2
    elif mutation == 'future_history': table['rows'][0]['history_last_trial'] = 4
    elif mutation == 'missing_person': table['rows'] = []
    else: table['source_identity']['TR1_complete'] = 'changed'
    write(table)
    with pytest.raises(ValueError): dc_run.load(inputs)
