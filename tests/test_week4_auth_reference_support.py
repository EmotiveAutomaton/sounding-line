from copy import deepcopy
import pytest
from runners.drive.cards import week4_auth_reference_support as a


def data():
    config = a.configuration('constructed')
    sessions = a.fixture()
    rows, selection, _ = a.pairs.draw(sessions, config['allocation'])
    return sessions, rows, selection, config


def test_cache_complete_and_intentionally_missing():
    requested = [{'pair_id': 'a'}, {'pair_id': 'b'}]
    complete, absent = a.coverage(requested, {'a', 'b'})
    assert complete['all_requested_present'] and not absent
    missing, absent = a.coverage(requested, {'a'})
    assert missing == dict(requested=2, available=1, missing=1, all_requested_present=False)
    assert absent == ['b']


def test_duplicate_request_refused():
    with pytest.raises(ValueError, match='duplicate'):
        a.coverage([{'pair_id': 'a'}]*2, {'a'})


def test_original_identity_and_role_counts():
    sessions, rows, selection, config = data()
    folds = a.roles.writer_folds(sessions)
    identity = {r['session']: r['writer'] for r in sessions}
    assert a.check_assignment(sessions, folds, identity) == sessions
    labels = a.roles.role_assignment(sessions, folds, 0, 20261102)
    changed = a.check_assignment(sessions, folds, labels)
    assert any(x['writer'] != y['writer'] for x, y in zip(sessions, changed))
    for x, y in zip(sessions, changed):
        assert {k: v for k, v in x.items() if k != 'writer'} == {k: v for k, v in y.items() if k != 'writer'}


def test_missing_session_refused():
    sessions, _, _, _ = data()
    with pytest.raises(ValueError, match='coverage'):
        a.check_assignment(sessions, a.roles.writer_folds(sessions), {})


def test_changed_counts_refused():
    sessions, _, _, _ = data()
    labels = {r['session']: r['writer'] for r in sessions}
    labels[sessions[0]['session']] = 'not-a-writer'
    with pytest.raises(ValueError, match='counts'):
        a.check_assignment(sessions, a.roles.writer_folds(sessions), labels)


def test_cross_role_permutation_refused():
    sessions, _, _, _ = data()
    folds = a.roles.writer_folds(sessions)
    left = sessions[0]
    right = next(r for r in sessions if r['prompt'] == left['prompt'] and folds[r['writer']] != folds[left['writer']])
    labels = {r['session']: r['writer'] for r in sessions}
    labels[left['session']], labels[right['session']] = right['writer'], left['writer']
    with pytest.raises(ValueError, match='role membership'):
        a.check_assignment(sessions, folds, labels)


def test_audit_replays_order_and_preserves_exclusions():
    sessions, rows, selection, config = data()
    summary, private = a.audit(sessions, rows, selection, config)
    assert a.audit(list(reversed(sessions)), rows, selection, config) == (summary, private)
    assert summary['eligible_main_pairs'] == len(rows)-2*config['allocation']['calibration_pairs']
    assert summary['optimistic']['missing'] == len(private['missing_optimistic'])
    assert summary['main']['missing'] >= summary['optimistic']['missing']
    assert not summary['scientific_admission'] and not summary['full_reference_validated']


def test_changed_original_refused():
    sessions, rows, selection, config = data()
    rows = deepcopy(rows); rows[0]['same_writer'] = False
    with pytest.raises(ValueError, match='identity reconstruction'):
        a.audit(sessions, rows, selection, config)


def test_handler_reentry_and_tamper(tmp_path):
    config = a.configuration('constructed')
    a.execute(tmp_path, {}, config)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert a.verify(tmp_path, {}, config)['complete_support_replay']
    a.execute(tmp_path, {}, config)
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    (tmp_path/'SUMMARY.json').write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='replay'):
        a.verify(tmp_path, {}, config)
