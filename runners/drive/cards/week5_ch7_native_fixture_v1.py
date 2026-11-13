"""Prepared complete CH7 source and numerical native qualification; no launch.

The earlier focused fixture remains intact. This additional counted handler
exercises the enriched real-source adapter with constructed raw game payloads,
then all three complete numerical cases, including the joint shape rules.
"""
from pathlib import Path
import json
import sqlite3
from . import week5_ch7_fixture_v1 as numerical
from . import week5_ch7_source_v1 as source
from .week5_ch_source import digest,write_json


def source_case(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    raw=output/'PRIVATE_CONSTRUCTED_RAW.sqlite'
    con=sqlite3.connect(raw)
    con.executescript('CREATE TABLE histories(month TEXT,ordinal INTEGER,payload TEXT,PRIMARY KEY(month,ordinal));CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT);')
    con.execute("INSERT INTO settings VALUES('constructed_fixture','true')")
    expected=[]
    for i,month in enumerate(source.MONTHS):
        payload=dict(game=f'constructed-source-{i}',meta=dict(players=['constructed-one','constructed-two'],
            ratings=[1500+i,1450+i],start=1500000000+i*2678400,end=None,initial=300,increment=2,
            time_control='blitz',rating_changes=[5,-5],result='1-0'),first_clocks=[300,300],
            rows=[dict(player='constructed-one',ply=1,clock_before=300,think_time=3),
                  dict(player='constructed-two',ply=2,clock_before=300,think_time=4)])
        text=json.dumps(payload,sort_keys=True);con.execute('INSERT INTO histories VALUES(?,?,?)',(month,i,text))
        expected.extend((player,month,value['game'],json.dumps(value,sort_keys=True,separators=(',',':')))
                        for player,value in source.projected(month,i,text))
    con.commit();con.close()
    inputs=dict(histories=dict(path=str(raw),sha256=digest(raw)));config=dict(constructed_fixture=True)
    target=output/'projection'
    if source.execute(target,inputs,config)['status']!='complete':raise AssertionError('Source fixture did not finish')
    if not source.verify(target,inputs,config).get('verified'):raise AssertionError('Full raw source replay failed')
    con=sqlite3.connect(target/'PRIVATE_PLAYER_HISTORY.sqlite')
    try:actual=con.execute('SELECT player,month,game,payload FROM player_history ORDER BY player,month,game').fetchall()
    finally:con.close()
    if actual!=sorted(expected):raise AssertionError('Constructed complete source projection differs')
    write_json(output/'SOURCE_FIXTURE.json',dict(passed=True,source_games=3,player_games=6,
        full_raw_replay=True,contents_sha256=json.loads((target/'INDEX.json').read_text())['contents_sha256']))


def execute(output,inputs,config):
    if inputs or config!={'constructed_fixture':True}:raise ValueError('Exact source-free fixture required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    source_case(output/'source')
    numerical.execute(output/'numerical',inputs,config)
    for case,expected in [('null','mixed'),('floor','floor'),('ladder','ladder')]:
        result=json.loads((output/'numerical'/case/'analysis/SCIENCE.json').read_text())
        if result['pattern']!=expected:raise AssertionError(f'Constructed {case} joint shape rule failed')
        if case=='null' and result['verdict']!='against':raise AssertionError('Null world did not return inside-band primary')
    write_json(output/'QUALIFICATION.json',dict(passed=True,constructed_only=True,source_full_replay=True,
        full_numerical_cases=3,bootstrap_draws=2000,null_histories=20,scientific_admission=False))
    return dict(status='complete',constructed_fixture=True)


def verify(output,inputs,config):
    output=Path(output);fresh=output/'independent_native'
    execute(fresh,inputs,config)
    for case in ('null','floor','ladder'):
        a=output/'numerical'/case/'analysis/SCIENCE.json';b=fresh/'numerical'/case/'analysis/SCIENCE.json'
        if digest(a)!=digest(b):raise ValueError('Fresh complete native numerical outputs differ')
    for relative in ('source/SOURCE_FIXTURE.json','QUALIFICATION.json'):
        if digest(output/relative)!=digest(fresh/relative):raise ValueError('Fresh complete native source proof differs')
    return dict(verified=True,complete_raw_and_numerical_replay=True)
