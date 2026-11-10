"""ID1 immutable snapshot continuation with transactional source-row cursors.

DESIGN CHECK: preserve every original pair, including split pairs across pauses;
HMAC before derived storage; no demographics. A prefix is never a population.
Fresh verification reconstructs the complete archive independently.
"""
from collections import Counter
from pathlib import Path
import json,sqlite3,tarfile,time,os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from . import week5_id_source as original
from .week5_go import write,sha
from .week5_la2_ic import requested

SOURCE_SHA=original.SOURCE_SHA
SOURCE_ROWS=70332355
PILOT_ROWS=3516618
SCHEMA='CREATE TABLE pairs(response TEXT PRIMARY KEY,person TEXT,session TEXT,ord INTEGER,kind TEXT,strict TEXT,n INTEGER,saved INTEGER,intervention INTEGER,human_sides INTEGER,pet_sides INTEGER,humans INTEGER,pets INTEGER,human_saved INTEGER,bad INTEGER) WITHOUT ROWID'


class Pause(Exception):pass


def state_write(db,state):
    db.execute('INSERT OR REPLACE INTO checkpoint VALUES(1,?)',(json.dumps(state,sort_keys=True),))


def seal(output,state):
    write(output/'SNAPSHOT.json',dict(state=state,database_sha256=sha(output/'pairs.sqlite')))


def open_state(output,binding):
    path=output/'pairs.sqlite'
    if path.exists():
        snapshot=json.loads((output/'SNAPSHOT.json').read_text('utf8'))
        if snapshot['database_sha256']!=sha(path):raise ValueError('ID1 stopped database snapshot changed')
        db=sqlite3.connect(path)
        state=json.loads(db.execute('SELECT value FROM checkpoint WHERE id=1').fetchone()[0])
        if state!=snapshot['state'] or state['binding']!=binding:db.close();raise ValueError('ID1 source cursor/binding changed')
        for index in range(state['parts']):
            p=output/'parts'/f'{index:06}.parquet';s=json.loads(p.with_suffix('.seal.json').read_text('utf8'))
            if s['sha256']!=sha(p) or s['binding']!=binding:db.close();raise ValueError('ID1 projected part changed')
    else:
        db=sqlite3.connect(path);db.execute(SCHEMA);db.execute('CREATE TABLE checkpoint(id INTEGER PRIMARY KEY,value TEXT)')
        state=dict(binding=binding,rows=0,pilot_done=False,source_complete=False,index_stage=0,parts=0,person_cursor='',projected_people=0,counts={})
        state_write(db,state);db.commit()
    db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA cache_size=-65536');db.execute('PRAGMA temp_store=FILE')
    return db,state


def ingest(db,state,output,archive,salt,config,stop):
    if state['source_complete']:return
    before=state['rows'];startcpu=time.process_time();skipped=0;position=0
    with tarfile.open(archive,'r:gz') as container:
        member=next(iter(container))
        if not member.isfile() or '..' in Path(member.name).parts or Path(member.name).is_absolute():raise ValueError('unexpected source member')
        with container.extractfile(member) as stream:
            reader=pd.read_csv(stream,usecols=original.BASE+original.HUMANS+original.PET,dtype=str,keep_default_na=False,chunksize=100000)
            for frame in reader:
                end=position+len(frame)
                if end<=state['rows']:
                    position=end;skipped+=len(frame)
                    if stop():raise Pause('resource/wall request while re-reading committed CSV prefix')
                    continue
                begin=max(0,state['rows']-position)
                take=frame.iloc[begin:]
                if not state['pilot_done']:
                    take=take.iloc[:max(0,config['pilot_rows']-state['rows'])]
                if stop():raise Pause('resource/wall request before next source transaction')
                if len(take):
                    db.execute('BEGIN')
                    try:
                        db.executemany(original.UPSERT,original.paired_rows(take,salt))
                        state['rows']+=len(take)
                        if state['rows']==config['pilot_rows']:state['pilot_done']=True
                        state_write(db,state);db.commit()
                    except BaseException:db.rollback();raise
                write(output/'PROGRESS.json',dict(phase='source_pairing',source_rows=state['rows'],source_total_rows=SOURCE_ROWS,prior_committed_rows=before))
                new=state['rows']-before
                if new:
                    elapsed=time.process_time()-startcpu
                    database_bytes=(output/'pairs.sqlite').stat().st_size
                    write(output/'COST.json',dict(new_source_rows=new,reparsed_committed_prefix_rows=skipped,cpu_seconds=elapsed,
                        forecast_ingestion_execute_plus_replay_cpu_seconds=2*elapsed*SOURCE_ROWS/new,
                        current_pair_database_bytes=database_bytes,
                        forecast_two_pair_databases_bytes=2*database_bytes*SOURCE_ROWS/state['rows'],
                        indexes_case_parts_and_immutable_copy_space_additional=True,
                        projection_index_and_copy_cost_not_in_forecast=True))
                if before<config['pilot_rows'] and state['rows']==config['pilot_rows']:
                    raise Pause('exact first-five-percent source pilot; complete pair state retained')
                position=end
    if state['rows']!=SOURCE_ROWS:raise ValueError('complete source record census differs')
    state['source_complete']=True;state_write(db,state);db.commit()


