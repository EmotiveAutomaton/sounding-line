import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_ch_collection as c
from runners.drive.cards.week5_ch_source import write_json,digest
from runners.drive.cards.week5_ch_engine import score_key


def world(tmp_path,drop_last=False):
    positions=[];scores=tmp_path/'scores';scores.mkdir();bindings={}
    for i in range(60):
        row=dict(player=str(i%10),month='2017-04' if i<30 else '2017-05',rating=1600,uci='e2e4' if i%3 else 'd2d4',fen='constructed',ordinal=i)
        positions.append(row)
        if drop_last and i==59:continue
        value=dict(position=row,engine=dict(mate_sentinel_used=False,top=[dict(move='e2e4',cp=0),dict(move='d2d4',cp=-50)],k50=2),node_limit=1000000)
        path=scores/(score_key(row,1000000)+'.json');write_json(path,value);bindings[path.name]=digest(path)
    c.write_rows(tmp_path/'positions.gz',positions)
    write_json(tmp_path/'verify.json',dict(all_scores_equal=True,verified_positions=len(bindings)))
    write_json(tmp_path/'batch.json',dict(node_limit=1000000,new_positions=len(bindings),reused_positions=0))
    write_json(tmp_path/'bindings.json',bindings)
    def spec(name):return dict(path=str(tmp_path/name),sha256=digest(tmp_path/name))
    batch=dict(path=str(scores),verify=spec('verify.json'),report=spec('batch.json'),score_bindings=spec('bindings.json'))
    return positions,batch,spec


def test_complete_population_requires_every_frozen_row(tmp_path):
    _,batch,_=world(tmp_path,True)
    with pytest.raises(ValueError,match='Incomplete frozen roster'):c.collect(tmp_path/'positions.gz',[batch])


def test_complete_collection_and_duplicate_refusal(tmp_path):
    positions,batch,_=world(tmp_path)
    rows,report=c.collect(tmp_path/'positions.gz',[batch]);assert len(rows)==60 and report['players']==10
    with pytest.raises(ValueError,match='Duplicate scored'):c.collect(tmp_path/'positions.gz',[batch,batch])
    path=next((tmp_path/'scores').glob('*.json'));path.write_text('{}')
    with pytest.raises(ValueError,match='Score changed'):c.collect(tmp_path/'positions.gz',[batch])


def test_calibration_month_never_uses_own_outcome(tmp_path):
    _,batch,_=world(tmp_path);rows,_=c.collect(tmp_path/'positions.gz',[batch]);first,_=c.with_entropy(rows)
    changed=[dict(r,uci='d2d4') if r['month']=='2017-04' else r for r in rows];second,_=c.with_entropy(changed)
    assert [r['entropy'] for r in first if r['month']=='2017-04']==[r['entropy'] for r in second if r['month']=='2017-04']
    assert [r['entropy'] for r in first if r['month']=='2017-05']!=[r['entropy'] for r in second if r['month']=='2017-05']


def test_complete_collection_serialized_replay(tmp_path):
    _,batch,spec=world(tmp_path);write_json(tmp_path/'batches.json',dict(batches=[batch]));inputs=dict(positions=spec('positions.gz'),batches=spec('batches.json'))
    c.execute(tmp_path/'output',inputs,dict(constructed_fixture=True));assert c.verify(tmp_path/'output',inputs,dict(constructed_fixture=True))['verified']
    rows=tmp_path/'output/PRIVATE_ANALYTICAL_ROWS.jsonl.gz';receipt=tmp_path/'output/COLLECTION.json'
    with pytest.raises(ValueError,match='constructed'):c.load_complete(dict(scores=dict(path=str(rows),sha256=digest(rows)),collection=dict(path=str(receipt),sha256=digest(receipt))))


def test_grid_unique_all_declared_primary_and_texture_routes():
    from runners.drive.cards.week5_ch_grid import grid
    rows=grid()['cells'];assert len({r['id'] for r in rows})==len(rows)
    assert {r['id'] for r in rows if r['kind']=='primary'}=={'CH2','CH3','CH4','CH5','CH6'}
    assert all(r['config']['draws']==200 for r in rows if r['kind']=='texture')
    assert all(r['cpu_ceiling']<=3600 for r in rows if r['kind']=='texture' and 'rescore_positions' not in r)
