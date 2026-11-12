"""Constructed-only checks; no real source rows, engines or native starts."""
from pathlib import Path
import json
import shutil
import sqlite3

import pytest
from runners.drive.cards import week5_ch_backhalf_roster_v1 as roster
from runners.drive.cards import week5_ch_queue_backhalf_v1 as queue
from runners.drive.cards import week5_ch_engine_bounded as engine
from runners.drive.cards import week5_ch_collection_backhalf_v1 as collection
from runners.drive.cards.week5_ch_collection import write_rows
from runners.drive.cards.week5_ch_source import digest,write_json


def frame(path):
    con=sqlite3.connect(path)
    con.execute('CREATE TABLE checkpoints(month TEXT,complete INTEGER)')
    con.execute('CREATE TABLE frame(player TEXT,month TEXT,tc TEXT,band INTEGER,n INTEGER,rating_sum REAL)')
    con.executemany('INSERT INTO checkpoints VALUES(?,1)',[(m,) for m in roster.MONTHS])
    rows=[]
    for tc in roster.QUOTAS:
        for mi,month in enumerate(roster.MONTHS):
            for i in range(80*(mi+1)):
                rows.append((f'constructed-{tc}-{mi}-{i}',month,tc,i%2,20,32000.))
    # Repeated identities remain a single assigned player, regardless of input order.
    rows += [('constructed-overlap',m,'blitz',4,20,32000.) for m in roster.MONTHS]
    con.executemany('INSERT INTO frame VALUES(?,?,?,?,?,?)',rows)
    con.commit();con.close()


def test_integer_proportions_ties_support():
    assert roster.allocate({'a':1,'b':1,'c':1},2)=={'a':1,'b':1,'c':0}
    assert roster.allocate({'a':1,'b':2},20)=={'a':1,'b':2}
    assert roster.allocate({'a':0,'b':0},3)=={'a':0,'b':0}
    with pytest.raises(ValueError):roster.allocate({'a':True},1)


def test_unique_player_three_months_and_proportional_roster(tmp_path):
    path=tmp_path/'frame.sqlite';frame(path)
    selected,counts=roster.choose_players(path,100,constructed=True)
    assert len(selected)==len({r['player'] for r in selected})==100
    assert {k:v['selected'] for k,v in counts.items()}=={'blitz':70,'bullet':10,'rapid':10,'classical':10}
    for tc,record in counts.items():
        support={m:v['assigned_unique_eligible'] for m,v in record['months'].items()}
        assert {m:v['selected'] for m,v in record['months'].items()}==roster.allocate(support,record['target'])
    assert roster.choose_players(path,100,constructed=True)==(selected,counts)
    with pytest.raises(ValueError,match='10,000'):roster.choose_players(path,100)
    con=sqlite3.connect(path);con.execute("INSERT INTO checkpoints VALUES('2026-07',1)");con.commit();con.close()
    with pytest.raises(ValueError,match='three complete'):roster.choose_players(path)


def test_shortfall_is_recorded_not_reallocated(tmp_path):
    path=tmp_path/'frame.sqlite';frame(path)
    selected,counts=roster.choose_players(path)
    assert len(selected)<10000
    assert all(v['selected']==v['eligible'] for v in counts.values())
    assert sum(v['shortfall'] for v in counts.values())==10000-len(selected)


class FakeScorer:
    calls=[]
    def __init__(self,path,nodes):self.nodes=nodes
    def score(self,row):
        self.calls.append(row['ordinal'])
        return dict(position=row,node_limit=self.nodes,threads=1,hash_mb=64,engine=dict(k50=1))
    def close(self):pass


def queue_world(tmp_path,monkeypatch):
    rows=[dict(ordinal=i,fen='constructed',uci='e2e4',month=roster.MONTHS[i%3],player='constructed-'+str(i)) for i in range(6)]
    write_rows(tmp_path/'positions.gz',rows)
    (tmp_path/'engine').write_bytes(b'constructed-only')
    inputs={name:dict(path=str(path),sha256=digest(path)) for name,path in
            [('positions',tmp_path/'positions.gz'),('engine',tmp_path/'engine')]}
    monkeypatch.setattr(engine,'Scorer',FakeScorer)
    FakeScorer.calls=[]
    def native(unit,operation,output):
        invocation=unit/'native'/(operation+'-000001');invocation.mkdir(parents=True)
        plan=queue.read(unit/'UNIT.json')
        result=getattr(engine,operation)(unit/'output',plan['inputs'],plan['config'])
        # Mock native evidence exercises sealing; this is never a native proof.
        write_json(invocation/'RESULT.json',result)
        write_json(invocation/'NATIVE.json',dict(pid=11 if operation=='execute' else 12,constructed_mock=True))
        write_json(invocation/(operation.upper()+'_JOB_USAGE.json'),dict(cpu_seconds=0.,exit_code=0,includes_all_descendants_and_exited_processes=True,constructed_mock=True))
        return result,invocation.relative_to(unit).as_posix()
    monkeypatch.setattr(queue,'native_operation',native)
    return inputs,dict(expected_positions=6,offset=0,unit_positions=2,nodes=1000000,queue_wall_seconds=3600,constructed_fixture=True)


def copy_attempt(old,new):
    saved={p.relative_to(old).as_posix():digest(p) for p in old.rglob('*') if p.is_file()}
    shutil.copytree(old,new)
    write_json(new.parent/'RESUMED_FROM.json',dict(copied=saved))
    return saved


