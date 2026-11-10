"""Identifier-stripped KLICKE source intake; no navigation outcomes or inference.

DESIGN CHECK: LESSONS 2/3/5; BK_PUBLIC_INTAKES.md. Known archives preserve
all event rows and exact text. Missing columns, ambiguous source pairs, unsafe
paths and source/output mutation fail closed; absence of an event class is a
support count, never an effect. Native fixture covers fresh complete replay.
"""
from collections import Counter
from pathlib import Path, PurePosixPath
import csv,gzip,hashlib,hmac,io,json,math,time,zipfile

ARCHIVE_SHA='ffa4d753fdb9a54f5cadd6836426d56a0cabe73ceade8e7e40dddbbae178555d'
COLUMNS=('DownEventID','UpEventID','DownTime','UpTime','ActionTime','DownEvent','UpEvent','CursorPosition','PauseTime','WordCount','TextChange','Activity')
NUMERIC=('DownTime','UpTime','ActionTime','CursorPosition','PauseTime','WordCount')


def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
    if path.suffix=='.gz':data=gzip.compress(data,mtime=0)
    if path.exists() and path.read_bytes()!=data:raise ValueError('Immutable intake output changed')
    if not path.exists():path.write_bytes(data)


def read(path):
    path=Path(path);data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix=='.gz' else data)


def collection_status(total,failed):
    if total<1 or not 0<=failed<=total:raise ValueError('Invalid collection denominator')
    return 'passes' if failed*100<=total else 'invalid_over_one_percent'


def inventory(z):
    files=z.infolist();names=set();pairs={};excluded=Counter();total=0
    for info in files:
        name=info.orig_filename;p=PurePosixPath(name);total+=info.file_size
        if (name in names or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name
            or ((info.external_attr>>16)&0o170000)==0o120000):raise ValueError('Unsafe or duplicate archive member')
        names.add(name)
        if info.file_size>32*1024**2 or total>10*1024**3:raise ValueError('Archive size cap')
        if info.is_dir():continue
        if p.suffix.lower() in ('.csv','.txt'):
            pairs.setdefault(p.stem,{}).setdefault(p.suffix.lower(),[]).append(info)
        else:excluded[p.suffix.lower()]+=1
    kept=[]
    for stem,parts in sorted(pairs.items()):
        if '.csv' not in parts or '.txt' not in parts:
            excluded['unpaired_'+next(iter(parts))]+=sum(map(len,parts.values()));continue
        if len(parts['.csv'])!=1 or len(parts['.txt'])!=1:raise ValueError('Ambiguous event/text pair')
        kept.append((stem,parts['.csv'][0],parts['.txt'][0]))
    return kept,dict(excluded)


def project(csv_bytes,text_bytes,key):
    rows=csv.DictReader(io.StringIO(csv_bytes.decode('utf-8-sig'),newline=''))
    if not set(COLUMNS)<=set(rows.fieldnames or []):raise ValueError('Missing required event schema')
    output=[];counts=Counter();last=-math.inf
    for ordinal,row in enumerate(rows):
        numbers={}
        for col in NUMERIC:
            try:value=float(row[col])
            except (TypeError,ValueError):raise ValueError('Invalid numeric event field') from None
            if not math.isfinite(value):raise ValueError('Nonfinite numeric event field')
            if col!='PauseTime' and value<0:raise ValueError('Negative event field')
            numbers[col]=value
        if numbers['DownTime']<last:raise ValueError('Event clock decreases')
        if numbers['UpTime']<numbers['DownTime']:raise ValueError('Negative key duration')
        if any(numbers[k]!=int(numbers[k]) for k in ('CursorPosition','WordCount')):raise ValueError('Noninteger event extent')
        last=numbers['DownTime'];event={**numbers,**{k:row[k] for k in ('DownEvent','UpEvent','TextChange','Activity')},'ordinal':ordinal}
        output.append(event)
        counts['events']+=1
        if row['DownEvent']=='Leftclick':counts['left_click_events']+=1
        if row['DownEvent'] in ('ArrowLeft','ArrowRight','ArrowUp','ArrowDown'):counts['arrow_key_events']+=1
    return dict(session=key,cluster_status='source_session_only_writer_link_not_authenticated',events=output,
                final_text=text_bytes.decode('utf-8-sig'),counts=dict(counts))


