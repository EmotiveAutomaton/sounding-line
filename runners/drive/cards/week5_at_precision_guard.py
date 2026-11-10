"""Self-owned resource guard for retained AT precision engineering cases.

Owner admission remains required. The guard obtains its identity directly,
never by searching for a process. Native runtime/Job accounting is authoritative;
these private receipts additionally retain process CPU on every guard outcome.
"""
from pathlib import Path
import ctypes,os,time,threading
from ctypes import wintypes
import psutil
from . import week5_at_precision_case as original
from .timing_p6 import write_equal

GIB=2**30
LIMITS=dict(start_commit_bytes=26*GIB,start_ram_bytes=20*GIB,
            request_commit_bytes=7*GIB,request_ram_bytes=7*GIB,
            hard_commit_floor_bytes=6*GIB,hard_ram_floor_bytes=6*GIB,
            cooperative_grace_seconds=60,poll_seconds=.25)


class NativeMemory(ctypes.Structure):
    _fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[(k,ctypes.c_ulonglong) for k in
        ('total_ram','available_ram','total_commit','available_commit','total_virtual','available_virtual','extended_virtual')]


def memory():
    if os.name!='nt':raise ValueError('Native Windows memory evidence required')
    value=NativeMemory();value.length=ctypes.sizeof(value)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):raise OSError('Native memory query failed')
    return dict(commit_headroom_bytes=value.available_commit,ram_available_bytes=value.available_ram)


def identity():
    process=psutil.Process(os.getpid())
    return dict(pid=process.pid,creation_time=process.create_time(),executable=process.exe(),command_line=process.cmdline())


def action(snapshot,requested_age=None,admission=False):
    if admission:
        return 'refuse' if snapshot['commit_headroom_bytes']<LIMITS['start_commit_bytes'] or snapshot['ram_available_bytes']<LIMITS['start_ram_bytes'] else 'admit'
    if snapshot['commit_headroom_bytes']<LIMITS['hard_commit_floor_bytes'] or snapshot['ram_available_bytes']<LIMITS['hard_ram_floor_bytes']:
        return 'terminate'
    if requested_age is not None and requested_age>=LIMITS['cooperative_grace_seconds']:return 'terminate'
    if snapshot['commit_headroom_bytes']<LIMITS['request_commit_bytes'] or snapshot['ram_available_bytes']<LIMITS['request_ram_bytes']:
        return 'request_yield'
    return 'continue'


def invoke(output,inputs,config,verifying):
    return original.run(output,inputs,config,verifying)


def hard_exit(output,receipt):
    write_equal(Path(output)/'NATIVE_GUARD_TERMINATION.json',receipt)
    os._exit(75)


def run(output,inputs,config,verifying=False):
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    owned=identity();started=time.process_time();wall=time.monotonic();first=memory()
    receipt_path=root/f"GUARD_{'VERIFY' if verifying else 'EXECUTE'}_{owned['pid']}_{round(owned['creation_time']*1000000)}.json"
    state=dict(identity=owned,limits=LIMITS,initial=first,phase='verify' if verifying else 'execute',events=[])
    def request(snapshot,reason):
        value=dict(reason=reason,snapshot=snapshot,identity=owned)
        for p in (root/'YIELD_REQUEST.json',root/'scores/YIELD_REQUEST.json'):
            if not p.exists():write_equal(p,value)
    if action(first,admission=True)=='refuse':
        request(first,'precision verification resource admission refused')
        state.update(status='refused_before_model_load',cpu_seconds=time.process_time()-started)
        write_equal(receipt_path,state)
        return dict(status='yielded',reason='native precision resource admission refused',model_loads=0)
    stop=threading.Event();requested=[None]
    def monitor():
        while not stop.wait(LIMITS['poll_seconds']):
            try:
                snapshot=memory();now=time.monotonic()
                choice=action(snapshot,None if requested[0] is None else now-requested[0])
            except BaseException as error:
                snapshot=dict(memory_query_error=repr(error));choice='request_yield';now=time.monotonic()
                if requested[0] is not None and now-requested[0]>=LIMITS['cooperative_grace_seconds']:choice='terminate'
            if choice in ('request_yield','terminate') and requested[0] is None:
                requested[0]=now;request(snapshot,'native precision memory guard requested a sealed-block yield')
                state['events'].append(dict(action='request_yield',snapshot=snapshot,elapsed_wall_seconds=now-wall))
            if choice=='terminate':
                hard_exit(root,dict(**state,status='guard_terminated_owned_process',cpu_seconds=time.process_time()-started,
                                    elapsed_wall_seconds=now-wall,final_snapshot=snapshot))
                return
    thread=threading.Thread(target=monitor,name='AT-native-memory-guard',daemon=True);thread.start()
    try:result=invoke(root,inputs,config,verifying)
    finally:
        stop.set();thread.join(timeout=2)
        if thread.is_alive():raise RuntimeError('Owned guard failed to stop')
        mi=psutil.Process(os.getpid()).memory_info()
        state.update(cpu_seconds=time.process_time()-started,wall_seconds=time.monotonic()-wall,
                     peak_working_set_bytes=getattr(mi,'peak_wset',mi.rss),status='returned')
        write_equal(receipt_path,state)
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('failed_root');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,dict(failed_root=a.failed_root),{})))
