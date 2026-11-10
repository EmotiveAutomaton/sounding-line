import json
import shutil
import pytest
from runners.drive.cards import week5_ch_analysis_bounded as b
from runners.drive.cards.week5_ch_source import digest, write_json


def fake(monkeypatch):
    calls=[]
    def body(output,inputs,config):
        name=b.legacy.begin('known-squares',10)
        values=[b.legacy.value(name,i,lambda i=i: calls.append(i) or i*i) for i in range(10)]
        write_json(output/'SCIENCE.json',dict(values=values))
        return dict(status='complete')
    monkeypatch.setattr(b,'body',body)
    return calls


def copy(old,new):
    saved={p.relative_to(old).as_posix():digest(p) for p in old.rglob('*') if p.is_file()}
    shutil.copytree(old,new)
    write_json(new.parent/'RESUMED_FROM.json',dict(copied=saved))
    return saved


def test_sealed_resume_matches_uninterrupted_and_replays_zero(tmp_path,monkeypatch):
    calls=fake(monkeypatch);config=dict(card='CH2',max_new_draws=3)
    old=tmp_path/'old/output';new=tmp_path/'new/output'
    assert b.execute(old,{},config)['status']=='yielded'
    assert calls==[0,1,2]
    original=copy(old,new);calls.clear()
    done=b.execute(new,{},dict(config,max_new_draws=10))
    assert done['reused_callbacks']==3 and calls==list(range(3,10))
    calls.clear();assert b.verify(new,{},config)['recomputed_callbacks']==10
    assert calls==list(range(10))
    pilot=(new/'PILOT.json').read_bytes();science=(new/'SCIENCE.json').read_bytes()
    b.execute(new,{},config);b.verify(new,{},config)
    assert (new/'PILOT.json').read_bytes()==pilot and (new/'SCIENCE.json').read_bytes()==science
    assert original=={p.relative_to(old).as_posix():digest(p) for p in old.rglob('*') if p.is_file()}


def test_verify_honors_top_request_and_ignores_verifier_cache(tmp_path,monkeypatch):
    calls=fake(monkeypatch);config=dict(card='CH2')
    root=tmp_path/'old/output';b.execute(root,{},config)
    write_json(root/'YIELD_REQUEST.json',dict(reason='owner_cancel',at='constructed-time'))
    calls.clear();assert b.verify(root,{},config)['status']=='yielded';assert calls==[]
    new=tmp_path/'new/output';copy(root,new)
    assert b.execute(new,{},config)['sealed_output_reused']
    assert b.verify(new,{},config)['recomputed_callbacks']==10
    assert calls==list(range(10))


def test_changed_contract_or_unsealed_cache_refuses(tmp_path,monkeypatch):
    fake(monkeypatch);config=dict(card='CH2',max_new_draws=2)
    old=tmp_path/'old/output';b.execute(old,{},config)
    with pytest.raises(ValueError,match='new authenticated'):b.execute(old,{},config)
    new=tmp_path/'new/output';copy(old,new)
    with pytest.raises(ValueError,match='contract'):b.execute(new,{'changed':True},config)
    with pytest.raises(ValueError,match='loose'):b.semantic({'resume_analysis':{}},config)


def test_changed_science_and_missing_loop_refuse(tmp_path,monkeypatch):
    fake(monkeypatch);config=dict(card='CH2')
    root=tmp_path/'complete/output';b.execute(root,{},config)
    (root/'SCIENCE.json').write_text('{}')
    with pytest.raises(ValueError,match='Sealed'):b.verify(root,{},config)
    old=tmp_path/'old/output';b.execute(old,{},dict(config,max_new_draws=2))
    new=tmp_path/'new/output';copy(old,new)
    def wrong(output,inputs,config):write_json(output/'SCIENCE.json',dict(values=[]))
    monkeypatch.setattr(b,'body',wrong)
    with pytest.raises(ValueError,match='not revisited'):b.execute(new,{},config)
