from pathlib import Path
import json
import pytest
from runners.drive.cards import week5_go3_collection as c
from runners.drive.cards.week5_go3_collection_fixture import make_source


def reseal(entry):
    root = Path(entry['root'])
    done = c.read(root / 'COMPLETE.json')
    done['outputs'] = {name: c.core.sha(root / name) for name in done['outputs']}
    c.core.write(root / 'COMPLETE.json', done)
    entry['complete_sha256'] = c.core.sha(root / 'COMPLETE.json')


@pytest.mark.parametrize('field,value', [('archive_sha256', '0' * 64), ('license_sha256', '0' * 64),
                                        ('source_sha256', '0' * 64), ('site', 'english')])
def test_invalid_original_binding_refuses_even_with_resealed_fixture(tmp_path, field, value):
    entry = make_source(tmp_path / 'source', 'writers')
    path = Path(entry['root']) / 'output/SNAPSHOT.json'
    snapshot = c.read(path)
    snapshot['state']['binding'][field] = value
    c.core.write(path, snapshot)
    reseal(entry)
    with pytest.raises(ValueError, match='binding differs'):
        c.authenticate('writers', entry, lambda: False)


def test_different_shared_salt_refuses_before_ingestion(tmp_path):
    roster = {site: make_source(tmp_path / site, site) for site in c.SITES}
    site = c.SITES[-1]
    path = Path(roster[site]['root']) / 'output/SNAPSHOT.json'
    snapshot = c.read(path)
    snapshot['state']['binding']['salt_sha256'] = '0' * 64
    c.core.write(path, snapshot)
    reseal(roster[site])
    path = tmp_path / 'roster.json'
    c.core.write(path, roster)
    with pytest.raises(ValueError, match='different campaign salts'):
        c.execute(tmp_path / 'collection', {'roster': str(path)}, {'phase': 'collect'})
    assert not (tmp_path / 'collection/projection.sqlite').exists()


def test_duplicate_source_roots_refuse(tmp_path):
    entry = make_source(tmp_path / 'source', 'writers')
    path = tmp_path / 'roster.json'
    c.core.write(path, {site: entry for site in c.SITES})
    with pytest.raises(ValueError, match='Duplicate'):
        c.check_roster(path)


def test_incomplete_explicit_source_replay_refuses(tmp_path):
    entry = make_source(tmp_path / 'source', 'writers')
    path = Path(entry['root']) / 'VERIFIED.json'
    c.core.write(path, {'verified': True, 'complete_independent_source_replay': False})
    reseal(entry)
    with pytest.raises(ValueError, match='source row replay'):
        c.authenticate('writers', entry, lambda: False)


def test_exclusion_accounting_mismatch_refuses(tmp_path):
    entry = make_source(tmp_path / 'source', 'writers')
    path = Path(entry['root']) / 'output/SOURCE.json'
    source = c.read(path)
    source['counts']['anonymous_edits_excluded'] = 1
    c.core.write(path, source)
    reseal(entry)
    with pytest.raises(ValueError, match='accounting'):
        c.authenticate('writers', entry, lambda: False)
