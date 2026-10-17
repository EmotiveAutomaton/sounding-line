"""CPU content representations with preserved source order and visible token scope.

DESIGN CHECK: LESSONS 3-5. NULL: labels and future actions cannot enter extraction;
missing candidates, source drift and nonfinite vectors refuse completion.
ALTERNATIVE: repeated text is identical, order is preserved, unit vectors and
exact coverage supply features only. No prediction, fitted model or scientific gate.
"""
import os
for _n in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_n]='1'
import argparse,threading,time,traceback
from pathlib import Path
import numpy as np
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,now,limits
from runners.stage13.detectors import cached_model,model_pins
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot,require_resources
from .foundation import PREPARED

ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-content-features-v2'
MODEL='sentence-transformers/all-MiniLM-L6-v2'

def scalar_features(document,menu):
    prior=set(document.lower().split())
    return [[len(s),len(s.split()),len(set(s.lower().split())-prior)/max(1,len(set(s.lower().split()))),i]
            for i,s in enumerate(menu)]

def token_view(tok,text,role):
    if role not in ('context','suggestion'):raise ValueError('unknown view')
    encoded=tok(text,add_special_tokens=False,return_offsets_mapping=True,truncation=False)
    ids=encoded['input_ids'];offsets=encoded['offset_mapping'];start=max(0,len(ids)-254) if role=='context' else 0
    used=ids[start:start+254];vis=offsets[start:start+254]
    if tok.cls_token_id is None or tok.sep_token_id is None:raise ValueError('BERT boundary tokens absent')
    return [tok.cls_token_id]+used+[tok.sep_token_id],dict(full_tokens=len(ids),used_tokens=len(used),
        first_native_token=start,codepoint_start=vis[0][0] if vis else 0,codepoint_end=vis[-1][1] if vis else 0,
        truncated=len(ids)>254,role=role,text_sha256=digest(text))

def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('already prepared')
    limits();require_resources(resource_snapshot());path=cached_model(MODEL)
    freeze(ROOT/'MODEL.json',dict(repo=MODEL,path=str(path),revision=path.name,files=model_pins(path)))
    src=[REPO/p for p in ('runners/drive/content_features_v2.py','runners/drive/foundation.py','runners/stage14/common.py',
        'runners/stage13/detectors.py','runners/next_round/queue.py','runners/stage9/process_identity.py',
        'tests/test_drive_content_features_v2.py','docs/design/stage-15/drive/CONTENT_FEATURES.md')]+[ROOT/'MODEL.json',PREPARED/'SESSIONS.json']
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(src),model=MODEL,device='cpu',dtype='float32',threads=1,
        max_wall_seconds=14400,max_unique=150000,max_output_bytes=2*1024**3,labels_accessed=False,scientific_admission=False))

def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    started=time.time();stop=threading.Event();lease=REPO/'results/.cpu.lock';owned=False
    token=f'{os.getpid()} drive-content-features-v2'.encode()
    def guard(task,progress):
        require_resources(resource_snapshot())
        if time.time()-started>plan['max_wall_seconds']:raise TimeoutError('content feature wall ceiling')
        atomic(ROOT/'PROGRESS.json',dict(at=now(),task=task,progress=progress))
    def deadline():
        if stop.wait(plan['max_wall_seconds']+90):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='hard content feature ceiling'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>90:raise TimeoutError('native monitor handshake')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor binding')
        fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd);owned=True
        import torch
        from transformers import AutoTokenizer,AutoModel
        torch.set_num_threads(1);identity=read(ROOT/'MODEL.json');path=Path(identity['path'])
        if model_pins(path)!=identity['files']:raise ValueError('model changed')
        tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False,use_fast=True)
        model=AutoModel.from_pretrained(path,local_files_only=True,trust_remote_code=False).to('cpu').eval()
        if any(p.device.type!='cpu' for p in model.parameters()):raise ValueError('unexpected GPU placement')
        cache={};vectors=[];visibility=[]
        def forward(ids):
            batch={'input_ids':torch.tensor([ids]),'attention_mask':torch.ones((1,len(ids)),dtype=torch.int64)}
            with torch.inference_mode():v=model(**batch).last_hidden_state.mean(1)[0].numpy().astype(np.float32)
            v=v/max(float(np.linalg.norm(v)),1e-12)
            if v.shape!=(384,) or not np.isfinite(v).all() or not np.isclose(np.linalg.norm(v),1,atol=1e-5):raise ValueError('invalid embedding')
            return v
        fixture=token_view(tok,'A fixed repeated sentence.', 'suggestion')[0]
        if fixture!=tok.encode('A fixed repeated sentence.',add_special_tokens=True):raise ValueError('native boundary mismatch')
        if not np.array_equal(forward(fixture),forward(fixture)):raise ValueError('encoder repeat differs')
        def encode(text,role):
            key=digest([text,role])
            if key not in cache:
                if len(vectors)>=plan['max_unique']:raise ValueError('unique representation cap')
                ids,scope=token_view(tok,text,role);v=forward(ids);cache[key]=len(vectors);vectors.append(v);visibility.append(dict(key=key,**scope))
            return cache[key]
        records=[];ss=read(PREPARED/'SESSIONS.json');total=sum(len(s['rows']) for s in ss);n=0
        for session in ss:
            for row in session['rows']:
                if n%16==0:guard('encode',dict(done=n,total=total,unique=len(vectors)))
                doc=encode(row['document'],'context');options=[encode(s,'suggestion') for s in row['menu']]
                records.append(dict(key=row['key'],session=session['session'],writer=session['writer'],context=doc,options=options,
                    cosine=[float(vectors[doc]@vectors[i]) for i in options],scalars=scalar_features(row['document'],row['menu'])))
                n+=1
        if n!=16855 or len({r['key'] for r in records})!=n:raise ValueError('cohort coverage differs')
        np.save(ROOT/'VECTORS.npy',np.asarray(vectors,np.float32),allow_pickle=False)
        freeze(ROOT/'RECORDS.json',records);freeze(ROOT/'VISIBILITY.json',visibility)
        if sum(p.stat().st_size for p in ROOT.iterdir() if p.is_file())>plan['max_output_bytes']:raise ValueError('output cap')
        check_pins(plan['pins'])
        freeze(ROOT/'SUMMARY.json',dict(decisions=n,candidates=sum(len(r['options']) for r in records),unique_vectors=len(vectors),
            truncated_vectors=sum(v['truncated'] for v in visibility),device='cpu',threads=1,dimensions=384,model_calls='local encoder only',
            labels_accessed=False,fit=False,scientific_admission=False))
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={p.name:filehash(p) for p in ROOT.iterdir()
            if p.suffix in ('.json','.npy') and p.name not in ('PROGRESS.json','MONITOR_READY.json')},write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc),traceback=traceback.format_exc()));raise
    finally:
        stop.set()
        if owned and lease.exists() and lease.read_bytes()==token:lease.unlink()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);a=ap.parse_args();prepare() if a.action=='prepare' else run()
