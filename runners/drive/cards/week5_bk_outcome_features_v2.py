"""FR1 single-writer calibration uncertainty guard; immutable v1 retained.

DESIGN CHECK: LESSONS3 one-independent-unit rule, 2026-11-07. Repeating a
sole writer cannot establish a population lower bound. At two or more writers
the frozen arithmetic is unchanged. No missing calibration becomes a zero.
"""
from types import FunctionType,SimpleNamespace
from . import week5_bk_outcome_features as original
from . import week3_frames_stats as stats


def interval(values,rng,n):
    result=stats.interval(values,rng,n)
    if result['writers']==1:result.update(ci95=None,uncertainty='one writer; no population interval')
    return result


def prepare(data,dictionary,card):
    namespace=SimpleNamespace(**dict(stats.__dict__,interval=interval))
    fn=FunctionType(original.prepare.__code__,dict(original.__dict__,fr=namespace))
    return fn(data,dictionary,card)


def run(output,inputs,config,verifying=False):
    fn=FunctionType(original.run.__code__,dict(original.__dict__,prepare=prepare))
    return fn(output,inputs,config,verifying)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
