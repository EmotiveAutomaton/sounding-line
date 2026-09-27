import json
from copy import deepcopy
import pytest
from runners.stage13.reconstruction import candidates,exact_locations,model_fit,predict,score_prediction,SLOTS,FIELDS
from runners.stage13.gpu import parse,request
from runners.stage13.calibration import fit,evaluate


def fixture():
    facts=[]
    for slot in SLOTS:
        f=dict(slot=slot,actor='unknown',operation='absent',relation='none',exact_spans=[])
        if slot=='entry':f.update(actor='model',operation='insert',relation='selected_by',exact_spans=[[4,8]])
        if slot=='selection':f.update(actor='human_writer',operation='select',relation='selects',exact_spans=[[4,8]])
        facts.append(f)
    e=dict(endpoint='Old new.\n',before='Old \n',alternatives=['new.'],anchors=[dict(id='a000',start=0,end=9)])
    row=dict(key='known',writer='writer',unit='unit',target=dict(handling='accept',facts=facts),views={'A':dict(endpoint=e['endpoint'],anchors=e['anchors']),'C':e,'D':dict(e,observed_operations=facts,observed_handling='accept')})
    return row


def test_exact_executor_coverage_and_wrong_location():
    r=fixture();e=r['views']['C']
    c=candidates(e);assert any(x['executed']==e['endpoint'] and x['handling']=='accept' for x in c)
    assert exact_locations(e,'accept')['entry']==[[4,8]]
    model=model_fit([r]);pred,meta=predict(r['views']['D'],model,'observed-extraction')
    scores=score_prediction(r,pred,meta);assert scores['location']['strict']==1 and scores['operation']['brier']==0 and scores['handling']['correct']==1
    pred['facts'][1]['exact_spans']=[[0,2]]
    assert score_prediction(r,pred,meta)['location']['strict']<1


def test_blind_views_do_not_gain_hidden_history_or_goal_truth():
    r=fixture();model=model_fit([r]);e=r['views']['A']
    p,m=predict(e,model,'joint-execution');q,n=predict(deepcopy(e),model,'without-goal-coupling')
    assert p==q and m['candidate_count']==0
    assert score_prediction(r,p,m)['goal_recovery'] is None
    r2=deepcopy(r);r2['target']['handling']='ignore'
    assert predict(r2['views']['A'],model,'joint-execution')[0]==p


def test_gpu_literal_parser_rejects_capped_and_location_corruption():
    r=fixture();p,_=predict(r['views']['D'],model_fit([r]),'observed-extraction')
    p.pop('attributes');p.update(goal_support=[.7,.2,.1,.4],unknown_history=.2)
    response=dict(done=True,done_reason='stop',prompt_eval_count=200,eval_count=500,message=dict(content=json.dumps(p)))
    assert parse(response,len(r['views']['A']['endpoint']))['goal_support']==[.7,.2,.1,.4]
    response['done_reason']='length'
    with pytest.raises(ValueError):parse(response,9)
    response['done_reason']='stop';p['facts'][0]['exact_spans']=[[0,100]];response['message']['content']=json.dumps(p)
    with pytest.raises(ValueError):parse(response,9)


def test_temperature_fit_and_attempt_denominators():
    cal=[dict(probabilities=[.8,.2],truth=0,unit='a'),dict(probabilities=[.2,.8],truth=1,unit='b')]
    model=fit(cal);result=evaluate(cal,model)
    assert result['attempts']==2 and result['invalid']==0 and result['correct']['mean']==1


def test_invalid_attempt_has_no_absent_location_credit():
    r=fixture();p=dict(invalid=True,handling=None,facts=[dict(slot=s,exact_spans=[]) for s in SLOTS])
    score=score_prediction(r,p,{})
    assert score['handling']['brier']==2 and score['location']['strict']==0


def test_missing_probabilities_stay_in_calibration_denominator():
    rows=[dict(probabilities=None,n=4,truth=1,unit='a')]
    result=evaluate(rows,fit(rows))
    assert result['invalid']==1 and result['brier']['mean']==2


def test_independent_memory_cannot_duplicate_a_connected_component():
    from runners.stage13.context import intervention
    r=fixture();r['unit']='reserve';t=fixture();t['key']='t1';u=deepcopy(t);u['key']='t2'
    assert intervention(r,[t,u],'independent')==(None,[])
