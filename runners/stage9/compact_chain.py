"""Two finite compact-context timing fits after the original packing pilots.

DESIGN CHECK: C05. Same learner states, sources, seed and target budgets; changed
packing is explicitly a new discarded recipe. Failures stop the chain.
"""
import subprocess
import sys
import time
from runners.stage9.common import REPO,ROOT,closure,freeze,read,write


def run():
    root=ROOT/'private/compact-chain-1'
    prior=read(ROOT/'private/matched-chain-1/COMPLETE.json')
    sources=closure([REPO/'runners/stage9'/n for n in
                     ('compact_chain.py','compact_matched_pilot.py','matching.py','train.py','neural.py','common.py')])
    freeze(root/'PLAN.json',{'families':['qwen','smollm'],'prior':prior,'sources':sources,'scientific_launch_accepted':False})
    for family in ('qwen','smollm'):
        if closure([REPO/k for k in sources['files']])!=sources:
            raise ValueError('compact pilot source changed')
        write(root/'STATUS.json',{'phase':'training','family':family,'at':time.time()})
        with (root/(family+'.stdout.log')).open('ab') as stdout,(root/(family+'.stderr.log')).open('ab') as stderr:
            p=subprocess.run([sys.executable,'-B','-m','runners.stage9.compact_matched_pilot','train','--family',family],
                             cwd=REPO,stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if p.returncode:
            write(root/'FAILED.json',{'family':family,'returncode':p.returncode,'at':time.time()})
            write(root/'STATUS.json',{'phase':'failed','family':family,'at':time.time()})
            return p.returncode
    freeze(root/'COMPLETE.json',{'families':['qwen','smollm'],'completed_at':time.time(),'scientific_launch_accepted':False})
    write(root/'STATUS.json',{'phase':'complete','at':time.time()})
    return 0


if __name__=='__main__':
    raise SystemExit(run())
