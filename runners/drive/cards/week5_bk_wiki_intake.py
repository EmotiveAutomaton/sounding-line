"""Frozen random-article recent-window intake; no text labels or model scores.

DESIGN CHECK: BK_PUBLIC_INTAKES.md, LESSONS2/3/5. Exact revision/parent/flag
joins are required. Unknown flags remain unknown and cannot masquerade as human.
The original lifetime T2.r remains held; this source is a separate recent scope.
"""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import hashlib,json,time,urllib.parse,urllib.request
from .week5_bk_klicke_intake import write,read,digest,collection_status

API='https://en.wikipedia.org/w/api.php'
UA='SoundingLineResearch/2026-11-07 (https://github.com/EmotiveAutomaton/sounding-line; commissioned public source intake)'
FORBIDDEN={'user','userid','rvuser','rvexcludeuser','rcuser','rcexcludeuser','aufrom','auprefix','ususers','ususerids'}


class IntakePause(Exception):pass
class SourceGap(ValueError):pass


def content_hash(text):
    number=int(hashlib.sha1(text.encode('utf8')).hexdigest(),16);alphabet='0123456789abcdefghijklmnopqrstuvwxyz';digits=''
    while number:number,remainder=divmod(number,36);digits=alphabet[remainder]+digits
    return (digits or '0').zfill(31)


def safe_params(params):
    if set(params)&FORBIDDEN:raise ValueError('Identity queries are forbidden')
    for key in ('rvprop','rcprop'):
        if set(str(params.get(key,'')).split('|'))&{'user','userid','comment','parsedcomment'}:raise ValueError('Identity or comment retrieval forbidden')
    return dict(action='query',format='json',formatversion=2,maxlag=5,**params)


class Wire:
    def __init__(self,root,verify=False,script=None):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.verify=verify;self.script=script;self.index=0;self.started=time.monotonic();self.network=0;self.byte_count=0

    def get(self,params):
        params=safe_params(params);i=self.index;self.index+=1;path=self.root/f'{i:06d}.json.gz'
        if path.exists():
            record=read(path)
            if record['params']!=params:raise ValueError('Cached request differs from frozen sequence')
            return record['response']
        if self.verify:raise ValueError('Missing frozen source response')
        if self.script is not None:
            record=self.script[i]
            if record['params']!=params:raise ValueError('Constructed request oracle mismatch')
            body=record['response']
        else:
            if time.monotonic()-self.started>10800 or self.network>=400:raise IntakePause('request_or_wall_quantum')
            request=urllib.request.Request(API+'?'+urllib.parse.urlencode(params),headers={'User-Agent':UA,'Api-User-Agent':UA,'Accept-Encoding':'identity'})
            try:
                with urllib.request.urlopen(request,timeout=60) as response:raw=response.read(32*1024**2+1)
            except Exception as error:raise RuntimeError('Public API transport failure; cached prefix retained: '+type(error).__name__) from None
            if len(raw)>32*1024**2:raise ValueError('Single response cap')
            self.byte_count+=len(raw);self.network+=1
            if self.byte_count>4*1024**3:raise ValueError('Intake attempt byte cap')
            body=json.loads(raw)
        if 'error' in body:raise ValueError('Public API returned an error; no source admission')
        if 'warnings' in body:raise ValueError('Public API warning requires source review')
        write(path,dict(params=params,response=body));return body


def page(response,pageid=None):
    pages=response.get('query',{}).get('pages',[])
    if len(pages)!=1:raise ValueError('Expected exactly one article')
    row=pages[0]
    if pageid is not None and row.get('pageid')!=pageid:raise ValueError('Article identity mismatch')
    if 'missing' in row or row.get('ns')!=0:raise ValueError('Missing or non-article source')
    return row