def indexing(db,state,stop):
    stages=[['CREATE INDEX person_session ON pairs(person,session,ord)'],
            ['CREATE TABLE people AS SELECT person,count(DISTINCT session) AS sessions FROM pairs GROUP BY person','CREATE UNIQUE INDEX person_key ON people(person)']]
    db.set_progress_handler(lambda:int(stop()),10000)
    try:
        while state['index_stage']<len(stages):
            if stop():raise Pause('resource/wall before index stage')
            previous_stage=state['index_stage']
            db.execute('BEGIN')
            try:
                for sql in stages[state['index_stage']]:db.execute(sql)
                state['index_stage']+=1;state_write(db,state);db.commit()
            except sqlite3.OperationalError as error:
                db.rollback();state['index_stage']=previous_stage
                if 'interrupt' in str(error).lower():raise Pause('interrupted index stage retained for restart') from error
                raise
    finally:db.set_progress_handler(None,0)


def project_person(person,values,counts):
    sessions=values[0][-1]
    valid=[v for v in values if v[5]==2 and v[6]==1 and v[7]==1 and v[12]==0]
    complete=sessions==1 and len(values)==13 and len(valid)==13 and sorted(v[1] for v in valid)==list(range(1,14))
    counts['single_complete_13_scenario_fingerprints']+=int(complete);out=[]
    for v in valid:
        session,order,kind,strict,_,n,saved,iv,hs,ps,human,pet,bad,human_saved,_=v
        pure=hs==1 and ps==1 and human>0 and pet>0
        species=pure and kind==strict=='Species' and human==pet;random=pure and kind=='Random'
        if not(species or random):continue
        out.append(dict(person=person,session=session,order=order,kind='Species' if species else 'Random',humans=human,pets=pet,
            human_saved=human_saved,primary_session=complete,sessions=sessions))
        counts['retained_'+('Species' if species else 'Random')]+=1
    return out


def part_commit(db,state,output,rows,counts,last_person,people):
    index=state['parts'];path=output/'parts'/f'{index:06}.parquet';path.parent.mkdir(parents=True,exist_ok=True)
    # Explicit empty schema keeps an all-excluded person block representable.
    schema=pa.schema([('person',pa.string()),('session',pa.string()),('order',pa.int64()),('kind',pa.string()),('humans',pa.int64()),('pets',pa.int64()),('human_saved',pa.int64()),('primary_session',pa.bool_()),('sessions',pa.int64())])
    table=pa.Table.from_pylist(rows,schema=schema);temp=path.with_suffix('.tmp.parquet');pq.write_table(table,temp,compression='zstd')
    if path.exists():
        if sha(path)!=sha(temp):temp.unlink();raise ValueError('uncommitted projection part differs')
        temp.unlink()
    else:os.replace(temp,path)
    write(path.with_suffix('.seal.json'),dict(binding=state['binding'],sha256=sha(path),people=people,rows=len(rows)))
    state.update(parts=index+1,counts=dict(counts),person_cursor=last_person,projected_people=state['projected_people']+people)
    state_write(db,state);db.commit()


def projection(db,state,output,stop):
    counts=Counter(state['counts'])
    query='SELECT p.person,p.session,p.ord,p.kind,p.strict,p.response,p.n,p.saved,p.intervention,p.human_sides,p.pet_sides,p.humans,p.pets,p.bad,p.human_saved,u.sessions FROM pairs p JOIN people u ON p.person=u.person WHERE p.person>? ORDER BY p.person,p.session,p.ord,p.response'
    current=None;records=[];batch=[];people=0;last=state['person_cursor']
    db.set_progress_handler(lambda:int(stop()),10000)
    try:
        for row in db.execute(query,(state['person_cursor'],)):
            if row[0]!=current:
                if current is not None:
                    batch.extend(project_person(current,records,counts));people+=1;last=current
                if people==1000:
                    db.set_progress_handler(None,0)
                    part_commit(db,state,output,batch,counts,last,people);batch=[];people=0
                    write(output/'PROGRESS.json',dict(phase='whole_person_projection',people_complete=state['projected_people'],parts=state['parts']))
                    if stop():raise Pause('resource/wall after complete person projection part')
                    db.set_progress_handler(lambda:int(stop()),10000)
                current=row[0];records=[]
            records.append(row[1:])
    except sqlite3.OperationalError as error:
        if 'interrupt' in str(error).lower():raise Pause('interrupted ordered projection; last whole-person part retained') from error
        raise
    finally:db.set_progress_handler(None,0)
    if current is not None:batch.extend(project_person(current,records,counts));people+=1;last=current
    if people:part_commit(db,state,output,batch,counts,last,people)


