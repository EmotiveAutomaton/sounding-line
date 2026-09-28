"""Resource-bounded successor for the frozen Stage 13 worker cards.

DESIGN CHECK: LESSONS 3-5. NULL: changed cards, live prior owners, unknown
attempts, failed gates and expired whole blocks refuse dispatch. ALTERNATIVE:
independent CPU cards run concurrently, exactly one GPU owner runs, and late
dependencies become runnable. Original workers, scores and reserves are unchanged.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import os
import subprocess
import time
from .common import RAW, REPO, read, atomic, freeze, filehash, check_pins, now, bound, limit_process
from .worker import verify
from .queue import topological
from runners.stage9.process_identity import native_identity
from tools.codex_common import singleton


def inventory(raw, cards, running, verified=None):
    verified = verified if verified is not None else set()
    states = {}
    for c in cards:
        name = c['id']; out = raw/'jobs'/name
        if name in running:
            states[name] = 'RUNNING'
        elif name in verified:
            states[name] = 'DONE'
        elif (out/'COMPLETE.json').exists():
            d = verify(out)
            if d['card_sha256'] != filehash(raw/'manifests'/f'{name}.json'):
                raise ValueError('completed card changed: '+name)
            states[name] = 'DONE'
            verified.add(name)
        elif (out/'FAILED.json').exists():
            states[name] = 'FAILED'
        elif (out/'DISPATCH.json').exists():
            raise RuntimeError('unknown attempt requires reconciliation: '+name)
        else:
            states[name] = 'PENDING'
    for c in topological(cards):
        if states[c['id']] != 'PENDING': continue
        if any(states.get(n) in ('FAILED', 'BLOCKED') for n in c.get('requires', [])):
            states[c['id']] = 'BLOCKED'
        for gate in c.get('gates', []):
            p = raw/'jobs'/gate/'ADMISSION.json'
            if p.exists() and read(p).get('admitted') is not True:
                states[c['id']] = 'BLOCKED'
    return states


def eligible(card, states, raw):
    if states[card['id']] != 'PENDING': return False
    for name in card.get('requires', []):
        if states.get(name) != 'DONE': return False
    for gate in card.get('gates', []):
        p = raw/'jobs'/gate/'ADMISSION.json'
        if not p.exists() or read(p).get('admitted') is not True: return False
    return True


def worker_command(card, plan, raw):
    entry = ("import os,sys,runpy;os.environ['SL_STAGE13_REPO']="+repr(str(REPO))+
             ";sys.path.insert(0,"+repr(plan['python_site_packages'])+
             ");sys.path.insert(0,"+repr(str(raw/plan['source_capsule']))+
             ");import runners;runners.__path__.append("+repr(str(REPO/'runners'))+
             ");runpy.run_module('runners.stage13.worker',run_name='__main__')")
    return [native_identity()['executable'], '-B', '-c', entry,
            '--card', str(raw/'manifests'/f"{card['id']}.json"), '--raw', str(raw)]


def run(plan_path, raw=RAW):
    import psutil
    limit_process(); raw=Path(raw); plan=read(plan_path)
    if filehash(Path(__file__)) != plan['dispatcher_sha256']: raise ValueError('dispatcher changed')
    if filehash(raw/'CONTRACT.json') != plan['contract_sha256']: raise ValueError('contract changed')
    check_pins(plan['source_pins'])
    cards=[]
    for name in plan['cards']:
        p=raw/'manifests'/f'{name}.json'
        if filehash(p)!=plan['manifest_hashes'][name]: raise ValueError('card changed')
        c=read(p)
        for p,h in c.get('input_pins',{}).items():
            if filehash(raw/p)!=h: raise ValueError('input changed')
        cards.append(c)
    cards=topological(cards); by={c['id']:c for c in cards}
    # Probe the exact native child environment before any production dispatch.
    if cards:
        probe=worker_command(cards[0],plan,raw)[:4]
        probe[3]=probe[3].split(";runpy.run_module(")[0]+";import psutil,torch,numpy,scipy,transformers"
        subprocess.run(probe,cwd=REPO,check=True,timeout=60,
                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if any(n not in by for c in cards for n in c.get('requires',[])):
        raise ValueError('successor must contain every dependency')
    if not 1<=plan['cpu_workers']<=8: raise ValueError('CPU allocation outside reviewed bound')
    q=raw/'queue'/plan['id']; running={}; handles={}; held={}; started={}; verified=set()
    for old in plan.get('prior_owners',[]):
        if native_identity(old['pid'])==old: raise RuntimeError('prior coordinator is still live')
    with singleton(raw/'locks/queue-kernel.lock'):
        freeze(q/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(plan_path)))
        # Adopt only explicitly recorded, unchanged running workers; never redispatch them.
        for name, n in plan.get('adopt',{}).items():
            out=raw/'jobs'/name
            if (out/'COMPLETE.json').exists() or (out/'FAILED.json').exists(): continue
            if read(out/'DISPATCH.json')['native']!=n or native_identity(n['pid'])!=n:
                raise RuntimeError('adopted attempt has unknown outcome')
            running[name]=dict(native=n,process=None,adopted=True)
        while True:
            for name, r in list(running.items()):
                proc=r['process']
                alive=(proc.poll() is None) if proc else native_identity(r['native']['pid'])==r['native']
                if alive:
                    out=raw/'jobs'/name
                    since=read(out/'DISPATCH.json')['at'] if (out/'DISPATCH.json').exists() else started[name]['at']
                    elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(since)).total_seconds()
                    if elapsed>by[name]['wall_seconds']+60:
                        if native_identity(r['native']['pid'])!=r['native']: raise RuntimeError('timeout identity changed')
                        # Only the exact owned worker is stopped; unknown GPU service keeps its lock.
                        psutil.Process(r['native']['pid']).terminate()
                        freeze(q/f'UNKNOWN-{name}.json',dict(status='failed',at=now(),job=name,native=r['native'],reason='whole-worker deadline; request outcome requires reconciliation'))
                        raise RuntimeError('worker deadline exceeded: '+name)
                    continue
                if name in handles: handles.pop(name).close()
                out=raw/'jobs'/name
                if not (out/'COMPLETE.json').exists() and not (out/'FAILED.json').exists():
                    freeze(q/f'UNKNOWN-{name}.json',dict(status='failed',at=now(),job=name,native=r['native'],reason='exited without terminal; never retry automatically'))
                    raise RuntimeError('worker exited without terminal: '+name)
                running.pop(name)
                failure=out/'FAILED.json'
                if failure.exists() and read(failure).get('phase')=='preflight':
                    raise RuntimeError('unexpected preflight failure; stop new dispatch and reconcile: '+name)
            states=inventory(raw,cards,running,verified)
            allocation=read(raw/'ALLOCATION.json')
            slots=plan['cpu_workers'] if allocation['gear']==2 else 1
            stop=any((raw/p).exists() for p in ('STOP.json','PAUSE.json')) or (q/'STOP_AFTER_CURRENT.json').exists()
            used=Counter(by[n]['resource'] for n in running)
            for c in cards:
                name=c['id']; resource=c['resource']
                if stop or not eligible(c,states,raw): continue
                if resource not in ('cpu','gpu'): raise ValueError('unknown resource')
                if used[resource]>=(slots if resource=='cpu' else 1): continue
                if resource=='gpu' and allocation['gear']!=2:
                    held[name]='held for Gear 1'; continue
                if psutil.virtual_memory().available < plan.get('free_host_floor_GiB',12)*1024**3:
                    held[name]='host memory floor'; continue
                try: bound(raw,c)
                except RuntimeError as exc:
                    held[name]=str(exc); continue
                # Optional infrastructure prerequisites never replace scientific gates.
                deps=plan.get('additional_requires',{}).get(name,[])
                if any(states.get(n)!='DONE' for n in deps):
                    held[name]='infrastructure prerequisite incomplete'; continue
                if resource=='gpu':
                    if (REPO/'results/.gpu.lock').exists():
                        held[name]='existing GPU owner or unknown request'; continue
                    try:
                        from runners.stage12.local_api import readiness,snapshot
                        if c['action'].startswith('qwen'):
                            from .gpu import PROFILE
                            ready=readiness(PROFILE)
                            if not ready['ready']: held[name]=ready['reason']; continue
                        elif snapshot()['free_MiB']<7500:
                            held[name]='frozen training/evaluation GPU memory floor'; continue
                    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:
                        held[name]='resource inspection failed: '+type(exc).__name__; continue
                held.pop(name,None)
                log=q/f'{name}.log';log.parent.mkdir(parents=True,exist_ok=True)
                fh=log.open('ab');handles[name]=fh
                proc=subprocess.Popen(worker_command(c,plan,raw),cwd=REPO,stdout=fh,stderr=subprocess.STDOUT,
                                      creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                n=native_identity(proc.pid)
                running[name]=dict(native=n,process=proc,adopted=False);started[name]=dict(at=now(),native=n)
                states[name]='RUNNING';used[resource]+=1
                atomic(q/'STARTED.json',started)
            atomic(q/'STATUS.json',dict(at=now(),gear=allocation['gear'],cpu_limit=slots,
                counts=dict(Counter(states.values())),states=states,held=held,
                running={n:{k:v for k,v in r.items() if k!='process'} for n,r in running.items()}))
            if not running:
                # No polling loop for exhausted/deadline/resource-blocked work. Notify operator.
                freeze(q/'AWAITING_SELECTION.json',dict(status='waiting',at=now(),states=states,held=held,scientific_verdict=False))
                freeze(q/'EXIT.json',dict(status='complete',at=now(),scientific_verdict=False))
                return
            time.sleep(10)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    try: run(a.plan)
    except BaseException as exc:
        freeze(RAW/'queue'/read(a.plan)['id']/'FAILED.json',dict(status='failed',at=now(),error=type(exc).__name__+': '+str(exc)))
        raise
