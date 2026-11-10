"""Transactional GO3 XML-byte pilot and complete sorted revision continuation.

DESIGN CHECK: each source prefix and each ordered history batch is transactional.
No partial source is complete; every projected row is independently replayed.
"""
from collections import Counter
from pathlib import Path
import json,math,sqlite3,time,xml.etree.ElementTree as ET
import pyarrow as pa
import pyarrow.parquet as pq
from . import week5_go3_source_integrity as integrity
from .week5_la2_ic import requested

core=integrity.original.core
base=integrity.original
READ_BYTES=4*1024*1024
PROJECTION_BATCH=1024
SCHEMA=pa.schema([(n,pa.string()) for n in ('editor','post','stamp','site')]+[('type',pa.int64()),('reason',pa.string()),
                 ('self_edit',pa.bool_()),('owner_known',pa.bool_()),('before',pa.string()),('after',pa.string())])


class Pause(Exception):pass


def put_state(db,state):db.execute('INSERT OR REPLACE INTO checkpoint VALUES(1,?)',(json.dumps(state,sort_keys=True),))


def seal(output,state):core.write(output/'SNAPSHOT.json',dict(state=state,database_sha256=core.sha(output/'projection.sqlite')))


def open_state(output,binding):
    path=output/'projection.sqlite'
    if path.exists():
        snap=json.loads((output/'SNAPSHOT.json').read_text('utf8'))
        if core.sha(path)!=snap['database_sha256']:raise ValueError('GO3 stopped database snapshot changed')
        db=sqlite3.connect(path);state=json.loads(db.execute('SELECT value FROM checkpoint WHERE id=1').fetchone()[0])
        if state!=snap['state'] or state['binding']!=binding:db.close();raise ValueError('GO3 checkpoint cursor/binding differs')
        for i in range(state['parts']):
            p=output/'parts'/f'{i:07d}.parquet';s=json.loads(p.with_suffix('.seal.json').read_text('utf8'))
            if s['binding']!=binding or s['sha256']!=core.sha(p):db.close();raise ValueError('GO3 projected part changed')
    else:
        db=sqlite3.connect(path)
        db.execute('CREATE TABLE posts(post TEXT PRIMARY KEY,author TEXT)')
        db.execute('CREATE TABLE history(post TEXT,stamp TEXT,ordinal INTEGER,type INTEGER,editor TEXT,label TEXT,body TEXT)')
        db.execute('CREATE TABLE checkpoint(id INTEGER PRIMARY KEY,value TEXT)')
        state=dict(binding=binding,phase=0,bytes=[0,0],records=[0,0],pilot_done=False,indexed=False,
                   parts=0,projection_cursor=None,current_post=None,previous={},projected_history_rows=0,retained=0,counts={},projection_complete=False)
        put_state(db,state);db.commit()
    db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=FULL')
    db.execute('PRAGMA cache_size=-65536');db.execute('PRAGMA temp_store=FILE')
    return db,state


def events(parser,stack,block,final=False):
    parser.feed(block)
    # Explicit flush makes a byte prefix's completed events independent of
    # how earlier feeds partitioned it (notably before/after a pilot cut).
    parser.flush()
    # Close before draining EOF events as well; byte completion alone is not
    # proof that the parser has emitted every complete row.
    if final:parser.close()
    rows=[]
    for event,element in parser.read_events():
        if event=='start':stack.append(element);continue
        if element.tag=='row':
            rows.append(dict(element.attrib))
            if len(stack)>1:stack[-2].remove(element)
            element.clear()
        stack.pop()
    return rows


