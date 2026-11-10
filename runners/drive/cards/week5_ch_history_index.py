"""Disk-backed per-player projection for CH4 and CH6, without engine features.

DESIGN CHECK: raw source histories are read exactly once per projection pass.
Only already-salted player keys are retained. Native replay checks every projected
value. Iteration loads one player at a time, rather than all move dictionaries.
"""
from collections.abc import Mapping
from pathlib import Path
import hashlib,json,sqlite3,shutil,time
from .week5_ch_collection import verified_spec
from .week5_ch_source import write_json,digest


def player_games(database):
    con=sqlite3.connect(database)
    try:
        for source_record,(month,ordinal,payload) in enumerate(con.execute('SELECT month,ordinal,payload FROM histories ORDER BY month,ordinal')):
            game=json.loads(payload);meta=game['meta']
            for player in sorted({r['player'] for r in game['rows']}):
                side=meta['players'].index(player)
                value=dict(game=game['game'],month=month,start=meta['start'],end=meta['end'],initial=meta['initial'],increment=meta['increment'],time_control=meta['time_control'],rating_change=meta['rating_changes'][side],result=(1 if meta['result']==('1-0' if side==0 else '0-1') else 0 if meta['result']=='1/2-1/2' else -1),first_clock=game['first_clocks'][side],rows=[{key:r[key] for key in ('ply','clock_before','think_time')} for r in game['rows'] if r['player']==player])
                yield player,value,source_record
    finally:con.close()


def project(source,database,constructed=False,progress=None,resume=None,source_sha256=None):
    if Path(database).exists():raise FileExistsError(database)
    source_con=sqlite3.connect(source)
    try:
        source_records=source_con.execute('SELECT count(*) FROM histories').fetchone()[0]
        if not constructed:
            states=source_con.execute('SELECT complete FROM checkpoints').fetchall()
            if not states or not all(x[0] for x in states):raise ValueError('Incomplete source histories')
        else:
            if source_con.execute("SELECT value FROM settings WHERE key='constructed_fixture'").fetchone()!=('true',):raise ValueError('Not a constructed source')
    finally:source_con.close()
    if resume:shutil.copy2(resume,database)
    con=sqlite3.connect(database)
    if not resume:
        con.executescript('CREATE TABLE player_history(player TEXT,month TEXT,game TEXT,payload TEXT,PRIMARY KEY(player,month,game)) WITHOUT ROWID; CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT);')
        con.executemany('INSERT INTO settings VALUES(?,?)',[('source_sha256',source_sha256),('constructed_fixture',json.dumps(constructed)),('complete','false')]);games=moves=0
    else:
        if con.execute("SELECT value FROM settings WHERE key='source_sha256'").fetchone()!=(source_sha256,):raise ValueError('Resume source changed')
        if con.execute("SELECT value FROM settings WHERE key='complete'").fetchone()!=('false',):raise ValueError('Resume requires incomplete index')
        games=int(con.execute("SELECT value FROM settings WHERE key='player_games'").fetchone()[0]);moves=int(con.execute("SELECT value FROM settings WHERE key='moves'").fetchone()[0])
    done=games;complete=True;started=time.process_time()
    def save(complete):
        con.executemany('INSERT OR REPLACE INTO settings VALUES(?,?)',[('complete',json.dumps(complete)),('player_games',str(games)),('moves',str(moves))]);con.commit()
    try:
        for ordinal,(player,game,source_record) in enumerate(player_games(source)):
            if ordinal<done:continue
            con.execute('INSERT INTO player_history VALUES(?,?,?,?)',(player,game['month'],game['game'],json.dumps(game,sort_keys=True,separators=(',',':'))));games+=1;moves+=len(game['rows'])
            if games%1000==0:
                save(False)
                if progress:
                    telemetry=dict(player_games=games,moves=moves,source_records_processed=source_record+1,total_source_records=source_records,complete=False,invocation_cpu_seconds=time.process_time()-started)
                    write_json(Path(progress)/'PROGRESS.json',telemetry,mutable=True)
                    if not resume and source_records and source_record+1>=.05*source_records and not (Path(progress)/'PILOT.json').exists():
                        write_json(Path(progress)/'PILOT.json',dict(telemetry,forecast_execute_cpu_seconds=telemetry['invocation_cpu_seconds']*source_records/(source_record+1),basis='first transaction after 5% of source history rows'))
                if progress and (Path(progress)/'YIELD_REQUEST.json').exists():complete=False;break
        players=con.execute('SELECT count(DISTINCT player) FROM player_history').fetchone()[0]
        save(complete)
    finally:con.close()
    return dict(player_games=games,moves=moves,players=players,complete=complete,constructed_fixture=constructed)


class HistoryStore(Mapping):
    def __init__(self,path,constructed=False):
        self.path=Path(path);self.con=sqlite3.connect(path)
        if self.con.execute("SELECT value FROM settings WHERE key='complete'").fetchone()!=('true',):raise ValueError('Incomplete player history projection')
        if self.con.execute("SELECT value FROM settings WHERE key='constructed_fixture'").fetchone()!=(json.dumps(constructed),):raise ValueError('History fixture/source mismatch')
    def __iter__(self):
        return (r[0] for r in self.con.execute('SELECT DISTINCT player FROM player_history ORDER BY player'))
    def __len__(self):return self.con.execute('SELECT count(DISTINCT player) FROM player_history').fetchone()[0]
    def __getitem__(self,key):
        rows=[json.loads(r[0]) for r in self.con.execute('SELECT payload FROM player_history WHERE player=? ORDER BY month,game',(key,))]
        if not rows:raise KeyError(key)
        return rows
    def close(self):self.con.close()


def contents_hash(database):
    h=hashlib.sha256();con=sqlite3.connect(database)
    try:
        for row in con.execute('SELECT player,month,game,payload FROM player_history ORDER BY player,month,game'):
            h.update((json.dumps(row,separators=(',',':'))+'\n').encode())
    finally:con.close()
    return h.hexdigest()


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);source=verified_spec(inputs['histories'])
    resume=verified_spec(inputs['resume_index']) if 'resume_index' in inputs else None
    result=project(source,output/'PRIVATE_PLAYER_HISTORY.sqlite',config.get('constructed_fixture',False),output,resume,inputs['histories']['sha256'])
    result.update(source_sha256=inputs['histories']['sha256'],contents_sha256=contents_hash(output/'PRIVATE_PLAYER_HISTORY.sqlite'))
    write_json(output/'INDEX.json',result)
    if not result['complete']:return dict(status='yielded',reason='History projection checkpointed requested yield',checkpoint=str(output/'PRIVATE_PLAYER_HISTORY.sqlite'),**result)
    return dict(status='complete',**result)


def verify(output,inputs,config):
    output=Path(output);execute(output/'replay',{k:v for k,v in inputs.items() if k!='resume_index'},config)
    if digest(output/'INDEX.json')!=digest(output/'replay/INDEX.json'):raise ValueError('Complete history projection replay differs')
    return dict(verified=True,complete_recalculation=True)
