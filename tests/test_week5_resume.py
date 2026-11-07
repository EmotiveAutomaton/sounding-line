import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_resume as r, week5_policy as p

def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')

def setup(tmp,monkeypatch):
    monkeypatch.setattr(p,'ROOT',tmp)
    monkeypatch.setattr(r,'is_same_live_process',lambda value:False)
    old=tmp/'old';new=tmp/'new'
    plan=dict(module='same',inputs={'source':'fixed'},family='MD',campaign='S15-WEEK5',
              config={'draws':2000,'max_new_draws':100},pins={})
    put(old/'PLAN.json',plan);put(old/'OWNER.json',{'native':{'pid':123}})
    put(old/'output/bootstrap.json',{'values':[1,2]})
    put(old/'output/YIELD_REQUEST.json',{'reason':'guard'})
    put(old/'PAUSED.json',dict(status='PAUSED',checkpoint_validation_required=True,
        checkpoint_outputs=r.output_manifest(old/'output')))
    nextplan={**plan,'config':{'draws':2000,'max_new_draws':2000},'resume':dict(root=str(old),
        plan_sha256=r.filehash(old/'PLAN.json'),paused_sha256=r.filehash(old/'PAUSED.json'))}
    return old,new,nextplan

def test_exact_copy_preserves_predecessor_and_omits_stop_request(tmp_path,monkeypatch):
    old,new,plan=setup(tmp_path,monkeypatch);before=r.output_manifest(old/'output')
    assert r.copy_checkpoint(new,plan)['copied']==before
    assert r.output_manifest(new/'output')==before
    assert r.output_manifest(old/'output')==before
    assert not (new/'output/YIELD_REQUEST.json').exists()

@pytest.mark.parametrize('defect',['tamper','extra','changed','live','ambiguous'])
def test_refuses_unsafe_resume(tmp_path,monkeypatch,defect):
    old,new,plan=setup(tmp_path,monkeypatch)
    if defect=='tamper':put(old/'output/bootstrap.json',{'values':[9]})
    if defect=='extra':put(old/'output/unbound.json',{})
    if defect=='changed':plan['config']['draws']=100
    if defect=='live':monkeypatch.setattr(r,'is_same_live_process',lambda value:True)
    if defect=='ambiguous':put(old/'FAILED.json',{})
    with pytest.raises(ValueError):r.copy_checkpoint(new,plan)
    assert not (new/'RESUMED_FROM.json').exists()
