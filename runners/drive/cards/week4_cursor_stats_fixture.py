"""Complete known S4 comparison with signed and exact-null native replay."""
from pathlib import Path
from .week4_cursor_stats import analyze
from .timing_census import read
from .timing_p6 import write_equal
CONFIG=dict(card='S4a-constructed',seed=20261102)
def compute():
    answers={}
    for kind,expected,state in [('positive',1,'positive'),('negative',-1,'negative'),('zero',0,'null')]:
        sessions=[]
        for writer in range(20):
            rows=[]
            for j in range(20):
                rows += [dict(bin='1',kind='jump',edit_near=kind=='positive' or kind=='zero' and j%2==0),dict(bin='1',kind='step',edit_near=kind=='negative' or kind=='zero' and j%2==0)]
            sessions.append(dict(writer=str(writer),session=str(writer),landings=rows))
        summary,private=analyze(sessions)
        if summary['estimate']!=expected or summary['state']!=state or summary['control_status']!='passes':raise ValueError('Known S4 answer differs')
        answers[kind]=dict(summary=summary,inference=private)
    return dict(passes=True,answers=answers)
def execute(output,inputs,config):
    if inputs or config!=CONFIG:raise ValueError('Constructed configuration required')
    write_equal(Path(output)/'RESULTS.json',compute());return dict(status='complete')
def verify(output,inputs,config):
    if inputs or config!=CONFIG or read(Path(output)/'RESULTS.json')!=compute():raise ValueError('Known S4 replay differs')
    return dict(verified=True)
