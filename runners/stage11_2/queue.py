"""Finite native dispatcher: absolute deadline, source pins and terminal guards.

DESIGN CHECK: LESSONS 3–5. NULL/ALTERNATIVE: missing gates block, absent produces
fail, changed sources refuse, original clock never resets. Complete cells are
replayed before reuse; worker failure stops dispatch for inspection, never retries
uncertain inference. No routine LLM wake or scope generation is implemented.
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
from .common import RAW,REPO,DEADLINE,MAX_GPU_SECONDS,atomic,charge_total,check_pins,digest,freeze,now,read,source_pins

def initial_plan(root=RAW):
    root=Path(root)
    jobs=[dict(id='ollama-admission',module='runners.stage11_2.model_study',args=['--branch','admission'],
               produces='ollama-admission/COMPLETE.json',maximum_seconds=7200,calls=192,needs=[])]
    for split in ('dev','test'):
        for branch in ('M0','M3','M4'):
            n=64 if split=='dev' else 128
            calls=n*({'M0':24,'M3':12,'M4':7}[branch])
            jobs.append(dict(id=f'{branch}-{split}',module='runners.stage11_2.model_study',
                args=['--branch',branch,'--split',split],produces=f'{branch}-ollama-{split}/COMPLETE.json',
                maximum_seconds=21600,calls=calls,needs=[dict(path='ollama-admission/COMPLETE.json',key='admitted',value=True)]))
    return freeze(root/'QUEUE-initial-v2.json',dict(schema='stage11.2-finite-queue-v2',jobs=jobs,
        source_pins=source_pins(),deadline=DEADLINE,maximum_gpu_seconds=MAX_GPU_SECONDS,
        forecast='generation pilot needed; no HF-forward rate substituted for Ollama generation',
        strategy='whole blocks; gate refusal blocks only dependent neural jobs; mechanism/executable continuations separate'))

def gate(job,root):
    for need in job.get('needs',[]):
        path=Path(root)/need['path']
        if not path.exists():return 'missing gate '+need['path']
        value=read(path)
        if value.get(need['key'])!=need['value']:return 'failed gate '+need['path']
    return None

def forecast(root,plan):
    samples=[]
    admission=Path(root)/'ollama-admission/ROWS.json'
    if admission.exists():samples=[r['seconds'] for r in read(admission)]
    if not samples:return dict(status='awaiting actual generation pilot',jobs=len(plan['jobs']))
    import numpy as np
    p50=float(np.median(samples));p90=float(np.quantile(samples,.9))
    remaining=[j for j in plan['jobs'] if not (Path(root)/j['produces']).exists() and not gate(j,root)]
    n=sum(j['calls'] for j in remaining)
    return dict(status='measured',generation_p50=p50,generation_p90=p90,
                pending_calls=n,p50_seconds=n*p50,p90_seconds=n*p90,
                twice_as_fast_seconds=n*p50/2,
                charged_gpu_seconds=charge_total(root),remaining_gpu_seconds=MAX_GPU_SECONDS-charge_total(root),
                backpropagation_forecast='separate neutral Jacobian receipt; not included in generation rates')

def run(manifest,root=RAW,fake=False):
    from runners.stage9.process_identity import native_identity
    root=Path(root).resolve();plan=read(manifest);out=root/'queue'/Path(manifest).stem
    if fake and root==RAW.resolve():raise ValueError('fake work forbidden in science root')
    check_pins(plan['source_pins'])
    if len({j['id'] for j in plan['jobs']})!=len(plan['jobs']) or len({j['produces'] for j in plan['jobs']})!=len(plan['jobs']):raise ValueError('duplicate job or produce')
    out.mkdir(parents=True,exist_ok=True)
    native=native_identity();freeze(out/f'NATIVE-{os.getpid()}.json',native)
    dispositions=[]
    try:
        for job in plan['jobs']:
            check_pins(plan['source_pins'])
            why=gate(job,root)
            if why:
                disposition=dict(id=job['id'],status='blocked',reason=why)
                freeze(out/f'{job["id"]}-DISPOSITION.json',disposition);dispositions.append(disposition);continue
            if not fake and (datetime.now(timezone.utc)>=datetime.fromisoformat(plan['deadline']) or charge_total(root)+330>MAX_GPU_SECONDS):
                dispositions.append(dict(id=job['id'],status='not run',reason='absolute deadline or cumulative ceiling'));continue
            atomic(out/'STATUS.json',dict(at=now(),job=job['id'],native=native,dispositions=dispositions))
            command=[sys.executable,'-B','-m',job['module'],*job['args'],'--root',str(root)]
            if fake:command=[sys.executable,'-B','-m','runners.stage11_2.smoke','--manifest',str(Path(manifest).resolve()),'--job',job['id'],'--root',str(root)]
            started=time.monotonic()
            # Actual worker reentry is deliberate: its semantic guard must run.
            with (out/(job['id']+'.stdout.log')).open('ab') as stdout,(out/(job['id']+'.stderr.log')).open('ab') as stderr:
                child=subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                atomic(out/'CHILD.json',dict(pid=child.pid,command=command,started=now()))
                # Deadline enforced at each service reservation and HF block.
                # This outer bound detects a stuck worker and leaves it for identity-
                # verified inspection rather than killing an ambiguous native child.
                while child.poll() is None:
                    if time.monotonic()-started>job['maximum_seconds']:
                        raise TimeoutError('worker exceeded outer bound; inspect exact native child before stopping')
                    time.sleep(1)
                if child.returncode:raise RuntimeError(f'{job["id"]} exited {child.returncode}; no automatic retry')
            terminal=root/job['produces']
            for _ in range(10):
                if terminal.exists():break
                time.sleep(1)
            if not terminal.exists():raise RuntimeError('clean exit without final produce')
            receipt=read(terminal)
            if receipt.get('status')!='complete':raise ValueError('unexpected final status')
            disposition=dict(id=job['id'],status='complete',produce_sha256=digest(receipt))
            freeze(out/f'{job["id"]}-DISPOSITION.json',disposition);dispositions.append(disposition)
            atomic(out/'FORECAST.json',forecast(root,plan))
        return freeze(out/'COMPLETE.json',dict(status='complete',dispositions=dispositions,
            manifest_sha256=digest(plan),fake=fake,scope='dispatch completion, not final scientific packet'))
    except BaseException as exc:
        freeze(out/f'FAILED-{os.getpid()}.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),dispositions=dispositions));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--manifest',type=Path);p.add_argument('--prepare',action='store_true');p.add_argument('--fake',action='store_true')
    a=p.parse_args()
    if a.prepare:print(initial_plan(a.root)['schema'])
    else:print(run(a.manifest,a.root,a.fake)['status'])
