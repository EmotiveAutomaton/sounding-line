"""Known typed-window decisions and fresh native replay, without human text."""
from pathlib import Path
from .week4_typed_windows import session_windows,classify
from .timing_p6 import write_equal
from .timing_census import read
CONFIG=dict(card='S1-typed-windows-constructed',seed=20261102)

def compute():
    words=[dict(index=i,ordinal=i*2+1,completed_ordinal=i*2+2,is_word=True,token='the' if i%4==0 else 'example',
        previous_typed_token_index=i-1 if i else None,sentence_start=i%8==0,length=3,seconds=float(i),revised=False) for i in range(72)]
    timings=[dict(ordinal=w['ordinal'],onset=True,stop=i%8==0,fast=.2 if i%8==0 else .95-(i//8)*.1,interval_seconds=1.) for i,w in enumerate(words)]
    windows,census=session_windows(dict(words=words),timings,{'the'})
    result=[dict(writer='known',windows=windows)];support=classify(result)
    if [w['indices'][0] for w in windows]!=list(range(0,72,8)) or support['known']['classes']!={'flow':3,'middle':3,'hesitant':3}:raise ValueError('Known window classifications failed')
    if any(len(w['grams'])!=5 for w in windows):raise ValueError('Known informative gram count failed')
    return dict(passes=True,census=census,support=support,windows=windows)

def execute(output,inputs,config):
    if inputs or config!=CONFIG:raise ValueError('Frozen constructed input required')
    write_equal(Path(output)/'RESULTS.json',compute());return dict(status='complete')

def verify(output,inputs,config):
    if inputs or config!=CONFIG or read(Path(output)/'RESULTS.json')!=compute():raise ValueError('Constructed replay differs')
    return dict(verified=True)
