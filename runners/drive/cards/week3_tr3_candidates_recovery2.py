"""TR3 candidate healing 2: preserve authenticated empty reopen events.

DESIGN CHECK: LESSONS 2-5. NULL and ALTERNATIVE count zero alternatives for
an explicitly empty reopen, including one after a nonempty menu. It changes
neither the earlier offer nor its identity. Wrong origin, missing empty flag
or nonempty mismatch refuses. This final ordinary healing attempt preserves
all previously representable counts; no scientific selection or effect.
"""
from contextlib import contextmanager
from . import week3_tr3_candidates as original
from . import week3_tr3_candidates_recovery as first


def prepare(unit,roster):
    view=[];last_origin=None;empty=0;previous=-1
    for d in unit['displays']:
        ordinal=d['ordinal']
        if type(ordinal) is not int or ordinal<=previous:raise ValueError('display order differs')
        previous=ordinal
        if not d['reopened']:last_origin=d['origin']
        if d['reopened'] and d['options']==[] and d['origin'] is not None:
            if d.get('empty_display_event') is not True or d['origin']!=last_origin:
                raise ValueError('empty reopen lacks source flag or matching origin')
            empty+=1
        else:view.append(d)
    result=first.prepare(dict(unit,displays=view),roster)
    result['empty_displays']=sum(d['options']==[] for d in unit['displays'])
    return result


@contextmanager
def handler():
    before=original.prepare;original.prepare=prepare
    try:yield
    finally:original.prepare=before


def execute(output,inputs,config):
    with handler():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with handler():return original.verify(output,inputs,config)
