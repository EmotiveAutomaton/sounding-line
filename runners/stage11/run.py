"""Finite literal CLI producer with durable attempts and conservative caps.

DESIGN CHECK: LESSONS 2-5. NULL: crash, timeout, changed input or invalid JSON
never grants a fresh uncharged request. ALTERNATIVE: resume is a no-call semantic
replay. Exhaustive dispositions: COMPLETE, INVALID, TRANSPORT_UNCERTAIN,
DEADLINE, GPU_CAP, CALL_CAP, STOPPED, FAILED. No outcome-driven extension.
"""
import argparse
from datetime import datetime, timezone
import os
import time
import traceback
import psutil
from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock
from runners.stage10.ollama import api, identity, now
from .core import *
from .prepare import prepare
from .report import attempt, reparse, analyze


def source_pin():
    paths=list(Path('runners/stage11').glob('*.py'))+[Path('runners/stage9/coauthor.py'),Path('runners/stage9/coauthor_cases.py'),
          Path('runners/stage10/ollama.py'),Path('runners/stage10/contracts.py'),Path('soundingline/gpulock.py')]
    return {p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.name!='viewer.py'}


def call(directory, public, arm, fake=False):
    request=request_for(public,arm)
    if (directory/'ATTEMPT.json').exists(): return reparse(directory,public,arm)
    if directory.exists(): raise ValueError('incomplete original attempt requires explicit recovery; no automatic repeat')
    directory.mkdir(parents=True)
    write_new(directory/'REQUEST.json',dict(at=now(),request=request,model_digest=MODEL_DIGEST,fake=fake))
    begin=time.perf_counter()
    try:
        if fake:
            response=dict(probabilities=[.25]*4,explanation='Synthetic transport rehearsal.')
            if arm=='account': response['events']=[]
            raw=dict(done=True,done_reason='stop',message=dict(content=canonical(response)),fake=True)
        else: raw=api('/api/chat',request,timeout=180)
        write_new(directory/'RAW.json',raw)
    except Exception as exc:
        raw={};write_new(directory/'TRANSPORT_FAILED.json',dict(error=repr(exc),at=now(),execution='uncertain; charged full block reservation'))
    try:
        if not raw: raise ValueError('transport uncertain; no raw response')
        forecast=parse(raw,arm); error=None
    except (ValueError,KeyError,TypeError) as exc: forecast=None;error=str(exc)
    result=dict(status='COMPLETE' if forecast else 'INVALID' if raw else 'TRANSPORT_UNCERTAIN',forecast=forecast,error=error,
                raw_digest=digest(raw) if raw else None,cost=dict(wall_seconds=time.perf_counter()-begin,
                input_tokens=raw.get('prompt_eval_count',0),output_tokens=raw.get('eval_count',0),
                server_seconds=(raw.get('total_duration') or 0)/1e9),fake=fake)
    write_new(directory/'ATTEMPT.json',result)
    return result


def fixture(selected=True):
    menu=[dict(index=0,original=' light',trimmed=' light')]
    rows=[dict(eventName='system-initialize',currentDoc='A small\n'),dict(eventName='suggestion-open',currentSuggestions=menu)]
    if selected:
        rows += [dict(eventName='suggestion-select',currentSuggestionIndex=0),
                 dict(eventName='text-insert',eventSource='api',textDelta={'ops':[{'retain':7},{'insert':' light'}]})]
    else:
        rows += [dict(eventName='suggestion-close'),dict(eventName='text-insert',eventSource='user',textDelta={'ops':[{'retain':7},{'insert':' light'}]})]
    return rows


def synthetic_rows():
    from .replay import replay
    result=[]
    for i in range(2):
        event=replay(fixture(i==0))['events'][0]
        result.append(dict(key='fixture'+str(i),writer='w'+str(i),prompt='p'+str(i),session='s'+str(i),
                           truth=event['decision'],event=event,views={v:evidence(event,v) for v in VIEWS},tranche='initial'))
    assert result[0]['views']['artifact']==result[1]['views']['artifact']
    return result


def rehearse(root):
    rows=synthetic_rows();cohort=dict(train=rows,development=rows,evaluation=rows);model=fit(rows)
    freeze(root/'COHORT.json',cohort);freeze(root/'BASELINES.json',model)
    freeze(root/'PREPARED.json',dict(cohort_digest=digest(cohort),baseline_digest=digest(model)))
    for row in rows:
        for v in VIEWS:
            for a in ARMS: call(attempt(root,'evaluation',row,v,a),row['views'][v],a,fake=True)
    first=analyze(root); second=analyze(root)
    assert first==second
    freeze(root/'REHEARSED.json',dict(status='COMPLETE',synthetic_only=True,comparison_digest=digest(first),semantic_replay=True))
    return dict(status='COMPLETE',calls=8,synthetic_only=True)


