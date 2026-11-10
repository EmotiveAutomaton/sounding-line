import json,sqlite3
from pathlib import Path
import pytest
from runners.drive.cards import week5_ch_progress as p
from runners.drive.cards import week5_ch_history_index as index
from runners.drive.cards.week5_ch_source import digest


def test_checkpoint_resume_only_reuses_bound_completed_draws(tmp_path):
    first=tmp_path/'first';first.mkdir();seen=[]
    with pytest.raises(p.YieldRequested):
        with p.tracking(first,{'source':{'sha256':'frozen'}},{'draws':20}):
            key=p.begin('known-values',20)
            for i in range(20):
                def compute():
                    seen.append(i)
                    if i==5:(first/'YIELD_REQUEST.json').write_text('{}')
                    return i*i
                p.value(key,i,compute)
    assert seen==list(range(6))
    inputs={'source':{'sha256':'frozen'},'resume_analysis':{'path':str(first/'CHECKPOINT.json'),'sha256':digest(first/'CHECKPOINT.json')}}
    values=[];seen=[]
    with p.tracking(tmp_path/'second',inputs,{'draws':20}):
        key=p.begin('known-values',20)
        for i in range(20):
            def compute():seen.append(i);return i*i
            values.append(p.value(key,i,compute))
    assert seen==list(range(6,20)) and values==[i*i for i in range(20)]
    with pytest.raises(ValueError,match='configuration changed'):
        with p.tracking(tmp_path/'invalid',inputs,{'draws':21}):pass


def test_history_projection_checkpoint_new_attempt_resume_equals_full(tmp_path):
    source=tmp_path/'raw.sqlite';con=sqlite3.connect(source);con.executescript('CREATE TABLE histories(month TEXT,ordinal INT,payload TEXT);CREATE TABLE settings(key TEXT,value TEXT);');con.execute("INSERT INTO settings VALUES('constructed_fixture','true')")
    for ordinal in range(1002):
        game=dict(game=str(ordinal),meta=dict(players=['constructed','other'],start=ordinal*100,end=None,initial=300,increment=2,time_control='blitz',rating_changes=[1,-1],result='1-0'),rows=[dict(player='constructed',ply=21,clock_before=200,think_time=3)],first_clocks=[300,300])
        con.execute('INSERT INTO histories VALUES(?,?,?)',('2017-04',ordinal,json.dumps(game)))
    con.commit();con.close();inputs={'histories':{'path':str(source),'sha256':digest(source)}}
    first=tmp_path/'first';first.mkdir();(first/'YIELD_REQUEST.json').write_text('{}')
    paused=index.execute(first,inputs,{'constructed_fixture':True});assert paused['status']=='yielded' and paused['player_games']==1000
    checkpoint=first/'PRIVATE_PLAYER_HISTORY.sqlite';resumed=index.execute(tmp_path/'second',dict(inputs,resume_index={'path':str(checkpoint),'sha256':digest(checkpoint)}),{'constructed_fixture':True})
    assert resumed['status']=='complete' and resumed['player_games']==1002
    assert index.verify(tmp_path/'second',dict(inputs,resume_index={'path':str(checkpoint),'sha256':digest(checkpoint)}),{'constructed_fixture':True})['verified']
    store=index.HistoryStore(tmp_path/'second/PRIVATE_PLAYER_HISTORY.sqlite',constructed=True)
    try:assert len(store)==1 and len(store['constructed'])==1002
    finally:store.close()
