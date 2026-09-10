"""Two finite discarded real-base loss/memory checks, with explicit failure produces."""
import subprocess
import sys
import time
from runners.stage9.common import REPO,ROOT,closure,freeze,write


def run():
    root=ROOT/'private/streamed-chain-1'
    source=closure([REPO/'runners/stage9'/name for name in
        ('streamed_chain.py','streamed_pilot.py','streamed_loss.py','train.py','common.py','process_identity.py')])
    freeze(root/'PLAN.json',{'sources':source,'families':['qwen','smollm'],'scientific_launch_accepted':False})
    for family in ('qwen','smollm'):
        if closure([REPO/p for p in source['files']])!=source:raise ValueError('memory pilot source changed')
        write(root/'STATUS.json',{'family':family,'phase':'calculation and memory pilot','at':time.time()})
        with (root/(family+'.stdout.log')).open('ab') as out,(root/(family+'.stderr.log')).open('ab') as err:
            child=subprocess.run([sys.executable,'-B','-m','runners.stage9.streamed_pilot','--family',family],
                cwd=REPO,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if child.returncode:
            freeze(root/'FAILED.json',{'family':family,'returncode':child.returncode,'at':time.time()})
            return child.returncode
    freeze(root/'COMPLETE.json',{'families':['qwen','smollm'],'completed_at':time.time(),'scientific_launch_accepted':False})
    return 0


if __name__=='__main__':raise SystemExit(run())
