from pathlib import Path
import pytest
from runners.drive import week5_dispatch_v2 as d
from runners.stage14.common import atomic,filehash

def entry(base,name,priority):
    root=base/name;atomic(root/'PLAN.json',dict(card=name))
    return dict(root=str(root),priority=priority,plan_sha256=filehash(root/'PLAN.json'))

def setup(monkeypatch):
    monkeypatch.setattr(d.launcher,'review',lambda p:None)
    monkeypatch.setattr(d.policy,'admission',lambda p:None)

def test_order_and_attempt_guards(tmp_path):
    a=entry(tmp_path,'late',9);b=entry(tmp_path,'early',1)
    assert d.candidates(dict(entries=[a,b]),tmp_path)==[b,a]
    atomic(Path(b['root'])/'DISPATCH_ATTEMPT.json',{})
    assert d.candidates(dict(entries=[a,b]),tmp_path)==[a]

def test_plan_and_boundary_refusal(tmp_path):
    a=entry(tmp_path,'only',1)
    with pytest.raises(ValueError,match='Duplicate'):d.candidates(dict(entries=[a,a]),tmp_path)
    with pytest.raises(ValueError):d.candidates(dict(entries=[a]),tmp_path/'different')
    atomic(Path(a['root'])/'PLAN.json',dict(card='changed'))
    with pytest.raises(ValueError,match='changed'):d.candidates(dict(entries=[a]),tmp_path)

def test_ambiguous_launch_never_retries(tmp_path,monkeypatch):
    setup(monkeypatch);a=entry(tmp_path,'only',1);calls=[]
    def launch(root):calls.append(root);raise TimeoutError('handshake')
    monkeypatch.setattr(d.launcher,'launch',launch)
    result=d.dispatch_once(dict(entries=[a]),tmp_path)
    assert result['waiting'][0]['owner_inspection_required']
    assert not (Path(a['root'])/'ATTEMPT.claim').exists()
    assert d.dispatch_once(dict(entries=[a]),tmp_path)==dict(started=[],waiting=[])
    assert len(calls)==1

def test_capacity_wait_then_one_success(tmp_path,monkeypatch):
    setup(monkeypatch);a=entry(tmp_path,'only',1)
    def unavailable(plan):raise RuntimeError('slots occupied')
    monkeypatch.setattr(d.policy,'admission',unavailable)
    assert d.dispatch_once(dict(entries=[a]),tmp_path)['waiting']
    assert not (Path(a['root'])/'DISPATCH_ATTEMPT.json').exists()
    monkeypatch.setattr(d.policy,'admission',lambda p:None)
    monkeypatch.setattr(d.launcher,'launch',lambda root:dict(root=str(root)))
    assert len(d.dispatch_once(dict(entries=[a]),tmp_path)['started'])==1
    assert not d.dispatch_once(dict(entries=[a]),tmp_path)['started']
