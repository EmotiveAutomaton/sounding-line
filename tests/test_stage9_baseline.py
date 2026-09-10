import pytest

from runners.stage9.revision_baseline import fit
from runners.stage9.features import predict, features, copy_probabilities
from runners.stage9.data import visible_revision


def examples(shuffled=False):
    rows = []
    for i in range(40):
        text = 'correct syntax grammar' if i % 2 else 'different meaning claim'
        label = ('fluency' if i % 2 else 'meaning-changed') if not shuffled else ('fluency' if i % 4 < 2 else 'meaning-changed')
        rows.append({'split': 'train', 'independent_unit': str(i), 'artifact': text, 'before': '', 'labels': [label]})
    return rows


def test_known_lexical_alternative_and_balanced_shuffled_null():
    ev = visible_revision({'artifact': 'correct syntax grammar'}, 'artifact')
    learned = predict(ev, fit(examples(), 'artifact'))
    null = predict(ev, fit(examples(shuffled=True), 'artifact'))
    assert learned['fluency'] > .95
    assert abs(null['fluency'] - null['meaning-changed']) < 1e-12
    assert all(p > 0 for p in learned.values())


def test_training_refuses_development_and_pair_uses_actual_delta():
    rows = examples()
    rows[0]['split'] = 'development'
    with pytest.raises(ValueError):
        fit(rows, 'artifact')
    observed = features({'before': 'old shared', 'after': 'new shared', 'context': 'revision'})
    assert observed['added:new'] == 1 and observed['deleted:old'] == 1
    assert 'added:shared' not in observed


def test_copied_text_known_answer_null_and_permutation():
    options = {'a': 'the old text', 'b': 'totally different replacement'}
    result = copy_probabilities('the old text', options)
    assert result['a'] > .9
    assert result == copy_probabilities('the old text', dict(reversed(list(options.items()))))
    assert copy_probabilities('x', {'a': 'a', 'b': 'b'}) == {'a': .5, 'b': .5}
