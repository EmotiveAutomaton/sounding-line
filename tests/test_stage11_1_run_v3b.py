"""Compact elicitation has explicit probabilities and independent method admission."""
import copy
import json
import pytest
from runners.stage11_1 import models_v3 as models,run_v3b as run
from runners.stage11_1.common import freeze,contract,allocation,digest,read
from runners.stage11.run import fixture
from runners.stage11.replay import replay
from runners.stage11_1.targets import public,project


def row():
    lines=fixture();e=replay(lines)['events'][0]
    return dict(key='test',writer='w',session='s',prompt='p',target=project(e,lines),views={'artifact':public(e,'artifact')})


def test_compact_forecast_declares_normalized_residual_and_retains_elicitation():
    e=row()['views']['artifact'];raw=run.fake_response('direct');f=models.parse(raw,e,'direct')
    for t in f['facts']:
        for k,labels in models.FIELDS.items():
            assert sum(t[k])==pytest.approx(1) and min(t[k])>=0
            assert t[k][labels.index('unknown')]==pytest.approx(.3)
    assert models.retained(f)==json.loads(raw['message']['content'])
    body=json.loads(models.request_for(e)['messages'][1]['content'])
    assert body['confidence_probability']==models.CONFIDENCE
    for k in ('target','truth','writer','trace'):
        with pytest.raises(ValueError):models.request_for(dict(e,**{k:'answer'}))


def test_bad_confidence_reference_duplicate_and_truncation_rejected():
    e=row()['views']['artifact'];raw=run.fake_response('direct');body=json.loads(raw['message']['content'])
    for failure in ('confidence','slot','span'):
        b=copy.deepcopy(body)
        if failure=='confidence':b['facts'][0]['actor']['confidence']='perfect'
        elif failure=='slot':b['facts'][0]['slot']='entry'
        else:b['facts'][0]['span_ids']=['a999']
        bad=dict(raw,message=dict(content=json.dumps(b)))
        with pytest.raises(ValueError):models.parse(bad,e,'direct')
    raw['done_reason']='length'
    with pytest.raises(ValueError):models.parse(raw,e,'direct')


def test_direct_pilot_admits_direct_without_admitting_other_methods(tmp_path,monkeypatch):
    contract(tmp_path);allocation(tmp_path);cohort=dict(pilot=[row()]);freeze(tmp_path/'COHORT.json',cohort)
    job=dict(id='pilot',branch='integration',partition='constructed',keys=['test'],views=['artifact'],methods=['direct'],
        threads=4,pilot=True,pilot_gate='DIRECT',pursuit='interface',warrant='instrument',next_action='direct reference')
    plan=dict(id='pilot',cohort_digest=digest(cohort),jobs=[job],next_action='direct reference');freeze(tmp_path/'PLAN.json',plan)
    first=run.execute(tmp_path,tmp_path/'PLAN.json',fake=True)
    assert first['charges']['attempts']==1 and (tmp_path/'DIRECT_PILOT_PASSED-v3.json').exists()
    def forbidden(*args,**kwargs):raise AssertionError('extra model call')
    monkeypatch.setattr(run,'api',forbidden)
    freeze(tmp_path/'calls/later/REQUEST.json',dict(branch='integration'))
    assert run.execute(tmp_path,tmp_path/'PLAN.json',fake=True)==first
    later=dict(job,id='unadmitted',methods=['account'],pilot=False,requires_pilot=True)
    freeze(tmp_path/'LATER.json',dict(plan,id='later',jobs=[later]))
    with pytest.raises(ValueError,match='account pilot'):run.execute(tmp_path,tmp_path/'LATER.json',fake=True)


def test_compact_two_pass_account_is_consumed_and_requests_replay(tmp_path):
    e=row()['views']['artifact']
    a=run.call(tmp_path/'first',e,'account','integration',fake=True)
    b=run.call(tmp_path/'second',e,'account_predict','integration',models.retained(a['forecast']),fake=True)
    assert a['status']==b['status']=='COMPLETE'
    assert b==run.call(tmp_path/'second',e,'account_predict','integration',models.retained(a['forecast']),fake=True)
    q=read(tmp_path/'second/REQUEST.json')['request']
    assert json.loads(q['messages'][1]['content'])['retained_intermediate']=={'events':[]}
