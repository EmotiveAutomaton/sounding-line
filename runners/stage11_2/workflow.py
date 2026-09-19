"""Prepared finite repaired-interface queue, including consumers and continuations.

DESIGN CHECK: LESSONS 3-5. NULL/ALTERNATIVE: failed admission, insufficient
capacity, altered sources or absent final output cannot become completion.
Whole CLI rehearses on a marked scratch root. No autonomous research selection.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import numpy as np
from .common import RAW,REPO,DEADLINE,MAX_GPU_SECONDS,atomic,charge_total,check_pins,digest,freeze,now,read,source_pins


def prepare(root=RAW):
    root=Path(root);jobs=[]
    for split in ['dev','test']:
        n=len(read(root/'fixture'/f'{split}-public.json'))
        for branch in ['M0','M3','M4']:
            jobs.append(dict(id=f'{branch}-{split}',kind='core',branch=branch,split=split,
                calls=n*{'M0':24,'M3':12,'M4':7}[branch],produces=f'repair-v1/{branch}-ollama-{split}/AUDIT.json'))
    # Extension order follows the commissioned explanatory uncertainties:
    # combinations/longer stale history, withheld family, context, state, repeats.
    for kind in ['history','summary','states','repeat']:
        for split in ['dev','test']:
            n=len(read(root/'fixture'/f'{split}-public.json'))
            jobs.append(dict(id=f'{kind}-{split}',kind=kind,split=split,
                calls=n*{'history':5,'summary':4,'states':12,'repeat':2}[kind],
                produces=f'repair-v1/extension-{kind}-{split}/COMPLETE.json'))
    return freeze(root/'QUEUE-repair-v1.json',dict(schema='stage11.2-repaired-complete-flow-v1',
        jobs=jobs,source_pins=source_pins(),deadline=DEADLINE,maximum_gpu_seconds=MAX_GPU_SECONDS,
        gate='repair-v1/ollama-admission/COMPLETE.json',forecast='actual repaired generation p50/p90; no backpropagation substitution',
        extension_scope='fresh goal/belief combination after delay; held-out dual-tool/rendering test; evidence/context and 36-event history; no seed padding'))


def verify_admission(root):
    from .repair import call
    from .world import prompt
    out=Path(root)/'repair-v1/ollama-admission';receipt=read(out/'COMPLETE.json');rows=read(out/'ROWS.json')
    if digest(rows)!=receipt['rows_sha256']:raise ValueError('admission rows changed')
    public=read(Path(root)/'fixture/dev-public.json');truth=read(Path(root)/'fixture/dev-evaluator.json');expected=[]
    for i,u in enumerate(public):
        q=(i//4)%4;t=truth[i]['queries'][q]
        for question in ['action','belief','goal']:
            path=out/'calls'/f'{i:03d}-{question}'
            if not (path/'COMPLETE.json').exists():raise ValueError('incomplete admission audit')
            text=prompt(u,q,'no_history',explicit=(t['preference'],t['skill']),question=question)
            result=call(text,4 if question=='action' else 2,path,Path(root)/'repair-v1')
            target=max(range(4),key=t['probabilities'].__getitem__) if question=='action' else t[question]
            expected.append(dict(unit=u['unit'],question=question,target=target,**result))
    if expected!=rows:raise ValueError('admission semantic roster differs')
    acc=lambda rs:sum(r['valid'] and max(range(len(r['probabilities'])),key=r['probabilities'].__getitem__)==r['target'] for r in rs)/len(rs)
    action=acc([r for r in rows if r['question']=='action']);state=acc([r for r in rows if r['question']!='action'])
    if (action,state,action>=.70 and state>=.80)!=(receipt['action_accuracy'],receipt['state_accuracy'],receipt['admitted']):raise ValueError('gate recomputation differs')
    return receipt


def fake_transport(root):
    import json
    from . import local_reader,repair
    from .world import prompt
    from soundingline import gpulock
    root=Path(root).resolve()
    if root==RAW.resolve() or not (root/'FAKE_ONLY.json').exists():raise ValueError('fake requires isolated marked root')
    gpulock.acquire_gpu_lock=lambda *args:None;gpulock.release_gpu_lock=lambda:None
    known={};public=read(root/'fixture/dev-public.json');truth=read(root/'fixture/dev-evaluator.json')
    for i,u in enumerate(public):
        q=(i//4)%4;t=truth[i]['queries'][q]
        for question in ['action','belief','goal']:
            n=4 if question=='action' else 2
            req=repair.request(prompt(u,q,'no_history',explicit=(t['preference'],t['skill']),question=question),n)
            known[digest(req)]=max(range(4),key=t['probabilities'].__getitem__) if question=='action' else t[question]
    def api(path,payload=None,timeout=None):
        if path=='/api/tags':return dict(models=[dict(name=local_reader.MODEL,digest=local_reader.MODEL_DIGEST)])
        if path=='/api/version':return dict(version='FAKE_ONLY')
        schema=payload['format']['properties']
        if 'summary' in schema:
            content=payload['messages'][0]['content'];facts=json.JSONDecoder().raw_decode(content.split('Facts: ',1)[1])[0]
            body=dict(summary='FAKE equipment summary',claims=facts)
        else:
            n=schema['probabilities']['maxItems'];p=[0.]*n;p[known.get(digest(payload),0)]=1.
            body=dict(analysis='FAKE ONLY',probabilities=p)
        return dict(done=True,done_reason='stop',message=dict(content=json.dumps(body)),fake=True,prompt_eval_count=20,eval_count=10)
    local_reader.api=api


def worker(job,root,fake=False):
    if fake:fake_transport(root)
    if job['kind']=='core':
        from .views import install
        install()
        from .repair import run
        from .consumer import run as audit
        run(job['branch'],job['split'],root)
        return audit(job['branch'],job['split'],root)
    from .extensions import run
    return run(job['kind'],job['split'],root)


def forecast(root,plan):
    paths=[Path(root)/'repair-v1/ollama-admission/ROWS.json']
    paths+=list((Path(root)/'repair-v1').glob('*/PREDICTIONS.json'))
    samples=[r['seconds'] for p in paths if p.exists() for r in read(p) if r.get('seconds',0)>0]
    p50,p90=[float(x) for x in np.quantile(samples,[.5,.9])]
    calls=sum(j['calls'] for j in plan['jobs'] if not (Path(root)/j['produces']).exists())
    return dict(p50=p50,p90=p90,pending_calls=calls,p50_seconds=p50*calls,p90_seconds=p90*calls,
        twice_as_fast_seconds=p50*calls/2,charged_gpu_seconds=charge_total(root),
        caveat='measured mixture; future prompt lengths and output lengths may change')


def run(root=RAW,fake=False):
    from runners.stage9.process_identity import native_identity
    root=Path(root).resolve();plan=read(root/'QUEUE-repair-v1.json');out=root/'queue/QUEUE-repair-v1'
    if fake and (root==RAW.resolve() or not (root/'FAKE_ONLY.json').exists()):raise ValueError('isolated fake root required')
    check_pins(plan['source_pins']);native=native_identity();freeze(out/f'NATIVE-{os.getpid()}.json',native)
    dispositions=[]
    try:
        gate=verify_admission(root)
        for job in plan['jobs']:
            check_pins(plan['source_pins']);terminal=root/job['produces']
            if not gate['admitted']:
                disposition=dict(id=job['id'],status='blocked',reason='single repaired interface failed capability')
            else:
                rates=forecast(root,plan);atomic(out/'FORECAST.json',rates)
                remaining=min(MAX_GPU_SECONDS-charge_total(root),(datetime.fromisoformat(DEADLINE)-datetime.now(timezone.utc)).total_seconds())
                required=0 if terminal.exists() else max(330,job['calls']*rates['p90'])
                if not fake and required>remaining:
                    disposition=dict(id=job['id'],status='not run',reason='whole block p90 exceeds remaining deadline or service budget',required=required,remaining=remaining)
                else:
                    atomic(out/'STATUS.json',dict(at=now(),job=job['id'],native=native,dispositions=dispositions))
                    command=[sys.executable,'-B','-m','runners.stage11_2.workflow','--root',str(root),'--worker',job['id']]+(['--fake'] if fake else [])
                    with (out/(job['id']+'.stdout.log')).open('ab') as stdout,(out/(job['id']+'.stderr.log')).open('ab') as stderr:
                        child=subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                        atomic(out/'CHILD.json',dict(pid=child.pid,native=native_identity(child.pid),command=command,started=now()))
                        child.wait(timeout=21600)
                    if child.returncode or not terminal.exists():raise RuntimeError('worker failed or missing produce: '+job['id'])
                    receipt=read(terminal)
                    if receipt.get('status')!='complete':raise ValueError('noncomplete terminal')
                    disposition=dict(id=job['id'],status='complete',produce_sha256=digest(receipt))
            freeze(out/(job['id']+'-DISPOSITION.json'),disposition);dispositions.append(disposition)
        return freeze(out/'COMPLETE.json',dict(status='complete',dispositions=dispositions,manifest_sha256=digest(plan),fake=fake,
            scope='finite execution completed; internal landings and Sunday curator packet remain separate'))
    except BaseException as exc:
        freeze(out/f'FAILED-{os.getpid()}.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),dispositions=dispositions));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--prepare',action='store_true');p.add_argument('--worker');p.add_argument('--fake',action='store_true')
    a=p.parse_args()
    if a.prepare:print(len(prepare(a.root)['jobs']))
    elif a.worker:
        job=next(j for j in read(a.root/'QUEUE-repair-v1.json')['jobs'] if j['id']==a.worker);print(worker(job,a.root,a.fake)['status'])
    else:print(run(a.root,a.fake)['status'])
