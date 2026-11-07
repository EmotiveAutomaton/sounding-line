"""Theory-days policy on the unchanged native-contained execution kernel.

DESIGN CHECK: LESSONS 3-5. Same containment for null and alternative; source
mutation or missing verification fails. No scientific outcome inferred here.
"""
import argparse
import os
from pathlib import Path
from runners.drive.cards import batch_runtime_v8 as kernel
from . import policy


def run(root):
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
                'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
        os.environ[key] = '1'
    kernel.admission = policy.admission
    kernel.yield_reason = policy.yield_reason
    kernel.DRAIN = policy.DRAIN
    kernel.run(Path(root).resolve())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    run(parser.parse_args().root)
