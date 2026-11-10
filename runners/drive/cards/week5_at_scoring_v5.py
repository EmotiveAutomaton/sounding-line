"""Idempotent completion accounting for the unchanged AT-FP64-1 scorer.

The scoring function's code is exactly v4's. Only its immutable COST write is
interposed: retain the first completed cost receipt, append every invocation's
actual process cost separately, and still rebuild all original score checks.
"""
from pathlib import Path
from types import FunctionType
import math
import os
import time
from . import week5_at_scoring_v4 as original
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal

NUMERICAL_SPEC=original.NUMERICAL_SPEC
score_binding=original.score_binding
load_model=original.load_model
progress=original.progress


def retained_cost(path):
    value=read(path)
    fields={'cold_load_wall_seconds','elapsed_wall_seconds','elapsed_process_cpu_seconds','forecast_note'}
    if set(value)!=fields:raise ValueError('Original completed cost receipt shape changed')
    for key in fields-{'forecast_note'}:
        if isinstance(value[key],bool) or not isinstance(value[key],(int,float)) or not math.isfinite(value[key]) or value[key]<0:
            raise ValueError('Invalid original completed cost quantity')
    if value['forecast_note']!='Add independent verification and all prior quantum accounting before admission':
        raise ValueError('Original cost accounting scope changed')
    return filehash(path)


def score_batch(output,rows,manifest,*,context='final',context_length=1024,max_wall_seconds=1200,verifying=False):
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    began=time.process_time();wall=time.monotonic();stamp=time.time_ns();result=None;error=None
    path=root/'COST.json';initial_sha=None
    try:
        if path.exists():
            initial_sha=retained_cost(path)
            if any(not (root/name).is_file() for name in ('BINDING.json','INDEX.json','SUMMARY.json')):
                raise ValueError('Completed cost exists without a complete scoring reduction')
        def checked_write(destination,value):
            target=Path(destination)
            if target.resolve()==path.resolve() and initial_sha is not None:
                if retained_cost(path)!=initial_sha:raise ValueError('Retained original completed cost changed during reentry')
                return
            return write_equal(destination,value)
        fn=FunctionType(original.score_batch.__code__,dict(original.score_batch.__globals__,
                        write_equal=checked_write,load_model=load_model,progress=progress),
                        original.score_batch.__name__,original.score_batch.__defaults__,original.score_batch.__closure__)
        fn.__kwdefaults__=original.score_batch.__kwdefaults__
        result=fn(root,rows,manifest,context=context,context_length=context_length,
                  max_wall_seconds=max_wall_seconds,verifying=verifying)
        if initial_sha is not None and retained_cost(path)!=initial_sha:
            raise ValueError('Original completed cost was overwritten')
        return result
    except BaseException as exc:
        error=type(exc).__name__;raise
    finally:
        receipt=dict(process_cpu_seconds=time.process_time()-began,wall_seconds=time.monotonic()-wall,
                     phase='verify' if verifying else 'execute',pid=os.getpid(),
                     status='exception' if error else ('verified' if result and result.get('verified') else (result or {}).get('status')),
                     error_class=error,retained_original_cost_sha256=initial_sha,
                     source_code_sha256=filehash(original.__file__),numerical_spec=NUMERICAL_SPEC,
                     runtime_all_attempt_cpu_including_startup_authoritative=True)
        write_equal(root/'invocation_costs'/f'{os.getpid()}-{stamp}.json',receipt)


def execute(output,inputs,config):return score_batch(output,gzread(inputs['rows']),read(inputs['model_manifest']),**config)
def verify(output,inputs,config):return score_batch(output,gzread(inputs['rows']),read(inputs['model_manifest']),verifying=True,**config)
