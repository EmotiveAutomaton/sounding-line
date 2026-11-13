import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_resume_v5 as r, week5_policy as old_root
from runners.drive.cards import week5_policy_v3 as p
from runners.stage9 import process_identity

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')

@pytest.mark.parametrize('module', ['week5_la_back_half','week5_la_back_half_source_v2'])
def test_only_language_stopping_quantum_changes(module):
    module='runners.drive.cards.'+module
    config=dict(phase='LA4',draws=2000,seed=20261112,max_new_blocks=1)
    expected=dict(phase='LA4',draws=2000,seed=20261112)
    assert r.semantic_config(module,config)==expected
    assert r.semantic_config('unreviewed.module',config)==config
    from runners.drive.cards import week5_resume_v4
    assert week5_resume_v4.semantic_config(module,config)==config
    for value in (0,-1,True,1.5,float('inf'),float('nan')):
        with pytest.raises(ValueError):r.semantic_config(module,dict(max_new_blocks=value))

def setup_copy(tmp,monkeypatch):
    monkeypatch.setattr(old_root,'ROOT',tmp)
    monkeypatch.setattr(r,'is_same_live_process',lambda _:False)
    old,new=tmp/'old',tmp/'new'; source=tmp/'input';source.write_bytes(b'fixed')
    config=dict(phase='LA4',draws=2000,max_new_blocks=1)
    plan=dict(module='runners.drive.cards.week5_la_back_half',family='LA',campaign='S15-WEEK5',
              inputs={'source':str(source)},config=config,pins={str(source):r.filehash(source)})
    put(old/'PLAN.json',plan);put(old/'OWNER.json',dict(native={'pid':1},plan_sha256=r.filehash(old/'PLAN.json')))
    put(old/'output/block.json',dict(values=[1,2]))
    put(old/'output/independent-replay/block.json',dict(values=[1]))
    put(old/'PAUSED.json',dict(status='PAUSED',checkpoint_validation_required=True,checkpoint_outputs=r.output_manifest(old/'output')))
    plan={**plan,'config':dict(phase='LA4',draws=2000),'pins':dict(plan['pins']),
          'resume':dict(root=str(old),plan_sha256=r.filehash(old/'PLAN.json'),paused_sha256=r.filehash(old/'PAUSED.json'))}
    return old,new,plan

@pytest.mark.parametrize('defect',['draws','phase','seed','input','pin','tamper','live','ambiguous','owner','target'])
def test_unsafe_language_continuation_refuses(tmp_path,monkeypatch,defect):
    old,new,plan=setup_copy(tmp_path,monkeypatch)
    if defect in ('draws','phase','seed'):plan['config'][defect]='changed'
    if defect=='input':plan['inputs']={'source':'changed'}
    if defect=='pin':plan['pins']={}
    if defect=='tamper':put(old/'output/block.json',{'values':[9]})
    if defect=='live':monkeypatch.setattr(r,'is_same_live_process',lambda _:True)
    if defect=='ambiguous':put(old/'FAILED.json',{})
    if defect=='owner':put(old/'OWNER.json',{'native':{},'plan_sha256':'changed'})
    if defect=='target':put(new/'output/extra.json',{})
    with pytest.raises((ValueError,RuntimeError)):r.copy_checkpoint(new,plan)
    assert not (new/'RESUMED_FROM.json').exists()

def test_actual_language_handler_continuation(tmp_path,monkeypatch):
    from runners.drive.cards import week5_la_back_half as m, week5_la_back_half_fixture as f
    monkeypatch.setattr(old_root,'ROOT',tmp_path)
    monkeypatch.setattr(r,'is_same_live_process',lambda _:False)
    inputs,pins=f.join_source(tmp_path/'inputs')
    config=dict(phase='LA4',pins=pins,constructed_fixture=True,draws=32,max_new_blocks=1)
    old,new=tmp_path/'old',tmp_path/'new'
    plan=dict(module=m.__name__,inputs=inputs,config=config,family='LA',campaign='S15-WEEK5',
              pins={path:r.filehash(path) for path in inputs.values()})
    put(old/'PLAN.json',plan);put(old/'OWNER.json',dict(native={},plan_sha256=r.filehash(old/'PLAN.json')))
    assert m.execute(old/'output',inputs,config)['status']=='yielded'
    before=r.output_manifest(old/'output')
    put(old/'PAUSED.json',dict(status='PAUSED',checkpoint_validation_required=True,checkpoint_outputs=before))
    plan={**plan,'config':{k:v for k,v in config.items() if k!='max_new_blocks'},
          'resume':dict(root=str(old),plan_sha256=r.filehash(old/'PLAN.json'),paused_sha256=r.filehash(old/'PAUSED.json'))}
    receipt=r.copy_checkpoint(new,plan);assert receipt['copied']==before
    assert m.execute(new/'output',inputs,plan['config'])['complete_card']
    assert m.verify(new/'output',inputs,plan['config'])['verified']
    assert r.output_manifest(old/'output')==before

