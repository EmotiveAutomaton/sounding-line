"""Admission, chronology, source identity, no-dispatch reentry and known rulers."""
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from runners.stage14 import worker,dispatcher_v2 as dispatcher,factorized,local
from runners.stage14.common import freeze,read,filehash,verify
from runners.stage14.personal_data import split_sessions
from runners.stage14.statistics import score
from runners.stage14.adaptive import proper
from runners.stage14.uncertainty import contrast
from runners.stage14.source_controls import compatible

def reply(value):return dict(done=True,done_reason='stop',message=dict(content=json.dumps(value)))

def test_new_controls_and_exact_composition():
    cases=factorized.controls();assert len(cases)==64
    assert any(f['relation']=='unrelated' for c in cases for f in c['target']['facts'])
    assert any(f['slot']=='removal' and f['operation']=='delete' for c in cases for f in c['target']['facts'])
    for c in cases:
        values={}
        for field in ['handling',*factorized.SLOTS]:
            req,labels=factorized.request(c,field,'fake')
            truth=c['target']['handling'] if field=='handling' else next(f['operation'] for f in c['target']['facts'] if f['slot']==field)
            body={l:float(l==truth) for l in labels}
            if field!='handling':body['spans']=next(f['exact_spans'] for f in c['target']['facts'] if f['slot']==field)
            values[field]=factorized.parse(reply(body),labels,len(c['event']['end_document']),field!='handling')
        result=factorized.evaluate(factorized.compose(values),c['target']);assert result['exact'] and result['half_brier']==0

@pytest.mark.parametrize('body',[{'a':.8,'b':.8},{'a':-1,'b':2},{'a':True,'b':0},{'a':float('nan'),'b':0}])
def test_literal_refusals(body):
    with pytest.raises(ValueError):factorized.parse(reply(body),['a','b'],10,False)

def test_known_scores_and_zero_mass():
    assert score([1,0,0,0],0)['half_brier']==0
    assert score([.25]*4,0)['half_brier']==.375
    assert score([1,0,0,0],1)['log_loss']=='Infinity'
    assert score([],0)['half_brier']==1
    assert proper([.2]*5,0)['half_brier']==pytest.approx(.4)

def test_missing_and_prompt_novel_splits():
    rows=[dict(timestamp=i,session=str(i),prompt=str(i)) for i in range(5)]
    result=split_sessions(rows)
    assert max(r['timestamp'] for r in result['train'])<result['calibration'][0]['timestamp']<result['evaluation'][0]['timestamp']
    rows[-1]['timestamp']=None;assert split_sessions(rows) is None
    assert split_sessions([dict(timestamp=i,session=str(i),prompt='same') for i in range(6)]) is None

def test_missing_is_not_absent():
    assert compatible({'handling':'accept'},{})
    assert compatible({'handling':'ignore'},{})
    assert not compatible({'handling':'accept'},{'handling':'ignore'})

def test_writer_resampling_not_sentence_resampling():
    rows=[dict(writer=str(w),prompt=str(w%2),scores=dict(a={'half_brier':.2},b={'half_brier':.2})) for w in range(6)]
    a=contrast(rows,'a','b',100);b=contrast(rows*10,'a','b',100)
    assert a==b and a['interval']==[0.,0.] and a['crossed_writer_prompt_interval']==[0.,0.]

def tiny_card(raw,identifier='one',requires=None,gates=None):
    c=dict(id=identifier,handler='fake',requires=requires or [],gates=gates or [],source_pins={},input_pins={},produces=['VALUE.json'],resource='cpu',wall_seconds=60)
    p=raw/'cards'/f'{identifier}.json';freeze(p,c);return p,c

def fake_module(counter):
    def run(card,out,raw,tick):counter.append(card['id']);freeze(out/'VALUE.json',dict(value=1));tick(dict(done=1))
    return SimpleNamespace(run=run)

def test_actual_worker_reentry_and_mutation(tmp_path,monkeypatch):
    p,c=tiny_card(tmp_path);counter=[]
    monkeypatch.setattr(worker.importlib,'import_module',lambda n:fake_module(counter))
    first=worker.run(p,tmp_path);assert worker.run(p,tmp_path)==first and counter==['one']
    (tmp_path/'jobs/one/VALUE.json').write_text('{}')
    with pytest.raises(ValueError):worker.run(p,tmp_path)

def test_unknown_attempt_refuses(tmp_path):
    p,c=tiny_card(tmp_path);freeze(tmp_path/'jobs/one/DISPATCH.json',dict(status='running'))
    with pytest.raises(RuntimeError,match='unknown attempt'):worker.run(p,tmp_path)

