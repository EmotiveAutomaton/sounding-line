"""Known-answer native Week 5 transport.

DESIGN CHECK: LESSONS 3-5. Exact sum must match direct arithmetic; both null
and alternative records use the same transport. Mutation refuses replay.
"""
import os
from pathlib import Path
from runners.stage14.common import freeze,read

def execute(output,inputs,config):
    if inputs or config!={'fixture':True}:raise ValueError('Constructed fixture only')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    value=dict(constructed_fixture_only=True,positive=sum(range(101)),negative=sum(-i for i in range(101)),
               exact_zero=sum(i-i for i in range(101)),threads={k:os.environ[k] for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')},cuda=os.environ.get('CUDA_VISIBLE_DEVICES'))
    freeze(output/'SUMMARY.json',value);return value

def verify(output,inputs,config):
    got=read(Path(output)/'SUMMARY.json')
    expected=dict(constructed_fixture_only=True,positive=5050,negative=-5050,exact_zero=0,
                  threads={k:'2' for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')},cuda='')
    if got!=expected:raise ValueError('Independent arithmetic or actual environment differs')
    return dict(verified=True,constructed_fixture_only=True)
