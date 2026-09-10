"""Actual finite numerical jobs with deliberately failed prelaunch branches.

DESIGN CHECK: LESSONS sections 3/5; X12. A failed producer must block its consumer
but neither an unrelated numerical job nor closure. An expired expansion horizon
must preserve the initial finite queue. Missing/incorrect produces never complete.
Known branch states and kernel equality are checked in a separate closure process.
No model, discovery unit, scientific assertion or synthetic model output is used.
"""
from .live_status import read as read_status
import argparse
import os
from pathlib import Path
from runners.stage9.common import Units,read,freeze,digest
from runners.stage9.construction import Replay,POP
from runners.stage9.kernel import probabilities
from runners.stage9.kernel_preparation import supplied_program
from runners.stage9.recipes import sampled_world


def run(mode,produce,queue_root):
    identity={'cell_identity':os.environ['S9_CELL_IDENTITY'],'fixture':mode,'scope':'discarded branch isolation rehearsal'}
    if mode=='blocked':raise AssertionError('ineligible consumer was executed')
    if mode=='closure':
        states=read_status(queue_root/'STATUS.json')['jobs']
        expected={'failed-producer':'FAILED','blocked-consumer':'NOT_RUN','unrelated-kernel':'COMPLETE',
                  'bad-produce':'FAILED','expired-expansion':'NOT_RUN'}
        if any(states[k]['status']!=v for k,v in expected.items()):
            raise ValueError('branch isolation/horizon failed')
        freeze(produce,identity|{'expected_branch_states':expected,'checks_pass':True})
        return
    units=Units(produce.parent/'units',identity)
    for i in range(8):
        world=sampled_world(POP.pop_lid(i,POP.DOMAINS[i%2],9938000),'both')
        replay=Replay(world,world['trajectory']['steps'][:min(4,len(world['trajectory']['steps']))])
        supplied=supplied_program(replay);actual=probabilities(supplied);expected=replay.probabilities()
        if actual.keys()!=expected.keys() or max(abs(actual[k]-expected[k]) for k in expected)>1e-12:
            raise ValueError('independent numerical fixture mismatch')
        units.put(str(i),{'input':digest(supplied),'prediction':digest(actual),'agrees':True})
        if mode=='fail':raise RuntimeError('deliberately failed prelaunch producer after one durable numerical unit')
    freeze(produce,identity|{'cell_identity':'deliberately-wrong' if mode=='bad' else identity['cell_identity'],
                            'numerical_units':8,'all_agree':True})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['fail','blocked','work','bad','closure'])
    p.add_argument('produce',type=Path);p.add_argument('queue_root',type=Path)
    a=p.parse_args();run(a.mode,a.produce.resolve(),a.queue_root.resolve())
