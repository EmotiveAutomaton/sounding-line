"""Two manually enumerated dose pilots; any failed process stops this prelaunch chain.

DESIGN CHECK: C05/X12. Completed compact pilots precede this new source lineage.
Actual scientific fits remain unaccepted and are never launched by this helper.
"""
import subprocess
import sys
import time
from runners.stage9.common import REPO,ROOT,closure,freeze,read,write


def run():
    root=ROOT/'private/dose-chain-1'
    prior=read(ROOT/'private/compact-chain-1/COMPLETE.json')
    names=('dose_chain.py','dose_pilot.py','learner.py','matching.py','recipes.py','construction.py',
           'common.py','runtime.py','reader.py','features.py','service_owner.py','model_service.py',
           'generation_policy.py','neural.py','train.py')
    sources=closure([REPO/'runners/stage9'/n for n in names])
    freeze(root/'PLAN.json',{'families':['qwen','smollm'],'prior':prior,'sources':sources,'scientific_launch_accepted':False})
    for family in ('qwen','smollm'):
        if closure([REPO/k for k in sources['files']])!=sources:
            raise ValueError('dose pilot sources changed')
        write(root/'STATUS.json',{'phase':'dose pilot','family':family,'at':time.time()})
        with (root/(family+'.stdout.log')).open('ab') as stdout,(root/(family+'.stderr.log')).open('ab') as stderr:
            process=subprocess.run([sys.executable,'-B','-m','runners.stage9.dose_pilot','--family',family],
                cwd=REPO,stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if process.returncode:
            write(root/'FAILED.json',{'family':family,'returncode':process.returncode,'at':time.time()})
            write(root/'STATUS.json',{'phase':'failed','at':time.time()});return process.returncode
    freeze(root/'COMPLETE.json',{'families':['qwen','smollm'],'completed_at':time.time(),'scientific_launch_accepted':False})
    write(root/'STATUS.json',{'phase':'complete','at':time.time()});return 0


if __name__=='__main__':
    raise SystemExit(run())
