"""Pinned public assets only; no generation, provider call or remote code.

DESIGN CHECK: LESSONS 2-5. NULL: missing rights, changed files or oversized
downloads refuse admission. ALTERNATIVE: immutable public bytes preserve exact
labels/offsets. Intake is infrastructure, not a successful detector experiment.
"""
from __future__ import annotations
import argparse
import urllib.request
from .common import RAW, freeze, read, filehash, atomic, limit_process, now

DATA_ID='OpAI-Bench1/OpAI-Bench'
DATA_REV='072c03c7051409346aaba05168d183cf6d863ee9'
E5_ID='MayZhou/e5-small-lora-ai-generated-detector'
E5_REV='483fc4969592dc20e00e5130e7187b5dd25dbcc7'
MAX_FILE=300*1024*1024
MAX_TOTAL=3*1024**3

def fetch(url,path,limit=MAX_FILE):
    receipt=path.with_name(path.name+'.download.json')
    if receipt.exists():
        r=read(receipt)
        if r['url']!=url or filehash(path)!=r['sha256']: raise ValueError('download changed')
        return r
    if path.exists(): raise RuntimeError('unreconciled download: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_name(path.name+'.partial')
    n=0
    with urllib.request.urlopen(url,timeout=90) as response, tmp.open('wb') as out:
        while True:
            b=response.read(1024*1024)
            if not b: break
            n+=len(b)
            if n>limit: raise ValueError('download bound exceeded')
            out.write(b)
    tmp.replace(path)
    r=dict(url=url,bytes=n,sha256=filehash(path),completed_at=now())
    freeze(receipt,r); return r

def run(raw=RAW):
    limit_process(); root=raw/'assets'; records=[]
    docs=[('dataset',DATA_ID,DATA_REV,'README.md'),('model',E5_ID,E5_REV,'README.md')]
    for kind,name,rev,file in docs:
        prefix='datasets/' if kind=='dataset' else ''
        records.append(fetch('https://huggingface.co/'+prefix+name+'/resolve/'+rev+'/'+file,root/kind/'README.md',1024**2))
    # The retrieved cards declare Apache-2.0 data and MIT model. Pin their full
    # bytes, retain upstream source restrictions, and never rehost passage text.
    for file in ('config.json','tokenizer_config.json','special_tokens_map.json','tokenizer.json','vocab.txt','model.safetensors'):
        records.append(fetch('https://huggingface.co/'+E5_ID+'/resolve/'+E5_REV+'/'+file,root/'e5'/file))
    for split in ('train','dev','test'):
        for domain in ('abstracts','essays','news','reports'):
            generators=('gemini-2.5-flash','gpt-5.4-nano','gpt-5.4') + (('qwen3-8b',) if split=='test' else ())
            for generator in generators:
                name=f'viewer/default/{split}/{domain}_{generator}.parquet'
                if sum(r['bytes'] for r in records)>MAX_TOTAL: raise ValueError('total intake bound exceeded')
                r=fetch('https://huggingface.co/datasets/'+DATA_ID+'/resolve/'+DATA_REV+'/'+name,root/'opai'/split/(domain+'_'+generator+'.parquet'), min(MAX_FILE,MAX_TOTAL-sum(r['bytes'] for r in records)))
                records.append(r)
                atomic(raw/'intake/PROGRESS.json',dict(at=now(),phase='public-assets',files=len(records),bytes=sum(r['bytes'] for r in records)))
    result=dict(status='complete',kind='infrastructure',data_revision=DATA_REV,model_revision=E5_REV,files=records,bytes=sum(r['bytes'] for r in records),no_remote_code=True)
    freeze(raw/'intake/COMPLETE.json',result)
    return result

if __name__=='__main__':
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=RAW);a=p.parse_args()
    try:
        r=run(a.raw); print('intake complete:',len(r['files']),'files')
    except Exception as e:
        atomic(a.raw/'intake/FAILED.json',dict(status='failed',at=now(),error=type(e).__name__+': '+str(e)))
        raise
