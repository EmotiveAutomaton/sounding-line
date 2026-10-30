import numpy as np
import pytest
from runners.drive.cards import week3_dr1_context as card
from runners.drive.cards import week3_identification_crossfit as crossfit


@pytest.mark.parametrize('kind,expected', [('constant', False), ('prompt', False), ('person', True)])
def test_complete_reference_constructions_and_support(kind, expected):
    rows = card.constructed_rows(kind); writers = sorted({r['writer'] for r in rows})
    # Component rehearsal only; native calibration retains all 1,000 permutations.
    config = dict(card.CONFIG, permutations=64)
    result, detail = card.analyze(rows, writers, config)
    assert result['independent_context']['pass_both'] == expected
    assert result['independent_context']['permutation']['attempted'] == 64
    assert not result['literal_licenses_claim'] and not result['routing_claim']
    probed = []
    for fold in detail['folds']:
        assert not set(fold['donor_writers']) & set(fold['gallery_writers']['style'])
        probed += fold['probe_writers']['style']
    assert sorted(probed) == writers


def test_missing_fixed_prompt_support_does_not_select_successful_writers():
    rows = card.constructed_rows('person'); writers = sorted({r['writer'] for r in rows})
    folds = crossfit.writer_folds(rows)
    # Every role has disjoint prompts, so donors supply no context to their probes.
    for row in rows: row['prompt'] += '-role'+str(folds[row['writer']])
    result, _ = card.analyze(rows, writers, dict(card.CONFIG, permutations=16))
    assert result['independent_context']['state'] == 'unsupported'
    assert result['writers'] == 12 and not result['independent_context']['pass_both']


def test_role_shuffle_preserves_every_prompt_role_membership_and_count():
    rows = card.constructed_rows('person'); folds = crossfit.writer_folds(rows)
    labels = crossfit.role_assignment(rows, folds, 0, 20261026)
    assert set(labels) == {r['session'] for r in rows}
    for row in rows: assert folds[labels[row['session']]] == folds[row['writer']]
    for prompt in {r['prompt'] for r in rows}:
        own = [r for r in rows if r['prompt'] == prompt]
        assert sorted(r['writer'] for r in own) == sorted(labels[r['session']] for r in own)


def test_source_feature_normalization_retains_non_dictionary_denominator():
    dictionary = dict(words=['named'], punctuation=[], character_bigrams=[])
    rows = [dict(session=str(i), writer=f'w{i}', prompt='p', timestamp=i,
                 word_counts={'named':2, 'other':8}, punctuation_counts={}, handling={},
                 tc_timing_mode='invalid') for i in range(6)]
    result = card.feature_rows(rows, dictionary, [f'w{i}' for i in range(6)])
    assert [r['features']['style'] for r in result] == [[.2]]*6


def test_changed_config_and_human_input_refuse_before_work(tmp_path):
    with pytest.raises(ValueError): card.execute(tmp_path, {}, dict(card.CONFIGS['constructed'], permutations=2))
    with pytest.raises(ValueError): card.execute(tmp_path, {'human':'forbidden'}, card.CONFIGS['constructed'])
