"""WB1.h1 effects known answers and independent native replay.

DESIGN CHECK: source-only repair. NULL no acceptance => missing retention;
ALTERNATIVE exact unchanged windows and original-unit survival. No gate tuned.
Complete legacy parity on supported sources; excluded physical insertions do
not become eligible effects. Corpus use stays behind source and cost admission.
"""
from pathlib import Path
from . import week3_insertion_provenance_h1 as source
from . import week3_pieces_effects as old
from . import week3_pieces_effects_h1 as new
from .timing_census import read
from .timing_p6 import write_equal

CONFIG=dict(mode='constructed',card='WB1.h1-effects-checks',schema=1)

def cases():
    result={}
    for kind in ('plain','newline','rewrite','repeated','unmatched','edited','deleted'):
        events,timeline=source.fixture(kind)
        events.append(dict(eventName='idle',eventSource='user',eventTimestamp=180000))
        # Whole construction precedes outcomes; physical source remains complete.
        anchors=[dict(source_ordinal=0,seconds=0.),dict(source_ordinal=len(events)-1,seconds=180.)]
        rows=new.effect_windows(events,timeline,anchors)
        expected={'plain':4,'newline':4,'rewrite':4,'edited':2,'deleted':0}
        assert rows[0]['full_followup'] and not rows[1]['full_followup']
        assert rows[1]['accepted_retained_share'] is None
        if kind in expected:
            assert rows[0]['accepted_original_utf16']==4
            assert rows[0]['accepted_surviving_utf16']==expected[kind]
            assert rows[0]['accepted_retained_share']==expected[kind]/4
            assert rows==old.effect_windows(events,timeline,anchors)
        else:
            assert rows[0]['accepted_original_utf16']==0
            assert rows[0]['accepted_retained_share'] is None
        result[kind]=rows
    return result

def execute(output,inputs,config):
    if inputs or config!=CONFIG: raise ValueError('constructed-only frozen configuration')
    value=cases();write_equal(Path(output)/'CASES.json',value)
    return dict(status='complete',cases=len(value),scientific_admission=False)

def verify(output,inputs,config):
    if inputs or config!=CONFIG: raise ValueError('constructed-only frozen configuration')
    if read(Path(output)/'CASES.json')!=cases(): raise ValueError('fresh complete effects replay differs')
    return dict(verified=True,complete_effects_parity=True,scientific_admission=False)
