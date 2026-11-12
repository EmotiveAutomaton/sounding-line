"""Constructed source preservation and exact raw-parser parity; no engine."""
import shutil
import sqlite3
import pytest
from runners.drive.cards import week5_ch_backhalf_roster_v1 as old
from runners.drive.cards import week5_ch_backhalf_roster_v2 as new
from runners.drive.cards import week5_ch_backhalf_fixture_v2 as fixture
from runners.drive.cards.week5_ch_source import digest


def frame(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path)
    con.execute('PRAGMA journal_mode=WAL')
    con.executescript('CREATE TABLE checkpoints(month TEXT,complete INTEGER);CREATE TABLE frame(player TEXT,month TEXT,tc TEXT,band INTEGER,n INTEGER,rating_sum REAL);')
    con.executemany('INSERT INTO checkpoints VALUES(?,1)',[(month,) for month in new.MONTHS])
    for month in new.MONTHS:
        for tc in new.QUOTAS:
            con.executemany('INSERT INTO frame VALUES(?,?,?,?,?,?)',
                [(f'constructed-{month}-{tc}-{i}',month,tc,i%2,20,32000.) for i in range(24)])
    con.commit();con.execute('PRAGMA wal_checkpoint(TRUNCATE)');con.close()


def inventory(root):return {p.name:digest(p) for p in root.iterdir() if p.is_file()}


def test_completed_frame_read_preserves_directory_and_original_selection(tmp_path):
    path=tmp_path/'source/frame.sqlite';frame(path)
    (path.parent/'retained.txt').write_text('constructed source sentinel')
    before=inventory(path.parent)
    inspected=[]
    def check_while_source_connection_is_open():
        assert inventory(path.parent)==before
        inspected.append(True)
    actual=new.choose_players(path,100,constructed=True,check=check_while_source_connection_is_open)
    assert inspected
    assert inventory(path.parent)==before
    copied=tmp_path/'oracle.sqlite';shutil.copyfile(path,copied)
    assert actual==old.choose_players(copied,100,constructed=True)
    assert inventory(path.parent)==before


@pytest.mark.parametrize('edit',["UPDATE checkpoints SET complete=0 WHERE month='2017-05'",
                                  "DELETE FROM checkpoints WHERE month='2017-06'"])
def test_unfinished_or_incomplete_frame_refuses_without_sidecars(tmp_path,edit):
    path=tmp_path/'source/frame.sqlite';frame(path)
    con=sqlite3.connect(path);con.execute(edit);con.commit();con.close()
    before=inventory(path.parent)
    with pytest.raises(ValueError,match='three complete'):new.choose_players(path,100,constructed=True)
    assert inventory(path.parent)==before


def test_uncheckpointed_wal_refuses_instead_of_ignoring_new_source_bytes(tmp_path):
    path=tmp_path/'source/frame.sqlite';frame(path)
    con=sqlite3.connect(path)
    try:
        con.execute('UPDATE frame SET n=21');con.commit()
        before=inventory(path.parent)
        assert (path.parent/'frame.sqlite-wal').stat().st_size>0
        with pytest.raises(ValueError,match='not checkpointed'):new.choose_players(path,100,constructed=True)
        assert inventory(path.parent)==before
    finally:con.close()


def test_full_constructed_raw_source_reference_parity_and_frame_preservation(tmp_path):
    result=fixture.source_fixture(tmp_path/'full',{},dict(constructed_fixture=True))
    assert result['frame_directory_unchanged']
    assert result['original_raw_collector_byte_parity'] and result['all_raw_sources_replayed']
    assert result['positions']>0
