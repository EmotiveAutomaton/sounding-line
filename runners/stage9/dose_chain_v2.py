"""Manually enumerated Qwen/Smol corrected discarded dose-packing pilots.

DESIGN CHECK: C05/X12. Failed earlier packing is required and preserved. Any new
failure stops this finite helper; actual scientific launch remains a separate gate.
"""
import subprocess
import sys
import time
from runners.stage9.common import REPO,ROOT,closure,freeze,read,write


def run():
    root=ROOT/'private/dose-chain-2'
    prior=read(ROOT/'private/dose-chain-1/FAILED.json')
    names=('dose_chain_v2.py','dose_packing.py','dose_pilot.py','mixed_recipes.py','learner.py','matching.py',
           'recipes.py','construction.py','common.py','runtime.py','reader.py','features.py','service_owner.py',
           'model_service.py','generation_policy.py','neural.py','train.py')
    sources=closure([REPO/'runners/stage9'/n for n in names])
    freeze(root/'PLAN.json',{'families':['qwen','smollm'],'prior_failure':prior,'sources':sources,'scientific_launch_accepted':False})
    for family in ('qwen','smollm'):
        if closure([REPO/k for k in sources['files']])!=sources:raise ValueError('dose packing sources changed')
        write(root/'STATUS.json',{'phase':'dose packing pilot','family':family,'at':time.time()})
        with (root/(family+'.stdout.log')).open('ab') as stdout,(root/(family+'.stderr.log')).open('ab') as stderr:
            p=subprocess.run([sys.executable,'-B','-m','runners.stage9.dose_packing','--family',family],
                 cwd=REPO,stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if p.returncode:
            write(root/'FAILED.json',{'family':family,'returncode':p.returncode,'at':time.time()})
            write(root/'STATUS.json',{'phase':'failed','at':time.time()});return p.returncode
    freeze(root/'COMPLETE.json',{'families':['qwen','smollm'],'completed_at':time.time(),'scientific_launch_accepted':False})
    write(root/'STATUS.json',{'phase':'complete','at':time.time()});return 0


if __name__=='__main__':raise SystemExit(run())
