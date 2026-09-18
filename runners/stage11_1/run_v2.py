"""Finite local blocks, write-ahead charges and immutable sequential intermediates.

DESIGN CHECK: LESSONS 2-5. NULL: missing response, changed source/request, existing
owner, deadline or exhausted budget cannot authorize an uncharged retry. ALTERNATIVE:
complete attempts reparse without network; only remaining new blocks dispatch.
Dispositions: COMPLETE, INVALID, STOPPED, DEADLINE, CALL_CAP, GPU_CAP, FAILED.
Transport uncertainty stops dispatch and retains the whole block reservation.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone,timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import time
import traceback
import psutil
from runners.stage10.ollama import api,identity,now,write_new
from soundingline.gpulock import GPU_LOCK,release_gpu_lock
from .common import PRIVATE,read,freeze,digest,canonical
from .models_v2 import request_for,parse,retained,MODEL,MODEL_DIGEST,SLOTS,FIELDS,ACTIONS

TIMEOUT=300


def source_pin():
    paths=[f'runners/stage11_1/{n}' for n in ('common.py','targets.py','models.py','models_v2.py','prepare.py','run.py','run_v2.py','TARGET_CONTRACT.md')]
    paths+=['runners/stage11/replay.py','runners/stage11/core.py','runners/stage9/coauthor.py','runners/stage10/ollama.py',
            'runners/stage10/contracts.py','soundingline/gpulock.py']
    return {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}


def fake_response(kind):
    if kind=='account':value=dict(events=[])
    else:value=dict(facts=[dict(slot=s,**{k:[1/len(v)]*len(v) for k,v in FIELDS.items()},span_ids=[],span_state='unknown') for s in SLOTS],
        handling=[.25]*4,attributes=dict(reviewed='unknown',endorsed='unknown',understood='unknown'))
    return dict(done=True,done_reason='stop',message=dict(content=canonical(value)),fake=True)


def call(directory,evidence,kind,branch,intermediate=None,*,threads=4,fake=False):
    request=request_for(evidence,kind,intermediate,threads)
    binding=digest(dict(request=request,model_digest=MODEL_DIGEST,branch=branch,fake=fake))
    if (directory/'ATTEMPT.json').exists():
        original=read(directory/'REQUEST.json');saved=read(directory/'ATTEMPT.json')
        if original['binding']!=binding or original['request']!=request:raise ValueError('changed original request')
        raw=read(directory/'RAW.json')
        if digest(raw)!=saved['raw_digest']:raise ValueError('changed raw response')
        f,error=parsed(raw,evidence,kind)
        if f!=saved['forecast'] or error!=saved['error']:raise ValueError('semantic replay differs')
        return saved
    if directory.exists():raise ValueError('incomplete attempt; explicit reconciliation required, no retry')
    directory.mkdir(parents=True)
    write_new(directory/'REQUEST.json',dict(at=now(),binding=binding,request=request,model_digest=MODEL_DIGEST,branch=branch,fake=fake))
    start=time.perf_counter()
    try:raw=fake_response(kind) if fake else api('/api/chat',request,timeout=TIMEOUT)
    except Exception as exc:
        write_new(directory/'TRANSPORT_FAILED.json',dict(at=now(),error=repr(exc),execution='uncertain; full block reserved'))
        raise RuntimeError('uncertain model transport; no automatic retry') from exc
    write_new(directory/'RAW.json',raw)
    f,error=parsed(raw,evidence,kind)
    result=dict(status='COMPLETE' if f is not None else 'INVALID',forecast=f,error=error,raw_digest=digest(raw),
        cost=dict(wall_seconds=time.perf_counter()-start,input_tokens=raw.get('prompt_eval_count',0),
                  output_tokens=raw.get('eval_count',0),server_seconds=(raw.get('total_duration') or 0)/1e9),fake=fake)
    write_new(directory/'ATTEMPT.json',result);return result


def parsed(raw,evidence,kind):
    try:return parse(raw,evidence,kind),None
    except (ValueError,KeyError,TypeError) as exc:return None,str(exc)


def budget(root):
    requests=[read(p) for p in (root/'calls').rglob('REQUEST.json')]
    blocks=list((root/'blocks').glob('*/START.json'))
    seconds=sum(read(p.with_name('END.json'))['charged_seconds'] if p.with_name('END.json').exists() else read(p)['reservation_seconds'] for p in blocks)
    return dict(attempts=len(requests),branches=dict(Counter(r['branch'] for r in requests)),charged_seconds=seconds)


def gate_budget(root,branch,calls,reservation,at=None):
    c=read(root/'CONTRACT.json');b=budget(root)
    at=at or datetime.now(timezone.utc)
    if (root/'STOP').exists() or (root/'PAUSE').exists():return 'STOPPED'
    # Stop admitting blocks in time for the absolute reporting checkpoint.
    if at+timedelta(seconds=reservation)>=datetime.fromisoformat(c['reporting_starts']):return 'DEADLINE'
    if b['attempts']+calls>c['maximum_attempts'] or b['branches'].get(branch,0)+calls>c['branch_attempts'][branch]:return 'CALL_CAP'
    if b['charged_seconds']+reservation>c['maximum_gpu_seconds']:return 'GPU_CAP'
    return 'ADMITTED'


def acquire():
    # Use the established file format without the legacy indefinite wait/stale reclaim.
    GPU_LOCK.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(GPU_LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    with os.fdopen(fd,'w') as f:f.write(f'{os.getpid()} stage11.1')


def chain(method):
    return {'direct':['direct'],'review':['direct','review'],'account':['account','account_predict']}[method]


def execute_block(root,job,row,view,method,*,fake=False):
    directory=root/'calls'/job['id']/row['key']/view/method
    steps=chain(method);intermediate=None;results=[]
    existing=[(directory/str(i)/'ATTEMPT.json').exists() for i in range(len(steps))]
    if all(existing):
        for i,kind in enumerate(steps):
            result=call(directory/str(i),row['views'][view],kind,job['branch'],intermediate,threads=job['threads'],fake=fake)
            results.append(result);intermediate=retained(result['forecast'])
        return 'COMPLETE',results
    if directory.exists():raise ValueError('partial block retained; explicit recovery required')
    reservation=TIMEOUT*len(steps)+30
    status=gate_budget(root,job['branch'],len(steps),reservation)
    if status!='ADMITTED':return status,[]
    block=root/'blocks'/digest([job['id'],row['key'],view,method])[:24]
    if block.exists():raise ValueError('original block needs reconciliation')
    if not fake:acquire()
    start=time.perf_counter();uncertain=False
    try:
        write_new(block/'START.json',dict(at=now(),reservation_seconds=reservation,pid=os.getpid(),branch=job['branch'],job=job['id'],fake=fake))
        for i,kind in enumerate(steps):
            result=call(directory/str(i),row['views'][view],kind,job['branch'],intermediate,threads=job['threads'],fake=fake)
            results.append(result);intermediate=retained(result['forecast'])
    except BaseException:
        uncertain=True;raise
    finally:
        if not fake:
            try:api('/api/generate',dict(model=MODEL,keep_alive=0),timeout=30)
            except Exception:uncertain=True
        write_new(block/'END.json',dict(at=now(),charged_seconds=reservation if uncertain else time.perf_counter()-start,
            uncertainty=uncertain,fake=fake))
        if not fake:release_gpu_lock()
    if uncertain:raise RuntimeError('uncertain model unload; stopped')
    return 'COMPLETE',results


def runtime32(root):
    if (root/'RUNTIME32.json').exists():return
    paths=sorted((root/'calls').rglob('ATTEMPT.json'),key=lambda p:read(p.with_name('REQUEST.json'))['at'])
    if len(paths)<32:return
    rows=[read(p) for p in paths[:32]];wall=[r['cost']['wall_seconds'] for r in rows]
    upper=max(wall)*1.25;b=budget(root)
    result=dict(status='COMPLETE',attempts=32,wall_mean_seconds=sum(wall)/32,wall_upper_seconds=upper,
        upper_basis='1.25 times the maximum of the first 32 attempts, including pilot/invalid attempts',
        invalid=sum(r['status']=='INVALID' for r in rows),charged_so_far=b,
        remaining_call_capacity_at_upper=min(6400-b['attempts'],int((86400-b['charged_seconds'])/(upper+5))),
        next_action='Allocate following branch tranches using this observed upper runtime; preserve hard per-block reservations')
    freeze(root/'RUNTIME32.json',result)


def execute(root,plan_path,fake=False):
    plan=read(plan_path);sources=source_pin()
    freeze(root/'sources'/f"{plan['id']}.json",sources)
    if not fake:
        if read(root/'GATES-v2.json')['sources']!=sources:raise ValueError('gates do not bind current producer')
        freeze(root/'MODEL.json',identity())
    cohort=read(root/plan.get('cohort_file','COHORT.json'))
    if digest(cohort)!=plan['cohort_digest']:raise ValueError('plan cohort changed')
    rows={r['key']:r for lane in cohort.values() for r in lane}
    for job in plan['jobs']:
        terminal=root/'jobs'/job['id']/'COMPLETE.json'
        if terminal.exists() and read(terminal)['status']!='COMPLETE':raise ValueError('noncomplete original job needs explicit continuation')
        if job.get('requires_pilot') and not (root/'PILOT_PASSED-v2.json').exists():raise ValueError('literal pilot not passed')
        freeze(root/'jobs'/job['id']/'JOB.json',job)
        status='COMPLETE';observed=[]
        for key in job['keys']:
            for view in job['views']:
                for method in job['methods']:
                    if source_pin()!=sources:raise ValueError('loaded producer sources changed')
                    status,result=execute_block(root,job,rows[key],view,method,fake=fake)
                    observed+=result
                    if status!='COMPLETE':break
                    runtime32(root)
                    print(canonical(dict(job=job['id'],finished_blocks=1,charges=budget(root))),flush=True)
                if status!='COMPLETE':break
            if status!='COMPLETE':break
        result=dict(status=status,job=job['id'],branch=job['branch'],partition=job['partition'],sources=sources,
            calls=len(observed),invalid=sum(r['status']=='INVALID' for r in observed),
            pursuit=job['pursuit'],warrant=job['warrant'],next_action=job['next_action'],fake=fake)
        freeze(terminal,result)
        if job.get('pilot'):
            # This gates grammar realization, not accuracy on the discarded examples.
            if status!='COMPLETE' or any(r['status']!='COMPLETE' for r in observed):raise ValueError('literal pilot grammar failure retained')
            freeze(root/'PILOT_PASSED-v2.json',dict(status='COMPLETE',job=job['id'],sources=sources,fake=fake))
        if status!='COMPLETE':break
    result=dict(status=status,plan=plan['id'],sources=sources,charges=budget(root),next_action=plan['next_action'],fake=fake)
    freeze(root/'plans'/f"{plan['id']}-COMPLETE.json",result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);p.add_argument('--root',type=Path,default=PRIVATE);p.add_argument('--fake',action='store_true');a=p.parse_args()
    import msvcrt
    a.root.mkdir(parents=True,exist_ok=True)
    with (a.root/'producer.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        proc=psutil.Process();owner=dict(pid=proc.pid,create_time=proc.create_time(),executable=proc.exe(),command=proc.cmdline(),at=now())
        write_new(a.root/f'OWNER-{proc.pid}.json',owner)
        try:result=execute(a.root,a.plan,a.fake)
        except BaseException:
            write_new(a.root/f'FAILED-{proc.pid}.json',dict(status='FAILED',at=now(),error=traceback.format_exc()));raise
        print(canonical(result))


if __name__=='__main__':main()
