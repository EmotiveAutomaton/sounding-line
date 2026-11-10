"""Manifest-bound CPU encoder batches and complete S3 collection."""
from pathlib import Path
import math,time
import numpy as np
from .week5_bk_s3_source import match
from .week5_go_readers import embeddings
from .timing_pmap_source import completed
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read,filehash

CONTEXTS=dict(primary='rest_before',next_paragraph='next_paragraph',prompt='prompt',final_document='rest_final')

def selected(rows):
    keys={(r['session'],r['ordinal']) for pair in match(rows) for r in pair}
    return sorted([r for r in rows if (r['session'],r['ordinal']) in keys],key=lambda r:(r['session'],r['ordinal']))

def score(rows,vector_by_text):
    output=[]
    for row in rows:
        values={}
        for cell,field in CONTEXTS.items():
            deltas=[]
            for t in row['targets']:
                if not t[field]:break
                before=np.asarray(vector_by_text[t['before']],float);after=np.asarray(vector_by_text[t['after']],float);context=np.asarray(vector_by_text[t[field]],float)
                if any(not np.isfinite(v).all() or abs(np.linalg.norm(v)-1)>1e-5 for v in (before,after,context)):raise ValueError('Invalid normalized encoder vector')
                deltas.append(float((after-before)@context))
            values[cell]=float(np.mean(deltas)) if len(deltas)==len(row['targets']) else None
        output.append({**{k:v for k,v in row.items() if k!='targets'},'position':float(np.mean([t['position'] for t in row['targets']])),'scores':values})
    return output

def source_rows(completion):
    completion=Path(completion);path=completion.parent/'output/PRIVATE_EVENTS.json.gz';completed(completion,path)
    return selected(gzread(path)),filehash(path)

def batches(completion,size=32):
    if not 1<=size<=64:raise ValueError('At most64events in one batch')
    rows,_=source_rows(completion)
    return [dict(card='BK-S3-encoder',phase='score',start=i,stop=min(i+size,len(rows))) for i in range(0,len(rows),size)]

def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config.get('phase')=='score':
        start,stop=config['start'],config['stop']
        if config!=dict(card='BK-S3-encoder',phase='score',start=start,stop=stop) or type(start)is not int or type(stop)is not int or not 0<=start<stop<=start+64:raise ValueError('Invalid bounded encoder batch')
        rows,digest=source_rows(inputs['source_completion'])
        if stop>len(rows):raise ValueError('Encoder slice exceeds full source')
        batch=rows[start:stop];texts=list(dict.fromkeys(v for r in batch for t in r['targets'] for k,v in t.items() if k in ('before','after',*CONTEXTS.values()) and v))
        count=0;started=time.monotonic();cpu=time.process_time()
        def check(text,vector):
            nonlocal count
            count+=1;progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'encode',done=count,total=len(texts)))
            if not verification and count==max(1,math.ceil(len(texts)*.05)):write_equal(output/'PILOT.json',dict(done=count,total=len(texts),cpu_seconds=time.process_time()-cpu))
            if (output/'YIELD_REQUEST.json').exists() or time.monotonic()-started>700:raise InterruptedError('S3 bounded encoder unit must yield')
        try:vectors=embeddings(texts,inputs['encoder_manifest'],on_vector=check)
        except InterruptedError:return dict(status='yielded',reason='S3 encoder boundary; new attempt restarts a smaller bounded slice')
        result=score(batch,dict(zip(texts,vectors)))
        summary=dict(start=start,stop=stop,total=len(rows),source_sha256=digest,encoder_manifest_sha256=filehash(inputs['encoder_manifest']),texts=len(texts))
        if verification:
            old=gzread(output/'PRIVATE_SCORED.json.gz')
            if summary!=read(output/'SUMMARY.json') or len(old)!=len(result):raise ValueError('S3 encoder coverage differs')
            for a,b in zip(old,result):
                if {k:v for k,v in a.items() if k!='scores'}!={k:v for k,v in b.items() if k!='scores'}:raise ValueError('S3 event identity differs')
                for k,v in a['scores'].items():
                    other=b['scores'][k]
                    if (v is None)!=(other is None) or v is not None and abs(v-other)>1e-7:raise ValueError('S3 fresh forward differs')
            return dict(verified=True,all_encoder_forwards_recomputed=True)
        gzip_equal(output/'PRIVATE_SCORED.json.gz',result);write_equal(output/'SUMMARY.json',summary)
        return dict(status='complete')
    if config!=dict(card='BK-S3-encoder',phase='collect'):raise ValueError('Unknown S3 encoder phase')
    expected,digest=source_rows(inputs['source_completion']);parts=[];encoder=None
    for value in inputs['scored_completions']:
        completion=Path(value);folder=completion.parent/'output'
        for name in ('SUMMARY.json','PRIVATE_SCORED.json.gz'):completed(completion,folder/name)
        summary=read(folder/'SUMMARY.json')
        if summary['source_sha256']!=digest or summary['total']!=len(expected):raise ValueError('S3 chunk source differs')
        if encoder is not None and encoder!=summary['encoder_manifest_sha256']:raise ValueError('S3 encoder changed across chunks')
        encoder=summary['encoder_manifest_sha256'];parts.append((summary,gzread(folder/'PRIVATE_SCORED.json.gz')))
    rows=[];next_start=0
    for summary,part in sorted(parts,key=lambda p:p[0]['start']):
        if summary['start']!=next_start or len(part)!=summary['stop']-summary['start']:raise ValueError('Incomplete or overlapping S3 chunks')
        rows+=part;next_start=summary['stop']
    if next_start!=len(expected) or [(r['session'],r['ordinal']) for r in rows]!=[(r['session'],r['ordinal']) for r in expected]:raise ValueError('S3 collection incomplete')
    summary=dict(events=len(rows),complete_collection=True,source_sha256=digest,encoder_manifest_sha256=encoder)
    if verification:
        if rows!=gzread(output/'PRIVATE_SCORED.json.gz') or summary!=read(output/'SUMMARY.json'):raise ValueError('S3 full collection replay differs')
        return dict(verified=True,all_chunks_authenticated=True)
    gzip_equal(output/'PRIVATE_SCORED.json.gz',rows);write_equal(output/'SUMMARY.json',summary);return dict(status='complete')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
