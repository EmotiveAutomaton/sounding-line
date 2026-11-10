"""Private, salted AMI/ICSI dialogue and laughter source projection.

DESIGN CHECK: LESSONS 3--5 and CONTROLS 1--6, 2026-11-07. Source labels
never enter lexical predictors. Word order is XML order, not an assumed ID
sequence. Missing timing/metadata is counted, never guessed from outcomes.
"""
from collections import Counter,defaultdict
from pathlib import Path,PurePosixPath
import hashlib,hmac,math,re,zipfile
import xml.etree.ElementTree as ET

from .timing_census import read,filehash
from .timing_p6 import gzip_equal,gzread,write_equal,progress

NID='{http://nite.sourceforge.net/}id'
LAUGH=re.compile('laugh',re.I)
PINS={'AMI':'b56e5babb2496b8795deeeda7e71178d7fbc9963f94276cf2a3f4b56ebbc9f9d',
      'ICSI-core':'cf4860245b9ca9c9ed11a66e5a74cfea2a99a686a52f7580aa0a6bc2225895a9',
      'ICSI-plus':'e4ab79a8b638bdd29121d744c452c680fe23791e406ffe5125e2f5b118923439'}


def tag(node):return node.tag.rsplit('}',1)[-1]
def number(value):
    try:
        x=float(value)
        return x if math.isfinite(x) and x>=0 else None
    except (TypeError,ValueError):return None


def pointer(href,nodes):
    ids=re.findall(r'id\(([^)]+)\)',href)
    if len(ids) not in (1,2):raise ValueError('Unknown NXT pointer syntax')
    lookup={a.get(NID):i for i,a in enumerate(nodes)}
    if len(lookup)!=len(nodes):raise ValueError('Duplicate XML word identity')
    if any(i not in lookup for i in ids):raise ValueError('Missing XML pointer endpoint')
    first,last=lookup[ids[0]],lookup[ids[-1]]
    if first>last:raise ValueError('Reversed XML pointer range')
    return nodes[first:last+1]


def time_bounds(nodes,index):
    a=nodes[index];start,end=number(a.get('starttime')),number(a.get('endtime'))
    if start is not None and end is not None and end>=start:return start,end,'explicit'
    before=next((number(x.get('endtime')) for x in reversed(nodes[:index])
                 if tag(x)=='w' and number(x.get('endtime')) is not None),None)
    after=next((number(x.get('starttime')) for x in nodes[index+1:]
                if tag(x)=='w' and number(x.get('starttime')) is not None),None)
    if before is not None and after is not None and after>=before:return before,after,'adjacent_words'
    return None,None,'missing'


def project_stream(nodes,meeting,speaker,corpus,counts):
    words=[];laughs=[]
    for i,a in enumerate(nodes):
        kind=tag(a);annotation=a.get('type',a.get('description',''))
        if kind=='w':
            text=''.join(a.itertext()).strip()
            if not text:counts['empty_word']+=1;continue
            words.append(dict(xml_id=a.get(NID),text=text,kind='word',
                              start=number(a.get('starttime')),end=number(a.get('endtime'))))
        else:
            counts['removed_'+kind]+=1
            is_laugh=(kind=='vocalsound' and (annotation=='laugh' if corpus=='AMI' else bool(LAUGH.search(annotation))))
            # Speech-comment annotations are retained separately as a declared
            # broader-label texture, never smuggled into the primary outcome.
            speech_laugh=kind=='comment' and bool(re.search(r'while .*laugh|while laugh|laughing on',annotation,re.I))
            if is_laugh or speech_laugh:
                start,end,method=time_bounds(nodes,i);counts['laugh_timing_'+method]+=1
                if start is not None:
                    laughs.append(dict(meeting=meeting,speaker=speaker,start=start,end=end,
                                       label='vocal' if is_laugh else 'speech_comment',timing=method))
    return words,laughs


def normalized(value):
    s=' '.join((value or '').lower().split())
    return None if s in ('','unknown','unspecified','n/a','none','non-native') else s