def test_queue_closed_unit_pause_resume_full_roster_replay(tmp_path,monkeypatch):
    inputs,config=queue_world(tmp_path,monkeypatch)
    # Leave room for one unit; the 1,800-second production minimum is a reserve.
    config['queue_wall_seconds']=3600
    old=tmp_path/'old/output'
    assert queue.execute(old,inputs,{**config,'max_new_draws':2})['status']=='yielded'
    assert sorted(FakeScorer.calls)==[0,0,1,1]
    new=tmp_path/'new/output';snapshot=copy_attempt(old,new)
    assert queue.execute(new,inputs,config)['end']==6
    assert queue.verify(new,inputs,config)['every_score_covered']
    assert snapshot=={p.relative_to(old).as_posix():digest(p) for p in old.rglob('*') if p.is_file()}
    assert sorted(FakeScorer.calls)==sorted(list(range(6))*2)
    batches=queue.read(new/'QUEUE_BATCHES.json')['batches']
    assert len(batches)==3


def test_queue_sealed_score_and_extra_file_refuse(tmp_path,monkeypatch):
    inputs,config=queue_world(tmp_path,monkeypatch);config['queue_wall_seconds']=3600
    out=tmp_path/'attempt/output';queue.execute(out,inputs,config)
    unit=next((out/'units').iterdir());path=next((unit/'output/PRIVATE_SCORES').glob('*.json'))
    saved=path.read_bytes();path.write_bytes(b'{}')
    with pytest.raises(ValueError,match='changed'):queue.verify(out,inputs,config)
    path.write_bytes(saved);(unit/'unbound.json').write_bytes(b'{}')
    with pytest.raises(ValueError,match='extra'):queue.verify(out,inputs,config)


def test_queue_final_verifier_pauses_and_resumes_with_authenticated_copy(tmp_path,monkeypatch):
    inputs,config=queue_world(tmp_path,monkeypatch);config['queue_wall_seconds']=3600
    old=tmp_path/'old/output';queue.execute(old,inputs,config)
    require=queue.ck.require
    def pause(root):
        checkpoint=Path(root)/'QUEUE_VERIFY_CHECKPOINT.json'
        if checkpoint.exists() and len(queue.read(checkpoint)['verified_units'])==1:
            raise queue.ck.YieldRequested('Constructed verifier boundary')
        require(root)
    monkeypatch.setattr(queue.ck,'require',pause)
    assert queue.verify(old,inputs,config)['status']=='yielded'
    monkeypatch.setattr(queue.ck,'require',require)
    new=tmp_path/'new/output';copy_attempt(old,new)
    assert queue.execute(new,inputs,config)['sealed_queue_reused']
    assert queue.verify(new,inputs,config)['verified']


def collection_world(root,heldout_choice='e2e4'):
    root.mkdir();scores=root/'scores';scores.mkdir();rows=[];bindings={}
    for mi,month in enumerate(roster.MONTHS):
        for i in range(24):
            row=dict(player=f'constructed-{mi}-{i}',ordinal=mi*24+i,month=month,rating=1600,fen='constructed',
                     uci=('e2e4' if i%4 else 'd2d4') if mi==0 else heldout_choice)
            rows.append(row)
            value=dict(position=row,node_limit=1000000,engine=dict(mate_sentinel_used=False,
                       top=[dict(move='e2e4',cp=0),dict(move='d2d4',cp=-50)],k50=2))
            file=scores/(collection.engine.score_key(row,1000000)+'.json');write_json(file,value);bindings[file.name]=digest(file)
    write_rows(root/'positions.gz',rows)
    write_json(root/'verify.json',dict(all_scores_equal=True,verified_positions=72))
    write_json(root/'batch.json',dict(node_limit=1000000,new_positions=72,reused_positions=0))
    write_json(root/'bindings.json',bindings)
    def spec(name):return dict(path=str(root/name),sha256=digest(root/name))
    batch=dict(path=str(scores),verify=spec('verify.json'),report=spec('batch.json'),score_bindings=spec('bindings.json'))
    write_json(root/'batches.json',dict(batches=[batch]))
    return dict(positions=spec('positions.gz'),batches=spec('batches.json'))


def test_april_only_temperature_and_all_april_entropy_excluded(tmp_path):
    config=dict(expected_positions=72,constructed_fixture=True)
    a=collection_world(tmp_path/'a');b=collection_world(tmp_path/'b','d2d4')
    for name,inputs in [('a',a),('b',b)]:
        out=tmp_path/name/'output'
        assert collection.execute(out,inputs,config)['status']=='complete'
        assert collection.verify(out,inputs,config)['verified']
    fit_a=queue.read(tmp_path/'a/output/TEMPERATURES.json')['fits']
    fit_b=queue.read(tmp_path/'b/output/TEMPERATURES.json')['fits']
    assert fit_a==fit_b and all(f['calibration_month']=='2017-04' for f in fit_a)
    rows=list(queue.scorer.iter_positions(tmp_path/'a/output/PRIVATE_ANALYTICAL_ROWS.jsonl.gz'))
    assert all(r['entropy'] is None and r['entropy_fixed100'] is None for r in rows if r['month']=='2017-04')
    assert all(r['entropy'] is not None for r in rows if r['month']!='2017-04')
