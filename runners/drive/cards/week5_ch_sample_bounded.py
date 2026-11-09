"""Transactional full-source CH1 sample, preserving original selection exactly.

DESIGN CHECK: LESSONS 2-5. Complete censuses determine the original frozen
players before clocks or engine outputs. All source ordinals are visited; saved
candidate lists retain exact hash order and missingness. Verification starts the
raw stream at ordinal zero and compares every output byte with execution.
"""
from pathlib import Path
from collections import Counter
import gzip,hashlib,io,json,math,sqlite3
from . import week5_ch_source as original
from . import week5_ch_pipeline_checkpoint as ck


def identity(inputs,config):
    if config.get('phase')!='sample':raise ValueError('Sample phase required')
    return ck.binding(inputs,config,dict(adapter=original.digest(__file__),source=original.digest(original.__file__)))


def prepare(inputs,config,check=None):
    frame=ck.checked(inputs['frame'],check);salt=ck.checked(inputs['salt'],check).read_bytes()
    con=sqlite3.connect(frame)
    try:
        stamps={m:(s,json.loads(c),complete) for m,s,c,complete in con.execute('SELECT month,source,counts,complete FROM checkpoints')}
        if not stamps or any(not x[2] for x in stamps.values()):raise ValueError('Complete source census required')
        if con.execute("SELECT value FROM settings WHERE key='salt_sha256'").fetchone()!=(hashlib.sha256(salt).hexdigest(),):raise ValueError('Campaign salt mismatch')
    finally:con.close()
    sources=config['sources']
    if len({s['month'] for s in sources})!=len(sources) or set(s['month'] for s in sources)!=set(stamps):raise ValueError('Source roster must exactly match all census months')
    for spec in sources:
        ck.checked(spec,check)
        if stamps[spec['month']][0]!=spec['sha256']:raise ValueError('Raw source does not match counted month')
    selected,counts=original.choose_players(frame,config.get('players',10000))
    return salt,sources,selected,counts,sum(x[1]['source_games'] for x in stamps.values())


