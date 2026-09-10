import pytest
from runners.stage9.neural_operations import generation_settings,unit_result
from runners.stage9.generation_policy import GREEDY,LEGACY
from runners.stage9.generation_analysis import summarize
from runners.stage9.generation_pilot import original_world
from runners.stage9.common import digest
from runners.stage8.reader import logfmt as LF


def worlds():
    return [original_world('S9GEN|'+d+'|pilot|original|reader|3') for d in ('essay','workshop_doc')]


def test_full_log_calls_keep_original_sampling_and_no_stepwise_assistance():
    assert generation_settings('broad_original')==(336,LEGACY)
    assert generation_settings('broad_expanded')==(336,LEGACY)
    assert generation_settings('self_outcome')==(32,GREEDY)
    w=worlds()[0];seen=[]
    def call(evidence,task,index):
        assert evidence['options']=={} and task['operation']=='generate' and task['max_new_tokens']==336
        assert index=='full-log';seen.append(evidence)
        return {'accepted':False,'failure':'retained fixture call failure'}
    row=unit_result({'unit':digest(w),'source_worlds':[w],'role':'pilot'},'broad_original',call)
    assert len(seen)==1 and not row['result']['call']['accepted'] and row['result']['max_lines']==28


def test_population_full_logs_pass_feasibility_and_story_calls_cannot_be_dropped():
    ws=worlds();predictions=[]
    for w in ws:
        text='\n'.join(LF.event_line(e['i'],e['type'],e['section'],e['slot'],e['outcome']) for e in w['trajectory']['steps'])
        predictions.append({'accepted':True,'prediction':{'text':text}})
    result=summarize(ws,predictions,[-100.,-100.],population='original',scope='pilot')
    assert result['rates']['legacy_feasible']['successes']==2 and result['comparison']['criterion_pass']
    predictions[1]={'accepted':True,'prediction':{'text':'An eloquent account without an action.'}}
    result=summarize(ws,predictions,[-100.,-100.],population='expanded',scope='pilot')
    assert result['rates']['legacy_feasible']['attempts']==2 and not result['comparison']['criterion_pass']
    with pytest.raises(ValueError,match='full assigned'):summarize(ws,predictions,[-100.,-100.],population='expanded',scope='scientific')
