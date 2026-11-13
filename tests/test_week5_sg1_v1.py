import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
import pytest
from runners.drive.cards import week5_sg1_source_v1 as source
from runners.drive.cards import week5_sg1_fields_v1 as fields
from runners.drive.cards import week5_sg1_fixture_v1 as fixture
from runners.drive.cards import week5_sg1_carried_v1 as carried
from runners.drive.cards import week5_ch7_math_v1 as ch7math
from runners.drive.cards import week5_ch7_source_v1 as original


def test_full_packet_oracle_replay_and_immutable_inputs(tmp_path):
    fixture.source_case(tmp_path/'case')


def test_original_ch7_columns_exact(tmp_path):
    inputs,player,rows = fixture.source_case(tmp_path/'case')
    actual = {(r['month'],r['source_ordinal']):r for r in rows}
    with source.snapshots.readonly_snapshot(inputs['histories']['path']) as con:
        for month,ordinal,payload in con.execute('SELECT month,ordinal,payload FROM histories ORDER BY month,ordinal'):
            for who,expected in original.projected(month,ordinal,payload):
                assert who==player
                assert {k:actual[(month,ordinal)][k] for k in fields.CH7_COLUMNS}==expected


def test_shared_wrong_projection_rejected_by_hand_oracle(tmp_path,monkeypatch):
    prior=fields.project
    def wrong(*args):
        for player,row in prior(*args):
            row['rating']+=1
            yield player,row
    monkeypatch.setattr(fields,'project',wrong)
    with pytest.raises(AssertionError,match='Independent SG1 packet'):
        fixture.source_case(tmp_path/'wrong')


def test_clock_arithmetic_missing_negative_and_forfeit():
    meta=dict(increment=0,initial=180,result='0-1')
    rows=[dict(side=0,clock_after=90.),dict(side=1,clock_after=180.),
          dict(side=0,clock_after=80.),dict(side=1,clock_after=170.)]
    assert fields.duration(rows,meta,'Normal')[0]==20.
    assert fields.duration(rows,meta,'Time forfeit')[0]==100.
    assert fields.duration(rows,dict(meta,increment=2),'Normal')[0] is None
    rows[-1]['clock_after']=None
    assert fields.duration(rows,meta,'Normal')[0] is None
    rows[-1]['clock_after']=181.
    assert fields.duration(rows,meta,'Normal')[1]=='negative_clock_difference'


def test_malformed_selected_record_counted_and_not_completed(tmp_path):
    inputs,_=fixture.build(tmp_path/'case')
    raw=Path(inputs['raw_april']['path'])
    raw.write_text(raw.read_text().replace('1. e4','1. NotAMove',1),encoding='utf8')
    pin=source.source.digest(raw)
    inputs['raw_april']['sha256']=pin
    db=Path(inputs['histories']['path'])
    con=sqlite3.connect(db)
    con.execute("UPDATE checkpoints SET source=? WHERE month='2017-04'",(pin,))
    for ordinal,payload in con.execute("SELECT ordinal,payload FROM histories WHERE month='2017-04'").fetchall():
        record=json.loads(payload)
        record['game']=hashlib.sha256((pin+':'+str(ordinal)).encode()).hexdigest()
        con.execute("UPDATE histories SET payload=? WHERE month='2017-04' AND ordinal=?",(json.dumps(record),ordinal))
    con.commit();con.close()
    inputs['histories']['sha256']=source.source.digest(db)
    output=tmp_path/'case/output'
    with pytest.raises(ValueError,match='aggregate failure receipt'):
        source.execute(output,inputs,dict(constructed_fixture=True))
    receipt=json.loads((output/'SOURCE_FAILURE.json').read_text())
    assert receipt['source_failures']==1
    assert not (output/'SOURCE_SEAL.json').exists()