def ingest(db,state,output,salt,site,sizes,stop):
    names=integrity.TARGETS;total=sum(sizes);pilot=math.ceil(total*.05)
    began=time.process_time();initial=sum(state['bytes']);replayed_bytes=0
    while state['phase']<2:
        phase=state['phase'];path=output/'xml'/names[phase]
        parser=ET.XMLPullParser(events=('start','end'));stack=[];ordinal=0
        with path.open('rb') as stream:
            left=state['bytes'][phase]
            while left:
                if stop():raise Pause('resource/wall while rebuilding committed XML parser prefix')
                block=stream.read(min(READ_BYTES,left))
                if not block:raise ValueError('XML saved prefix exceeds source')
                final=state['bytes'][phase]-left+len(block)==sizes[phase]
                ordinal+=len(events(parser,stack,block,final));left-=len(block);replayed_bytes+=len(block)
            if ordinal!=state['records'][phase]:raise ValueError('XML committed record cursor differs')
            while state['bytes'][phase]<sizes[phase]:
                if stop():raise Pause('resource/wall before next source transaction')
                take=min(READ_BYTES,sizes[phase]-state['bytes'][phase])
                if not state['pilot_done']:take=min(take,pilot-sum(state['bytes']))
                if take<=0:raise ValueError('Invalid first-five-percent source cursor')
                block=stream.read(take)
                if len(block)!=take:raise ValueError('XML byte census differs')
                values=events(parser,stack,block,state['bytes'][phase]+len(block)==sizes[phase]);counts=Counter(state['counts'])
                db.execute('BEGIN')
                try:
                    if phase==0:
                        for row in values:
                            owner=row.get('OwnerUserId')
                            db.execute('INSERT INTO posts VALUES (?,?)',(base.salted(salt,site+'-post',row['Id']),base.salted(salt,site+'-user',owner) if owner else None))
                            counts['posts']+=1
                    else:
                        for row in values:
                            kind=int(row['PostHistoryTypeId'])
                            if kind in (1,2,3,4,5,6,24):
                                user=row.get('UserId')
                                db.execute('INSERT INTO history VALUES (?,?,?,?,?,?,?)',(base.salted(salt,site+'-post',row['PostId']),row['CreationDate'],int(row['Id']),kind,
                                    base.salted(salt,site+'-user',user) if user else None,base.reason(row.get('Comment','')),row.get('Text','')))
                                counts['history_rows']+=1
                    state['bytes'][phase]+=len(block);state['records'][phase]+=len(values);state['counts']=dict(counts)
                    reached=not state['pilot_done'] and sum(state['bytes'])==pilot
                    if reached:state['pilot_done']=True
                    put_state(db,state);db.commit()
                except BaseException:db.rollback();raise
                complete=sum(state['bytes']);new=complete-initial;cpu=time.process_time()-began
                core.write(output/'PROGRESS.json',dict(phase='source',completed=complete,total=total,source_records=sum(state['records'])))
                core.write(output/'COST.json',dict(new_source_bytes=new,reparsed_prefix_bytes=replayed_bytes,source_total_bytes=total,
                    cpu_seconds=cpu,forecast_ingest_execute_and_replay_cpu_seconds=2*cpu*total/max(new,1),
                    database_bytes=(output/'projection.sqlite').stat().st_size,
                    forecast_two_databases_bytes=2*(output/'projection.sqlite').stat().st_size*total/max(complete,1),
                    extraction_hash_index_projection_and_immutable_copy_cost_additional=True))
                if reached:raise Pause('exact first-five-percent authenticated XML-byte pilot')
        state['phase']+=1;put_state(db,state);db.commit()


def indexing(db,state,stop):
    if state['indexed']:return
    if stop():raise Pause('resource/wall before sorted history index')
    db.set_progress_handler(lambda:int(stop()),10000)
    try:
        db.execute('BEGIN')
        try:
            db.execute('CREATE INDEX by_post_date ON history(post,stamp,ordinal)')
            state['indexed']=True;put_state(db,state);db.commit()
        except sqlite3.OperationalError as error:
            db.rollback();state['indexed']=False
            if 'interrupt' in str(error).lower():raise Pause('index interrupted; retained state restarts this stage') from error
            raise
    finally:db.set_progress_handler(None,0)