def article(wire,entry,start,end):
    pageid=entry['pageid'];revisions=[];continuation={};seen=set()
    while True:
        response=wire.get(dict(prop='revisions',pageids=pageid,rvprop='ids|timestamp|sha1|content',rvslots='main',rvlimit=50,rvstart=end,rvend=start,rvdir='older',**continuation))
        got=page(response,pageid)
        if got['title']!=entry['title']:raise SourceGap('Article moved during source freeze')
        revisions.extend(got.get('revisions',[]));continuation=response.get('continue',{})
        if not continuation:break
        token=json.dumps(continuation,sort_keys=True)
        if token in seen or set(continuation)-{'continue','rvcontinue'}:raise ValueError('Invalid revision continuation')
        seen.add(token)
        if len(seen)>2000:raise ValueError('Article history bound reached')
    revisions.sort(key=lambda r:(r['timestamp'],r['revid']))
    if len({r['revid'] for r in revisions})!=len(revisions):raise ValueError('Repeated revision ID')
    flags={};continuation={};seen=set()
    while True:
        response=wire.get(dict(list='recentchanges',rcnamespace=0,rctype='edit|new',rctitle=entry['title'],rcprop='ids|timestamp|flags|sha1',rclimit=500,rcstart=start,rcend=end,rcdir='newer',**continuation))
        for row in response.get('query',{}).get('recentchanges',[]):
            if row['pageid']!=pageid or row['revid'] in flags:raise ValueError('Ambiguous recent-change join')
            if type(row.get('bot')) is not bool:raise SourceGap('Missing event-level bot flag')
            flags[row['revid']]=row
        continuation=response.get('continue',{})
        if not continuation:break
        token=json.dumps(continuation,sort_keys=True)
        if token in seen or set(continuation)-{'continue','rccontinue'}:raise ValueError('Invalid recent-change continuation')
        seen.add(token)
    if set(flags)!={r['revid'] for r in revisions}:raise SourceGap('Recent-change flags do not cover complete frozen window')
    clean=[]
    for rev in revisions:
        flag=flags[rev['revid']]
        if rev.get('sha1')!=flag.get('sha1') or rev['timestamp']!=flag['timestamp'] or rev.get('parentid')!=flag.get('old_revid'):raise ValueError('Revision/flag binding mismatch')
        content=rev.get('slots',{}).get('main',{}).get('content')
        if not isinstance(content,str) or not rev.get('sha1'):raise SourceGap('Hidden content/hash source gap')
        if content_hash(content)!=rev['sha1']:raise ValueError('Revision content checksum mismatch')
        clean.append(dict(revision=rev['revid'],parent=rev['parentid'],timestamp=rev['timestamp'],sha1=rev['sha1'],bot_flag=flag['bot'],text=content))
    baseline=None
    if clean and clean[0]['parent']:
        response=wire.get(dict(prop='revisions',revids=clean[0]['parent'],rvprop='ids|timestamp|sha1|content',rvslots='main'))
        old=page(response,pageid).get('revisions',[])
        if len(old)!=1 or old[0]['revid']!=clean[0]['parent']:raise SourceGap('Baseline parent absent')
        old=old[0];content=old.get('slots',{}).get('main',{}).get('content')
        if not isinstance(content,str) or not old.get('sha1'):raise SourceGap('Hidden baseline content/hash')
        if old['timestamp']>=start:raise ValueError('Invalid baseline boundary')
        if content_hash(content)!=old['sha1']:raise ValueError('Baseline content checksum mismatch')
        baseline=dict(revision=old['revid'],timestamp=old['timestamp'],sha1=old['sha1'],text=content,bot_flag=None,left_censored=True)
    for previous,current in zip(clean,clean[1:]):
        if current['parent']!=previous['revision']:raise ValueError('Revision-chain gap')
    return dict(pageid=pageid,title=entry['title'],window_start=start,window_end=end,revisions=clean,baseline=baseline,
                scope='recent_event_flags_only_not_lifetime_or_verified_human',labels_computed=False)


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config.get('card')!='BK-T2.r-recent-intake' or config.get('mode') not in ('constructed','corpus'):raise ValueError('Wrong source scope')
    if set(config)-{'card','mode','articles','window_start','window_end','max_new_draws'}:raise ValueError('Unknown source config')
    if config['mode']=='corpus' and config['articles']!=200:raise ValueError('Frozen200article scope required')
    if type(config.get('max_new_draws',10)) is not int or config.get('max_new_draws',10)<1:raise ValueError('Positive article quantum required')
    start,end=config['window_start'],config['window_end'];a=datetime.fromisoformat(start.replace('Z','+00:00'));b=datetime.fromisoformat(end.replace('Z','+00:00'))
    if b-a!=timedelta(days=7):raise ValueError('Exactly seven-day proposed window required')
    if config['mode']=='corpus' and not verification and (b>datetime.now(timezone.utc)-timedelta(minutes=30) or a<datetime.now(timezone.utc)-timedelta(days=29)):raise ValueError('Window outside safe recent-change retention')
    script=read(inputs['constructed_wire']) if config['mode']=='constructed' else None
    wire=Wire(output/'wire',verification,script);roster=[];considered=[];seen=set()
    while len(roster)<config['articles']:
        response=wire.get(dict(list='random',rnnamespace=0,rnfilterredir='nonredirects',rnlimit=1))
        randoms=response.get('query',{}).get('random',[])
        if len(randoms)!=1:raise ValueError('Random draw must return one article')
        candidate=randoms[0];pid=candidate['id']
        if pid in seen:considered.append(dict(pageid=pid,status='duplicate'));continue
        seen.add(pid)
        eligible=page(wire.get(dict(prop='revisions',pageids=pid,rvprop='ids|timestamp',rvlimit=50,rvstart=end,rvdir='older')),pid)
        count=len(eligible.get('revisions',[]));record=dict(pageid=pid,title=eligible['title'],eligible=count>=50,revision_prefix_count=count)
        considered.append(record)
        if record['eligible']:roster.append(dict(pageid=pid,title=eligible['title']))
        if len(considered)>10000:raise ValueError('Random candidate cap; no reduced roster')
    write(output/'ROSTER.json',dict(articles=roster,considered=considered,window_start=start,window_end=end))
    new=0;records=[]
    for ordinal,entry in enumerate(roster):
        dest=output/'articles'/f'{ordinal:05d}.json.gz';existed=dest.exists()
        try:record=article(wire,entry,start,end)
        except SourceGap as error:record=dict(pageid=entry['pageid'],title=entry['title'],status='source_gap',reason=str(error),revisions=[],baseline=None,labels_computed=False)
        if verification:
            if not existed or read(dest)!=record:raise ValueError('Independent frozen-wire replay mismatch')
        else:write(dest,record)
        new+=not existed;records.append(dict(ordinal=ordinal,sha256=digest(dest),revisions=len(record['revisions']),bot_events=sum(r['bot_flag'] for r in record['revisions']),baseline=record['baseline'] is not None,source_gap=record.get('status')=='source_gap'))
        if not verification and ordinal+1<len(roster) and (new>=config.get('max_new_draws',10) or (output/'YIELD_REQUEST.json').exists()):
            (output/'CHECKPOINT.json').write_text(json.dumps(dict(articles=ordinal+1,total=len(roster),cached_requests=wire.index)),encoding='utf8')
            return dict(status='yielded',reason='article_quantum',checkpoint='CHECKPOINT.json',completed_units=ordinal+1)
    result=dict(status='complete',articles=len(roster),requests=wire.index,records=records,collection_status=collection_status(len(roster),sum(r['source_gap'] for r in records)),scope='recent_window_input_only',source_licence='CC-BY-SA-4.0',scientific_inference=False,lifetime_T2r_held=True)
    if verification:
        if read(output/'SUMMARY.json')!=result:raise ValueError('Frozen-wire aggregate replay mismatch')
    else:write(output/'SUMMARY.json',result)
    return dict(status='complete',articles=len(roster),new_articles=new,verified=verification)


def execute(output,inputs,config):
    try:return run(output,inputs,config)
    except IntakePause as error:
        output=Path(output);count=len(list((output/'wire').glob('*.json.gz')))
        (output/'CHECKPOINT.json').write_text(json.dumps(dict(cached_requests=count,reason=str(error))),encoding='utf8')
        return dict(status='yielded',reason=str(error),checkpoint='CHECKPOINT.json',completed_units=count)
def verify(output,inputs,config):return run(output,inputs,config,True)
