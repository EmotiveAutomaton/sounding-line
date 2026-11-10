"""Constructed native checks of complete byte bindings and producer checkpoints.

DESIGN CHECK: LESSONS 3–5. Exact retained bytes and checkpoint status must agree
under every scientific outcome. No corpus or model is read.
"""
from . import week5_runtime_fixture as base

def execute(output, inputs, config):
    output.mkdir(parents=True,exist_ok=True)
    if config.get('yield'):
        (output/'checkpoint.bin').write_bytes(b'constructed checkpoint\n')
        return dict(status='yielded',reason='fixture self-quantum',fixture_only=True)
    result=base.execute(output,inputs,dict(fixture=True))
    (output/'extra.parquet').write_bytes(b'constructed extension coverage, not a table\n')
    return result

def verify(output,inputs,config):
    if config.get('yield'):raise AssertionError('Incomplete checkpoint is not a complete card')
    result=base.verify(output,inputs,dict(fixture=True))
    assert (output/'extra.parquet').read_bytes()==b'constructed extension coverage, not a table\n'
    return dict(**result,extra_bytes_verified=True)
