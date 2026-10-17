"""Bounded official public-source GETs; no paid calls or corpus-wide inference.

DESIGN CHECK: LESSONS 3-5. NULL: incomplete pagination, duplicate revision,
changed hash, wrong host or exhausted bound fails rather than claiming complete
source. ALTERNATIVE: exact bytes, EOF and continuation evidence authenticate
the frozen source window. Retry-After only for safe GETs, never paid dispatch.
"""
import argparse,hashlib,json,os,re,threading,time,traceback,urllib.request,urllib.parse,urllib.error
from pathlib import Path
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,now,limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot,require_resources

RAW=REPO/'results/phase_2_4_stage_15/raw'
UA='SoundingLineResearch/2026-10-16 (https://github.com/EmotiveAutomaton/sounding-line; local research)'
TITLES=['Empathy','Theory of mind','Affective neuroscience','Jaak Panksepp','Aesthetics']
CHESS='lichess_db_standard_rated_2026-07.pgn.zst'


def get(url):
    if urllib.parse.urlsplit(url).hostname not in ('en.wikipedia.org','database.lichess.org'):raise ValueError('source host not authorized')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*a,**k):raise ValueError('source redirect needs review')
    op=urllib.request.build_opener(NoRedirect(),urllib.request.ProxyHandler({}))
    for attempt in range(4):
        try:return op.open(urllib.request.Request(url,headers={'User-Agent':UA,'Api-User-Agent':UA,'Accept-Encoding':'identity'}),timeout=60)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429,503) or attempt==3:raise
            delay=exc.headers.get('Retry-After','10')
            if not delay.isdigit() or int(delay)>60:raise ValueError('long/unknown Retry-After; stop for reviewed retry')
            time.sleep(max(1,int(delay)))


def query(parameters):
    return 'https://en.wikipedia.org/w/api.php?'+urllib.parse.urlencode(dict(action='query',format='json',formatversion=2,maxlag=5,**parameters))


def prepare(kind):
    root=RAW/f'drive-{kind}-intake-v1'
    if (root/'PLAN.json').exists():raise ValueError('already prepared')
    source=[REPO/p for p in ('runners/drive/intake.py','runners/stage14/common.py','runners/stage9/process_identity.py',
        'runners/next_round/queue.py','docs/design/stage-15/drive/INTAKE.md','tests/test_drive_intake.py')]
    freeze(root/'PLAN.json',dict(kind=kind,at=now(),pins=pins(source),upper_timestamp=now(),
        max_wall_seconds=14400 if kind=='wikipedia' else 43200,max_bytes=1024**3 if kind=='wikipedia' else 35*1024**3,
        max_requests=5000,max_revisions=250000,concurrency=1,model_calls=0,provider_spend_cents=0))


def metadata_page(data,seen):
    if 'error' in data:raise ValueError('MediaWiki API error: '+str(data['error'].get('code')))
    pages=data.get('query',{}).get('pages',[])
    if len(pages)!=1 or 'missing' in pages[0]:raise ValueError('missing/ambiguous article')
    rows=pages[0].get('revisions',[])
    for row in rows:
        if type(row.get('revid'))!=int or row['revid'] in seen:raise ValueError('invalid/duplicate revision')
        seen.add(row['revid'])
    return pages[0],rows,data.get('continue')


def wiki(root,plan,guard):
    total_bytes=requests=revisions=0
    def fetch(parameters,name):
        nonlocal total_bytes,requests
        guard('revision_metadata',dict(requests=requests,bytes=total_bytes,revisions=revisions))
        if requests>=plan['max_requests']:raise ValueError('request ceiling')
        url=query(parameters)
        with get(url) as response:body=response.read(16*1024**2+1)
        if len(body)>16*1024**2:raise ValueError('individual response bound')
        total_bytes+=len(body);requests+=1
        if total_bytes>plan['max_bytes']:raise ValueError('response byte ceiling')
        dest=root/'responses'/(name+'.json');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
        freeze(root/'requests'/(name+'.json'),dict(url=url,sha256=filehash(dest),bytes=len(body)))
        data=json.loads(body)
        if 'error' in data:raise ValueError('API error: '+str(data['error'].get('code')))
        return data
    random=fetch(dict(list='random',rnnamespace=0,rnlimit=100,rnfilterredir='nonredirects'),'random')
    titles=TITLES+[r['title'] for r in random['query']['random']]
    if len(set(titles))!=105:raise ValueError('random roster overlaps named article or duplicates; preserve and review')
    freeze(root/'ROSTER.json',dict(titles=titles,random_count=100,named=TITLES,upper_timestamp=plan['upper_timestamp']))
    index=[]
    for article,title in enumerate(titles):
        cont=None;seen=set();batch=0;last=None
        while True:
            parameters=dict(prop='revisions',titles=title,rvdir='newer',rvend=plan['upper_timestamp'],rvlimit=500,
                rvprop='ids|timestamp|user|userid|comment|sha1|tags|size|flags')
            if cont:parameters.update(cont)
            data=fetch(parameters,f'{article:03}-{batch:04}');page,rows,next_cont=metadata_page(data,seen)
            for row in rows:
                if last is not None and row['timestamp']<last:raise ValueError('nonchronological revision chain')
                last=row['timestamp']
            revisions+=len(rows)
            if revisions>plan['max_revisions']:raise ValueError('revision ceiling')
            batch+=1
            if not next_cont:break
            if next_cont==cont:raise ValueError('continuation did not advance')
            cont=next_cont
        index.append(dict(article=article,title=page['title'],pageid=page['pageid'],revisions=len(seen),batches=batch,history_complete=True))
        freeze(root/'articles'/f'{article:03}.json',index[-1])
    freeze(root/'INDEX.json',dict(articles=index,revisions=revisions,requests=requests,response_bytes=total_bytes,
        metadata_only=True,full_text_history_ready=False,source_window_ended_at=plan['upper_timestamp']))


