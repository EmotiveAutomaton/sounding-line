"""Literal common-form, dependency, privacy, budget and crash/replay checks."""
import copy
from datetime import datetime,timezone
import json
import pytest
from runners.stage11.replay import replay
from runners.stage11.run import fixture
from runners.stage11_1 import models,run
from runners.stage11_1.common import contract,allocation,freeze,read,digest
from runners.stage11_1.targets import public,project


def evidence():return public(replay(fixture())['events'][0],'alternatives')
def raw(body):return dict(done=True,done_reason='stop',message=dict(content=json.dumps(body)))


def test_public_boundary_and_equal_pass_limits():
    e=evidence();qs=[models.request_for(e,k) for k in ('direct','review','account','account_predict')]
    assert len({q['options']['num_predict'] for q in qs})==1
    assert all(json.loads(q['messages'][1]['content'])['evidence']==e for q in qs)
    for key in ('truth','target','selected_index','trace','key','writer'):
        with pytest.raises(ValueError):models.request_for(dict(e,**{key:'PRIVATE_CANARY'}))
    assert 'PRIVATE_CANARY' not in str(qs)
    with pytest.raises(ValueError):models.request_for(e,'review',{'x':'z'*models.MAX_RETAINED_BYTES})


def test_probability_schema_truncation_and_absent_span_gates():
    e=evidence();r=run.fake_response('direct')
    assert models.parse(r,e,'direct')['handling']==[.25]*4
    body=json.loads(r['message']['content'])
    for mutation in ('sum','bool','nan','slot','span','fiction'):
        b=copy.deepcopy(body)
        if mutation=='sum':b['facts'][0]['actor']=[.3]*4
        elif mutation=='bool':b['facts'][0]['actor']=[True,0,0,0]
        elif mutation=='nan':b['facts'][0]['actor']=[float('nan'),0,0,0]
        elif mutation=='slot':b['facts'][1]['slot']='selection'
        elif mutation=='span':b['facts'][0]['span_ids']=['a999']
        else:b['facts'][0]['actor']='story narrator'
        with pytest.raises(ValueError):models.parse(raw(b),e,'direct')
    r['done_reason']='length'
    with pytest.raises(ValueError):models.parse(r,e,'direct')


def test_account_reference_and_order_checks():
    e=evidence()
    event=dict(id='e1',slot='selection',actor='human_writer',operation='select',span_ids=['a000'],span_state='located',
        relation='selects',depends_on=[],evidence_pointer='endpoint',confidence=.5,alternative='independent typing',unresolved='no record')
    assert models.parse(raw({'events':[event]}),e,'account')['events'][0]['id']=='e1'
    for field,value in [('actor','a fictional character'),('depends_on',['future']),('span_ids',['a100']),('evidence_pointer','private_trace'),('confidence',float('nan'))]:
        b=copy.deepcopy(event);b[field]=value
        with pytest.raises(ValueError):models.parse(raw({'events':[b]}),e,'account')
    entry=dict(event,id='e2',slot='entry',actor='model',operation='insert')
    with pytest.raises(ValueError):models.parse(raw({'events':[entry,event]}),e,'account')


def test_no_call_restart_changed_request_raw_and_uncertain_directory(tmp_path,monkeypatch):
    e=evidence();p=tmp_path/'first';first=run.call(p,e,'direct','S1',fake=True)
    def forbidden(*a,**kw):raise AssertionError('network during replay')
    monkeypatch.setattr(run,'api',forbidden)
    assert run.call(p,e,'direct','S1',fake=True)==first
    with pytest.raises(ValueError):run.call(p,e,'review','S1',fake=True)
    r=read(p/'RAW.json');r['extra']='tampered';(p/'RAW.json').write_text(json.dumps(r),encoding='utf-8')
    with pytest.raises(ValueError):run.call(p,e,'direct','S1',fake=True)
    incomplete=tmp_path/'uncertain';incomplete.mkdir()
    with pytest.raises(ValueError):run.call(incomplete,e,'direct','S1',fake=True)


def test_attempt_and_incomplete_block_charges_and_caps(tmp_path):
    contract(tmp_path);assert allocation(tmp_path)['gear']==2
    freeze(tmp_path/'calls/a/REQUEST.json',dict(branch='S1'))
    freeze(tmp_path/'blocks/a/START.json',dict(reservation_seconds=630))
    assert run.budget(tmp_path)==dict(attempts=1,branches={'S1':1},charged_seconds=630)
    assert run.gate_budget(tmp_path,'S1',1800,30)=='CALL_CAP'
    assert run.gate_budget(tmp_path,'S1',1,86400)=='GPU_CAP'
    assert run.gate_budget(tmp_path,'S1',1,30,datetime(2026,9,20,13,tzinfo=timezone.utc))=='DEADLINE'
    freeze(tmp_path/'blocks/a/END.json',dict(charged_seconds=42))
    assert run.budget(tmp_path)['charged_seconds']==42


def test_literal_two_pass_rehearsal_and_completed_plan_replay(tmp_path,monkeypatch):
    contract(tmp_path);allocation(tmp_path);e=evidence()
    rows=[dict(key='known',views={'alternatives':e})];cohort={'pilot':rows}
    freeze(tmp_path/'COHORT.json',cohort)
    job=dict(id='pilot',branch='integration',partition='constructed',keys=['known'],views=['alternatives'],
        methods=['direct','review','account'],threads=4,pilot=True,pursuit='grammar',warrant='instrument',next_action='scientific reference')
    plan=dict(id='test',cohort_digest=digest(cohort),jobs=[job],next_action='reference')
    freeze(tmp_path/'PLAN.json',plan)
    first=run.execute(tmp_path,tmp_path/'PLAN.json',fake=True)
    assert first['charges']['attempts']==5
    def forbidden(*a,**kw):raise AssertionError('replay called service')
    monkeypatch.setattr(run,'api',forbidden)
    assert run.execute(tmp_path,tmp_path/'PLAN.json',fake=True)==first
    q=read(tmp_path/'calls/pilot/known/alternatives/account/1/REQUEST.json')['request']
    assert json.loads(q['messages'][1]['content'])['retained_intermediate']=={'events':[]}
