import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_policy_pin_migration as m, week5_resume_v6 as r
from runners.drive.cards import week5_policy as old_root

def put(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v),encoding='utf8')

def setup(tmp,monkeypatch):
    monkeypatch.setattr(m,'REPO',tmp);monkeypatch.setattr(old_root,'ROOT',tmp)
    monkeypatch.setattr(r,'is_same_live_process',lambda _:False)
    source=tmp/'source';source.write_bytes(b'fixed')
    old,new=tmp/'old',tmp/'new'
    prior=dict(module='runners.drive.cards.week5_bk_v1',family='BK',campaign='S15-WEEK5',
      inputs={'source':str(source)},config={'draws':2000,'seed':42,'max_new_fits':1},
      pins={str(source):m.filehash(source)})
    put(old/'PLAN.json',prior);put(old/'OWNER.json',dict(native={},plan_sha256=m.filehash(old/'PLAN.json')))
    put(old/'output/saved.json',{'answer':5});put(old/'output/YIELD_REQUEST.json',{'reason':'resource'})
    put(old/'PAUSED.json',dict(status='PAUSED',checkpoint_validation_required=True,checkpoint_outputs=r.output_manifest(old/'output')))
    plan={**prior,'pins':dict(prior['pins']),'config':{**prior['config'],'max_new_fits':2},
      'resume':dict(root=str(old),plan_sha256=m.filehash(old/'PLAN.json'),paused_sha256=m.filehash(old/'PAUSED.json'))}
    return old,new,plan

def test_exact_real_policy_epochs():
    q=m.qualify();assert q['admitted_families']==['AT','BK']
    pins=m.normalize({str(m.POLICY):m.OLD},'AT')
    assert pins=={str(m.POLICY.resolve()):m.CURRENT,str(m.ARCHIVE.resolve()):m.OLD}
    from runners.drive.cards import week5_policy_v2 as v2,week5_policy_v3 as v3
    assert all(v2.FAMILY_CEILINGS[k]==v3.FAMILY_CEILINGS[k] for k in ['AT','BK'])

@pytest.mark.parametrize('defect',['unknown_hash','wrong_family','missing_archive','changed_current','changed_other','alias'])
def test_policy_refusals(tmp_path,monkeypatch,defect):
    pins={str(m.POLICY):m.OLD};family='BK'
    if defect=='unknown_hash':pins[str(m.POLICY)]='0'*64
    if defect=='wrong_family':family='MD'
    if defect=='missing_archive':monkeypatch.setattr(m,'ARCHIVE',tmp_path/'missing')
    if defect=='changed_current':monkeypatch.setattr(m,'CURRENT','0'*64)
    if defect=='changed_other':pins[str(m.ARCHIVE)]='0'*64
    if defect=='alias':pins['runners/drive/cards/week5_policy_v2.py']=m.CURRENT
    with pytest.raises((ValueError,FileNotFoundError)):m.normalize(pins,family)

@pytest.mark.parametrize('defect',['tamper','extra','semantic','module','input','live','ambiguous','owner','drop_pin','source','manifest','target'])
def test_resume_refusals(tmp_path,monkeypatch,defect):
    old,new,plan=setup(tmp_path,monkeypatch)
    if defect=='tamper':put(old/'output/saved.json',{'answer':7})
    if defect=='extra':put(old/'output/extra.json',{})
    if defect=='semantic':plan['config']['draws']=3000
    if defect=='module':plan['module']='other'
    if defect=='input':plan['inputs']={}
    if defect=='live':monkeypatch.setattr(r,'is_same_live_process',lambda _:True)
    if defect=='ambiguous':put(old/'FAILED.json',{})
    if defect=='owner':put(old/'OWNER.json',dict(native={},plan_sha256='changed'))
    if defect=='drop_pin':plan['pins']={}
    if defect=='source':(tmp_path/'source').write_bytes(b'changed')
    if defect=='manifest':plan['resume']['paused_sha256']='wrong'
    if defect=='target':put(new/'output/extra.json',{})
    with pytest.raises((ValueError,RuntimeError)):r.copy_checkpoint(new,plan)
    assert not (new/'RESUMED_FROM.json').exists()

def test_unchanged_checkpoint_copy(tmp_path,monkeypatch):
    old,new,plan=setup(tmp_path,monkeypatch)
    receipt=r.copy_checkpoint(new,plan)
    assert receipt['copied']==r.output_manifest(old/'output')==r.output_manifest(new/'output')
    assert not (new/'output/YIELD_REQUEST.json').exists()

def test_at_historical_validation_keeps_source_guards():
    from runners.drive.cards import week5_at_admission_prepare_v2 as a
    values=a.pin_map({str(m.POLICY):m.OLD})
    assert values[str(m.POLICY.resolve()).casefold()]==m.CURRENT
    assert values[str(m.ARCHIVE.resolve()).casefold()]==m.OLD
    with pytest.raises(ValueError):a.pin_map({str(m.POLICY):'0'*64})
