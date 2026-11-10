from pathlib import Path
import json
import sqlite3
import pytest
from runners.drive.cards import week5_go3_collection as c
from runners.drive.cards.week5_go3_collection_fixture import make_source


def test_complete_constructed_source_authenticates(tmp_path):
    source = make_source(tmp_path / 'source', 'writers')
    value = c.authenticate('writers', source, lambda: False)
    assert value['rows'] == 450 and value['site'] == 'writers'


def test_changed_source_projection_refuses(tmp_path):
    source = make_source(tmp_path / 'source', 'writers')
    with (Path(source['root']) / 'output/edits.parquet').open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(ValueError, match='output changed'):
        c.authenticate('writers', source, lambda: False)


def test_source_site_mismatch_refuses(tmp_path):
    source = make_source(tmp_path / 'source', 'writers')
    with pytest.raises(ValueError, match='site differs'):
        c.authenticate('english', source, lambda: False)


def test_ambiguous_source_terminal_refuses(tmp_path):
    source = make_source(tmp_path / 'source', 'writers')
    (Path(source['root']) / 'FAILED.json').write_text('{}')
    with pytest.raises(ValueError, match='Ambiguous'):
        c.authenticate('writers', source, lambda: False)


def test_missing_site_roster_refuses(tmp_path):
    path = tmp_path / 'roster.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='five-site'):
        c.check_roster(path)


def test_changed_collection_snapshot_refuses(tmp_path):
    db, state = c.open_state(tmp_path, {'constructed': True})
    c.seal(tmp_path, db, state, {'constructed': True})
    with (tmp_path / 'projection.sqlite').open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(ValueError, match='checkpoint changed'):
        c.open_state(tmp_path, {'constructed': True})


def count_db(users=25, classes=5):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE counts(cell TEXT,editor TEXT,label TEXT,n INTEGER)')
    for user in range(users):
        for label in c.source.PRIMARY[:classes]:
            db.execute('INSERT INTO counts VALUES(?,?,?,1)', ('all', f'constructed-{user:03d}', label))
    return db


@pytest.mark.parametrize('users,classes,expected', [(25, 5, True), (19, 5, False), (25, 4, False), (0, 0, False)])
def test_source_support_and_descriptive_routes(users, classes, expected):
    db = count_db(users, classes)
    try:
        result = c.classifier_support(db, 'all')
        assert result['user_disjoint_support'] == expected
        assert result['rows'] == users * classes
        assert len(result['folds']) == 5
    finally:
        db.close()


def test_authentication_yields_before_source_read(tmp_path):
    source = make_source(tmp_path / 'source', 'writers')
    with pytest.raises(c.Paused, match='authentication'):
        c.authenticate('writers', source, lambda: True)
