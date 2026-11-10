"""Constructed exact-engine function fixture; no model or human text."""
from pathlib import Path
from .week5_at_engine import modules,map_marks,COMMIT
from .timing_census import read
from .timing_p6 import write_equal


def fixture(inputs):
    if set(inputs)!={'engine_source'}:raise ValueError('Exact frozen engine source required')
    surface,_=modules(inputs['engine_source'])
    class Reader:
        def score(self,text,context='',check=lambda:None):
            return [dict(start=i,end=i+1,nats=1.+(i%5)) for i in range(len(text))]
    text='Ordinary makers choose small details. They notice unexpected changes. Names Alex and code `x=42` remain held.'
    capture=dict(regions=[dict(id='document',anchor=dict(exact=text))])
    result=surface.deviation_map(capture,Reader())
    words=[dict(row_key=str(i),start=m.start(),end=m.end()) for i,m in enumerate(surface.WORD.finditer(text))]
    mapped=map_marks(text,words,result)
    expected=[]
    for word,value in zip(words,mapped):
        literal=text[word['start']:word['end']]
        if literal in ('Alex','42','x') and value['supported']:raise ValueError('Exact engine holdout fixture failed')
        expected.append(dict(value,literal=literal))
    if not any(r['supported'] and r['marked'] for r in mapped):raise ValueError('Exact product marks absent')
    return dict(fixture_only=True,engine_commit=COMMIT,rows=expected,source_holdouts=True)


def execute(output,inputs,config):
    write_equal(Path(output)/'FIXTURE.json',fixture(inputs));return dict(status='complete',fixture_only=True)
def verify(output,inputs,config):
    if read(Path(output)/'FIXTURE.json')!=fixture(inputs):raise ValueError('Exact engine fixture replay differs')
    return dict(verified=True,complete_exact_function_replay=True)
