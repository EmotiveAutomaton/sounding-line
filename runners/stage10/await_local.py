"""Native finite dependency wait; never a model polling loop.

DESIGN CHECK: current transition-only contract and LESSONS5. A matching native
process may continue; a terminal produce advances; disappearance or PID reuse
without a terminal refuses. No process is started, restarted, killed or adopted.
"""
import argparse
from pathlib import Path
import time
from runners.stage9.process_identity import native_identity
from .queue import read
from .ollama import write_new,now
from .revision_bank import sha,finish,checked


def run(owner,complete,failure,output,inspect=native_identity,pause=time.sleep):
    expected=read(owner)['native']
    if not isinstance(expected,dict) or not expected.get('pid'):raise ValueError('native predecessor identity required')
    if (output/'COMPLETE.json').exists():return checked(output)
    while True:
        if complete.exists():
            result=read(complete)
            if result.get('status')!='COMPLETE':raise ValueError('predecessor receipt is not complete')
            output.mkdir(parents=True,exist_ok=False)
            write_new(output/'PREDECESSOR.json',{'native':expected,'owner_sha256':sha(owner),'complete_sha256':sha(complete),
                      'all_jobs_succeeded':result.get('all_jobs_succeeded',True),'path':complete.as_posix()})
            return finish(output,sha(complete))
        if failure.exists():raise RuntimeError('predecessor failed; inspect original evidence')
        if inspect(expected['pid'])!=expected:raise RuntimeError('predecessor disappeared or native identity changed')
        pause(10)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['owner','complete','failure','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:run(a.owner,a.complete,a.failure,a.output)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():write_new(a.output/'FAILED.json',{'at':now(),'error':repr(exc)})
        raise
