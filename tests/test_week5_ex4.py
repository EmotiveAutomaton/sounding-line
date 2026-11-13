import json
import pytest
from runners.drive.cards import week5_ex4 as study
from runners.drive.cards import week5_ex4_words as words
from runners.drive.cards import week5_ex4_fixture as fixture


def test_exact_final_offsets_and_timing_including_unicode():
    session = fixture.Session(); session.type('😀 cat ', 1.); session.type('dog', 2.)
    result = words.replay(session.record())
    assert result['final_text'] == '😀 cat dog'
    rows = result['words']; assert [(r['start'], r['end']) for r in rows] == [(2, 5), (6, 9)]
    assert rows[1]['pause_seconds'] == pytest.approx(2.) and rows[1]['stop_2_seconds'] is True
    assert all(r['timing_status'] == 'supported' for r in rows)
    assert result['writer_id_included'] is False


def test_deleted_start_does_not_receive_a_new_word_pause():
    session = fixture.Session(); session.type('cat', 2.)
    session.add('Remove/Cut', 'c', 0)
    result = words.replay(session.record())
    assert result['final_text'] == 'at'
    assert result['words'][0]['timing_status'] == 'original_word_start_did_not_survive'
    assert result['words'][0]['pause_seconds'] is None


def test_inserted_later_and_original_typing_order_are_separate():
    session = fixture.Session(); session.type('old ', 2.)
    session.add('Input', 'n', 1, 3.)
    session.add('Input', 'e', 2)
    session.add('Input', 'w', 3)
    session.add('Input', ' ', 4)
    result = words.replay(session.record())
    assert result['final_text'] == 'new old '
    assert [result['final_text'][r['start']:r['end']] for r in result['words']] == ['old', 'new']
    assert result['words'][1]['inserted_later'] is True


def test_moves_preserve_origins_and_word_merges_are_nullable():
    session = fixture.Session(); session.type('cat ', 2.); session.type('dog ', 3.)
    session.add('Move From [4, 8] To [0, 4]', 'dog ', 4)
    result = words.replay(session.record())
    assert result['final_text'] == 'dog cat '
    assert [r['pause_seconds'] for r in result['words']] == pytest.approx([2., 3.])
    assert result['words'][1]['moved_after_typing'] is True
    session.add('Remove/Cut', ' ', 3)
    merged = words.replay(session.record())
    assert merged['words'][0]['pause_seconds'] is None


def test_paste_bulk_and_clock_inconsistency_never_become_fluent():
    session = fixture.Session(); session.add('Paste', 'paste ', 6); session.add('Input', 'bulk', 10)
    result = words.replay(session.record())
    assert result['counts']['words_without_typed_material'] == 1
    assert result['words'][0]['pause_seconds'] is None
    plain = fixture.Session(); plain.type('word', 3.); record = plain.record()
    record['events'][1]['PauseTime'] = 10
    result = words.replay(record)
    assert result['words'][0]['timing_status'] == 'missing_overlapping_or_inconsistent_clock'


def test_percentile_uses_supported_essay_pauses_with_ties():
    session = fixture.Session(); session.type('a ', 1.); session.type('b ', 2.); session.type('c ', 3.); session.type('d ', 3.)
    result = words.replay(session.record())
    assert result['essay_pause_p80_seconds'] == pytest.approx(3.)
    assert sum(row['stop_essay_p80'] for row in result['words']) == 2


def test_complete_roster_failures_checkpoint_and_replay(tmp_path, monkeypatch):
    root, result, proof, terminals = fixture.constructed_chain(tmp_path, monkeypatch)
    assert result['source_sessions'] == 2 and result['session_status']['replay_parse_failed'] == 1
    assert proof['verified'] is True
    assert all(row.get('verified') is False for row in terminals if row.get('status') == 'yielded')
    record = json.loads((root / 'bundle/sessions/00000.json').read_text())
    assert 'writer' not in record


def test_integrity_failure_is_not_a_parse_exclusion(tmp_path, monkeypatch):
    complete = tmp_path / 'source/COMPLETE.json'
    monkeypatch.setattr(study, 'authenticate', lambda inputs: (complete, complete.parent, [{'ordinal': 0, 'session': 'x'}], {'fixed': True}))
    def corrupted(*args):
        raise ValueError('Changed native source hash')
    monkeypatch.setattr(study.source, 'source_record', corrupted)
    with pytest.raises(ValueError, match='Changed native source'):
        study.execute(tmp_path / 'run', {}, {'phase': 'EX4'})


def test_unapproved_local_or_external_copy_refuses(tmp_path):
    with pytest.raises(ValueError, match='named ignored local'):
        study.materialize(tmp_path / 'none', tmp_path / 'copy')
