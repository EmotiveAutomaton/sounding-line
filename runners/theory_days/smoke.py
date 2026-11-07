"""Constructed runtime fixture, never science.

DESIGN CHECK: LESSONS 3-5. Exact known square sum must replay; mutation fails.
"""
from pathlib import Path
from runners.stage14.common import freeze,read

def execute(output, inputs, config):
    result=dict(constructed=True,total=sum(x*x for x in range(100)))
    freeze(Path(output)/'FIXTURE.json',result)
    return result

def verify(output, inputs, config):
    if read(Path(output)/'FIXTURE.json')!={'constructed':True,'total':328350}:
        raise ValueError('Known-answer mismatch')
    return dict(verified=True,constructed=True)
