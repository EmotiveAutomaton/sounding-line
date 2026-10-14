import json,time
import numpy as np
import pytest
from runners.stage14_midweek import protocol,budget,cloud,baselines

def test_probability_contract_and_half_brier_known_answers():
    good=json.dumps({'probabilities':dict.fromkeys(protocol.ACTIONS,.25),'choice':'accept'})
    assert protocol.parse(good)['probabilities']==[.25]*4
    assert baselines.proper(np.array([.25]*4),0)['half_brier']==.375
    assert baselines.proper(np.array([1.,0,0,0]),0)['half_brier']==0
    for bad in ['{}',good.replace('0.25','NaN'),good.replace('0.25','true'),good.replace('"choice": "accept"','"choice":"accept","choice":"edit"')]:assert protocol.parse(bad) is None
    p={'probabilities':dict(zip(protocol.ACTIONS,[.249,.25,.25,.25])),'choice':'accept'}
    assert abs(sum(protocol.parse(json.dumps(p))['probabilities'])-1)<1e-12

def test_cents_caps_duplicate_unknown_never_reset():
    r=dict(campaign_id=budget.CAMPAIGN,invocation='a',node='P',booked_cents=349,status='UNKNOWN')
    budget.guard([r],'P','b',1)
    for node,ident,amount in [('P','a',1),('P','b',2),('M-27','b',1401),('Reserve','b',1)]:
        with pytest.raises(ValueError):budget.guard([r],node,ident,amount)
    assert budget.cost(3300)<=350

def test_known_writer_intercept_recovers_rates_and_permutation_no_feature_signal():
    y=np.tile([0,0,0,1],30);logits=np.zeros((len(y),4))
    r=baselines.intercept_fit(logits,y,np.ones(len(y)),.001)
    p=baselines.softmax(r)
    assert p[0]>.7 and p[2]<.03
    r2=baselines.intercept_fit(logits,y[::-1],np.ones(len(y)),.001)
    np.testing.assert_allclose(r,r2,atol=1e-8)

def test_target_truth_poison_refused():
    row={'public':{'common':{'writing_prompt':'x','draft_end':'x','menu':['a'],'handling':'edit'},'history':[]}}
    with pytest.raises(ValueError):protocol.public_only(row)

def test_actual_remote_worker_archive_and_inference_free_replay(tmp_path,monkeypatch):
    class Volume:
        def reload(self):pass
        def commit(self):pass
    class Server:
        def __init__(self,*a,**k):self.ended=False
        def poll(self):return 0 if self.ended else None
        def terminate(self):self.ended=True
        def kill(self):self.ended=True
        def wait(self,**k):return 0
    calls=[]
    class Response:
        def __init__(self,value):self.value=value
        def read(self):return json.dumps(self.value).encode()
        def __enter__(self):return self
        def __exit__(self,*a):pass
    class Opener:
        def open(self,req,timeout):
            path=req.full_url.rsplit('/',1)[-1]
            if path=='version':value={'version':'0.32.14'}
            elif path=='tags':value={'models':[dict(name=cloud.MODEL,digest=cloud.MODEL_SHA)]}
            elif path=='ps':value={'models':[dict(digest=cloud.MODEL_SHA,size_vram=100,size=100,context_length=16384,details={'quantization_level':'Q4_K_M'})]}
            else:
                wire=json.loads(req.data)
                if 'prompt' in wire:
                    assert timeout==300;calls.append(wire)
                    value={'done':True,'done_reason':'stop','prompt_eval_count':20,'response':json.dumps({'probabilities':dict.fromkeys(protocol.ACTIONS,.25),'choice':'edit'})}
                else:value={'done':True}
            return Response(value)
    import subprocess,urllib.request
    monkeypatch.setattr(subprocess,'Popen',Server);monkeypatch.setattr(subprocess,'check_output',lambda *a,**k:'NVIDIA L40S, 48000 MiB, 40000 MiB')
    monkeypatch.setattr(urllib.request,'build_opener',lambda *a:Opener())
    rows=[dict(id=f'r{i}',prompt='test',input_tokens=20,maximum_output_tokens=2048) for i in range(4)]
    payload=dict(model=cloud.MODEL,model_digest=cloud.MODEL_SHA,schema=protocol.SCHEMA,phases=[dict(concurrency=1,rows=rows[:2]),dict(concurrency=2,rows=rows[2:])],call_seconds=240,http_seconds=300)
    result=cloud.remote_run(Volume(),'fixture',payload,time.time()+600,str(tmp_path))
    assert result['status']=='COMPLETE' and len(calls)==4
    from runners.stage12.cloud import restore
    restored=restore(tmp_path/result['archive_path'],tmp_path/'restored',result['archive_sha256'])
    assert all(protocol.verify_rows(restored['rows'],rows))
    assert len(calls)==4
    with pytest.raises(RuntimeError):cloud.remote_run(Volume(),'fixture',payload,time.time()+600,str(tmp_path))

def test_pilot_variance_is_only_from_discarded_serial_writers(tmp_path,monkeypatch):
    from runners.stage14.common import freeze
    from runners.stage14_midweek import cloud
    monkeypatch.setattr(cloud,'RAW',tmp_path)
    targets=[dict(key=f't{i}',writer=f'w{i}',handling='accept',pilot=True) for i in range(3)]
    targets += [dict(key='main',writer='heldout',handling='edit',pilot=False)]
    bundles=[];rows=[]
    for i in range(3):
        for arm in ('H2','H3'):
            ident=f'{i}{arm}';bundles.append(dict(id=ident,target=f't{i}',arm=arm,pilot=True))
            p=[.25]*4 if arm=='H3' else [.4,.2,.2,.2]
            text=json.dumps(dict(probabilities=dict(zip(protocol.ACTIONS,p)),choice='accept'))
            rows.append(dict(id=ident,response={'response':text}))
    rows.append(dict(id='not-a-target-c2',response={'response':'invalid duplicate must be ignored'}))
    freeze(tmp_path/'data-v2/READER.json',bundles);freeze(tmp_path/'data-v2/EVALUATOR.json',targets)
    freeze(tmp_path/'modal-pilot-v1/restored/TERMINAL.json',dict(rows=rows))
    (tmp_path/'modal-pilot-v1/OUTPUT.zip').write_bytes(b'fixture')
    p=cloud.pilot_planning()
    assert p['pilot_writers']==3 and p['main_writers']==1
    assert p['pilot_writer_sd']==pytest.approx(0.)

def test_account_limits_include_not_yet_reported_allocations():
    from runners.stage14_midweek.budget import account_headroom,CAMPAIGN
    account=dict(usage_limit_cents=4250,metered_at_check_cents=86,storage_allowance_cents=30,spend_limit_cents=1250,billed_at_check_cents=0,observed_at=10)
    pending=[dict(campaign_id=CAMPAIGN,invocation='modal-pilot-v1',ts=11,booked_cents=241)]
    assert account_headroom(account,pending)==979
    del account['spend_limit_cents']
    with pytest.raises(ValueError):account_headroom(account,pending)
