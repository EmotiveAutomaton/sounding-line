"""Unrun constructed exact-output fixture for CH merge/sample/history adapters.

DESIGN CHECK: LESSONS 2-5. Real original PGN parsing and full source methods
produce the reference. No mock statistics or human source enter this fixture.
Run only under an owner-reviewed counted plan; native pause chains remain a
separate required proof before human admission.
"""
from pathlib import Path
import gzip,json,shutil,sqlite3
from . import week5_ch_source as old
from . import week5_ch_history_index as old_index
from . import week5_ch_merge_bounded as merge
from . import week5_ch_sample_bounded as sample
from . import week5_ch_history_index_bounded as index
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_census_replay import compare
from .week5_ch_fixture import PGN


def spec(path):return dict(path=str(path),sha256=old.digest(path))


def build(root,check=lambda:None):
    root.mkdir(parents=True,exist_ok=False)
    salt=root/'CONSTRUCTED_SALT.bin';salt.write_bytes(b'constructed-ch-pipeline-fixture-20261107')
    names=[];number=0
    while len(names)<2:
        name='constructed-player-'+str(number);number+=1
        if old.selected_history(old.pseudonym(name,salt.read_bytes())):names.append(name)
    sources=[];frames={}
    for month in ('2017-04','2017-05','2026-07'):
        check()
        texts=[]
        for tc in ('60+0','300+2','900+10','1800+0'):
            for game in range(48):
                text=PGN.replace('fixture-white',names[0]).replace('fixture-black',names[1])
                text=text.replace('2017.04.01',month.replace('-','.')+'.01').replace('300+2',tc)
                if game%5==0:text=text.replace(' { [%clk 0:04:58] }','')
                if game%7==0:text=text.replace('0:04:57','0:05:00')
                if game%11==0:text=text.replace('0:04:59','0:00:00')
                texts.append(text)
        path=root/(month+'.pgn');path.write_text('\n'.join(texts),encoding='utf8',newline='\n')
        item=dict(month=month,**spec(path));sources.append(item)
        output=root/('census-'+month)
        old.execute(output,dict(source=spec(path),salt=spec(salt)),dict(phase='census',month=month))
        frames['frame'+str(len(frames))]=spec(output/'PRIVATE_FRAME.sqlite')
    return salt,sources,frames


def table_hash(path,table):
    import hashlib
    con=sqlite3.connect(path);h=hashlib.sha256()
    try:
        n=len(con.execute('PRAGMA table_info('+table+')').fetchall())
        for row in con.execute('SELECT * FROM '+table+' ORDER BY '+','.join(str(i+1) for i in range(n))):
            h.update((json.dumps(row,separators=(',',':'))+'\n').encode())
    finally:con.close()
    return h.hexdigest()


def refuses(callback):
    try:callback()
    except ValueError:return
    raise AssertionError('False source or resealed output was accepted')


def reseal_constructed_copy(root):
    """Deliberately forge only a disposable fixture copy, never a saved attempt."""
    path=root/'SOURCE_SEAL.json';record=json.loads(path.read_text(encoding='utf8'))
    record['files']={name:old.digest(root/name) for name in record['files']}
    path.write_text(json.dumps(record,sort_keys=True)+'\n',encoding='utf8',newline='\n')


