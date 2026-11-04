"""First S1 nuisance engineering heal: explicit source milliseconds to seconds.

DESIGN CHECK: original source, history, comparisons and missingness unchanged.
P6 occurrence seconds and session metadata milliseconds are different units.
Known mixed-unit input must yield elapsed seconds; original failed attempt and
module stay immutable. No outcome was computed before this source failure.
"""
from types import FunctionType
from collections import Counter
from . import week4_s1_nuisance as original

configuration=original.configuration

def features(window,record,geometry,medians,own_counts,own_total,session_order):
    converted=dict(record,timestamp=record['timestamp']/1000.)
    return original.features(window,converted,geometry,medians,own_counts,own_total,session_order)

def known_check():
    checks=original.known_check()
    words=[dict(index=i,ordinal=i+1,token='a',length=1,population_log_frequency=-2.,sentence_start=False,seconds=12.+i) for i in range(2)]
    x,reason=features(dict(indices=[0,1],ordinals=[1,2]),dict(words=words,timestamp=10000.),
        {2:dict(state='supported',pair=' a',paragraph_boundary=False)},{' a':.5},Counter(a=4),4,2)
    assert reason is None and x[-2]==2.
    return dict(checks,millisecond_session_seconds_occurrence=True)

run=FunctionType(original.run.__code__,dict(original.run.__globals__,features=features,known_check=known_check),
                 original.run.__name__,original.run.__defaults__,original.run.__closure__)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