def finish(db,state,output,stop):
    # These source-only counts are independent of responses' fitted effects.
    queries=dict(responses='SELECT count(*) FROM pairs',orphans='SELECT count(*) FROM pairs WHERE n=1',
        duplicates='SELECT count(*) FROM pairs WHERE n>2',invalid_source_rows_or_pairs='SELECT count(*) FROM pairs WHERE bad!=0',
        fingerprints='SELECT count(*) FROM people',multi_session_fingerprints_excluded_primary='SELECT count(*) FROM people WHERE sessions!=1')
    counts=dict(source_rows=state['rows'],**state['counts'])
    db.set_progress_handler(lambda:int(stop()),10000)
    try:
        for name,query in queries.items():
            if stop():raise Pause('resource/wall before final source census')
            counts[name]=db.execute(query).fetchone()[0]
    except sqlite3.OperationalError as error:
        if 'interrupt' in str(error).lower():raise Pause('interrupted final source census; checkpoint preserved') from error
        raise
    finally:db.set_progress_handler(None,0)
    destination=output/'cases.parquet';temp=output/'cases.tmp.parquet';writer=None
    try:
        for index in range(state['parts']):
            if stop():raise Pause('resource/wall during deterministic final part concatenation')
            table=pq.read_table(output/'parts'/f'{index:06}.parquet')
            if writer is None:writer=pq.ParquetWriter(temp,table.schema,compression='zstd')
            writer.write_table(table)
    finally:
        if writer is not None:writer.close()
    if writer is not None:os.replace(temp,destination)
    return dict(source_only=True,prefix_only=False,counts=counts,source_sha256=SOURCE_SHA,
        cases_sha256=sha(destination) if writer else None,
        chronology='single complete13-scenario session only; orders1–6 first half,7–13 second half; no intersession chronology invented',
        no_demographics_loaded=True,complete_source_rows=SOURCE_ROWS)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if set(inputs)!={'source','salt'} or set(config)-{'phase','pilot_rows','max_wall_seconds'}:raise ValueError('unregistered ID source contract')
    if config.get('phase')!='prepare' or config.get('pilot_rows')!=PILOT_ROWS:raise ValueError('fixed first-five-percent source pilot required')
    archive=Path(inputs['source']);salt=Path(inputs['salt']).read_bytes()
    if len(salt)!=32 or sha(archive)!=SOURCE_SHA:raise ValueError('source archive or salt differs')
    binding=dict(source_sha256=SOURCE_SHA,source_rows=SOURCE_ROWS,salt_sha256=sha(inputs['salt']),pilot_rows=PILOT_ROWS,
        original_module_sha256=sha(original.__file__),module_sha256=sha(__file__))
    db,state=open_state(output,binding);started=time.monotonic()
    stop=lambda:requested(output) or time.monotonic()-started>=config.get('max_wall_seconds',900)
    result=None
    try:
        if (output/'SOURCE.json').exists():return json.loads((output/'SOURCE.json').read_text('utf8'))
        ingest(db,state,output,archive,salt,config,stop);indexing(db,state,stop)
        projection(db,state,output,stop);result=finish(db,state,output,stop)
    except Pause as reason:
        result=dict(status='yielded',reason=str(reason),source_only=True,source_rows=state['rows'],source_total_rows=SOURCE_ROWS,
            projected_people=state['projected_people'],prefix_only=True)
    finally:
        db.close();seal(output,state)
    if result.get('status')!='yielded':write(output/'SOURCE.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output);actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return dict(actual,verified=False)
    if actual!=json.loads((output/'SOURCE.json').read_text('utf8')):raise ValueError('complete ID source replay differs')
    # Pair rows include all incomplete, invalid and excluded cases, not merely
    # retained analytical rows. Compare every field in deterministic key order.
    binding=dict(execution_snapshot_sha256=sha(output/'SNAPSHOT.json'),replay_snapshot_sha256=sha(output/'independent-replay/SNAPSHOT.json'),module_sha256=sha(__file__))
    path=output/'PAIR_VERIFICATION.json';progress=dict(binding=binding,last_response='',pairs=0)
    if path.exists():
        progress=json.loads(path.read_text('utf8'))
        if progress['binding']!=binding or json.loads(path.with_suffix('.seal.json').read_text('utf8'))['sha256']!=sha(path):raise ValueError('pair verification prefix changed')
    started=time.monotonic()
    a=sqlite3.connect(output/'pairs.sqlite');b=sqlite3.connect(output/'independent-replay/pairs.sqlite')
    try:
        left=a.execute('SELECT * FROM pairs WHERE response>? ORDER BY response',(progress['last_response'],));right=b.execute('SELECT * FROM pairs WHERE response>? ORDER BY response',(progress['last_response'],))
        while True:
            x=left.fetchmany(10000);y=right.fetchmany(10000)
            if x!=y:raise ValueError('complete pair-state replay differs')
            if not x:break
            progress.update(last_response=x[-1][0],pairs=progress['pairs']+len(x))
            write(path,progress);write(path.with_suffix('.seal.json'),dict(sha256=sha(path)))
            if requested(output) or time.monotonic()-started>=config.get('max_wall_seconds',900):
                return dict(status='yielded',verified=False,reason='bounded full pair-state verification',verified_pairs=progress['pairs'])
        if progress['pairs']!=actual['counts']['responses']:raise ValueError('verified pair census differs')
    finally:a.close();b.close()
    return dict(verified=True,full_source_replay=True,all_pair_state_fields_compared=True,source_only=True)
