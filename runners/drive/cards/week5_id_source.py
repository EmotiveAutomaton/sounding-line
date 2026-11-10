"""ID1 source-only complete-pair projection and chronological case census.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Character counts determine pure
human-versus-pet cases; Species labels do not invent quantity differences.
Only one complete 13-scenario session supplies the chronological primary.
Identifiers are salted before derived storage. No response effect is fitted.
"""
from collections import Counter
from pathlib import Path
import hashlib,hmac,json,sqlite3,tarfile
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from . import week5_go as common

SOURCE_SHA='4c8e32872b432831a4b8670b3a2b4b797f4af8f9b39543b784a939aaf49bd7a9'
HUMANS=['Man','Woman','Pregnant','Stroller','OldMan','OldWoman','Boy','Girl','Homeless','LargeWoman','LargeMan','Criminal','MaleExecutive','FemaleExecutive','FemaleAthlete','MaleAthlete','FemaleDoctor','MaleDoctor']
PET=['Dog','Cat']
BASE=['ResponseID','ExtendedSessionID','UserID','ScenarioOrder','Intervention','Saved','ScenarioType','ScenarioTypeStrict','NumberOfCharacters']
UPSERT='''INSERT INTO pairs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(response) DO UPDATE SET
 n=pairs.n+1,saved=pairs.saved+excluded.saved,intervention=pairs.intervention+excluded.intervention,
 human_sides=pairs.human_sides+excluded.human_sides,pet_sides=pairs.pet_sides+excluded.pet_sides,
 humans=pairs.humans+excluded.humans,pets=pairs.pets+excluded.pets,human_saved=pairs.human_saved+excluded.human_saved,
 bad=pairs.bad+excluded.bad+(pairs.person!=excluded.person OR pairs.session!=excluded.session OR pairs.ord!=excluded.ord OR pairs.kind!=excluded.kind),
 strict=CASE WHEN pairs.strict=excluded.strict THEN pairs.strict ELSE '' END'''


def key(value,salt,namespace):return hmac.new(salt,(namespace+':'+str(value)).encode(),hashlib.sha256).hexdigest()


def paired_rows(frame,salt):
    numbers=frame[HUMANS+PET+['NumberOfCharacters','ScenarioOrder']].apply(pd.to_numeric,errors='coerce')
    integer=np.isfinite(numbers).all(axis=1)&numbers.ge(0).all(axis=1)&numbers.eq(np.floor(numbers)).all(axis=1)
    human=numbers[HUMANS].sum(axis=1);pet=numbers[PET].sum(axis=1)
    valid=integer&(human+pet).eq(numbers.NumberOfCharacters)&frame.Saved.isin(['0','1'])&frame.Intervention.isin(['0','1'])
    valid=valid.to_numpy();human=human.to_numpy();pet=pet.to_numpy()
    lookups={name:{value:key(value,salt,namespace) for value in frame[name].unique()} for name,namespace in
             [('ResponseID','moral-response'),('UserID','moral-person'),('ExtendedSessionID','moral-session')]}
    for at,row in enumerate(frame[BASE].itertuples(index=False,name=None)):
        response,session,person,order,intervention,saved,kind,strict,_=row
        good=bool(valid[at]) and bool(response and session and person)
        h=int(human[at]) if np.isfinite(human[at]) else 0;p=int(pet[at]) if np.isfinite(pet[at]) else 0
        hs=int(h>0 and p==0);ps=int(p>0 and h==0);choice=int(saved) if saved in ['0','1'] else 0;iv=int(intervention) if intervention in ['0','1'] else 0
        sequence=int(float(order)) if good else -1
        yield (lookups['ResponseID'][response],lookups['UserID'][person],lookups['ExtendedSessionID'][session],sequence,kind,strict,
               1,choice,iv,hs,ps,h if hs else 0,p if ps else 0,hs*choice,int(not good))


