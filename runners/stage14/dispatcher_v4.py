"""Manually commissioned finite DAG, local six-slot host and one exclusive GPU.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-11. NULL: duplicate owner, unknown attempt, failed gate,
changed source, low resource or insufficient whole-block time refuses dispatch.
ALTERNATIVE: independent admitted cards run, complete guards prevent repetition,
and terminal starvation is visible. No retry, stale-lock reclamation or TODO parser.
"""
import argparse,ctypes,os,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
import psutil
from .common import REPO,RAW,REPORTING,read,freeze,atomic,verify,check_pins,filehash,limits,now
from runners.stage9.process_identity import native_identity,is_same_live_process
from .terminal_reconciliation import load_reconciled,check_failed_binding,failed_binding
from .unknown_reconciliation import load_unknown,check_unknown_binding,record_unknown

def disposition(card,states,raw=RAW):
    for dep in card.get('requires',[]):
        if states.get(dep) in ('failed','blocked','unknown','timeout'):return 'blocked','dependency '+dep+' did not complete'
        if states.get(dep)!='complete':return 'waiting','dependency '+dep
    for gate in card.get('gates',[]):
        if states.get(gate)!='complete':return 'waiting','gate '+gate
        if read(raw/'jobs'/gate/'ADMISSION.json').get('admitted') is not True:return 'blocked','scientific admission refused: '+gate
    return 'eligible','dependencies verified'

def readiness(card):
    if psutil.virtual_memory().available<8*1024**3:return False,'host free RAM below 8 GiB'
    if psutil.disk_usage(str(REPO)).free<20*1024**3:return False,'disk reserve below 20 GiB'
    if card['resource']=='cpu':return True,'CPU admitted'
    if (REPO/'results/.gpu.lock').exists():return False,'GPU lock held; no automatic reclamation'
    from .local import ready,api
    if 'model_digest' in card:
        value=ready(card['model'],card['model_digest'],card['memory_MiB']);return value['ready'],value['reason']
    from runners.stage12.local_api import snapshot
    if api('/api/ps')['models']:return False,'dedicated Ollama model must unload before torch'
    snap=snapshot();return snap['free_MiB']>=card['memory_MiB'] and snap['temperature_C']<=78,'torch memory/temperature admission'

def stop_owned(dispatch,card_path):
    identity=dispatch['native']
    if not is_same_live_process(identity):return
    proc=psutil.Process(identity['pid']);command=proc.cmdline()
    normalized=' '.join(command).replace('\\','/').lower()
    candidates=[str(card_path).replace('\\','/').lower(),str(card_path.relative_to(REPO)).replace('\\','/').lower()]
    if not any(c in normalized for c in candidates):raise RuntimeError('timeout command identity mismatch')
    if not is_same_live_process(identity):raise RuntimeError('timeout native identity changed')
    proc.terminate()
    try:proc.wait(timeout=10)
    except psutil.TimeoutExpired:raise RuntimeError('owned process did not terminate; no escalation or GPU release')

