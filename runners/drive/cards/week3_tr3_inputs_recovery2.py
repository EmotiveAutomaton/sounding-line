"""TR3 source healing 2: retain empty reopens before any original menu.

DESIGN CHECK: LESSONS 2-5. NULL and ALTERNATIVE retain all source records.
An empty reopen with no preceding menu is an unanchored log event with zero
offers, not an exposure or an inferred choice. No nonempty orphan is accepted.
The original clock, source-join and complete replay guards remain. Prior
representable outputs must be identical. This is the last ordinary healing pass.
"""
from contextlib import contextmanager
import json
from . import week3_tr3_inputs as original
from . import week3_tr3_inputs_recovery as first


def prepare(meta,events,timeline,canonical,p6):
    orphan=[];view=[];opened=False
    for ordinal,e in enumerate(events):
        if e.get('eventName')=='suggestion-open':opened=True
        value=e.get('currentSuggestions')
        if e.get('eventName')=='suggestion-reopen' and not opened:
            value=json.loads(value) if isinstance(value,str) else value
            if value!=[]:raise ValueError('nonempty reopen without original display')
            orphan.append(ordinal)
            view.append(dict(e,eventName='tr3-empty-unanchored-reopen'))
        else:view.append(e)
    out=first.prepare(meta,view,timeline,canonical,p6)
    out['displays'].extend(dict(ordinal=i,timestamp=events[i]['eventTimestamp'],origin=None,reopened=True,
        options=[],handling=None,handling_usable=False,handling_exclusion='empty reopen has no original menu',
        empty_display_event=True,unanchored_display_event=True) for i in orphan)
    out['displays'].sort(key=lambda r:r['ordinal'])
    return out


@contextmanager
def handler():
    before=original.prepare;original.prepare=prepare
    try:yield
    finally:original.prepare=before


def execute(output,inputs,config):
    with handler():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with handler():return original.verify(output,inputs,config)
