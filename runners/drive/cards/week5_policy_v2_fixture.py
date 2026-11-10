"""Actual Windows file-sharing denial and fresh-process accounting fixture."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ctypes,json,subprocess,sys,time
from ctypes import wintypes
from . import week5_policy_v2 as policy
from .batch_runtime import freeze,filehash

def hold(path,ready,release):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    kernel.CreateFileW.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.CreateFileW(str(path),0x80000000,0,None,3,0x80,None)
    if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    try:
        ready.write_text('locked',encoding='utf8');deadline=time.monotonic()+10
        while not release.exists():
            if time.monotonic()>deadline:raise TimeoutError('constructed lock release')
            time.sleep(.005)
    finally:kernel.CloseHandle(handle)

def case(folder,permanent):
    folder.mkdir(parents=True);job=folder/'job';job.mkdir()
    freeze(job/'PLAN.json',dict(campaign='S15-WEEK5',family='CH',max_cpu_seconds=100))
    (job/'ATTEMPT.claim').touch();path=job/'BUDGET_PROGRESS.json'
    freeze(path,dict(at=datetime.now(timezone.utc).isoformat(),cpu_seconds=7))
    ready=folder/'LOCK_READY';release=folder/'RELEASE'
    child=subprocess.Popen([sys.executable,'-X','utf8','-B','-m',__name__ if __name__!='__main__' else 'runners.drive.cards.week5_policy_v2_fixture',
                            '--hold',str(path),'--ready',str(ready),'--release',str(release)])
    try:
        deadline=time.monotonic()+5
        while not ready.exists():
            if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Native lock not established')
            time.sleep(.005)
        # Verify that this OS handle actually blocks Python's ordinary read.
        try:path.read_text('utf8')
        except PermissionError:pass
        else:raise AssertionError('Fixture did not establish a real sharing denial')
        if not permanent:
            import threading
            timer=threading.Timer(.06,lambda:release.write_text('release',encoding='utf8'));timer.start()
        started=time.monotonic()
        if permanent:
            try:policy.charges(folder)
            except policy.AccountingReadError:pass
            else:raise AssertionError('Unreadable active accounting did not fail closed')
        else:
            value=policy.charges(folder)['CH'];assert 41<=value<65
        assert time.monotonic()-started<2
    finally:
        release.write_text('release',encoding='utf8');child.wait(timeout=10)
        if not permanent:timer.join()
    if child.returncode:raise RuntimeError('Native sharing holder failed')
    # Complete replay after the native lock closes must retain the same known
    # terminal CPU, without a sampling-time nuisance in the final expectation.
    freeze(job/'FAILED.json',dict(cpu_seconds=7))
    assert policy.charges(folder)['CH']==37
    return dict(real_windows_denial=True,transient_recovered=not permanent,persistent_failed_closed=permanent,terminal_charge=37)

def own_usage_case(folder):
    from .week5_runtime_v4 import failure_charge
    folder.mkdir(parents=True);path=folder/'EXECUTE_JOB_USAGE.json';freeze(path,dict(cpu_seconds=7))
    ready=folder/'LOCK_READY';release=folder/'RELEASE'
    child=subprocess.Popen([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_policy_v2_fixture','--hold',str(path),'--ready',str(ready),'--release',str(release)])
    try:
        deadline=time.monotonic()+5
        while not ready.exists():
            if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Native own-usage lock not established')
            time.sleep(.005)
        assert failure_charge(folder,{'max_cpu_seconds':100},['execute'],0)==(100,True)
    finally:release.write_text('release',encoding='utf8');child.wait(timeout=10)
    assert failure_charge(folder,{'max_cpu_seconds':100},['execute'],0)==(7,False)
    return dict(unreadable_started_child_charged_full_cap=True,exact_job_usage_recovers=7)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--replay',action='store_true')
    parser.add_argument('--hold',type=Path);parser.add_argument('--ready',type=Path);parser.add_argument('--release',type=Path);args=parser.parse_args()
    if args.hold:hold(args.hold,args.ready,args.release);return
    output=args.output;output.mkdir(parents=True,exist_ok=True)
    result=dict(transient=case(output/'transient',False),persistent=case(output/'persistent',True),own_usage=own_usage_case(output/'own-usage'))
    if not args.replay:
        child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_policy_v2_fixture','--output',str(output/'fresh'),'--replay'],capture_output=True,text=True)
        if child.returncode:raise RuntimeError(child.stderr[-2000:])
        assert json.loads(child.stdout)==result
        freeze(output/'COMPLETE.json',dict(passed=True,constructed=True,fresh_process_replay=True,results=result,
               source_pins={name:filehash(Path(__file__).with_name(name)) for name in ('week5_policy_v2.py','week5_runtime_v4.py','week5_policy_v2_fixture.py')}))
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
