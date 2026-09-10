"""Two measured matched-recipe fits after the active generation pilots release GPU.

DESIGN CHECK: C05/X12. A complete prior chain is required; failure stops this finite
preparation chain. No scientific adapter or queue is admitted by a timing pilot.
"""
import subprocess
import sys
import time
from runners.stage9.common import REPO, ROOT, closure, freeze, read, write


def run():
    output = ROOT/'private/matched-chain-1'
    prior = ROOT/'private/generation-chain-2'
    sources = closure([REPO/'runners/stage9'/name for name in
                       ('matched_chain.py','matched_pilot.py','matching.py','train.py','neural.py','common.py')])
    freeze(output/'PLAN.json', {'families':['qwen','smollm'], 'wait_for':str(prior/'COMPLETE.json'),
                               'wait_limit_seconds':7200,'sources':sources,'scientific_launch_accepted':False})
    started = time.time()
    while not (prior/'COMPLETE.json').exists():
        if (prior/'FAILED.json').exists() or time.time()-started>7200:
            write(output/'FAILED.json', {'phase':'waiting','reason':'prior generation chain failed or wait cap exceeded','at':time.time()})
            return 1
        write(output/'STATUS.json', {'phase':'waiting for generation GPU release','at':time.time()})
        time.sleep(5)
    for family in ('qwen','smollm'):
        if closure([REPO/k for k in sources['files']]) != sources:
            raise ValueError('matched pilot source changed before execution')
        if not (ROOT/'private/pilot-matched'/family/'PREPARATION.json').exists():
            raise ValueError('missing completed matched-recipe preparation')
        write(output/'STATUS.json', {'phase':'training','family':family,'at':time.time()})
        with (output/(family+'.stdout.log')).open('ab') as stdout,(output/(family+'.stderr.log')).open('ab') as stderr:
            child=subprocess.run([sys.executable,'-B','-m','runners.stage9.matched_pilot','train','--family',family],
                                 cwd=REPO,stdout=stdout,stderr=stderr,
                                 creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if child.returncode:
            write(output/'FAILED.json', {'family':family,'returncode':child.returncode,'at':time.time()})
            return child.returncode
    freeze(output/'COMPLETE.json', {'families':['qwen','smollm'],'completed_at':time.time(),
                                   'scientific_launch_accepted':False})
    return 0


if __name__=='__main__':
    raise SystemExit(run())