def run(plan_path,raw=RAW):
    RAW=Path(raw)
    limits();plan=read(plan_path);root=RAW/'queue'/plan['id'];root.mkdir(parents=True,exist_ok=True)
    # OS-released mutex is authoritative, not a timestamp-based lock file.
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p
    handle=kernel.CreateMutexW(None,True,'Local\\SoundingLineStage14Queue')
    if not handle or ctypes.get_last_error()==183:raise RuntimeError('another Stage14 dispatcher owns the queue')
    children={};states={};reasons={};verified=set();first_absent={}
    try:
        if (root/'DISPATCH.json').exists():raise RuntimeError('queue attempt already exists; explicit reconciled successor required')
        cards={}
        for identifier in plan['cards']:
            p=RAW/'cards'/f'{identifier}.json';c=read(p)
            if c['id']!=identifier or filehash(p)!=plan['card_pins'][identifier]:raise ValueError('plan/card binding mismatch')
            check_pins(c['source_pins']);check_pins(c.get('input_pins',{}));cards[identifier]=c
        if len(cards)!=len(plan['cards']):raise ValueError('duplicate job identity')
        for c in cards.values():
            if any(d not in cards for d in c.get('requires',[])+c.get('gates',[])):raise ValueError('dependency outside frozen plan')
        check_pins(plan.get('coordinator_pins',{}))
        retired=load_reconciled(plan,RAW);unknown=load_unknown(plan,RAW)
        freeze(root/'DISPATCH.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(plan_path),host_slots=6,gpu_slots=1))
        cutoff=datetime.fromisoformat(plan.get('reporting',REPORTING));start=time.monotonic()
        while True:
            held=False;active=0;gpu=0
            for identifier,c in cards.items():
                out=RAW/'jobs'/identifier;cp=RAW/'cards'/f'{identifier}.json'
                if identifier in unknown:
                    check_unknown_binding(out,cp,unknown[identifier])
                    states[identifier]='unknown';continue
                if identifier in retired:
                    check_failed_binding(out,cp,retired[identifier])
                    states[identifier]='failed';continue
                if (out/'COMPLETE.json').exists():
                    if identifier not in verified:verify(out,cp);verified.add(identifier)
                    states[identifier]='complete';continue
                if not (out/'DISPATCH.json').exists() and (out/'FAILED.json').exists():states[identifier]='failed';continue
                if (out/'DISPATCH.json').exists():
                    dispatch=read(out/'DISPATCH.json');live=is_same_live_process(dispatch['native'])
                    if live:
                        states[identifier]='running';active+=1;gpu+=c['resource']=='gpu'
                        age=(datetime.now(timezone.utc)-datetime.fromisoformat(dispatch['at'])).total_seconds()
                        if age>c['wall_seconds']:
                            stop_owned(dispatch,cp);freeze(out/'TIMEOUT.json',dict(at=now(),status='timeout',budget_seconds=c['wall_seconds'],gpu_completion_unknown=c['resource']=='gpu'))
                        continue
                    if (out/'FAILED.json').exists():
                        retired[identifier]=failed_binding(out,cp)
                        freeze(root/'retired'/f'{identifier}.json',dict(at=now(),method='native identity verified exited',**retired[identifier]))
                        states[identifier]='failed';continue
                    if (out/'TIMEOUT.json').exists():states[identifier]='timeout';continue
                    first_absent.setdefault(identifier,time.monotonic())
                    if time.monotonic()-first_absent[identifier]<10:states[identifier]='finishing';active+=1;gpu+=c['resource']=='gpu';continue
                    unknown[identifier]=record_unknown(out,cp);states[identifier]='unknown';continue
                if (out/'BLOCKED.json').exists():states[identifier]='blocked';continue
                if identifier in children:
                    proc=children[identifier]
                    if proc.poll() is None:states[identifier]='starting';active+=1;gpu+=c['resource']=='gpu';continue
                    states[identifier]='failed';freeze(out/'FAILED.json',dict(at=now(),status='failed',reason='worker exited before DISPATCH',returncode=proc.returncode));continue
                states[identifier]='pending'
            pause=any((RAW/x).exists() for x in ('PAUSE.json','STOP.json'))
            for identifier,c in cards.items():
                if states[identifier]!='pending':continue
                state,reason=disposition(c,states,RAW);reasons[identifier]=reason
                out=RAW/'jobs'/identifier
                if state=='blocked':
                    freeze(out/'BLOCKED.json',dict(at=now(),status='blocked',reason=reason,card_sha256=filehash(RAW/'cards'/f'{identifier}.json')));states[identifier]='blocked';continue
                if state!='eligible':continue
                remaining=(cutoff-datetime.now(timezone.utc)).total_seconds()
                if remaining<c['wall_seconds']:
                    states[identifier]='deadline-held';reasons[identifier]='whole block does not fit before reporting reserve';continue
                if pause:states[identifier]='paused';held=True;continue
                if active>=6 or (c['resource']=='gpu' and gpu):continue
                try:ok,reason=readiness(c)
                except Exception as exc:ok=False;reason='preflight unavailable: '+repr(exc)
                if not ok:states[identifier]='resource-held';reasons[identifier]=reason;held=True;continue
                cp=RAW/'cards'/f'{identifier}.json';check_pins(c['source_pins']);check_pins(c.get('input_pins',{}));out.mkdir(parents=True,exist_ok=True)
                with (out/'stdout.log').open('ab') as stdout,(out/'stderr.log').open('ab') as stderr:
                    child=subprocess.Popen([str(REPO/'.venv/Scripts/python.exe'),'-B','-m','runners.stage14.worker','--card',str(cp)],cwd=REPO,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
                children[identifier]=child;freeze(out/'LAUNCH.json',dict(at=now(),native=native_identity(child.pid),command_card=str(cp.relative_to(REPO))))
                states[identifier]='starting';active+=1;gpu+=c['resource']=='gpu'
            atomic(root/'STATUS.json',dict(at=now(),elapsed_seconds=time.monotonic()-start,states=states,reasons=reasons,host_active=active,gpu_active=gpu,reporting=cutoff.isoformat(),paused=pause))
            if not active and not held and all(v in ('complete','failed','blocked','unknown','timeout','deadline-held') for v in states.values()):
                freeze(root/'AWAITING_SELECTION.json',dict(at=now(),status='complete',states=states,reason='finite plan has no eligible remaining work; inspect failures/conditional forest'))
                freeze(root/'EXIT.json',dict(at=now(),status='complete',plan_sha256=filehash(plan_path)));return
            if datetime.now(timezone.utc)>=cutoff and not active:
                freeze(root/'EXIT.json',dict(at=now(),status='complete',reason='reporting reserve reached',states=states));return
            time.sleep(10 if active else 60)
    except BaseException as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='failed',error=repr(exc),states=states));raise
    finally:
        kernel.ReleaseMutex.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        kernel.ReleaseMutex(handle);kernel.CloseHandle(handle)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);run(p.parse_args().plan)
