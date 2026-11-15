"""Small reporting-boundary checks; no model fitting or human source reads."""
import numpy as np
import pytest

from runners.drive.cards import week6_la6_runner_v1 as la
from runners.drive.cards import week6_dc1_v1 as dc


@pytest.mark.parametrize('bounds,expected', [
    ([.61, .9], 'supports'), ([.60, .9], 'inconclusive'),
    ([.5, .60], 'against'), ([.60, .60], 'against'),
    ([.59, .61], 'inconclusive'), ([0, .1], 'against'), ([0, 1], 'inconclusive')])
def test_la6_original_auc_scale_boundaries(bounds, expected):
    assert la.classify_interval(bounds) == expected


@pytest.mark.parametrize('bounds,expected', [
    ([.06, .2], 'supports'), ([.05, .2], 'inconclusive'),
    ([-.2, -.001], 'against'), ([-.2, 0], 'inconclusive'),
    ([-.01, .01], 'against'), ([-.05, .05], 'against'),
    ([-.051, .01], 'inconclusive'), ([-.2, -.05], 'against'),
    ([-.1, .06], 'inconclusive'), ([.049, .051], 'inconclusive'),
    ([.05, .05], 'against'), ([0, .05], 'against'), ([-.05, 0], 'against')])
def test_dc1_each_distinct_part_has_exact_three_states(bounds, expected):
    assert dc.classify_interval(bounds) == expected


def test_invalid_intervals_do_not_receive_scientific_outcomes():
    for fn in (la.classify_interval, dc.classify_interval):
        for value in ([.2, .1], [np.nan, .1], [.1]):
            with pytest.raises(ValueError, match='interval'):
                fn(value)
    with pytest.raises(ValueError, match='AUC interval'):
        la.classify_interval([-.1, .1])


def test_summary_classifiers_and_noninferential_statuses_are_separate():
    values = np.linspace(-.2, -.001, 2000)
    draws = [{'parts': [float(v), .02 + float(v) / 100]} for v in values]
    result = dc.summarize({'parts': [-.1, .02]}, draws, 40)
    assert [p['outcome'] for p in result['parts']] == ['against', 'against']
    assert all(p['status'] == 'ok' for p in result['parts']) and not result['both_supported']
    descriptive = dc.summarize({'parts': [-.1, .02]}, draws, 19)
    assert all(p['outcome'] is None and p['status'] == 'below floor, descriptive' for p in descriptive['parts'])
    constant = dc.summarize({'parts': [.1, .1]}, [{'parts': [.1, .1]}] * 2000, 40)
    assert all(p['outcome'] is None and p['status'] == 'degenerate, descriptive' for p in constant['parts'])
    bad = [*draws]; bad[7] = None
    assert dc.summarize({'parts': [-.1, .02]}, bad, 40)['status'] == 'invalid_uncertainty'
    base = {key: {'auc': .57, 'categories': ['a'], 'coefficients': [], 'folds': []}
            for key in ('True', 'False')}
    bank = [{key: {'auc': .57 + i / 200000, 'coefficients': []} for key in base} for i in range(2000)]
    summary = la.summarize(base, bank, 20)
    assert all(a['outcome'] == 'against' and a['status'] == 'ok' for a in summary.values())
    assert all(a['outcome'] is None for a in la.summarize(base, bank, 19).values())
