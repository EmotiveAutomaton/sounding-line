import json, struct
from pathlib import Path
import pytest
from runners.drive.cards import week5_at_memory_r1 as rules
from runners.drive.cards import week5_at_scoring_guard_r1 as runner

G=2**30


def put(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')
    return rules.filehash(path)


def example(tmp_path):
    weights=tmp_path/'model.safetensors'
    head=json.dumps({'weight':{'shape':[2,10],'dtype':'F32','data_offsets':[0,80]}}).encode()
    weights.write_bytes(struct.pack('<Q',len(head))+head+bytes(80))
    manifest=tmp_path/'MANIFEST.json'
    put(manifest,dict(model='constructed',files={str(weights):rules.filehash(weights)}))
    profile=tmp_path/'PROFILE.json'
    put(profile,dict(schema='AT-R1-memory-v1',model_manifest_sha256=rules.filehash(manifest),
        condition=dict(context='final',context_length=1024),completed_guard_receipts=[]))
    return weights,manifest,profile


def add_completed(tmp_path, manifest, profile):
    root=tmp_path/'completed';guard=root/'output/GUARD_EXECUTE_1.json'
    put(guard,dict(status='returned',phase='execute',identity=dict(pid=1,creation_time=1,executable='constructed'),
                   peak_working_set_bytes=4*G,peak_private_commit_bytes=8*G))
    plan=root/'PLAN.json'
    put(plan,dict(inputs=dict(model_manifest=str(manifest)),config=dict(context='final',context_length=1024)))
    done=root/'COMPLETE.json'
    put(done,dict(status='COMPLETE',fresh_process_verified=True,outputs={'PLAN.json':rules.filehash(plan),'output/'+guard.name:rules.filehash(guard)}))
    value=rules.read(profile)
    value['completed_guard_receipts']=[dict(root=str(root),complete_sha256=rules.filehash(done),guard_relative='output/'+guard.name)]
    put(profile,value)
    return root,guard,done


def test_exact_memory_envelopes_and_floor():
    value=rules.envelope(4*G,[8.01*G],[19*G])
    assert value['declared_peak_bytes']==10.5*G
    assert value['limits']['start_commit_bytes']==17.5*G
    assert value['limits']['start_ram_bytes']==18.5*G
    assert rules.envelope(4*G,[],[8.01*G])['declared_peak_bytes']==12.5*G
    unseen=rules.envelope(12*G)
    assert unseen['declared_peak_bytes']==30*G
    assert unseen['limits']['start_commit_bytes']==36*G
    assert rules.envelope(8*G,legacy_start_GiB=26)['limits']['start_commit_bytes']==26*G
    assert rules.envelope(8*G,legacy_start_GiB=28)['limits']['start_commit_bytes']==27*G


@pytest.mark.parametrize('bad',[True,0,-1,float('nan'),float('inf')])
def test_invalid_quantities_refuse(bad):
    with pytest.raises(ValueError):rules.envelope(bad)
    with pytest.raises(ValueError):rules.envelope(G,[bad])


def test_headers_and_completed_peak_provenance(tmp_path):
    weights,manifest,profile=example(tmp_path)
    assert rules.weight_bytes(rules.read(manifest))==160
    assert rules.profile(profile,manifest,{})['basis']=='unobserved_float64_weights'
    add_completed(tmp_path,manifest,profile)
    value=rules.profile(profile,manifest,{})
    assert value['basis']=='completed_private_commit' and value['declared_peak_bytes']==10*G
    weights.write_bytes(b'changed')
    with pytest.raises(ValueError,match='weight bytes'):rules.profile(profile,manifest,{})


def test_partial_or_changed_native_receipts_refuse(tmp_path):
    _,manifest,profile=example(tmp_path);root,guard,done=add_completed(tmp_path,manifest,profile)
    guard.write_text('{}')
    with pytest.raises(ValueError,match='not sealed'):rules.profile(profile,manifest,{})
    add_completed(tmp_path,manifest,profile)
    terminal=rules.read(done);terminal['status']='PAUSED';put(done,terminal)
    p=rules.read(profile);p['completed_guard_receipts'][0]['complete_sha256']=rules.filehash(done);put(profile,p)
    with pytest.raises(ValueError,match='Partial chunk'):rules.profile(profile,manifest,{})


def test_condition_and_manifest_refuse(tmp_path):
    _,manifest,profile=example(tmp_path)
    with pytest.raises(ValueError,match='condition differs'):rules.profile(profile,manifest,{'context_length':256})
    put(manifest,dict(model='different',files={}))
    with pytest.raises(ValueError,match='model binding'):rules.profile(profile,manifest,{})


def test_original_largest_reader_gate_is_pythia(tmp_path,monkeypatch):
    _,manifest,profile=example(tmp_path)
    monkeypatch.setattr(rules,'weight_bytes',lambda m:8*G)
    for model,expected in [('EleutherAI/pythia-1.4b-deduped',27*G),('gpt2-large',26*G)]:
        m=rules.read(manifest);m['model']=model;put(manifest,m)
        p=rules.read(profile);p['model_manifest_sha256']=rules.filehash(manifest);put(profile,p)
        assert rules.profile(profile,manifest,{})['limits']['start_commit_bytes']==expected


def test_refusal_before_invoke_and_native_peak_record(tmp_path,monkeypatch):
    profile=rules.envelope(G,[8*G])
    monkeypatch.setattr(rules,'profile',lambda *a:profile)
    called=[]
    monkeypatch.setattr(runner,'invoke',lambda *a:called.append(1))
    monkeypatch.setattr(runner,'memory',lambda:dict(commit_headroom_bytes=profile['limits']['start_commit_bytes']-1,ram_available_bytes=100*G))
    result=runner.execute(tmp_path,dict(rows='unused',model_manifest='unused',memory_profile='unused'),{})
    assert result['model_loads']==0 and not called
    receipt=rules.read(next(tmp_path.glob('GUARD_*.json')))
    assert receipt['peak_private_commit_bytes']>0 and receipt['peak_working_set_bytes']>0
    assert receipt['status']=='refused_before_model_load'


def test_admitted_wrapper_preserves_result_and_hard_boundaries(tmp_path,monkeypatch):
    profile=rules.envelope(G,[8*G]);limits=profile['limits']
    monkeypatch.setattr(rules,'profile',lambda *a:profile)
    monkeypatch.setattr(runner,'memory',lambda:dict(commit_headroom_bytes=100*G,ram_available_bytes=100*G))
    result={'status':'complete','constructed':True}
    monkeypatch.setattr(runner,'invoke',lambda *a:result)
    assert runner.execute(tmp_path,dict(rows='unused',model_manifest='unused',memory_profile='unused'),{})==result
    receipt=rules.read(next(tmp_path.glob('GUARD_*.json')))
    assert receipt['status']=='returned' and receipt['limits']==limits
    from types import FunctionType
    base=runner.guard.action
    action=FunctionType(base.__code__,dict(base.__globals__,LIMITS=limits),base.__name__,base.__defaults__)
    assert action(dict(commit_headroom_bytes=7*G-1,ram_available_bytes=9*G))=='request_yield'
    assert action(dict(commit_headroom_bytes=6*G-1,ram_available_bytes=9*G))=='terminate'
    assert action(dict(commit_headroom_bytes=9*G,ram_available_bytes=6*G-1))=='terminate'
    assert action(dict(commit_headroom_bytes=9*G,ram_available_bytes=9*G),60)=='terminate'
