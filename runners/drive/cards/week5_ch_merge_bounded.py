"""Cooperative exact-table merge of independently completed CH month censuses.

DESIGN CHECK: LESSONS 3-5. No month prefix defines a frame. Transaction cursors
commit beside copied rows; independent verification compares every source row
and total without trusting a copied execution prefix or duplicating a huge DB.
"""
from pathlib import Path
import json,sqlite3
from . import week5_ch_source as original
from . import week5_ch_pipeline_checkpoint as ck

TABLES=('frame','openings','opening_positions','histories','checkpoints')


def source_info(inputs,check=None):
    salt=ck.checked(inputs['salt'],check);sources=[];months=set();total=0
    for key,spec in sorted(inputs.items()):
        if not key.startswith('frame'):continue
        path=ck.checked(spec,check);con=sqlite3.connect(path)
        try:
            states=con.execute('SELECT month,complete FROM checkpoints').fetchall()
            if not states or any(not x[1] for x in states):raise ValueError('Full independently completed month required')
            for month,_ in states:
                if month in months:raise ValueError('Overlapping census month')
                months.add(month)
            if con.execute("SELECT value FROM settings WHERE key='salt_sha256'").fetchone()!=(original.digest(salt),):raise ValueError('Campaign salt mismatch')
            counts={t:con.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES}
            total+=sum(counts.values());sources.append((path,counts))
        finally:con.close()
    if not sources:raise ValueError('No complete month frames')
    return sources,total,original.digest(salt)


def key_columns(con,table):
    rows=con.execute('PRAGMA table_info('+table+')').fetchall()
    return [r[1] for r in sorted(rows,key=lambda r:r[5]) if r[5]]


def batches(con,table,last=None):
    keys=key_columns(con,table);expr='('+','.join(keys)+')'
    where='' if last is None else ' WHERE '+expr+'>('+','.join('?' for _ in keys)+')'
    query='SELECT * FROM '+table+where+' ORDER BY '+','.join(keys)+' LIMIT 1000'
    columns=[r[1] for r in con.execute('PRAGMA table_info('+table+')')]
    positions=[columns.index(k) for k in keys]
    while True:
        rows=con.execute(query,() if last is None else last).fetchall()
        if not rows:break
        last=[rows[-1][i] for i in positions]
        yield rows,last
        query='SELECT * FROM '+table+' WHERE '+expr+'>('+','.join('?' for _ in keys)+') ORDER BY '+','.join(keys)+' LIMIT 1000'


def identity(inputs,config):
    if config.get('phase')!='merge':raise ValueError('Merge phase required')
    return ck.binding(inputs,config,dict(adapter=original.digest(__file__),source=original.digest(original.__file__)))


def _execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);bound=identity(inputs,config)
    control=ck.Control(output,output,config,'execute')
    check=lambda:ck.require(output)
    if ck.sealed(output,bound,check):return dict(status='complete',sealed_output_reused=True)
    sources,total,salt=source_info(inputs,check);database=output/'PRIVATE_FRAME.sqlite'
    if database.exists():ck.copied(database,output,check)
    con=original.open_database(database)
    try:
        state=ck.initialize(con,bound,dict(source=0,table=0,last=None,done=0))
        con.execute("INSERT OR IGNORE INTO settings VALUES('salt_sha256',?)",(salt,));con.commit()
        for i,(path,_) in enumerate(sources):
            if i<state['source']:continue
            src=sqlite3.connect(path)
            try:
                for j,table in enumerate(TABLES):
                    if i==state['source'] and j<state['table']:continue
                    last=state['last'] if i==state['source'] and j==state['table'] else None
                    for rows,last in batches(src,table,last):
                        if control.stop():return control.yielded(state['done'],total)
                        con.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for _ in rows[0])+')',rows)
                        state.update(source=i,table=j,last=last,done=state['done']+len(rows))
                        ck.put(con,'state',state);con.commit();control.tick(len(rows),state['done'],total)
                    state.update(source=i,table=j+1,last=None);ck.put(con,'state',state);con.commit()
            finally:src.close()
            state.update(source=i+1,table=0,last=None);ck.put(con,'state',state);con.commit()
        # Keep the private operational cursor so a crash during finalization
        # cannot turn a fully copied database into an apparent empty checkpoint.
        # Original scientific tables and their schemas are unchanged.
        con.commit()
    except BaseException:con.rollback();raise
    finally:con.execute('PRAGMA wal_checkpoint(TRUNCATE)');con.close()
    original.write_json(output/'SOURCE.json',dict(merged=True))
    ck.seal(output,bound,['PRIVATE_FRAME.sqlite','SOURCE.json'],check)
    return dict(status='complete',merged=True,source_rows=total)


def _verify(output,inputs,config):
    output=Path(output);bound=identity(inputs,config)
    control=ck.Control(output/'verification',output,config,'verify');done=0
    check=lambda:ck.require(output)
    if not ck.sealed(output,bound,check):raise ValueError('Complete merge execution required')
    sources,total,salt=source_info(inputs,check);target=sqlite3.connect(output/'PRIVATE_FRAME.sqlite')
    try:
        if target.execute("SELECT value FROM settings WHERE key='salt_sha256'").fetchone()!=(salt,):raise ValueError('Merged salt changed')
        if target.execute('SELECT count(*) FROM settings').fetchone()[0]!=1:raise ValueError('Extra merged setting')
        for table in TABLES:
            if target.execute('SELECT count(*) FROM '+table).fetchone()[0]!=sum(c[table] for _,c in sources):raise ValueError('Merged row denominator differs')
        for path,_ in sources:
            src=sqlite3.connect(path)
            try:
                for table in TABLES:
                    if src.execute('PRAGMA table_info('+table+')').fetchall()!=target.execute('PRAGMA table_info('+table+')').fetchall():raise ValueError('Merged schema changed')
                    cols=[r[1] for r in src.execute('PRAGMA table_info('+table+')')];keys=key_columns(src,table);positions=[cols.index(k) for k in keys]
                    query='SELECT * FROM '+table+' WHERE '+' AND '.join(k+'=?' for k in keys)
                    for rows,_ in batches(src,table):
                        if control.stop():return control.yielded(done,total)
                        for row in rows:
                            if target.execute(query,[row[k] for k in positions]).fetchone()!=row:raise ValueError('Independent merged source row differs')
                        done+=len(rows);control.tick(len(rows),done,total)
            finally:src.close()
    finally:target.close()
    return dict(verified=True,complete_recalculation=True,source_start_ordinal=0,every_source_row_compared=done)


def execute(output,inputs,config):return ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config):return ck.guarded(_verify,output,inputs,config)
