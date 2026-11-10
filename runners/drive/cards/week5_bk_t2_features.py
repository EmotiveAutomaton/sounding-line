"""T2 final-only features with bounded real CPU encoder forwards."""
from pathlib import Path
import hashlib,re,time
import numpy as np
from .week5_go_readers import embeddings
from .timing_pmap_source import completed
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read,filehash
from .timing_text import TOKEN,WORD

PUNCTUATION=('.',',',';',':','!','?','-','(',')','"',"'",'\n')


def lexical(text,position,dictionary):
    words=[m.group().casefold() for m in TOKEN.finditer(text) if WORD.fullmatch(m.group())]
    skeleton=[word if word in dictionary else '<CONTENT>' for word in words]
    vector=np.zeros(256)
    for n in (1,2,3):
        for i in range(len(skeleton)-n+1):
            key=str(n)+'\0'+'\0'.join(skeleton[i:i+n]);index=int.from_bytes(hashlib.sha256(key.encode()).digest()[:4],'big')%256
            vector[index]+=1/max(1,len(words)-n+1)
    baseline=[float(len(text)),float(len(words)),float(position)]
    return baseline,baseline+[float(text.count(p)) for p in PUNCTUATION]+vector.tolist()


def source(completion):
    c=Path(completion);p=c.parent/'output/PRIVATE_SENTENCES.json.gz';completed(c,p)
    rows=gzread(p)
    if len({(r['session'],r['index']) for r in rows})!=len(rows):raise ValueError('Duplicate final sentence')
    return rows,filehash(p)


def dictionary(completion):
    c=Path(completion);p=c.parent/'output/FROZEN_DICTIONARY.json';completed(c,p);data=read(p);words=data['words']
    if len(words)!=150 or len(set(words))!=150:raise ValueError('Frozen150word skeleton required')
    return set(words),filehash(p)


def batches(completion,size=32):
    if type(size)is not int or not 1<=size<=64:raise ValueError('At most64sentences per batch')
    rows,_=source(completion)
    return [dict(card='BK-T2-features',phase='score',start=i,stop=min(len(rows),i+size)) for i in range(0,len(rows),size)]


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rows,sourcehash=source(inputs['source_completion'])
    if config.get('phase')=='score':
        a,b=config['start'],config['stop']
        if config!=dict(card='BK-T2-features',phase='score',start=a,stop=b) or type(a)is not int or type(b)is not int or not 0<=a<b<=min(len(rows),a+64):raise ValueError('Frozen bounded sentence batch required')
        words,wordhash=dictionary(inputs['dictionary_completion']);texts=list(dict.fromkeys(r['text'] for r in rows[a:b]));count=0;started=time.monotonic()
        def check(text,vector):
            nonlocal count
            count+=1;progress(output/'PROGRESS.json',dict(done=count,total=len(texts),phase='verify' if verification else 'encode'))
            if (output/'YIELD_REQUEST.json').exists() or time.monotonic()-started>700:raise InterruptedError('T2 bounded forward boundary')
        try:vec=dict(zip(texts,embeddings(texts,inputs['encoder_manifest'],on_vector=check)))
        except InterruptedError:return dict(status='yielded',reason='T2 owner/time request; restart smaller bounded encoder slice')
        result=[]
        for row in rows[a:b]:
            base,full=lexical(row['text'],row['position'],words);vector=np.asarray(vec[row['text']],float)
            if not np.isfinite(vector).all() or abs(np.linalg.norm(vector)-1)>1e-5:raise ValueError('Invalid encoder vector')
            result.append({**{k:v for k,v in row.items() if k!='text'},'baseline':base,'features':full+vector.tolist()})
        summary=dict(start=a,stop=b,total=len(rows),source_sha256=sourcehash,dictionary_sha256=wordhash,encoder_manifest_sha256=filehash(inputs['encoder_manifest']),dimensions=len(result[0]['features']))
        if verification:
            old=gzread(output/'PRIVATE_FEATURES.json.gz')
            if summary!=read(output/'SUMMARY.json') or len(old)!=len(result):raise ValueError('T2 feature coverage differs')
            for x,y in zip(old,result):
                if {k:v for k,v in x.items() if k!='features'}!={k:v for k,v in y.items() if k!='features'} or not np.allclose(x['features'],y['features'],atol=1e-7,rtol=0):raise ValueError('Fresh T2 features differ')
            return dict(verified=True,all_encoder_forwards_recomputed=True)
        gzip_equal(output/'PRIVATE_FEATURES.json.gz',result);write_equal(output/'SUMMARY.json',summary);return dict(status='complete')
    if config!=dict(card='BK-T2-features',phase='collect'):raise ValueError('Unknown T2 feature phase')
    parts=[];pins=None
    for value in inputs['feature_completions']:
        c=Path(value);out=c.parent/'output'
        for name in ('SUMMARY.json','PRIVATE_FEATURES.json.gz'):completed(c,out/name)
        summary=read(out/'SUMMARY.json');part=gzread(out/'PRIVATE_FEATURES.json.gz')
        if summary['source_sha256']!=sourcehash or summary['total']!=len(rows):raise ValueError('T2 feature source differs')
        current=(summary['dictionary_sha256'],summary['encoder_manifest_sha256'],summary['dimensions'])
        if pins is not None and pins!=current:raise ValueError('T2 feature pins differ')
        pins=current;parts.append((summary,part))
    result=[];position=0
    for summary,part in sorted(parts,key=lambda v:v[0]['start']):
        if summary['start']!=position or len(part)!=summary['stop']-summary['start']:raise ValueError('T2 feature slices missing/overlap')
        result+=part;position=summary['stop']
    if position!=len(rows) or [{k:v for k,v in r.items() if k not in ('features','baseline')} for r in result]!=[{k:v for k,v in r.items() if k!='text'} for r in rows]:raise ValueError('T2 collection changed rows/labels')
    summary=dict(sentences=len(rows),complete_collection=True,source_sha256=sourcehash,feature_pins=pins)
    # JSON has no tuples; normalize the final summary before equality checking.
    if pins is not None:summary['feature_pins']=list(pins)
    if verification:
        if result!=gzread(output/'PRIVATE_FEATURES.json.gz') or summary!=read(output/'SUMMARY.json'):raise ValueError('T2 collection replay differs')
        return dict(verified=True,complete_collection_replayed=True)
    gzip_equal(output/'PRIVATE_FEATURES.json.gz',result);write_equal(output/'SUMMARY.json',summary);return dict(status='complete')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
