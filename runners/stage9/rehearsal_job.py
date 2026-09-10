"""Discarded actual kernel computation with durable units for queue interruption.

DESIGN CHECK: X12. Each complete source unit contains independent executor/kernel
agreement, and its existing receipt must be reused unchanged. A deliberate 0.2 s
checkpoint delay permits native operator inspection; it is never scientific work.
"""
import argparse
import os
from pathlib import Path
import time

from runners.stage9.common import Units, digest, freeze
from runners.stage9.construction import Replay, POP
from runners.stage9.kernel import probabilities
from runners.stage9.kernel_preparation import supplied_program
from runners.stage9.recipes import sampled_world


def run(output, count=192, checkpoint_delay=.2):
    if not .2 <= checkpoint_delay <= 1.:
        raise ValueError('bounded discarded checkpoint-inspection pause required')
    identity = {'cell_identity':os.environ['S9_CELL_IDENTITY'], 'units':count, 'band':9932000,
                'scope':'discarded actual numerical-kernel interruption fixture', 'checkpoint_inspection_delay':checkpoint_delay}
    units = Units(output,identity)
    if (output/'COMPLETE.json').exists():
        return
    for i in range(count):
        key = str(i)
        if units.get(key) is not None:
            continue
        domain = POP.DOMAINS[i%len(POP.DOMAINS)]
        world = sampled_world(POP.pop_lid(i,domain,9932000),'both')
        replay = Replay(world,world['trajectory']['steps'][:min(4,len(world['trajectory']['steps']))])
        program = supplied_program(replay)
        observed, expected = probabilities(program), replay.probabilities()
        if observed.keys() != expected.keys() or max(abs(observed[k]-expected[k]) for k in expected)>1e-12:
            raise ValueError('actual independent numerical fixture failed')
        units.put(key,{'source_sha256':digest(program),'distribution_sha256':digest(observed),
                       'completed_at':time.time(),'kernel_agrees':True})
        time.sleep(checkpoint_delay)
    rows = units.all()
    if len(rows)!=count or len({r['key'] for r in rows})!=count:
        raise ValueError('lost or duplicate completed unit')
    freeze(output/'COMPLETE.json',{'cell_identity':identity['cell_identity'], 'units':count,
                                  'units_sha256':digest(rows),'all_agree':True,'scope':identity['scope']})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path)
    p.add_argument('--checkpoint-delay',type=float,default=.2)
    args=p.parse_args();run(args.output.resolve(),checkpoint_delay=args.checkpoint_delay)