def chess(root,plan,guard):
    if resource_snapshot()['disk_free_GiB']<50:raise ValueError('50 GiB download floor')
    checksum_url='https://database.lichess.org/standard/sha256sums.txt'
    with get(checksum_url) as response:data=response.read(1024**2+1)
    if len(data)>1024**2:raise ValueError('checksum listing bound')
    (root/'sha256sums.txt').write_bytes(data)
    matches=[line.split()[0] for line in data.decode().splitlines() if len(line.split())==2 and line.split()[1]==CHESS]
    if len(matches)!=1 or not re.fullmatch('[0-9a-f]{64}',matches[0]):raise ValueError('missing authoritative checksum')
    url='https://database.lichess.org/standard/'+CHESS;freeze(root/'SOURCE.json',dict(url=url,sha256=matches[0],checksum_listing_sha256=filehash(root/'sha256sums.txt'),license='CC0',selection='smallest of last three completed months: 2026-07..09'))
    h=hashlib.sha256();n=0;last=time.time()
    with get(url) as response, (root/CHESS).open('xb') as dest:
        length=response.headers.get('Content-Length');length=int(length) if length else None
        if length is not None and length>plan['max_bytes']:raise ValueError('declared download exceeds byte cap')
        while True:
            chunk=response.read(1024**2)
            if not chunk:break
            n+=len(chunk)
            if n>plan['max_bytes']:raise ValueError('download byte ceiling')
            dest.write(chunk);h.update(chunk)
            if time.time()-last>=5:guard('download',dict(bytes=n,expected_bytes=length));last=time.time()
    if length is not None and n!=length:raise ValueError('incomplete content length')
    if h.hexdigest()!=matches[0]:raise ValueError('published source checksum mismatch')
    freeze(root/'DOWNLOAD.json',dict(bytes=n,sha256=h.hexdigest(),published_sha256_equal=True,complete_eof=True,
        parsed=False,inference_cohort_frozen=False))


def run(kind):
    root=RAW/f'drive-{kind}-intake-v1';limits();plan=read(root/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    with (root/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    started=time.time();stop=threading.Event()
    def guard(task,progress):
        require_resources(resource_snapshot())
        if time.time()-started>plan['max_wall_seconds']:raise TimeoutError('intake wall ceiling')
        atomic(root/'PROGRESS.json',dict(at=now(),task=task,progress=progress))
    def deadline():
        if stop.wait(plan['max_wall_seconds']+90):return
        atomic(root/'FAILED.json',dict(status='FAILED',at=now(),reason='hard intake deadline'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (root/'MONITOR_READY.json').exists():
            if time.time()-started>90:raise TimeoutError('native monitor handshake')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('monitor binding')
        (wiki if kind=='wikipedia' else chess)(root,plan,guard);check_pins(plan['pins'])
        # Source file hashes are retained in DOWNLOAD/individual request receipts.
        freeze(root/'COMPLETE.json',dict(status='COMPLETE',at=now(),kind=kind,
            outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*.json') if p.name not in ('PROGRESS.json','MONITOR_READY.json')},
            source_only=True,scientific_admission=False,write_through_required=True))
    except BaseException as exc:
        freeze(root/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc),traceback=traceback.format_exc()));raise
    finally:stop.set()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);ap.add_argument('kind',choices=['wikipedia','lichess']);a=ap.parse_args()
    prepare(a.kind) if a.action=='prepare' else run(a.kind)
