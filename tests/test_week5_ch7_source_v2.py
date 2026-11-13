"""Independent source answers and evidence-preservation regression checks."""
import json
import sqlite3
from pathlib import Path
import pytest
from runners.drive.cards import week5_ch7_source_v2 as source
from runners.drive.cards import week5_ch7_native_fixture_v2 as fixture
from runners.drive.cards.week5_ch_source import digest


def database(path):
    con = sqlite3.connect(path)
    try:
        con.execute('CREATE TABLE example(value INTEGER)')
        con.execute('INSERT INTO example VALUES(7)')
        con.commit()
    finally:
        con.close()
    return path


def test_snapshot_cannot_write_or_create_files(tmp_path):
    path = database(tmp_path / 'spaces # percent %.sqlite')
    before = digest(path)
    with source.readonly_snapshot(path) as con:
        assert con.execute('SELECT value FROM example').fetchall() == [(7,)]
        con.execute('PRAGMA query_only=OFF')  # URI read-only survives this toggle.
        with pytest.raises(sqlite3.OperationalError):
            con.execute('INSERT INTO example VALUES(8)')
    assert digest(path) == before
    assert list(tmp_path.iterdir()) == [path]
    missing = tmp_path / 'missing.sqlite'
    with pytest.raises(FileNotFoundError), source.readonly_snapshot(missing):
        pass
    assert not missing.exists()


@pytest.mark.parametrize('suffix', ['-wal', '-shm', '-journal'])
def test_sidecars_refused_even_when_empty(tmp_path, suffix):
    path = database(tmp_path / 'source.sqlite')
    before = digest(path)
    sidecar = Path(str(path) + suffix)
    sidecar.write_bytes(b'')
    with pytest.raises(ValueError, match='sidecar'), source.readonly_snapshot(path):
        pass
    assert digest(path) == before and sidecar.read_bytes() == b''


def test_source_known_answers_and_replay_preserve_snapshots(tmp_path):
    root = tmp_path / 'fixture'
    fixture.source_case(root)
    receipt = json.loads((root / 'SOURCE_FIXTURE.json').read_text())
    assert receipt['passed'] and receipt['independent_expected_rows']
    assert receipt['source_games'] == 4 and receipt['player_games'] == 8
    raw = root / 'PRIVATE_CONSTRUCTED_RAW.sqlite'
    target = root / 'projection/PRIVATE_PLAYER_HISTORY.sqlite'
    pins = {p: digest(p) for p in [raw, target]}
    inputs = {'histories': {'path': str(raw), 'sha256': pins[raw]}}
    proof = source.verify(root / 'projection', inputs, {'constructed_fixture': True})
    assert proof['source_records'] == 4 and proof['every_player_game_compared'] == 8
    assert {p: digest(p) for p in pins} == pins
    assert not list(root.rglob('*-wal')) and not list(root.rglob('*-shm'))
    rows = list(source.source_rows(raw, ['2017-05', 1]))
    assert [(row[0], row[1]) for row in rows] == [('2017-06', 2), ('2017-06', 3)]


@pytest.mark.parametrize('field', ['rating', 'opponent_rating', 'result', 'source_ordinal'])
def test_known_answers_reject_shared_projection_bug(tmp_path, monkeypatch, field):
    original = source.projected
    def damaged(*args):
        for player, value in original(*args):
            value[field] = 999
            yield player, value
    monkeypatch.setattr(source, 'projected', damaged)
    # Execute and replay agree on the same corruption; the independent oracle must fail.
    with pytest.raises(AssertionError, match='Independent constructed source answers'):
        fixture.source_case(tmp_path / 'damaged')


@pytest.mark.parametrize('problem', ['hash', 'month', 'incomplete', 'fixture_flag'])
def test_source_admission_rejects_invalid_snapshot(tmp_path, problem):
    path = tmp_path / 'source.sqlite'
    con = sqlite3.connect(path)
    try:
        con.executescript('CREATE TABLE histories(month TEXT,ordinal INTEGER,payload TEXT);CREATE TABLE settings(key TEXT,value TEXT);CREATE TABLE checkpoints(complete INTEGER);')
        months = source.MONTHS[:-1] if problem == 'month' else source.MONTHS
        con.executemany('INSERT INTO histories VALUES(?,0,?)', [(m, '{}') for m in months])
        con.execute('INSERT INTO settings VALUES(?,?)', ('constructed_fixture', 'false' if problem == 'fixture_flag' else 'true'))
        con.execute('INSERT INTO checkpoints VALUES(?)', (0 if problem == 'incomplete' else 1,))
        con.commit()
    finally:
        con.close()
    before = digest(path)
    inputs = {'histories': {'path': str(path), 'sha256': '0' * 64 if problem == 'hash' else before}}
    with pytest.raises(ValueError):
        source.source_info(inputs, {'constructed_fixture': problem != 'incomplete'})
    assert digest(path) == before
    assert list(tmp_path.iterdir()) == [path]


def test_changed_sealed_output_is_rejected(tmp_path):
    root = tmp_path / 'fixture'
    fixture.source_case(root)
    raw = root / 'PRIVATE_CONSTRUCTED_RAW.sqlite'
    target = root / 'projection/PRIVATE_PLAYER_HISTORY.sqlite'
    con = sqlite3.connect(target)
    try:
        con.execute("UPDATE settings SET value='0' WHERE key='moves'")
        con.commit()
    finally:
        con.close()
    with pytest.raises(ValueError):
        source.verify(root / 'projection', {'histories': {'path': str(raw), 'sha256': digest(raw)}}, {'constructed_fixture': True})