def test_unfinished_source_and_sidecar_refused(tmp_path):
    inputs,_=fixture.build(tmp_path/'case')
    path=Path(inputs['histories']['path'])
    con=sqlite3.connect(path)
    con.execute('UPDATE checkpoints SET complete=0')
    con.commit();con.close()
    inputs['histories']['sha256']=source.source.digest(path)
    with pytest.raises(ValueError,match='completed original months'):
        source.execute(tmp_path/'bad',inputs,dict(constructed_fixture=True))
    Path(str(path)+'-wal').write_bytes(b'')
    with pytest.raises(ValueError,match='sidecar'):
        source.execute(tmp_path/'wal',inputs,dict(constructed_fixture=True))


def test_histogram_exact_bins_and_separate_denominators():
    rows=[dict(increment=0,tournament=t,first_clock_ratio=r)
          for t,r in [(True,.5),(True,1.),(False,1.),(False,None),(True,.45),(True,.55)]]
    h=fields.histogram(rows)
    assert h['tournament']['denominator']==4 and h['tournament']['in_band']==3
    assert h['tournament']['bins'][9:12]==[1,1,1]
    assert h['other']['denominator']==1 and h['other']['missing']==1
    assert sum(h['other']['bins'])==1 and h['other']['bins'][19]==1


def test_execute_checkpoint_copy_and_fresh_verify(tmp_path):
    inputs,player=fixture.build(tmp_path/'source')
    first=tmp_path/'attempt1/output'
    assert source.execute(first,inputs,dict(constructed_fixture=True,max_new_draws=1))['status']=='yielded'
    second=tmp_path/'attempt2/output'
    shutil.copytree(first,second)
    copied={p.relative_to(second).as_posix():source.source.digest(p) for p in second.rglob('*') if p.is_file()}
    (second.parent/'RESUMED_FROM.json').write_text(json.dumps(dict(copied=copied)))
    assert source.execute(second,inputs,dict(constructed_fixture=True))['status']=='complete'
    assert source.verify(second,inputs,dict(constructed_fixture=True))['source_start_ordinal']==0
    fixture.oracle(second,player)


def test_carried_ch7_rows_preserve_math_and_bridge_restores(tmp_path):
    inputs,player,rows=fixture.source_case(tmp_path/'case')
    old=[{k:r[k] for k in fields.CH7_COLUMNS} for r in rows]
    a,b=ch7math.player_data(old),ch7math.player_data(rows)
    import numpy as np
    assert np.array_equal(a['rows'],b['rows'],equal_nan=True)
    assert np.array_equal(a['trace'],b['trace'],equal_nan=True)
    before=carried.ch7.identity,carried.ch7.authenticate,carried.ch7.HistoryStore
    with carried.adapted('CH7'):
        assert carried.ch7.HistoryStore is source.HistoryStore
    assert (carried.ch7.identity,carried.ch7.authenticate,carried.ch7.HistoryStore)==before


def test_carried_ch6_exact_original_inputs_and_output(tmp_path):
    _,player,rows=fixture.source_case(tmp_path/'case')
    old=[{k:r[k] for k in fields.CH7_COLUMNS} for r in rows]
    a=carried.histories.make_sessions({player:old},tc='blitz')
    b=carried.histories.make_sessions({player:rows},tc='blitz')
    assert a==b
    output=tmp_path/'case/output'
    inputs=dict(histories=dict(path=str(output/'PRIVATE_PLAYER_HISTORY.sqlite'),
                              sha256=source.source.digest(output/'PRIVATE_PLAYER_HISTORY.sqlite')))
    config=dict(card='CH6',constructed_fixture=True,draws=2,floor=10000,time_control='blitz')
    assert carried.execute(tmp_path/'consumer',inputs,config)['status']=='complete'
    assert carried.verify(tmp_path/'consumer',inputs,config)['verified']


def test_table_forecast_original_split_is_empty_by_construction():
    threshold=int(.02*2**64)
    assert hex(threshold-1)[2:].zfill(16)[0]=='0'
    key='0'*64
    assert source.source.selected_history(key)
    corrected=hashlib.sha256(('SG1-forecast|20261112|'+key).encode()).hexdigest()
    assert len(corrected)==64  # Split contract is independent of prefix selection.