def prepare(output,inputs,config):
    archive=Path(inputs['source']);salt=Path(inputs['salt']).read_bytes()
    if len(salt)!=32 or common.sha(archive)!=SOURCE_SHA:raise ValueError('Moral Machine source or salt pin differs')
    output.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(output/'pairs.sqlite')
    db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF');db.execute('PRAGMA cache_size=-65536');db.execute('PRAGMA temp_store=FILE')
    db.execute('CREATE TABLE pairs(response TEXT PRIMARY KEY,person TEXT,session TEXT,ord INTEGER,kind TEXT,strict TEXT,n INTEGER,saved INTEGER,intervention INTEGER,human_sides INTEGER,pet_sides INTEGER,humans INTEGER,pets INTEGER,human_saved INTEGER,bad INTEGER) WITHOUT ROWID')
    count=0
    with tarfile.open(archive,'r:gz') as container:
        member=next(iter(container))
        if not member.isfile() or '..' in Path(member.name).parts or Path(member.name).is_absolute():raise ValueError('unexpected source member')
        with container.extractfile(member) as stream:
            for frame in pd.read_csv(stream,usecols=BASE+HUMANS+PET,dtype=str,keep_default_na=False,chunksize=100000,nrows=config.get('max_rows')):
                db.executemany(UPSERT,paired_rows(frame,salt));db.commit();count+=len(frame);common.write(output/'PROGRESS.json',{'source_rows':count})
    counts=Counter(source_rows=count)
    counts['responses']=db.execute('SELECT count(*) FROM pairs').fetchone()[0]
    counts['orphans']=db.execute('SELECT count(*) FROM pairs WHERE n=1').fetchone()[0]
    counts['duplicates']=db.execute('SELECT count(*) FROM pairs WHERE n>2').fetchone()[0]
    counts['invalid_source_rows_or_pairs']=db.execute('SELECT count(*) FROM pairs WHERE bad!=0').fetchone()[0]
    if config.get('max_rows'):
        db.close();receipt={'source_only':True,'prefix_only':True,'counts':dict(counts),'source_sha256':SOURCE_SHA};common.write(output/'SOURCE.json',receipt);return receipt
    db.execute('CREATE INDEX person_session ON pairs(person,session,ord)');db.commit()
    # Session count includes incomplete and invalid responses, preventing a
    # returning fingerprint from masquerading as a one-session participant.
    db.execute('CREATE TABLE people AS SELECT person,count(DISTINCT session) AS sessions FROM pairs GROUP BY person')
    db.execute('CREATE UNIQUE INDEX person_key ON people(person)');db.commit()
    counts['fingerprints']=db.execute('SELECT count(*) FROM people').fetchone()[0]
    counts['multi_session_fingerprints_excluded_primary']=db.execute('SELECT count(*) FROM people WHERE sessions!=1').fetchone()[0]
    writer=None;batch=[];current=None;records=[];all_users=0
    def emit(person,values):
        nonlocal writer,batch,all_users
        if person is None:return
        all_users+=1;sessions=values[0][-1]
        valid=[v for v in values if v[5]==2 and v[6]==1 and v[7]==1 and v[12]==0]
        complete=sessions==1 and len(values)==13 and len(valid)==13 and sorted(v[1] for v in valid)==list(range(1,14))
        counts['single_complete_13_scenario_fingerprints']+=int(complete)
        for v in valid:
            session,order,kind,strict,_,n,saved,iv,hs,ps,human,pet,bad,human_saved,_=v
            pure=hs==1 and ps==1 and human>0 and pet>0
            species=pure and kind==strict=='Species' and human==pet
            random=pure and kind=='Random'
            if not (species or random):continue
            batch.append({'person':person,'session':session,'order':order,'kind':'Species' if species else 'Random','humans':human,'pets':pet,
                          'human_saved':human_saved,'primary_session':complete,'sessions':sessions})
            counts['retained_'+('Species' if species else 'Random')]+=1
            if len(batch)>=4096:
                table=pa.Table.from_pylist(batch)
                if writer is None:writer=pq.ParquetWriter(output/'cases.parquet',table.schema,compression='zstd')
                writer.write_table(table);batch=[]
    query='SELECT p.person,p.session,p.ord,p.kind,p.strict,p.response,p.n,p.saved,p.intervention,p.human_sides,p.pet_sides,p.humans,p.pets,p.bad,p.human_saved,u.sessions FROM pairs p JOIN people u ON p.person=u.person ORDER BY p.person,p.session,p.ord,p.response'
    for row in db.execute(query):
        if row[0]!=current:emit(current,records);current=row[0];records=[]
        records.append(row[1:])
    emit(current,records)
    if batch:
        table=pa.Table.from_pylist(batch)
        if writer is None:writer=pq.ParquetWriter(output/'cases.parquet',table.schema,compression='zstd')
        writer.write_table(table)
    if writer is not None:writer.close()
    db.close();receipt={'source_only':True,'prefix_only':False,'counts':dict(counts),'source_sha256':SOURCE_SHA,
                        'cases_sha256':common.sha(output/'cases.parquet') if writer else None,
                        'chronology':'single complete13-scenario session only; orders1–6 first half,7–13 second half; no intersession chronology invented',
                        'no_demographics_loaded':True}
    common.write(output/'SOURCE.json',receipt);return receipt


def execute(output:Path,inputs:dict,config:dict):return prepare(output,inputs,config)
def verify(output:Path,inputs:dict,config:dict):
    actual=prepare(output/'independent-replay',inputs,config);expected=json.loads((output/'SOURCE.json').read_text('utf8'))
    if actual!=expected:raise ValueError('all-source ID1 pair replay differs')
    return {'verified':True,'full_source_replay':True,'source_only':True}
