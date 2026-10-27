"""TR3 source healing 1: an empty reopen is a logged event, not an offer.

DESIGN CHECK: LESSONS 2-5. NULL and ALTERNATIVE preserve the full census.
Empty display arrays remain with zero alternatives; unknown handling remains
unknown. Changed openings or valid-menu mismatches still fail. Malformed offers
are not made empty. Exact prior nonempty unit outputs must remain unchanged.
Original failure, program and native checks stay immutable; no score is fitted.
"""
from contextlib import contextmanager
import json
from . import week3_tr3_inputs as original
from runners.stage9.coauthor import suggestions, delta_ops


def prepare(meta,events,timeline,canonical,p6):
    # Preserve the original handler exactly for all sessions it can represent.
    exceptional=[]
    for i,e in enumerate(events):
        if e.get('eventName') not in ('suggestion-open','suggestion-reopen'):continue
        value=e.get('currentSuggestions')
        value=json.loads(value) if isinstance(value,str) else value
        if value==[]:exceptional.append(i)
    if not exceptional:return ORIGINAL_PREPARE(meta,events,timeline,canonical,p6)
    # Empty events carry no offered alternative. Remove only for the validation
    # view, substituting the active original set so original chronology and
    # canonical opening checks still run at unchanged raw ordinals. Restore the
    # exact empty content in the retained output and mark its scope explicitly.
    # Empty *openings* are independently compared to their canonical record.
    modified=[];active=None;empty_openings={}
    for i,e in enumerate(events):
        replacement=dict(e)
        if e.get('eventName')=='suggestion-open':
            active=i
            if i in exceptional:
                c=next((r for r in canonical['events'] if r['ordinal']==i),None)
                if c is None or c['usable'] or c['options']!=[]:raise ValueError('empty opening lacks canonical exclusion')
                empty_openings[i]=c
        if i in exceptional:
            if active is None:raise ValueError('empty reopen without original display')
            c=next(r for r in canonical['events'] if r['ordinal']==active)
            replacement['currentSuggestions']=c['options'] or [dict(index=0,original='',trimmed='')]
        modified.append(replacement)
    canonical_view=dict(canonical,events=[dict(r,options=[dict(index=0,original='',trimmed='')]) if r['ordinal'] in empty_openings else r for r in canonical['events']])
    # Nonempty reopen after an empty opening remains unsupported and refuses;
    # it is not guessed to be the empty opening's alternatives.
    out=ORIGINAL_PREPARE(meta,modified,timeline,canonical_view,p6)
    for d in out['displays']:
        if d['ordinal'] in exceptional:
            d['options']=[]
            d['empty_display_event']=True
    return out


ORIGINAL_PREPARE=original.prepare


@contextmanager
def handler():
    before=original.prepare;original.prepare=prepare
    try:yield
    finally:original.prepare=before


def execute(output,inputs,config):
    with handler():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with handler():return original.verify(output,inputs,config)