def project(db,state,output,site,stop):
    if state['projection_complete']:return
    last=state['projection_cursor'];where='' if last is None else 'WHERE (h.post,h.stamp,h.ordinal,h.rowid) > (?,?,?,?) '
    sql='SELECT h.post,h.stamp,h.ordinal,h.type,h.editor,h.label,h.body,p.author,h.rowid FROM history h LEFT JOIN posts p ON h.post=p.post '+where+'ORDER BY h.post,h.stamp,h.ordinal,h.rowid'
    cursor=db.execute(sql,[] if last is None else last)
    while True:
        if stop():raise Pause('resource/wall before next sorted history batch')
        batch=cursor.fetchmany(PROJECTION_BATCH)
        if not batch:state['projection_complete']=True;put_state(db,state);db.commit();return
        counts=Counter(state['counts']);previous=dict(state['previous']);current=state['current_post'];rows=[]
        for post,stamp,ordinal,kind,editor,label,body,author,rowid in batch:
            if post!=current:previous={};current=post
            channel='body' if kind in (2,5,24) else 'title' if kind in (1,4) else 'tags'
            before=previous.get(channel);previous[channel]=body
            if kind not in (4,5,6,24):continue
            counts['edit_type_'+str(kind)]+=1;counts['label_'+label]+=1
            if editor is None:counts['anonymous_edits_excluded']+=1;continue
            if before is None:counts['missing_before_excluded']+=1;continue
            if before==body:counts['unchanged_text_excluded']+=1;continue
            rows.append(dict(editor=editor,post=post,stamp=stamp,site=site,type=kind,reason=label,
                self_edit=editor==author if author else False,owner_known=author is not None,before=before,after=body))
        path=output/'parts'/f"{state['parts']:07d}.parquet";path.parent.mkdir(parents=True,exist_ok=True)
        pq.write_table(pa.Table.from_pylist(rows,schema=SCHEMA),path,compression='zstd')
        core.write(path.with_suffix('.seal.json'),dict(binding=state['binding'],sha256=core.sha(path)))
        db.execute('BEGIN')
        try:
            state['projection_cursor']=[batch[-1][0],batch[-1][1],batch[-1][2],batch[-1][-1]]
            state['current_post']=current;state['previous']=previous;state['counts']=dict(counts)
            state['parts']+=1;state['retained']+=len(rows);state['projected_history_rows']+=len(batch)
            put_state(db,state);db.commit()
        except BaseException:db.rollback();raise
        core.write(output/'PROGRESS.json',dict(phase='projection',completed=state['projected_history_rows'],total=counts['history_rows']))


def concatenate(output,state,stop):
    if state['retained']==0:raise ValueError('no supported revision rows')
    with pq.ParquetWriter(output/'edits.parquet',SCHEMA,compression='zstd') as writer:
        for i in range(state['parts']):
            if stop():raise Pause('resource/wall while concatenating sealed ordered parts')
            writer.write_table(pq.read_table(output/'parts'/f'{i:07d}.parquet'))