def _execute(output,inputs,config,request_root=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if inputs or config!={'constructed_fixture':True}:raise ValueError('Exact source-free constructed fixture required')
    check=lambda:ck.require(output if request_root is None else request_root)
    check()
    salt,sources,frames=build(output/'constructed_inputs',check)
    assert ck.file_digest(salt)==old.digest(salt)
    hash_checks=0
    def stop_hash():
        nonlocal hash_checks
        hash_checks+=1
        if hash_checks==2:raise ck.YieldRequested('constructed partial authentication')
    try:ck.file_digest(salt,stop_hash)
    except ck.YieldRequested:pass
    else:raise AssertionError('Interrupted authentication accepted a partial hash')
    merge_inputs=dict(salt=spec(salt),**frames)
    check()
    old.execute(output/'original_merge',merge_inputs,dict(phase='merge'))
    merge.execute(output/'bounded_merge',merge_inputs,dict(phase='merge'))
    compared=compare(output/'original_merge/PRIVATE_FRAME.sqlite',output/'bounded_merge/PRIVATE_FRAME.sqlite')
    assert (output/'original_merge/SOURCE.json').read_bytes()==(output/'bounded_merge/SOURCE.json').read_bytes()
    assert merge.verify(output/'bounded_merge',merge_inputs,dict(phase='merge'))['verified']
    check()
    frame=output/'bounded_merge/PRIVATE_FRAME.sqlite'
    source_inputs=dict(frame=spec(frame),salt=spec(salt));settings=dict(phase='sample',players=100,sources=sources)
    old.execute(output/'original_sample',source_inputs,settings)
    sample.execute(output/'bounded_sample',source_inputs,settings)
    for name in ('PRIVATE_SELECTED_PLAYERS.json','PRIVATE_POSITIONS.jsonl.gz','SOURCE.json'):
        assert (output/'original_sample'/name).read_bytes()==(output/'bounded_sample'/name).read_bytes(),name
    with gzip.open(output/'bounded_sample/PRIVATE_POSITIONS.jsonl.gz','rt',encoding='utf8') as rows:
        assert sum(1 for _ in rows)>0,'Fixture must exercise actual selected positions'
    assert sample.verify(output/'bounded_sample',source_inputs,settings)['verified']
    check()
    history_inputs=dict(histories=spec(frame))
    old_index.execute(output/'original_index',history_inputs,{})
    index.execute(output/'bounded_index',history_inputs,{})
    assert (output/'original_index/INDEX.json').read_bytes()==(output/'bounded_index/INDEX.json').read_bytes()
    for table in ('player_history','settings'):
        assert table_hash(output/'original_index/PRIVATE_PLAYER_HISTORY.sqlite',table)==table_hash(output/'bounded_index/PRIVATE_PLAYER_HISTORY.sqlite',table)
    assert index.verify(output/'bounded_index',history_inputs,{})['verified']
    check()
    # Unsupported source flags/salts and duplicated months cannot become frames.
    refuses(lambda:merge.source_info(dict(merge_inputs,frame_duplicate=frames['frame0'])))
    wrong_salt=output/'CONSTRUCTED_WRONG_SALT.bin';wrong_salt.write_bytes(b'other constructed salt')
    refuses(lambda:merge.source_info(dict(merge_inputs,salt=spec(wrong_salt))))
    partial=output/'CONSTRUCTED_INCOMPLETE_FRAME.sqlite'
    shutil.copyfile(frames['frame0']['path'],partial)
    con=sqlite3.connect(partial)
    try:con.execute('UPDATE checkpoints SET complete=0');con.commit()
    finally:con.close()
    refuses(lambda:merge.source_info(dict(merge_inputs,frame0=spec(partial))))
    # Fresh source verification must reject even a correctly rehashed false
    # execution result. Originals and their complete byte hashes stay intact.
    copied=output/'tampered_merge';shutil.copytree(output/'bounded_merge',copied)
    con=sqlite3.connect(copied/'PRIVATE_FRAME.sqlite')
    try:
        con.execute('UPDATE frame SET n=n+1')
        con.commit()
    finally:con.close()
    reseal_constructed_copy(copied)
    refuses(lambda:merge.verify(copied,merge_inputs,dict(phase='merge')))
    check()
    copied_sample=output/'tampered_sample';shutil.copytree(output/'bounded_sample',copied_sample)
    with gzip.open(copied_sample/'PRIVATE_POSITIONS.jsonl.gz','ab') as stream:stream.write(b'{}\n')
    reseal_constructed_copy(copied_sample)
    refuses(lambda:sample.verify(copied_sample,source_inputs,settings))
    check()
    copied_index=output/'tampered_index';shutil.copytree(output/'bounded_index',copied_index)
    con=sqlite3.connect(copied_index/'PRIVATE_PLAYER_HISTORY.sqlite')
    try:
        player,month,game,payload=con.execute('SELECT player,month,game,payload FROM player_history LIMIT 1').fetchone()
        false=json.loads(payload);false['result']=42
        con.execute('UPDATE player_history SET payload=? WHERE player=? AND month=? AND game=?',
                    (json.dumps(false,sort_keys=True,separators=(',',':')),player,month,game));con.commit()
    finally:con.close()
    reseal_constructed_copy(copied_index)
    refuses(lambda:index.verify(copied_index,history_inputs,{}))
    result=dict(passed=True,constructed=True,source_months=3,source_games=576,
                merged_scientific_table_rows=compared,exact_selection_and_position_gzip=True,
                original_history_payloads_and_receipt_equal=True,
                complete_hash_and_interrupted_hash_refusal=True,
                source_scope_refusals=3,rehashed_false_output_refusals=3,
                all_adapter_independent_verifiers_passed=True,
                actual_counted_pause_integration_still_required=True,
                selected_sha256=old.digest(output/'bounded_sample/PRIVATE_SELECTED_PLAYERS.json'),
                positions_sha256=old.digest(output/'bounded_sample/PRIVATE_POSITIONS.jsonl.gz'),
                history_contents_sha256=json.loads((output/'bounded_index/INDEX.json').read_text())['contents_sha256'])
    old.write_json(output/'FIXTURE.json',result)
    return dict(status='complete',constructed=True)


def _verify(output,inputs,config):
    output=Path(output);ck.require(output)
    _execute(output/'fresh_independent',inputs,config,request_root=output)
    ck.require(output)
    if (output/'FIXTURE.json').read_bytes()!=(output/'fresh_independent/FIXTURE.json').read_bytes():raise ValueError('Independent whole-fixture replay differs')
    return dict(verified=True,complete_recalculation=True,constructed=True)


def execute(output,inputs,config):return ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config):return ck.guarded(_verify,output,inputs,config)
