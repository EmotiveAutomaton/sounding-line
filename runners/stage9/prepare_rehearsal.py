"""Manually reviewed one-job X12 queue; no scientific card or result is admitted."""
from pathlib import Path
import sys
import time
from runners.stage9 import rehearsal_job, queue
from runners.stage9.common import ROOT,REPO,closure,freeze,read


def prepare():
    root=ROOT/'private/queue-rehearsal-3'
    sources=[]
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and Path(path).is_absolute() and Path(path).suffix=='.py':
            path=Path(path).resolve()
            if path.is_relative_to(REPO) and '.venv' not in path.parts:
                sources.append(path)
    sources += [REPO/'runners/stage9/source_bootstrap.py',REPO/'runners/stage8/engines.py']
    campaign=read(ROOT/'CAMPAIGN.json')
    result=root/'work/COMPLETE.json'
    plan={'kind':'prelaunch_rehearsal','campaign_start':campaign['started_epoch'],
          'horizon_epoch':campaign['horizon_epoch'],'sources':closure(sources),
          'jobs':[{'id':'X12-real-kernel','module':'runners.stage9.rehearsal_job',
                   'arguments':[str(result.parent)],'produces':result.relative_to(REPO).as_posix(),
                   'after':[],'requires':[],'resource':'cpu','role':'work','estimated_gpu_seconds':0,
                   'interruption_rehearsal':True}]}
    queue.validate_manifest(plan)
    freeze(root/'PLAN.json',plan)
    print(root/'PLAN.json')


if __name__=='__main__':
    prepare()
