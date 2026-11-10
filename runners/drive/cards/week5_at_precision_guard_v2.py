"""Unchanged self-owned native guard around idempotent precision-case replay."""
from types import FunctionType
from . import week5_at_precision_guard as original
from . import week5_at_precision_case_v2 as case

LIMITS=original.LIMITS
memory=original.memory

def invoke(output,inputs,config,verifying):return case.run(output,inputs,config,verifying)

def run(output,inputs,config,verifying=False):
    fn=FunctionType(original.run.__code__,dict(original.run.__globals__,invoke=invoke,memory=memory),
                    original.run.__name__,original.run.__defaults__,original.run.__closure__)
    return fn(output,inputs,config,verifying)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