def run(output,request_root,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);bound=identity(inputs,config)
    control=ck.Control(output,request_root,config,operation)
    check=lambda:ck.require(request_root)
    salt,sources,selected,frame,total=prepare(inputs,config,check)
    original.write_json(output/'PRIVATE_SELECTED_PLAYERS.json',selected)
    wanted={(r['month'],r['player']):r for r in selected}
    db=output/'PRIVATE_SAMPLING.sqlite';exists=db.exists()
    if exists and operation=='execute':ck.copied(db,request_root,check)
    con=sqlite3.connect(db);con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=FULL')
    con.execute('CREATE TABLE IF NOT EXISTS candidates(player TEXT PRIMARY KEY,games TEXT)')
    state=ck.initialize(con,bound,dict(source=0,ordinal=-1,done=0,counts={}))
    if operation=='verify':
        # This is only this new attempt's copied scratch. The predecessor stays
        # intact, and no original source or execution candidate is cleared.
        con.execute('DELETE FROM candidates');state=dict(source=0,ordinal=-1,done=0,counts={})
        ck.put(con,'state',state);con.commit()
    counts=Counter(state['counts'])
    since=0
    def save():
        nonlocal since
        state['counts']=dict(counts);ck.put(con,'state',state);con.commit()
        control.tick(since,state['done'],total);since=0
    try:
        for i,spec in enumerate(sources):
            if i<state['source']:continue
            done=state['ordinal'] if i==state['source'] else -1
            with original.source_stream(spec['path']) as stream:
                for ordinal,text in enumerate(original.records(stream)):
                    if ordinal<=done:
                        if ordinal%100==0 and control.stop():
                            save();return control.yielded(state['done'],total)
                        continue
                    if (ordinal%100==0 or since>=1000) and control.stop():
                        save();return control.yielded(state['done'],total)
                    meta,reason=original.decode_headers(text,salt);month=spec['month']
                    if not reason and any((month,p) in wanted for p in meta['players']):
                        try:rows,_,_=original.parse_game(text,meta)
                        except ValueError:counts['parse_failure']+=1
                        else:
                            game=hashlib.sha256((spec['sha256']+':'+str(ordinal)).encode()).hexdigest()
                            for player in meta['players']:
                                key=(month,player)
                                if key not in wanted or meta['time_control']!=wanted[key]['time_control']:continue
                                moves=[dict(r,game=game,month=month,**{k:meta[k] for k in ('initial','increment','time_control')}) for r in rows if r['player']==player and r['ply']>4]
                                if not moves:counts['games_without_postopening_moves']+=1;continue
                                rank=hashlib.sha256(f'{original.SEED}:game:{player}:{game}'.encode()).hexdigest()
                                moves=sorted(moves,key=lambda r:hashlib.sha256(f'{original.SEED}:move:{rank}:{r["ply"]}'.encode()).hexdigest())[:4]
                                old=con.execute('SELECT games FROM candidates WHERE player=?',(player,)).fetchone()
                                candidates=[] if old is None else json.loads(old[0])
                                candidates.append([rank,moves]);candidates=sorted(candidates,key=lambda x:x[0])[:10]
                                con.execute('INSERT OR REPLACE INTO candidates VALUES(?,?)',(player,json.dumps(candidates,sort_keys=True)))
                    state.update(source=i,ordinal=ordinal,done=state['done']+1);since+=1
                    if since>=1000:save()
            state.update(source=i+1,ordinal=-1);save()
        # Candidate lists are small per player, never the whole raw month.
        if state['done']!=total:raise ValueError('Full raw-source record count differs from censuses')
        emitted=0;final=Counter(counts)
        with (output/'PRIVATE_POSITIONS.jsonl.gz').open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as binary:
            with io.TextIOWrapper(binary,encoding='utf8',newline='\n') as stream:
                for player,payload in con.execute('SELECT player,games FROM candidates ORDER BY player'):
                    if ck.requested(request_root):return control.yielded(state['done'],total)
                    games=json.loads(payload);final['sampled_players']+=1
                    if len(games)<10:final['below_ten_games_players']+=1
                    pools=[moves for _,moves in games]
                    for index in range(40):
                        pool=pools[index%len(pools)];offset=index//len(pools)
                        if offset<len(pool):stream.write(json.dumps(pool[offset],sort_keys=True)+'\n');emitted+=1
        final['sampled_positions']=emitted
        original.write_json(output/'SOURCE.json',dict(final,frame=frame))
    except BaseException:con.rollback();raise
    finally:con.execute('PRAGMA wal_checkpoint(TRUNCATE)');con.close()
    return dict(status='complete',source_records=state['done'],sampled_positions=emitted)


def _execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);bound=identity(inputs,config)
    check=lambda:ck.require(output)
    if ck.sealed(output,bound,check):return dict(status='complete',sealed_output_reused=True)
    result=run(output,output,inputs,config,'execute')
    if result['status']=='complete':ck.seal(output,bound,['PRIVATE_SELECTED_PLAYERS.json','PRIVATE_POSITIONS.jsonl.gz','SOURCE.json'],check)
    return result


def _verify(output,inputs,config):
    output=Path(output)
    check=lambda:ck.require(output)
    if not ck.sealed(output,identity(inputs,config),check):raise ValueError('Complete sample execution required')
    result=run(output/'independent_sample',output,inputs,config,'verify')
    if result['status']=='yielded':return result
    for name in ('PRIVATE_SELECTED_PLAYERS.json','PRIVATE_POSITIONS.jsonl.gz','SOURCE.json'):
        if ck.file_digest(output/name,check)!=ck.file_digest(output/'independent_sample'/name,check):raise ValueError('Full raw-source sample replay differs: '+name)
    return dict(verified=True,complete_recalculation=True,raw_source_start_ordinal=0,execution_candidates_excluded=True)


def execute(output,inputs,config):return ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config):return ck.guarded(_verify,output,inputs,config)
