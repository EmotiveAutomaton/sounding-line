"""TR3 candidate schema healing 1: canonical indexed display records.

DESIGN CHECK: LESSONS 2-5. NULL and ALTERNATIVE use the same displayed text
and discovery split. Original/index/trimmed metadata must validate and reopened
records must agree completely. Exact count parity holds on equivalent text;
malformed or changed records refuse. No scientific selection or effect occurs.
"""
from contextlib import contextmanager
from runners.stage9.coauthor import suggestions
from . import week3_tr3_candidates as original

_original_prepare = original.prepare


def prepare(unit, roster):
    displays=[];menus={}
    for d in unit['displays']:
        options=d['options']
        if not isinstance(options,list):raise ValueError('canonical option list required')
        options=suggestions(options) if options else []
        if d['reopened']:
            if d['origin'] is not None and menus.get(d['origin'])!=options:
                raise ValueError('canonical reopen metadata differs')
        else:
            if d['origin'] in menus:raise ValueError('duplicate canonical menu')
            menus[d['origin']]=options
        displays.append(dict(d,options=[o['trimmed'] for o in options]))
    return _original_prepare(dict(unit,displays=displays),roster)


@contextmanager
def handler():
    before=original.prepare;original.prepare=prepare
    try:yield
    finally:original.prepare=before


def execute(output,inputs,config):
    with handler():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with handler():return original.verify(output,inputs,config)