def execute(output,inputs,config):
    if config.get('phase')!='prepare' or set(config)-{'phase','site','max_wall_seconds'}:raise ValueError('Declared GO3 source configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);site=config['site'];archive=Path(inputs['archive']);salt=Path(inputs['salt']).read_bytes()
    if len(salt)!=32:raise ValueError('Campaign salt must be 32 bytes')
    if site not in base.ARCHIVES or core.sha(archive)!=base.ARCHIVES[site]:raise ValueError('Stack archive pin mismatch')
    if core.sha(inputs['license'])!=base.LICENSE_SHA:raise ValueError('dump licence notice mismatch')
    began=time.monotonic();maximum=float(config.get('max_wall_seconds',900))
    if not math.isfinite(maximum) or maximum<=0:raise ValueError('Positive finite wall quantum required')
    stop=lambda:requested(output) or time.monotonic()-began>=maximum
    binding=dict(archive_sha256=base.ARCHIVES[site],site=site,salt_sha256=core.sha(inputs['salt']),license_sha256=base.LICENSE_SHA,
                 source_sha256=core.sha(__file__),integrity_sha256=core.sha(integrity.__file__),original_sha256=core.sha(base.__file__))
    db=None;state=None
    try:
        # Extraction is an atomic setup unit. Failed/unsealed decode is retained
        # and refuses reentry; it is never presented as an ingestion checkpoint.
        if stop():raise Pause('resource/wall before authenticated extraction setup')
        members=integrity.extract(archive,output/'xml')
        sizes=[(output/'xml'/name).stat().st_size for name in integrity.TARGETS]
        db,state=open_state(output,binding)
        ingest(db,state,output,salt,site,sizes,stop)
        indexing(db,state,stop);project(db,state,output,site,stop)
        concatenate(output,state,stop)
        result=dict(site=site,archive_sha256=base.ARCHIVES[site],member_sha256=members,counts=state['counts'],
            retained_edits=state['retained'],projection_sha256=core.sha(output/'edits.parquet'),
            license='CC BY-SA 3.0 per supplied dump notice; source text private; citation and attribution required for redistribution',
            privacy='Identifiers salted locally; comments used only for category then dropped; Users profiles never read.',
            source_only=True,complete_source_bytes=sum(state['bytes']),source_records_by_member=state['records'])
        core.write(output/'SOURCE.json',result);return result
    except Pause as error:
        completed=sum(state['bytes']) if state else 0
        return dict(status='yielded',reason=str(error),phase='source_projection',completed=completed,
            total=sum((output/'xml'/name).stat().st_size for name in integrity.TARGETS) if state else 0,
            source_only=True,complete_card=False)
    finally:
        if db is not None:db.close();seal(output,state)


def verify(output,inputs,config):
    began=time.monotonic();output=Path(output);actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return {**actual,'verified':False}
    expected=json.loads((output/'SOURCE.json').read_text('utf8'))
    if actual!=expected:raise ValueError('Complete GO3 source receipt differs')
    left=pq.ParquetFile(output/'edits.parquet');right=pq.ParquetFile(output/'independent-replay/edits.parquet')
    if left.metadata.num_rows!=right.metadata.num_rows:raise ValueError('GO3 row census differs')
    binding=dict(left_sha256=core.sha(output/'edits.parquet'),right_sha256=core.sha(output/'independent-replay/edits.parquet'),source_sha256=core.sha(__file__))
    path=output/'COMPARED.json';saved=json.loads(path.read_text('utf8')) if path.exists() else dict(binding=binding,rows=0)
    if saved['binding']!=binding:raise ValueError('GO3 replay comparison cursor binding differs')
    prior=int(saved['rows']);position=0
    if prior<0 or prior>left.metadata.num_rows:raise ValueError('GO3 invalid row comparison cursor')
    from itertools import zip_longest
    for a,b in zip_longest(left.iter_batches(batch_size=1024),right.iter_batches(batch_size=1024)):
        if a is None or b is None:raise ValueError('Every GO3 sorted revision row must reconstruct')
        end=position+a.num_rows
        if end>prior:
            if not a.equals(b):raise ValueError('Every GO3 sorted revision row must reconstruct')
            saved['rows']=end
            if end%65536==0:core.write(path,saved)
        position=end
        if requested(output) or time.monotonic()-began>=float(config.get('max_wall_seconds',900)):
            core.write(path,saved)
            return dict(status='yielded',verified=False,phase='compare_all_rows',completed=saved['rows'],total=left.metadata.num_rows)
    if position!=left.metadata.num_rows:raise ValueError('GO3 complete row comparison required')
    saved['rows']=position;core.write(path,saved)
    return dict(verified=True,complete_independent_source_replay=True)
