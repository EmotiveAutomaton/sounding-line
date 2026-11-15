"""Constructed LA6 checks, with no corpus loading or result interpretation."""
import numpy as np
import pytest
from runners.drive.cards import week6_la6_v1 as la


def act(name, start, *, laughed=False, speaker='A', meeting='M', text='A plain remark.', kind='statement', end=None):
    return {'id': name, 'meeting': meeting, 'speaker': speaker, 'start': start,
            'end': start + 1 if end is None else end, 'text': text,
            'act_type': kind, 'laughed_after': laughed}


def test_matching_uses_speaker_meeting_and_distance_but_not_act_or_length():
    rows = [act('case', 100, laughed=True, kind='question'), act('too_close', 71),
            act('left', 70, text='one'), act('right', 130), act('wrong_speaker', 40, speaker='B'),
            act('wrong_meeting', 0, meeting='other'), act('no_control', 0, speaker='C', laughed=True)]
    pairs, audit = la.match(rows)
    assert pairs == [{'meeting': 'M', 'case': 'case', 'control': 'left', 'distance_seconds': 30}]
    assert audit['matched'] == 1 and len(audit['unsupported']) == 1
    assert la.match(list(reversed(rows))) == (pairs, audit)


def test_control_reuse_is_explicit_and_timestamp_ties_are_deterministic():
    pairs, audit = la.match([act('b', 0), act('a', 0), act('case1', 40, laughed=True), act('case2', 50, laughed=True)])
    assert [p['control'] for p in pairs] == ['a', 'a']
    assert audit['reused_control_copies'] == 1


def test_features_have_only_completed_history_and_past_laughs():
    rows = [act('old', 0, speaker='B', text='blue'), act('overlap', 5, end=100, speaker='C', text='secret'),
            act('last', 10, speaker='B', text='red blue'),
            act('now', 20, text="I'm not blue?", laughed=True)]
    laughs = [{'meeting': 'M', 'start': 2, 'end': 3}, {'meeting': 'M', 'start': 21, 'end': 22}]
    value = la.feature_rows(rows, laughs)[('M', 'now')]['numeric']
    assert value[:7] == [3, 1, 1 / 3, 1, 1, 1, 1]
    assert value[8] == 17
    assert la.feature_rows(rows, laughs[:-1])[('M', 'now')]['numeric'] == value


def table(null=False):
    rows = []
    for meeting in range(24):
        for label in (0, 1):
            marked = 3 if null or label == 0 else 5
            for ordinal in range(15):
                rows.append({'meeting': f'{meeting:02d}', 'id': f'{label}-{ordinal}', 'label': label,
                             'act_type': 'marked' if ordinal < marked else 'base', 'numeric': [0.] * 9})
    return rows


def test_exact_binary_act_fixture_and_true_null_meeting_folds():
    rows = table()
    value = la.held_out(rows)
    assert value['auc'] == pytest.approx(.5 + .5 * (1 / 3 - .2), abs=1e-12)
    for fold in value['folds']:
        assert not set(fold['training_meetings']) & set(fold['test_meetings'])
    assert la.held_out(table(True))['auc'] == .5
    strong = table()
    for row in strong:
        ordinal = int(row['id'].split('-')[1])
        if row['label']:
            row['act_type'] = 'marked' if ordinal < 12 else 'base'
    assert la.held_out(strong)['auc'] > la.BAR
    model, _ = la.fitted(rows)
    # Fixed regularization shrinks the fitted odds slightly toward one.
    assert np.exp(model.coef_[0][-1]) == pytest.approx(2., abs=.1)


def test_cluster_bootstrap_has_both_registered_feature_arms_and_no_single_meeting_interval():
    result = la.analyze(table(), draws=4)
    assert set(result['arms']) == {'with_laugh_history', 'without_laugh_history'}
    assert result['meetings'] == 24
    assert result['arms']['with_laugh_history']['act_interval_failed_draws'] == []
    assert la.analyze([r for r in table() if r['meeting'] == '00'], draws=4)['draws'] == 0


def test_duplicate_source_identity_and_nonboolean_labels_fail():
    row = act('a', 0)
    with pytest.raises(ValueError, match='Duplicate'):
        la.match([row, row])
    with pytest.raises(ValueError, match='Boolean'):
        la.match([dict(row, laughed_after=1)])


def test_original_parser_word_count_survives_numeric_and_punctuation_tokens():
    row = dict(act('a', 0, text='42 ...'), word_count=2)
    assert la.feature_rows([row], [])[('M', 'a')]['numeric'][0] == 2
    with pytest.raises(ValueError, match='word count'):
        la.feature_rows([dict(row, word_count=-1)], [])
