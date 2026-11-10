"""Retained failed-case engineering replay using idempotent v5 accounting."""
from types import FunctionType
from . import week5_at_precision_case as original
from . import week5_at_scoring_v5 as scorer

run=FunctionType(original.run.__code__,dict(original.run.__globals__,scorer=scorer),
                 original.run.__name__,original.run.__defaults__,original.run.__closure__)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
