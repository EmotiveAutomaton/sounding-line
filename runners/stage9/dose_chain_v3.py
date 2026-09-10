"""Finite full-dose epoch timing after the actual-base streamed-loss checks."""
import subprocess
import sys
import time
from runners.stage9.common import REPO,ROOT,closure,freeze,read,write


def run():
    root=ROOT/'private/dose-chain-3'
    prior=read(ROOT/'private/pilot-dose-v2/qwen/ATTEMPT_DISPOSITION.json')
    names=('dose_chain_v3.py','dose_packing.py','dose_pilot.py','mixed_recipes.py','learner.py','matching.py',
           'recipes.py','construction.py','common.py','runtime.py','reader.py','features.py','service_owner.py',
           'model_service.py','generation_policy.py','neural.py','train.py','streamed_loss.py')
    sources=closure([REPO/'runners/stage9'/n for n in names])
    freeze(root/'PLAN.json',{'families':['qwen','smollm'],'prior_disposition':prior,'sources':sources,
        'loss_computation':'streamed','actual_base_check_sha256':closure([ROOT/'pilot/STREAMED_LOSS.json'])['sha256'],
        'scientific_launch_accepted':False})
    for family in ('qwen','smollm'):
        if closure([REPO/k for k in sources['files']])!=sources:raise ValueError('dose packing sources changed')
        write(root/'STATUS.json',{'phase':'streamed dose packing pilot','family':family,'at':time.time()})
        with (root/(family+'.stdout.log')).open('ab') as out,(root/(family+'.stderr.log')).open('ab') as err:
            child=subprocess.run([sys.executable,'-B','-m','runners.stage9.dose_packing','--family',family,'--loss-mode','streamed'],
                cwd=REPO,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if child.returncode:
            freeze(root/'FAILED.json',{'family':family,'returncode':child.returncode,'at':time.time()});return child.returncode
    freeze(root/'COMPLETE.json',{'families':['qwen','smollm'],'completed_at':time.time(),'scientific_launch_accepted':False})
    return 0


if __name__=='__main__':raise SystemExit(run())