def settings(inputs,config):
    if config.get('card')!='BK-S4.k-intake' or config.get('mode') not in ('constructed','corpus'):raise ValueError('Wrong intake config')
    if set(config)-{'card','mode','expected_sessions','max_new_draws'}:raise ValueError('Unknown intake config')
    if type(config.get('max_new_draws',250)) is not int or config.get('max_new_draws',250)<1:raise ValueError('Positive session quantum required')
    archive=Path(inputs['archive']);salt=Path(inputs['identity_salt']).read_bytes()
    if len(salt)!=32:raise ValueError('Identity salt must contain32bytes')
    expected=inputs['archive_sha256']
    if config['mode']=='corpus' and (expected!=ARCHIVE_SHA or config['expected_sessions']!=4992):raise ValueError('Unregistered source')
    if digest(archive)!=expected:raise ValueError('Archive hash mismatch')
    return archive,salt


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);archive,salt=settings(inputs,config);start=time.process_time();counts=Counter();index=[];new=0;reused=0
    with zipfile.ZipFile(archive) as z:
        rows,excluded=inventory(z)
        if len(rows)!=config['expected_sessions']:raise ValueError('Full archive roster mismatch')
        for ordinal,(stem,events,text) in enumerate(rows):
            key=hmac.new(salt,stem.encode(),hashlib.sha256).hexdigest();dest=output/'sessions'/f'{ordinal:05d}.json.gz'
            if not verification and dest.exists():value=read(dest);reused+=1
            else:
                try:value=project(z.read(events),z.read(text),key)
                except (ValueError,UnicodeError,csv.Error) as error:
                    value=dict(session=key,status='parse_failed',reason=str(error) if isinstance(error,ValueError) and not isinstance(error,UnicodeError) else type(error).__name__,counts=dict(parse_failed_sessions=1))
                new+=1
                if verification:
                    if not dest.exists() or read(dest)!=value:raise ValueError('Independent archive replay mismatch')
                else:write(dest,value)
            if value['session']!=key:raise ValueError('Session binding mismatch')
            counts.update(value['counts']);index.append(dict(ordinal=ordinal,session=key,path=dest.relative_to(output).as_posix(),sha256=digest(dest)))
            if not verification:
                (output/'PROGRESS.json').write_text(json.dumps(dict(sessions=ordinal+1,total=len(rows),cpu_seconds=time.process_time()-start)),encoding='utf8')
            if not verification and ordinal+1<len(rows) and (new>=config.get('max_new_draws',250) or (output/'YIELD_REQUEST.json').exists()):
                (output/'CHECKPOINT.json').write_text(json.dumps(dict(sessions=ordinal+1,total=len(rows),archive_sha256=inputs['archive_sha256'])),encoding='utf8')
                return dict(status='yielded',reason='source_session_quantum',checkpoint='CHECKPOINT.json',completed_units=ordinal+1,new_sessions=new,reused_sessions=reused)
    result=dict(status='complete',sessions=len(index),counts=dict(counts),collection_status=collection_status(len(index),counts['parse_failed_sessions']),excluded_members=excluded,archive_sha256=inputs['archive_sha256'],scientific_inference=False,
                identity_fields_removed=True,source_text_private=True,licence='CC-BY-4.0',cluster_status='source_session_only_writer_link_not_authenticated')
    if verification:
        if read(output/'INDEX.json')!=index or read(output/'SUMMARY.json')!=result:raise ValueError('Fresh aggregate replay mismatch')
    else:write(output/'INDEX.json',index);write(output/'SUMMARY.json',result)
    return dict(status='complete',sessions=len(index),new_sessions=new,reused_sessions=reused,independent_source_replay=verification)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