def execute(root, pilot=False):
    freeze(root/'PRODUCER_SOURCES.json',source_pin())
    terminal=root/('PILOT.json' if pilot else 'COMPLETE.json')
    if terminal.exists():
        # A completed producer resumes by semantic replay, with no new calls.
        saved=read(terminal)
        if saved['sources']!=source_pin(): raise ValueError('completed producer sources changed')
        cohort=read(root/'COHORT.json')
        phases=[('pilot',synthetic_rows())] if pilot else [('development',cohort['development']),('evaluation',cohort['evaluation'])]
        for lane,rows in phases:
            for row in rows:
                for v in VIEWS:
                    for a in ARMS:
                        directory=attempt(root,lane,row,v,a)
                        if (directory/'ATTEMPT.json').exists(): reparse(directory,row['views'][v],a)
        return saved
    gate=read(PRIVATE/'rehearsal/REHEARSED.json')
    if gate['status']!='COMPLETE': raise ValueError('literal CLI rehearsal missing')
    if not pilot and read(root/'PILOT.json')['status']!='COMPLETE': raise ValueError('literal model interface gate missing')
    contract=read(root/'CONTRACT.json');cohort=read(root/'COHORT.json')
    if digest(cohort)!=read(root/'PREPARED.json')['cohort_digest']: raise ValueError('cohort mutated')
    freeze(root/'MODEL.json',identity())
    phases=[('pilot',synthetic_rows())] if pilot else [('development',cohort['development']),('evaluation',cohort['evaluation'])]
    status='COMPLETE';done=0
    for lane,rows in phases:
        for row in rows:
            dirs=[attempt(root,lane,row,v,a) for v in VIEWS for a in ARMS]
            if all((p/'ATTEMPT.json').exists() for p in dirs):
                for v in VIEWS:
                    for a in ARMS: reparse(attempt(root,lane,row,v,a),row['views'][v],a)
                continue
            if any(p.exists() for p in dirs): raise ValueError('partial block retained; explicit recovery required')
            if (root/'STOP').exists():status='STOPPED';break
            if datetime.now(timezone.utc)>=datetime.fromisoformat(contract['admissions_end']):status='DEADLINE';break
            records=list((root/'calls').rglob('REQUEST.json'))
            if len(records)+4>contract['total_calls'] or len(list((root/'calls'/lane).rglob('REQUEST.json')))+4>contract[lane+'_calls']:
                status='CALL_CAP';break
            service=0.
            for p in (root/'blocks').glob('*/START.json'):
                end=p.with_name('END.json')
                service+=read(end)['charged_seconds'] if end.exists() else read(p)['reservation_seconds']
            if service+780>contract['gpu_seconds']:status='GPU_CAP';break
            # Refuse existing holder rather than invoking the legacy unbounded wait.
            from soundingline.gpulock import GPU_LOCK
            if GPU_LOCK.exists(): raise RuntimeError('GPU held by another producer; no dispatch')
            acquire_gpu_lock('stage11-'+lane)
            block=root/'blocks'/digest([lane,row['key']])[:20];start=time.perf_counter();uncertain=False
            write_new(block/'START.json',dict(at=now(),reservation_seconds=780,pid=os.getpid()))
            try:
                for v in VIEWS:
                    for a in ARMS:
                        result=call(attempt(root,lane,row,v,a),row['views'][v],a)
                        done+=1
                        if result['status']=='TRANSPORT_UNCERTAIN': uncertain=True;raise RuntimeError('uncertain transport; producer stopped')
            finally:
                try: api('/api/generate',dict(model=MODEL,keep_alive=0),timeout=30)
                except Exception: uncertain=True
                write_new(block/'END.json',dict(at=now(),charged_seconds=780 if uncertain else time.perf_counter()-start,
                                               uncertainty=uncertain))
                release_gpu_lock()
            print(canonical(dict(lane=lane,completed_calls=done,episode_finished=True)),flush=True)
        if status!='COMPLETE':break
    if pilot:
        saved=[read(p) for p in (root/'calls/pilot').rglob('ATTEMPT.json')]
        if len(saved)!=8 or any(r['status']!='COMPLETE' for r in saved): raise ValueError('discarded interface pilot did not realize both grammars')
    result=dict(status=status,new_calls=done,at=now(),sources=source_pin())
    freeze(root/('PILOT.json' if pilot else 'COMPLETE.json'),result)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','rehearse','pilot','run','report'])
    parser.add_argument('--root',type=Path,default=PRIVATE);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    if args.command=='prepare': result=prepare(args.root)
    elif args.command=='rehearse': result=rehearse(args.root)
    elif args.command=='report':
        result=analyze(args.root,write=not args.verify)
        if args.verify and result!=read(args.root/'COMPARISONS.json'): raise ValueError('report reproduction differs')
    else:
        import msvcrt
        args.root.mkdir(parents=True,exist_ok=True)
        with (args.root/'producer.lock').open('a+b') as lock:
            lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            p=psutil.Process()
            owner=dict(pid=p.pid,create_time=p.create_time(),executable=p.exe(),command=p.cmdline(),at=now())
            write_new(args.root/('OWNER-'+str(p.pid)+'.json'),owner)
            try: result=execute(args.root,pilot=args.command=='pilot')
            except Exception:
                write_new(args.root/('FAILED-'+str(p.pid)+'.json'),dict(at=now(),error=traceback.format_exc()));raise
    print(canonical(result))


if __name__=='__main__': main()
