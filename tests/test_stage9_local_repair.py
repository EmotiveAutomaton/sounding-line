import copy
import pytest
from runners.stage9.local_repair import task_case,input_for,consequence,repair_truth,evaluate_unit
from runners.stage9.generation_pilot import original_world
from runners.stage9.construction import Replay
from runners.stage9.common import digest


def actual_case():
    w=original_world('S9GEN|essay|pilot|original|reader|3')
    return {'source_worlds':[w],'requested_boundary':3,'unit':digest(w)}


def answer(text):return {'accepted':True,'prediction':{'text':text}}


def test_same_edit_question_across_views_and_no_producer_clock_or_hidden_state():
    case=actual_case();a=task_case(case,'artifact');b=task_case(case,'process_record')
    assert (a['requested_mark'],a['proposed_edit'])==(b['requested_mark'],b['proposed_edit'])
    text=input_for(a,'repair')['prefix']
    assert '00 numbers this new interaction' in text
    assert not any(k in text for k in ('persistent_tendency','expertise_law','changes','belief_state','source_worlds'))
    altered=copy.deepcopy(case);altered['unit']='renamed'
    assert task_case(altered,'artifact')['public_task_sha256']==a['public_task_sha256']


def test_requested_mark_wrong_mark_story_and_clock_are_distinct_outcomes():
    task=task_case(actual_case(),'artifact')
    replay=Replay(task['world'],task['events'],extend_visible=True)
    legal=[a for a in replay.legal_actions() if a['outcome']=='done']
    target,other=legal[:2]
    task['requested_mark']=':'.join(target[k] for k in ('type','section','slot'))
    line=lambda a:'00 '+' '.join(a[k] for k in ('type','section','slot'))+' failed'
    exact=repair_truth(task,answer(line(target)))
    assert exact['fixable'] and exact['legal'] and exact['goal_improving'] and not exact['collateral_damage']
    assert exact['supplied_outcome']  # A wrong claimed outcome was supplied externally.
    wrong=repair_truth(task,answer(line(other)))
    assert wrong['legal'] and not wrong['goal_improving'] and wrong['collateral_damage']
    for text in ('A fluent story.','99 stop'):
        refused=repair_truth(task,answer(text))
        assert not refused['legal'] and refused['marks_before']==refused['marks_after']


def test_unavailable_tool_and_later_arrival_have_independent_known_outcomes():
    case=actual_case();w=copy.deepcopy(case['source_worlds'][0]);w['trajectory']['changes']=[]
    w['state']['external_context']['tools']['library']=False
    case={**case,'source_worlds':[w],'requested_boundary':0};task=task_case(case,'artifact')
    section=w['doc']['sections'][0]['name'];task['requested_mark']=task['proposed_edit']='cite:'+section+':ref'
    assert consequence(task)=='failed'
    assert not repair_truth(task,answer('00 cite '+section+' ref done'))['fixable']
    w['trajectory']['changes']=[(0,'library_arrives')]
    assert consequence(task)=='done'
    assert repair_truth(task,answer('00 cite '+section+' ref failed'))['goal_improving']
    task['proposed_edit']='stop';assert consequence(task)=='stopped'
    task['proposed_edit']='write:missing:slot';assert consequence(task)=='illegal'


def test_prospective_query_precedes_repair_without_revealing_its_answer():
    seen=[]
    def call(evidence,arguments,index):
        assert set(evidence)=={'prefix','options'}
        seen.append(index)
        if index=='prospective':return {'accepted':True,'prediction':{'probs':{k:.25 for k in evidence['options']}}}
        assert arguments['max_new_tokens']==32
        return answer('00 stop')
    result=evaluate_unit(actual_case(),'artifact',call)
    assert seen==['prospective','repair'] and result['repair_execution']['legal']
    assert not result['repair_execution']['goal_improving']