def new_plan():return dict(campaign='S15-WEEK5',family='RF',accounting_runtime='week5-v11')

def legacy(tmp,terminal=True):
    job=tmp/'legacy';put(job/'PLAN.json',dict(campaign='S15-WEEK5',family='CH',max_cpu_seconds=100))
    (job/'ATTEMPT.claim').touch()
    put(job/'OWNER.json',dict(native={'pid':123},plan_sha256=r.filehash(job/'PLAN.json')))
    if terminal:put(job/'PAUSED.json',dict(status='PAUSED',cpu_seconds=7))
    return job

def test_exact_new_ceilings_and_preserved_old_policy():
    from runners.drive.cards import week5_policy_v2 as old
    assert {k:p.FAMILY_CEILINGS[k] for k in p.NEW_FAMILIES}==dict(RF=40000,CP=60000,IS=40000,SV=60000)
    assert {k:v for k,v in p.FAMILY_CEILINGS.items() if k not in p.NEW_FAMILIES}==old.FAMILY_CEILINGS
    assert p.CEILING==old.CEILING and p.FREEZE==old.FREEZE and p.DRAIN==old.DRAIN

@pytest.mark.parametrize('defect',['live','unterminated','missing_owner','bad_binding','two_terminals','identity_denied'])
def test_transition_refuses_unleased_legacy_attempt(tmp_path,monkeypatch,defect):
    job=legacy(tmp_path,terminal=defect!='unterminated')
    monkeypatch.setattr(process_identity,'is_same_live_process',lambda _:defect=='live')
    if defect=='missing_owner':(job/'OWNER.json').unlink()
    if defect=='bad_binding':put(job/'OWNER.json',dict(native={},plan_sha256='changed'))
    if defect=='two_terminals':put(job/'FAILED.json',dict(cpu_seconds=7))
    if defect=='identity_denied':
        def denied(_):raise PermissionError('constructed identity denial')
        monkeypatch.setattr(process_identity,'is_same_live_process',denied)
    with pytest.raises((RuntimeError,PermissionError)):p.require_new_family_transition(new_plan(),tmp_path)

def test_transition_after_reconciled_exit_and_legacy_charge(tmp_path,monkeypatch):
    legacy(tmp_path);monkeypatch.setattr(process_identity,'is_same_live_process',lambda _:False)
    p.require_new_family_transition(new_plan(),tmp_path)
    assert p.charges(tmp_path)['CH']==37

def test_starting_claim_without_owner_refuses(tmp_path):
    job=legacy(tmp_path,False);(job/'OWNER.json').unlink()
    with pytest.raises(RuntimeError):p.require_new_family_transition(new_plan(),tmp_path)

def test_missing_accounting_and_runtime_binding_refuse(tmp_path):
    with pytest.raises(p.AccountingReadError):p.require_new_family_transition(new_plan(),tmp_path/'absent')
    with pytest.raises(ValueError):p.runtime_contract({'accounting_runtime':'week5-v8'})
    with pytest.raises(ValueError):p.runtime_contract({})

def test_existing_family_can_coexist(tmp_path):
    legacy(tmp_path,False)
    p.require_new_family_transition({**new_plan(),'family':'LA'},tmp_path)

def test_new_policy_keeps_denied_accounting_closed(tmp_path,monkeypatch):
    job=legacy(tmp_path);original=p.raw_read
    def denied(path):
        if Path(path).name=='PAUSED.json':raise PermissionError('constructed accounting denial')
        return original(path)
    monkeypatch.setattr(p,'raw_read',denied)
    with pytest.raises(p.AccountingReadError):p.charges(tmp_path)
