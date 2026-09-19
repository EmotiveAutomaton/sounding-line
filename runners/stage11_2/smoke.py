"""Explicit scratch-only fake transport through the real worker entry points.

DESIGN CHECK: LESSONS 3–5. All fake outputs are marked; science-root execution
refuses. Known fake admission permits the whole queue path, including reentry,
without GPU ownership, networking or scientific claims.
"""
import argparse
import json
from pathlib import Path
from .common import RAW,digest,freeze,read

def execute(manifest,job_id,root):
    root=Path(root).resolve()
    if root==RAW.resolve() or not (root/'FAKE_ONLY.json').exists():raise ValueError('scratch fixture required')
    from soundingline import gpulock
    gpulock.acquire_gpu_lock=lambda *args:None
    gpulock.release_gpu_lock=lambda:None
    from . import model_study as study
    from .local_reader import request,parse,MODEL_DIGEST
    from .world import prompt
    public=read(root/'fixture/dev-public.json');truth=read(root/'fixture/dev-evaluator.json');known={}
    for i,u in enumerate(public):
        q=(i//4)%4;t=truth[i]['queries'][q]
        for question in ('action','belief','goal'):
            text=prompt(u,q,'no_history',explicit=(t['preference'],t['skill']),question=question)
            known[text]=max(range(4),key=t['probabilities'].__getitem__) if question=='action' else t[question]
    def fake_call(text,n,path,root):
        path=Path(path);req=request(text,n)
        binding=digest(dict(request=req,model_digest=MODEL_DIGEST))
        if (path/'COMPLETE.json').exists():
            saved=read(path/'COMPLETE.json')
            assert saved['binding']==binding and read(path/'REQUEST.json')==req
            assert parse(read(path/'RAW.json'),n)==saved['probabilities']
            return saved
        label=known.get(text,0);prob=[0.0]*n;prob[label]=1.0
        raw=dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(probabilities=prob))),fake=True)
        freeze(path/'REQUEST.json',req);freeze(path/'RAW.json',raw)
        return freeze(path/'COMPLETE.json',dict(binding=binding,raw_sha256=digest(raw),probabilities=prob,valid=True,error=None,seconds=.01,cost={},semantics='FAKE TEST ONLY',fake=True))
    study.call=fake_call;study.identity=lambda:dict(fake=True)
    job=next(j for j in read(manifest)['jobs'] if j['id']==job_id)
    branch=job['args'][1]
    if branch=='admission':return study.admission(root)
    split=job['args'][job['args'].index('--split')+1]
    return study.run(branch,split,root)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--job',required=True)
    a=p.parse_args();print(execute(a.manifest,a.job,a.root)['status'])
