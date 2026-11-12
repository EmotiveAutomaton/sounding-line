"""All source input opens, including prepare(), preserve the completed frame."""
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import pytest
from runners.drive.cards import week5_ch_backhalf_roster_v2 as previous
from runners.drive.cards import week5_ch_backhalf_roster_v3 as study
from runners.drive.cards import week5_ch_backhalf_fixture_v3 as fixture
from runners.drive.cards import week5_ch_sample_bounded as sampler


def inventory(folder):return {p.name:study.source.digest(p) for p in Path(folder).iterdir() if p.is_file()}
def spec(path):return dict(path=str(path),sha256=study.source.digest(path))


def inputs(root):
    root.mkdir();salt=root/'constructed.salt';salt.write_bytes(b'constructed-frame-input-salt-0001')
    sources=[]
    for month in study.MONTHS:
        raw=root/(month+'.txt');raw.write_text('constructed source '+month)
        sources.append(dict(month=month,**spec(raw)))
    path=root/'frame.sqlite';con=sqlite3.connect(path);con.execute('PRAGMA journal_mode=WAL')
    con.executescript('CREATE TABLE checkpoints(month TEXT,source TEXT,counts TEXT,complete INTEGER);CREATE TABLE settings(key TEXT,value TEXT);CREATE TABLE frame(player TEXT,month TEXT,tc TEXT,band INTEGER,n INTEGER,rating_sum REAL);')
    con.execute('INSERT INTO settings VALUES(?,?)',('salt_sha256',hashlib.sha256(salt.read_bytes()).hexdigest()))
    for row in sources:
        con.execute('INSERT INTO checkpoints VALUES(?,?,?,1)',(row['month'],row['sha256'],json.dumps(dict(source_games=24))))
        for tc in study.QUOTAS:
            con.executemany('INSERT INTO frame VALUES(?,?,?,?,?,?)',[(f'constructed-{row["month"]}-{tc}-{i}',row['month'],tc,i%2,20,32000.) for i in range(24)])
    con.commit();con.execute('PRAGMA wal_checkpoint(TRUNCATE)');con.close()
    return dict(frame=spec(path),salt=spec(salt)),dict(phase='sample',sources=sources,players=100,constructed_fixture=True)


def observe_input_opens(monkeypatch):
    actual=study.completed_frame;observed=[]
    def observed_open(path):
        path=Path(path);before=inventory(path.parent);con=actual(path)
        assert inventory(path.parent)==before
        class Connection:
            def execute(self,sql,*args):
                cursor=con.execute(sql,*args)
                assert inventory(path.parent)==before
                observed.append(sql)
                return cursor
            def close(self):
                assert inventory(path.parent)==before
                con.close()
                assert inventory(path.parent)==before
        return Connection()
    monkeypatch.setattr(study,'completed_frame',observed_open)
    return observed


def test_prepare_input_stays_immutable_while_open_and_matches_original(tmp_path,monkeypatch):
    bindings,config=inputs(tmp_path/'source');before=inventory(tmp_path/'source')
    observed=observe_input_opens(monkeypatch)
    original_prepare=sampler.prepare
    with study.adapted(tmp_path/'output',config):
        assert sampler.prepare is study.prepare
        actual=sampler.prepare(bindings,config)
    assert sampler.prepare is original_prepare
    assert 'SELECT month,source,counts,complete FROM checkpoints' in observed
    assert "SELECT value FROM settings WHERE key='salt_sha256'" in observed
    assert inventory(tmp_path/'source')==before
    oracle=tmp_path/'oracle.sqlite';shutil.copyfile(bindings['frame']['path'],oracle)
    with previous.selector(tmp_path/'reference',config):
        expected=original_prepare(dict(bindings,frame=spec(oracle)),config)
    assert actual==expected
    assert inventory(tmp_path/'source')==before


def test_prepare_refuses_outstanding_wal_before_reading_stale_frame(tmp_path):
    bindings,config=inputs(tmp_path/'source');path=Path(bindings['frame']['path']);con=sqlite3.connect(path)
    try:
        con.execute('UPDATE frame SET n=21');con.commit();before=inventory(path.parent)
        assert Path(str(path)+'-wal').stat().st_size>0
        with pytest.raises(ValueError,match='not checkpointed'):
            with study.adapted(tmp_path/'out',config):sampler.prepare(bindings,config)
        assert inventory(path.parent)==before
    finally:con.close()


@pytest.mark.parametrize('edit,message',[("UPDATE checkpoints SET complete=0 WHERE month='2017-05'",'Complete source census'),
    ("UPDATE settings SET value='wrong' WHERE key='salt_sha256'",'Campaign salt mismatch')])
def test_prepare_keeps_original_completion_and_salt_checks(tmp_path,edit,message):
    bindings,config=inputs(tmp_path/'source');path=Path(bindings['frame']['path']);con=sqlite3.connect(path)
    con.execute(edit);con.commit();con.close();bindings['frame']=spec(path);before=inventory(path.parent)
    with pytest.raises(ValueError,match=message):
        with study.adapted(tmp_path/'out',config):sampler.prepare(bindings,config)
    assert inventory(path.parent)==before


def test_complete_raw_reference_parity_with_both_prepare_input_connections_observed(tmp_path,monkeypatch):
    observed=observe_input_opens(monkeypatch)
    result=fixture.source_fixture(tmp_path/'full',{},dict(constructed_fixture=True))
    assert result['original_raw_collector_byte_parity'] and result['frame_directory_unchanged']
    assert result['all_raw_sources_replayed']
    assert observed.count('SELECT month,source,counts,complete FROM checkpoints')==2
    assert observed.count("SELECT value FROM settings WHERE key='salt_sha256'")==2
