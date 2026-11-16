"""Invented-only native pause/continuation/full-replay rehearsal.

DESIGN CHECK: LESSONS3-5. Uses the real unchanged rider body and 2,000 draws.
First execution yields at100; a native authenticated successor finishes the
remaining fixed units with repeated same-config entry. No monkeypatch or shorter
scientific bank. Only the literal KP2 known-answer capsule is permitted here.
"""
from pathlib import Path
import math
from . import week6_kp_riders_capsule_v1 as rider
from .week6_kp_source_v1 import read,digest


def require(inputs,config):
    if (inputs.get('data_access')!='constructed-fixture-only' or config.get('card')!='KP2'
            or config.get('seed')!=20261115 or config.get('max_new_draws')!=100
            or config.get('bootstrap_draws')!=2000 or config.get('permutations')!=200):
        raise ValueError('Only literal complete-bank KP2 native rehearsal is allowed')


def execute(output,inputs,config):
    require(inputs,config);output=Path(output);work=output/'actual-rider'
    resumed=(work/'CHECKPOINT_0099.json').exists()
    if resumed:
        receipt=read(output.parent/'RESUMED_FROM.json')
        if (receipt.get('adapter')!='week6_resume_v1' or
                receipt.get('copied',{}).get('actual-rider/CHECKPOINT_0099.json')!=digest(work/'CHECKPOINT_0099.json')):
            raise ValueError('Actual authenticated native checkpoint reentry required')
    preserved=digest(work/'draws/0000.json') if resumed else None
    result=rider.execute(work,inputs,config)
    if not resumed:
        if result.get('status')!='yielded' or result.get('completed_units')!=100:
            raise ValueError('Expected actual first100 fixed-draw checkpoint')
        return result
    for _ in range(19):
        if result.get('status')=='complete':break
        if (output/'YIELD_REQUEST.json').exists():return result
        result=rider.execute(work,inputs,config)
    if result.get('status')!='complete' or result.get('draws')!=2000:
        raise ValueError('Rehearsal did not finish every fixed draw')
    if digest(work/'draws/0000.json')!=preserved:raise ValueError('Original checkpoint draw changed')
    point=read(work/'POINT.json')
    if point['failure'] is not None or not math.isclose(point['value'],80.,rel_tol=0,abs_tol=1e-8):
        raise ValueError('Literal held-out80-percent contrast not recovered')
    return dict(result,constructed_only=True,actual_handler='week6_kp_riders_capsule_v1')


def verify(output,inputs,config):
    require(inputs,config);work=Path(output)/'actual-rider'
    result=rider.verify(work,inputs,config)
    if result.get('verified') is not True or result.get('draws')!=2000:
        raise ValueError('Full fresh-process replay missing')
    return dict(result,constructed_only=True,known_answer_percent=80.,
                native_pause_reentry_required=True,production_admission=False)
