"""Fresh native execute/replay child for one N-bounded CH1 queue unit.

No slot claim: the nested Windows Job is a descendant of the admitted queue's
counted Job. The queue retains exact all-descendant accounting and native exits.
"""
from pathlib import Path
import argparse
import json
import os
import time

for _key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_key] = '2'
os.environ['CUDA_VISIBLE_DEVICES'] = ''


def run(unit, operation, invocation, queue):
    import psutil
    from threadpoolctl import threadpool_info, threadpool_limits
    from . import week5_ch_engine_bounded as engine
    from .week5_ch_source import digest, write_json
    from .batch_runtime import native_identity
    unit, invocation, queue = Path(unit), Path(invocation), Path(queue)
    plan = json.loads((unit/'UNIT.json').read_text(encoding='utf8'))
    for path, expected in plan['pins'].items():
        if digest(path) != expected:
            raise ValueError('Queue worker source closure changed')
    write_json(invocation/'NATIVE.json', native_identity())
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    original_requested = engine.requested
    engine.requested = lambda output: original_requested(queue) or (invocation/'YIELD_REQUEST.json').exists()
    started = time.monotonic()
    try:
        with threadpool_limits(limits=2):
            pools = threadpool_info()
            if any(pool['num_threads'] > 2 for pool in pools):
                raise RuntimeError('Numerical pools exceed two threads')
            write_json(invocation/'ENVIRONMENT.json', dict(pools=pools,engine_threads=1,engine_hash_mb=64,cuda_visible=''))
            result = getattr(engine, operation)(unit/'output', plan['inputs'], plan['config'])
            if operation == 'verify' and result.get('status') != 'yielded' and result.get('verified') is not True:
                raise ValueError('Unit replay did not verify')
            write_json(invocation/'RESULT.json', result)
    finally:
        engine.requested = original_requested
        cpu = psutil.Process().cpu_times()
        write_json(invocation/'SELF_USAGE.json', dict(cpu_seconds=cpu.user+cpu.system,
            wall_seconds=time.monotonic()-started,engines_excluded=True,
            accounting_authority='Parent retained nested Job receipt; entire queue parent Job is charged once.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('unit', type=Path)
    parser.add_argument('operation', choices=['execute','verify'])
    parser.add_argument('invocation', type=Path)
    parser.add_argument('queue', type=Path)
    args = parser.parse_args()
    run(args.unit,args.operation,args.invocation,args.queue)
