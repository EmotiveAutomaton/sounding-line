"""Counted full WB1 checkpoint and original small-model batch validation.

DESIGN CHECK: LESSONS3--5. Original raw/statistical answers and exact pinned
small-model arrays must survive checkpointing; every text is constructed.
"""
from pathlib import Path
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash
from .timing_p6 import write_equal
from . import week5_bk_wb1_fixture_v2 as full
from . import week5_bk_wb1_vector_fixture as vectors


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'content_model','content_complete'} or config:raise ValueError('Original small model identity only')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='before constructed WB1 component')
    value=(full.verify if verifying else full.execute)(root/'full',{}, {})
    if value.get('status')=='yielded':return value
    if verifying and value.get('verified') is not True:raise ValueError('Complete WB1 handler proof missing')
    if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='complete constructed WB1 statistics boundary')
    value=(vectors.verify if verifying else vectors.execute)(root/'vectors',inputs,{})
    if value.get('status')=='yielded':return value
    if verifying and value.get('verified') is not True:raise ValueError('Complete original encoder proof missing')
    proof=dict(fixture_only=True,complete_original_raw_statistics_and_coverage_pilot=True,
               pinned_model_batch_equality_and_checkpoint_continuation=True,
               full_fixture_sha256=filehash(root/'full/FIXTURE.json'),
               vector_fixture_sha256=filehash(root/'vectors/FIXTURE.json'))
    if verifying:
        if read(root/'FIXTURE.json')!=proof:raise ValueError('Complete checkpoint proof changed')
        return dict(verified=True,complete_wb1_checkpoint_and_pilot_replay=True)
    write_equal(root/'FIXTURE.json',proof);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config)
def verify(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config,True)
