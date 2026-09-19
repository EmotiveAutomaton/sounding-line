"""Known-answer and fault fixtures; no scientific model calls."""
import copy
import itertools
import math
from pathlib import Path
import pytest
from runners.stage11_2 import world
from runners.stage11_2.common import read, freeze, charge_total, gpu_service, MAX_GPU_SECONDS
from runners.stage11_2.executable import predict_all, semantic_replay, metrics

def test_independent_policy_oracle_and_manipulations():
    for p,k,g,b in itertools.product(range(2),repeat=4):
        for family in sum(world.FAMILIES.values(),[]):
            for tools in itertools.product(range(2),repeat=2):
                actual=world.distribution(p,k,g,b,family,tools)
                assert actual==world.reference(p,k,g,b,family,tools)
                other=world.distribution(p,k,1-g,b,family,tools)
                assert actual!=other
                assert actual==world.distribution(p,k,1-g,1-b,family,tools)

def test_fixture_partition_and_exact_reentry(tmp_path):
    first=world.prepare(tmp_path)
    assert first==world.prepare(tmp_path)
    sets=[]
    for split in ('train','dev','test'):
        rows=read(tmp_path/f'{split}-public.json')
        assert len(rows)=={'train':96,'dev':64,'test':128}[split]
        assert all('action' not in q and 'preference' not in q for r in rows for q in r['queries'])
        sets.append({r['cluster'] for r in rows})
    assert not (sets[0]&sets[1] or sets[1]&sets[2] or sets[0]&sets[2])

def test_public_projection_and_private_reader_notice():
    public,truth=world.make_unit('dev',0)
    original=world.prompt(public,0)
    truth['queries'][0]['action']=99
    assert world.prompt(public,0)==original
    obs=public['queries'][1]['observation']
    before=world.enumerate_predict(public['history'],obs)
    changed=copy.deepcopy(obs);changed['reader_only_notice']='irrelevant'
    assert before==world.enumerate_predict(public['history'],changed)

def test_ambiguity_and_diagnostic_observation():
    obs=world.observe(0,0,'switch',[0,0])
    post=world.enumerate_predict([dict(observation=obs,action=0)],obs)
    assert post['weights'][0]==post['weights'][1]
    assert post['weights'][0]>post['weights'][2]
    after=world.enumerate_predict([dict(observation=world.observe(0,0,'switch',[1,0]),action=1)],obs,post['weights'])
    assert after['weights'][1]>after['weights'][0]

def test_persistent_equals_full_replay_and_donor_can_fail():
    public=[world.make_unit('dev',i)[0] for i in range(8)]
    rows=predict_all(public); assert semantic_replay(rows)==len(rows)
    paired={(r['unit'],r['encounter'],r['arm']):r for r in rows}
    for unit in public:
        for q in range(4):
            p=paired[(unit['unit'],q,'persistent')]; r=paired[(unit['unit'],q,'raw_history')]
            assert p['probabilities']==r['probabilities']
    assert any(r['probabilities']!=paired[(r['unit'],r['encounter'],'raw_history')]['probabilities'] for r in rows if r['arm']=='other_maker')
    rows[0]['probabilities'][0]+=.01
    with pytest.raises(ValueError):semantic_replay(rows)

def test_proper_score_and_invalid_denominator():
    truth=dict(action=0,probabilities=[1,0,0,0])
    assert metrics(dict(probabilities=[1,0,0,0]),truth)['log_loss']==0
    assert metrics(dict(probabilities=[.25]*4),truth)['log_loss']==math.log(4)
    assert metrics(dict(probabilities=[float('nan')]*4),truth)['valid'] is False

def test_immutable_and_reserved_failures_charge(tmp_path):
    freeze(tmp_path/'x.json',dict(a=1))
    with pytest.raises(ValueError):freeze(tmp_path/'x.json',dict(a=2))
    freeze(tmp_path/'charges/x.json',dict(reserved_seconds=MAX_GPU_SECONDS))
    assert charge_total(tmp_path)==MAX_GPU_SECONDS
    with pytest.raises(RuntimeError):
        with gpu_service(tmp_path,'must refuse',reservation=1):pass

