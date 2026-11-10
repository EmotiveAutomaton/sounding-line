"""Prepared checks; no human data, external calls or native launch on import."""
import copy
import json
import numpy as np
import pytest
from runners.drive.cards import week5_bk_t2_transfer_model as transfer
from runners.drive.cards import week5_bk_t2_analysis as original
from runners.drive.cards import week5_bk_t2_wiki_text as wiki
from runners.drive.cards.week5_bk_t2_transfer_uncertainty import ArticleBank


def constructed_rows(kind='signal'):
    rows = []
    for writer in range(20):
        for index in range(8):
            label = index % 2
            base = [float(label) if kind == 'baseline_only' else 12., 3., .5]
            vector = base + [0.] * 268 + [float(label) if kind == 'signal' else 0., 1.]
            rows.append(dict(writer=f'constructed-{writer}', session=f'constructed-{writer}',
                             index=index, genre='creative', labels=dict(a=None, b=label, c=None),
                             baseline=base, features=vector))
    return rows


@pytest.mark.parametrize('kind', ['signal', 'null', 'baseline_only'])
def test_serialized_models_equal_exact_original_pooled_fit(kind):
    rows = constructed_rows(kind)
    selected, y, base, full = transfer.matrices(rows)
    model = json.loads(json.dumps(transfer.fit(rows, ['constructed', 'constructed', full.shape[1]])))
    bp, fp = transfer.predict(model, base, full)
    assignment = np.full(len(selected), -1)
    assert np.allclose(bp, original.predict(base, y, assignment, 'ridge'), atol=1e-12, rtol=0)
    assert np.allclose(fp, original.predict(full, y, assignment, 'ridge'), atol=1e-12, rtol=0)
    gain = original.auc(y, fp) - original.auc(y, bp)
    assert gain > .45 if kind == 'signal' else abs(gain) < 1e-12


def test_external_labels_and_metadata_cannot_enter_prediction_or_features():
    rows = constructed_rows()
    model = transfer.fit(rows, ['constructed', 'constructed', 273])
    base, full = [r['baseline'] for r in rows], [r['features'] for r in rows]
    before = transfer.predict(model, base, full)
    altered = copy.deepcopy(rows)
    for row in altered:
        row['labels']['b'] = 1 - row['labels']['b']
        row['writer'] = 'different-held-out-identity'
        row['revision_count'] = 10**9
    after = transfer.predict(model, [r['baseline'] for r in altered], [r['features'] for r in altered])
    assert all(np.array_equal(a, b) for a, b in zip(before, after))
    with pytest.raises(TypeError):
        transfer.predict(model, base, full, labels=[r['labels']['b'] for r in altered])


def test_fit_refuses_incomplete_classes_duplicate_units_and_nonfinite_columns():
    for mutation in ('one_class', 'duplicate', 'nonfinite', 'baseline'):
        rows = constructed_rows()
        if mutation == 'one_class':
            for row in rows: row['labels']['b'] = 0
        if mutation == 'duplicate': rows.append(copy.deepcopy(rows[0]))
        if mutation == 'nonfinite': rows[0]['features'][-1] = float('nan')
        if mutation == 'baseline': rows[0]['baseline'][0] += 1
        with pytest.raises(ValueError): transfer.fit(rows, [])


def test_nested_templates_tables_references_and_visible_links():
    value = "A {{outer|{{inner|x}}|{{{fallback|z}}}}} [[Target|visible]] statement.<ref name='n'>Secret {{citation}}</ref>\n{| class='wikitable'\n| nested {|x|}\n|}\nAn [https://example.org external] '''ending'''."
    text, counts = wiki.clean_wikitext(value)
    assert text == 'A visible statement.\nAn external ending.'
    assert counts['dropped_templates'] == counts['dropped_tables'] == counts['dropped_ref'] == 1
    assert counts['visible_internal_links'] == counts['external_links'] == 1


@pytest.mark.parametrize('value', ['A {{broken.', 'A <ref>broken.', 'A <unknown>x</unknown>.',
                                  'A [[missing.', 'A __TOC__.', 'A <nowiki>{{literal}}</nowiki>.', 'A <ref'])
def test_unhandled_structure_is_not_silently_labelled_plain_text(value):
    with pytest.raises(wiki.ParseBoundary): wiki.final_sentences(value)


def test_final_version_contract_is_retrospective_not_a_forecast():
    before = wiki.final_sentences('The first sentence. The old second sentence.')
    after = wiki.final_sentences('The first sentence. The rewritten final sentence.')
    assert before['sentences'][0]['text'] == after['sentences'][0]['text']
    assert before['sentences'][-1]['text'] != after['sentences'][-1]['text']
    assert after['labels_computed'] is False
    assert after['feature_time'] == 'final_current_version'
    with pytest.raises(TypeError): wiki.final_sentences('Final sentence.', history=[])


def test_article_sampling_keeps_inactive_and_undefined_outcomes():
    rows = [dict(article='a', sentence=0, outcome=0, status='eligible', prediction=.1, baseline_prediction=.5),
            dict(article='b', sentence=0, outcome=1, status='eligible', prediction=.9, baseline_prediction=.5),
            dict(article='c', sentence=0, outcome=None, status='left_censored', prediction=None, baseline_prediction=None)]
    bank = ArticleBank(rows, ['a', 'b', 'c', 'inactive'])
    assert bank.point() == [1., .5, .5]
    assert bank.counts['articles_without_labelled_sentence'] == 2
    assert bank.counts['undefined_outcomes'] == 1
    draws = [bank.draw(i) for i in range(2000)]
    summary = bank.summary(draws)
    assert summary['undefined_draws'] > 0 and summary['interval'] is None
    assert summary['support_scope'] == 'below floor, descriptive'
    assert draws == [bank.draw(i) for i in range(2000)]
    with pytest.raises(ValueError): bank.summary(draws[:-1])
    false_negative = copy.deepcopy(rows)
    false_negative[-1]['outcome'] = 0
    with pytest.raises(ValueError): ArticleBank(false_negative, ['a', 'b', 'c', 'inactive'])
