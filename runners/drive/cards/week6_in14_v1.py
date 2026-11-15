"""IN14 Week 6 entry point. DESIGN CHECK: full contract in IN14_V1.md."""
from . import week6_in14_in16_run_v1 as run

def execute(output,inputs,config):
    return run.execute('IN14',output,inputs,config)

def verify(output,inputs,config):
    return run.verify('IN14',output,inputs,config)