def test_failed_gate_isolated(tmp_path):
    freeze(tmp_path/'jobs/gate/ADMISSION.json',dict(admitted=False))
    assert dispatcher.disposition(dict(requires=['gate'],gates=['gate']),dict(gate='complete'),tmp_path)[0]=='blocked'
    assert dispatcher.disposition(dict(requires=[],gates=[]),dict(gate='failed'),tmp_path)[0]=='eligible'

def test_windows_preflight_uses_native_path(monkeypatch):
    monkeypatch.setattr(dispatcher.psutil,'virtual_memory',lambda:SimpleNamespace(available=20*1024**3))
    def disk(path):
        assert type(path) is str
        return SimpleNamespace(free=50*1024**3)
    monkeypatch.setattr(dispatcher.psutil,'disk_usage',disk)
    assert dispatcher.readiness(dict(resource='cpu'))[0]

def test_actual_dispatcher_and_worker(tmp_path,monkeypatch):
    p,c=tiny_card(tmp_path);plan=tmp_path/'plan.json';freeze(plan,dict(id='test',cards=['one'],card_pins={'one':filehash(p)},reporting='2099-01-01T00:00:00+00:00'))
    counter=[];monkeypatch.setattr(worker.importlib,'import_module',lambda n:fake_module(counter));monkeypatch.setattr(dispatcher,'readiness',lambda c:(True,'fixture'))
    # The real queue owns the global mutex during live validation. Isolate only
    # its OS lease/identity adapter; exercise actual dispatch and worker bodies.
    kernel=SimpleNamespace(CreateMutexW=lambda *a:1,ReleaseMutex=lambda *a:1,CloseHandle=lambda *a:1)
    monkeypatch.setattr(dispatcher.ctypes,'WinDLL',lambda *a,**k:kernel)
    monkeypatch.setattr(dispatcher.ctypes,'get_last_error',lambda:0)
    monkeypatch.setattr(dispatcher,'native_identity',lambda *a:dict(pid=123,created_ticks=1,executable='fixture'))
    monkeypatch.setattr(worker,'native_identity',lambda *a:dict(pid=123,created_ticks=1,executable='fixture'))
    class Child:
        def __init__(self,args,**kwargs):
            import os
            self.pid=os.getpid();self.returncode=0;worker.run(Path(args[-1]),tmp_path)
        def poll(self):return 0
    monkeypatch.setattr(dispatcher.subprocess,'Popen',Child);monkeypatch.setattr(dispatcher.time,'sleep',lambda t:None)
    dispatcher.run(plan,tmp_path)
    assert read(tmp_path/'queue/test/STATUS.json')['states']=={'one':'complete'} and counter==['one']
    verify(tmp_path/'jobs/one',p)

@pytest.mark.parametrize('resident,free,expected',[
    ([],7023,False),([],7024,True),
    ([dict(name='m',digest='d',context_length=8192,size=6000,size_vram=6000,expires_at='2099-01-01T00:00:00+00:00')],1024,True),
    ([dict(name='m',digest='d',context_length=8192,size=6000,size_vram=5999,expires_at='2099-01-01T00:00:00+00:00')],9000,False),
    ([dict(name='m',digest='d',context_length=4096,size=6000,size_vram=6000,expires_at='2099-01-01T00:00:00+00:00')],9000,False)])
def test_strict_resource_admission(monkeypatch,resident,free,expected):
    monkeypatch.setattr(local,'snapshot',lambda:dict(free_MiB=free,temperature_C=50))
    def api(path):return dict(models=resident) if path=='/api/ps' else dict(models=[dict(name='m',digest='d')]) if path=='/api/tags' else dict(version='fixture')
    monkeypatch.setattr(local,'api',api);assert local.ready('m','d',6000)['ready'] is expected
def test_single_writer_has_no_population_interval():
    from runners.stage14.uncertainty_v2 import contrast
    rows=[dict(writer='w',prompt='p',scores={'a':{'half_brier':.1},'b':{'half_brier':.2}})]
    result=contrast(rows,'a','b')
    assert result['interval'] is None
    assert result['disposition']=='UNRESOLVED_INSUFFICIENT_WRITERS'
    assert result['crossed_writer_prompt_interval'] is None


