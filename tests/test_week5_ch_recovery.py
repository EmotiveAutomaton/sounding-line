import sqlite3,json
from runners.drive.cards.week5_ch_census_recovery import snapshot
from runners.drive.cards.week5_ch_source import open_database

def test_committed_wal_copied_without_changing_source(tmp_path):
    source=tmp_path/'old.sqlite';con=open_database(source)
    try:
        con.execute("INSERT INTO settings VALUES('salt_sha256','constructed')")
        con.execute('INSERT INTO checkpoints VALUES(?,?,?,?,?)',('2017-05',2,'source',json.dumps({'source_games':3}),0))
        con.execute('INSERT INTO histories VALUES(?,?,?)',('2017-05',2,'{}'));con.commit()
        result=snapshot(source,tmp_path/'recovered')
        assert result['ordinal']==2 and result['census']['source_games']==3 and result['table_rows']['histories']==1
        assert 'old.sqlite-wal' in result['retained_member_pins'] and result['full_source_replay_required']
        assert not result['prefix_independently_verified']
    finally:con.close()