def corpus_data(z,corpus,salt,counts):
    def identity(kind,value):return hmac.new(salt,(corpus+'|'+kind+'|'+value).encode(),hashlib.sha256).hexdigest()[:24]
    names=set(z.namelist());prefix='' if corpus=='AMI' else 'ICSI/'
    word_dir='words' if corpus=='AMI' else 'Words';da_dir='dialogueActs' if corpus=='AMI' else 'DialogueActs'
    word_files=sorted(n for n in names if n.startswith(prefix+word_dir+'/') and n.endswith('.xml'))
    metadata=defaultdict(lambda:dict(duration=0.,speakers={},corpus=corpus));streams={};all_laughs=[];acts=[]
    ami_speakers={};ami_people={};icsi_people={}
    if corpus=='AMI':
        for p in ET.fromstring(z.read('corpusResources/participants.xml')):
            ami_people[p.get(NID)]=dict(native_language=normalized(p.get('native_language')))
        for m in ET.fromstring(z.read('corpusResources/meetings.xml')):
            for s in m:
                if tag(s)=='speaker':ami_speakers[(m.get('observation'),s.get('nxt_agent'))]=s.get('global_name')
    else:
        for s in ET.fromstring(z.read('ICSI/speakers.xml')):
            language=next((a for a in s if tag(a)=='language'),None)
            if language is None:continue
            fields={tag(a):normalized(a.text) for a in language if tag(a) in ('variety','region')}
            # The archive records a variety of English, not necessarily native
            # language or nationality. Preserve that exact construct.
            icsi_people[s.get('tag')]=dict(english_variety=fields.get('variety'),region=fields.get('region'))
    for path in word_files:
        stem=PurePosixPath(path).name.split('.');rawmeeting,agent=stem[0],stem[1]
        meeting=identity('meeting',rawmeeting);speaker=identity('speaker',rawmeeting+'|'+agent)
        nodes=list(ET.fromstring(z.read(path)));words,laughs=project_stream(nodes,meeting,speaker,corpus,counts)
        streams[path]=(nodes,{w['xml_id']:w for w in words},meeting,speaker)
        all_laughs.extend(laughs);counts['word_streams']+=1
        times=[w['end'] for w in words if w['end'] is not None]+[a['end'] for a in laughs]
        metadata[meeting]['duration']=max([metadata[meeting]['duration']]+times)
        info=ami_people.get(ami_speakers.get((rawmeeting,agent)),{}) if corpus=='AMI' else {}
        metadata[meeting]['speakers'][speaker]=info
    for path in sorted(n for n in names if n.startswith(prefix+da_dir+'/') and n.endswith('.xml')):
        for node in ET.fromstring(z.read(path)):
            counts['annotated_acts']+=1
            children=[a for a in node if tag(a)=='child']
            if len(children)!=1:counts['act_unsupported_pointer_count']+=1;continue
            href=children[0].get('href','');target=href.split('#')[0].replace('\\','/')
            wordpath=prefix+word_dir+'/'+PurePosixPath(target).name
            if wordpath not in streams:counts['act_missing_wordstream']+=1;continue
            nodes,lookup,meeting,speaker=streams[wordpath]
            try:selected=pointer(href,nodes)
            except ValueError:counts['act_pointer_unsupported']+=1;continue
            words=[lookup[a.get(NID)] for a in selected if a.get(NID) in lookup]
            start=number(node.get('starttime'));end=number(node.get('endtime'))
            if start is None:start=next((w['start'] for w in words if w['start'] is not None),None)
            if end is None:end=next((w['end'] for w in reversed(words) if w['end'] is not None),None)
            if start is None or end is None or end<start:counts['act_missing_timing']+=1;continue
            if not words:counts['act_no_lexical_words']+=1;continue
            if corpus=='AMI':
                types=[a.get('href','').split('#')[-1] for a in node if tag(a)=='pointer' and a.get('role')=='da-aspect']
                acttype=types[0] if len(types)==1 else None
            else:
                acttype=node.get('type');person=node.get('participant')
                if person in icsi_people:metadata[meeting]['speakers'][speaker]=icsi_people[person]
            if not acttype:counts['act_missing_type']+=1;continue
            acts.append(dict(id=identity('act',path+'|'+str(node.get(NID))),meeting=meeting,speaker=speaker,
                             corpus=corpus,start=start,end=end,act_type=acttype,
                             words=[{k:v for k,v in w.items() if k!='xml_id'} for w in words]))
            counts['supported_acts']+=1
    return acts,all_laughs,dict(metadata)


def produce(output,inputs,config,verifying=False):
    if set(inputs)!={'archive_root','identity_salt'} or config!={}:raise ValueError('Exact LA source inputs/config required')
    salt=Path(inputs['identity_salt']).read_bytes()
    if len(salt)!=32:raise ValueError('Campaign identity salt must have 32 bytes')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);source=Path(inputs['archive_root'])
    pins={name:filehash(source/(name+'.zip')) for name in PINS}
    if pins!=PINS:raise ValueError('Laughter archive pin changed')
    allacts=[];alllaughs=[];metadata={};counts={}
    for archive,corpus in [('AMI','AMI'),('ICSI-core','ICSI')]:
        counter=Counter()
        with zipfile.ZipFile(source/(archive+'.zip')) as z:
            acts,laughs,meta=corpus_data(z,corpus,salt,counter)
        allacts.extend(acts);alllaughs.extend(laughs);metadata.update(meta);counts[corpus]=dict(counter)
        progress(root/'PROGRESS.json',dict(phase='verify_source' if verifying else 'source',corpus=corpus))
    # Core and plus contain duplicate transcript layers; plus is pinned and
    # retained, not concatenated as an independent population.
    values={'ACTS.json.gz':allacts,'LAUGHS.json.gz':alllaughs,'METADATA.json.gz':metadata}
    for name,value in values.items():
        if verifying:
            if gzread(root/name)!=value:raise ValueError('Full laughter source replay differs')
        else:gzip_equal(root/name,value)
    summary=dict(status='complete',source_sha256=pins,salt_sha256=hashlib.sha256(salt).hexdigest(),
                 meetings=len(metadata),acts=len(allacts),laughs=len(alllaughs),counts=counts,
                 ICSI_plus='pinned duplicate transcript layer; not double counted',
                 metadata_constructs={'AMI':'self-reported native language','ICSI':'English variety and region, not presumed nationality/native language'})
    if verifying:
        if read(root/'SUMMARY.json')!=summary:raise ValueError('Laughter aggregate replay differs')
        return dict(verified=True,complete_source_replay=True)
    write_equal(root/'SUMMARY.json',summary);return summary


def execute(output,inputs,config):return produce(output,inputs,config)
def verify(output,inputs,config):return produce(output,inputs,config,True)