def test_candidate_mixture_gradient_and_heterogeneous_choices():
    import numpy as np
    from runners.stage14.choice_model import objective,packed,fit,predict
    rng=np.random.default_rng(17);cases=[]
    for i in range(96):
        x=rng.normal(size=(3,2));writer=str(i%8)
        cases.append(dict(writer=writer,x=x,truth=int(np.argmax(x[:,0]*(1 if int(writer)<4 else -1)))))
    pack=packed(cases);beta=np.array([.2,-.1]);weights=np.ones(len(cases))
    _,gradient=objective(beta,pack,weights,.01)
    fd=np.array([(objective(beta+np.eye(2)[j]*1e-5,pack,weights,.01)[0]-objective(beta-np.eye(2)[j]*1e-5,pack,weights,.01)[0])/2e-5 for j in range(2)])
    assert np.allclose(gradient,fd,atol=1e-7)
    model=fit(cases,2,.01)
    predictions=[predict(model,[c],c['writer'])[0] for c in cases]
    assert np.mean([np.argmax(p)==c['truth'] for p,c in zip(predictions,cases)])>.8
    for p in predictions:assert abs(sum(p)-1)<1e-8


def test_repaired_head_retains_missing_event_support(tmp_path,monkeypatch):
    import numpy as np
    from runners.stage14 import personal_head_v2 as m
    from runners.stage14.common import freeze,read
    source=tmp_path/'jobs'/'data';rows=[];truth=[]
    # No model is needed to exercise actual whole-consumer skip and exclusion.
    for w,parts in [('a',['train','calibration','evaluation']),('b',['train','calibration','evaluation']),('empty_cal',['train','evaluation'])]:
        for part in parts:
            key=w+part;rows.append(dict(key=key,writer=w,prompt='p',timestamp={'train':1,'calibration':2,'evaluation':3}[part],partition=part,evidence=dict(document='A.',alternatives=['one','two'])))
            truth.append(dict(key=key,handling='accept'))
    freeze(source/'READER.json',rows);freeze(source/'EVALUATOR.json',truth)
    monkeypatch.setattr(m,'fit',lambda x,y,wi,nw,penalty,personal:dict(weights=np.zeros((8,4)).tolist(),residual=np.zeros((nw,4)).tolist() if personal else None))
    out=tmp_path/'output';m.run(dict(requires=['data']),out,tmp_path,lambda p:None)
    assert read(out/'SUMMARY.json')['writers']==2
    assert any(x['writer']=='empty_cal' for x in read(out/'EXCLUSIONS.json'))



def test_complete_derived_fields_match_constructor(tmp_path):
    from runners.stage14 import derived_fields
    derived_fields.run({},tmp_path,None,lambda _:None)
    assert read(tmp_path/'SUMMARY.json')['cases']==64
    assert read(tmp_path/'ADMISSION.json')['admitted'] is True
    with pytest.raises(ValueError):
        c=factorized.controls()[0]
        from runners.stage14.compact import free
        value=free(c['target']);value['present'][0]=.5
        derived_fields.derive(value,c['event']['end_document'])


def test_generated_token_support_is_complete_or_invalid():
    import math
    from runners.stage14.option_ids import decode
    r=dict(done=True,logprobs=[dict(token='1',logprob=math.log(.3),top_logprobs=[dict(token='2',logprob=math.log(.2))])])
    value=decode(r,2)
    assert value['probabilities']==pytest.approx([.6,.4])
    assert value['legal_mass']==pytest.approx(.5)
    r['logprobs'][0]['top_logprobs']=[]
    with pytest.raises(ValueError):decode(r,2)
    with pytest.raises(ValueError):decode(dict(done=True),2)


def test_reporting_checkpoints_actual_run_and_reentry(tmp_path):
    from runners.stage14 import checkpoints
    from runners.stage14.common import freeze, filehash
    schedule={k:'2000-01-01T00:00:00+00:00' for k in ('reporting','final_review','deadline')}
    freeze(tmp_path/'CONTRACT.json',dict(schedule=schedule,source_pins={}))
    checkpoints.run(tmp_path)
    before={k:filehash(tmp_path/(k+'.json')) for k in schedule}
    checkpoints.run(tmp_path)
    assert before=={k:filehash(tmp_path/(k+'.json')) for k in schedule}
    assert read(tmp_path/'EXIT.json')['status']=='complete'
    assert read(tmp_path/'HEARTBEAT.json')['pending']=={}


def test_reporting_checkpoints_cancel_does_not_emit_future(tmp_path):
    from runners.stage14 import checkpoints
    from runners.stage14.common import freeze
    schedule={k:'2099-01-01T00:00:00+00:00' for k in ('reporting','final_review','deadline')}
    freeze(tmp_path/'CONTRACT.json',dict(schedule=schedule,source_pins={}))
    freeze(tmp_path/'CANCEL.json',dict(reason='test'))
    checkpoints.run(tmp_path)
    assert not (tmp_path/'deadline.json').exists()
    assert read(tmp_path/'EXIT.json')['reason']=='explicit cancellation'