def test_overlapping_lens_coordinates_are_not_orthogonal():
    import torch
    from runners.stage11_2.lens import coordinate_swap,donor_patch
    v=torch.tensor([[1.,1.],[0.,1.],[0.,0.]])
    h=torch.tensor([[5.,3.,7.]])  # coordinates (2,3), orthogonal remainder (0,0,7)
    actual,c,delta=coordinate_swap(h,v)
    assert torch.allclose(c,torch.tensor([[2.,3.]]),atol=1e-6)
    assert torch.allclose(actual,torch.tensor([[5.,2.,7.]]),atol=1e-6)
    assert torch.allclose(coordinate_swap(h,v,0)[0],h)
    donor=torch.tensor([[9.,5.,99.]])
    patched,*_=donor_patch(h,donor,v)
    assert torch.allclose(patched,torch.tensor([[9.,5.,7.]]),atol=2e-6)

def test_pinned_average_jacobian_against_linear_oracle():
    import torch
    from runners.stage11_2.lens import vendor
    jacobian,_=vendor()
    class Tiny:
        n_layers=2;d_model=3
        def __init__(self):
            self.layers=torch.nn.ModuleList([torch.nn.Linear(3,3,bias=False) for _ in range(2)])
            for m in self.layers:m.requires_grad_(False)
            self.layers[1].weight.copy_(torch.tensor([[1.,2.,0.],[0.,1.,1.],[2.,0.,1.]]))
        def encode(self,prompt,max_length):return torch.arange(20)[None,:]
        def forward(self,ids):
            h=ids.float().unsqueeze(-1).expand(-1,-1,3)
            for layer in self.layers:h=layer(h)
            return h
    model=Tiny();result,n,valid=jacobian(model,'synthetic',[0],dim_batch=2)
    assert n==20 and valid==3
    assert torch.allclose(result[0],model.layers[1].weight)
    assert all(len(m._forward_hooks)==0 for m in model.layers)

def test_alignment_rotation_inverse_and_selective_subspace():
    import torch
    from runners.stage11_2.alignment import interchange
    torch.manual_seed(112)
    rotation=torch.linalg.qr(torch.randn(8,8))[0]
    h=torch.randn(3,8);donor=torch.randn(3,8)
    assert torch.allclose((h@rotation)@rotation.T,h,atol=2e-6)
    q=rotation[:,:2]
    changed=interchange(h,donor,q)
    assert torch.allclose(changed@q,donor@q,atol=2e-6)
    assert torch.allclose(changed@rotation[:,2:],h@rotation[:,2:],atol=2e-6)
    assert torch.equal(interchange(h,donor,q,0),h)

def test_probability_parser_refuses_unnormalized_and_truncation():
    from runners.stage11_2.local_reader import parse
    import json
    raw=dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(probabilities=[.1,.2,.3,.4]))))
    assert parse(raw,4)==[.1,.2,.3,.4]
    raw['message']['content']=json.dumps(dict(probabilities=[.2]*4))
    with pytest.raises(ValueError):parse(raw,4)
    raw['done_reason']='length'
    with pytest.raises(ValueError):parse(raw,4)

def test_gate_requires_verdict_not_file(tmp_path):
    from runners.stage11_2.queue import gate
    job=dict(needs=[dict(path='gate.json',key='admitted',value=True)])
    assert gate(job,tmp_path).startswith('missing')
    freeze(tmp_path/'gate.json',dict(admitted=False))
    assert gate(job,tmp_path).startswith('failed')

def test_full_native_queue_fake_and_no_call_reentry(tmp_path):
    from runners.stage11_2.queue import initial_plan,run
    world.prepare(tmp_path/'fixture',dict(train=2,dev=2,test=2))
    freeze(tmp_path/'FAKE_ONLY.json',dict(fake=True))
    plan=initial_plan(tmp_path)
    first=run(tmp_path/'QUEUE-initial-v2.json',tmp_path,fake=True)
    assert all(d['status']=='complete' for d in first['dispositions'])
    calls={str(p):p.read_bytes() for p in tmp_path.rglob('calls/**/RAW.json')}
    assert len(calls)==178
    assert run(tmp_path/'QUEUE-initial-v2.json',tmp_path,fake=True)==first
    assert calls=={str(p):p.read_bytes() for p in tmp_path.rglob('calls/**/RAW.json')}
