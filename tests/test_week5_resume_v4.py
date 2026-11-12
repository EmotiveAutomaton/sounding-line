import json
import pytest
from runners.drive.cards import week5_resume_v4 as r, week5_policy as p


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')


def setup(tmp, monkeypatch, module='runners.drive.cards.week5_ex1'):
    monkeypatch.setattr(p, 'ROOT', tmp)
    monkeypatch.setattr(r, 'is_same_live_process', lambda value: False)
    old, new = tmp / 'old', tmp / 'new'
    source = tmp / 'source.bin'; source.write_bytes(b'fixed source')
    plan = dict(module=module, inputs={'source':str(source)}, family='GO', campaign='S15-WEEK5',
                config={'phase':'prepare', 'max_new_documents':72},
                pins={str(source):r.filehash(source)})
    put(old / 'PLAN.json', plan)
    put(old / 'OWNER.json', {'native':{'pid':123}, 'plan_sha256':r.filehash(old / 'PLAN.json')})
    put(old / 'output/checkpoint.json', {'values':[1,2]})
    put(old / 'output/independent-replay/chunk.json', {'values':[1]})
    put(old / 'output/YIELD_REQUEST.json', {'reason':'guard'})
    put(old / 'PAUSED.json', dict(status='PAUSED', checkpoint_validation_required=True,
        checkpoint_outputs=r.output_manifest(old / 'output')))
    nextplan = {**plan, 'pins':dict(plan['pins']), 'config':{**plan['config'], 'max_new_documents':1431},
                'resume':dict(root=str(old), plan_sha256=r.filehash(old / 'PLAN.json'), paused_sha256=r.filehash(old / 'PAUSED.json'))}
    return old, new, nextplan


def test_exact_copy_and_nested_replay(tmp_path, monkeypatch):
    old, new, plan = setup(tmp_path, monkeypatch)
    before = r.output_manifest(old / 'output')
    assert r.copy_checkpoint(new, plan)['copied'] == before
    assert r.output_manifest(new / 'output') == before == r.output_manifest(old / 'output')
    assert not (new / 'output/YIELD_REQUEST.json').exists()


@pytest.mark.parametrize('defect', ['tamper','extra','semantic','module','input','live','ambiguous','owner','drop_pin','source','manifest','target'])
def test_refuses_unsafe_resume(tmp_path, monkeypatch, defect):
    old, new, plan = setup(tmp_path, monkeypatch)
    if defect == 'tamper': put(old / 'output/checkpoint.json', {'values':[9]})
    if defect == 'extra': put(old / 'output/unbound.json', {})
    if defect == 'semantic': plan['config']['phase'] = 'analyse'
    if defect == 'module': plan['module'] = 'other'
    if defect == 'input': plan['inputs'] = {'source':'other'}
    if defect == 'live': monkeypatch.setattr(r, 'is_same_live_process', lambda value:True)
    if defect == 'ambiguous': put(old / 'FAILED.json', {})
    if defect == 'owner': put(old / 'OWNER.json', {'native':{}, 'plan_sha256':'other'})
    if defect == 'drop_pin': plan['pins'] = {}
    if defect == 'source': (tmp_path / 'source.bin').write_bytes(b'changed')
    if defect == 'manifest': plan['resume']['paused_sha256'] = 'wrong'
    if defect == 'target': put(new / 'output/existing.json', {})
    with pytest.raises((ValueError, RuntimeError)): r.copy_checkpoint(new, plan)
    assert not (new / 'RESUMED_FROM.json').exists()


@pytest.mark.parametrize('module,key', [(m,k) for m, keys in r.MODULE_KEYS.items() for k in keys])
def test_only_scoped_bounds_are_operational(module,key):
    assert r.semantic_config(module, {key:10, 'fixed':1}) == {'fixed':1}
    assert r.semantic_config('unreviewed.module', {key:10}) == {key:10}
    for invalid in [0,-1,True,float('inf'),float('nan')]:
        with pytest.raises(ValueError): r.semantic_config(module, {key:invalid})


def test_draw_wall_compatibility():
    assert r.semantic_config('old', {'draws':2000,'max_new_draws':100,'max_wall_seconds':900}) == {'draws':2000}
    with pytest.raises(ValueError): r.semantic_config('old', {'max_new_draws':1.5})


def test_predecessor_adapter_stays_strict():
    from runners.drive.cards import week5_resume_v2
    assert week5_resume_v2.semantic_config('runners.drive.cards.week5_ex1', {'max_new_documents':70}) == {'max_new_documents':70}

def test_ex1_cpu_limit_is_not_operational():
    assert r.semantic_config('runners.drive.cards.week5_ex1', {'max_cpu_seconds':900}) == {'max_cpu_seconds':900}


def test_go1_predecessor_stays_strict():
    from runners.drive.cards import week5_resume_v3
    config=dict(phase='GO1-score',reader='encoder',max_new_texts=143,max_cpu_seconds=1800,distractors=49)
    assert week5_resume_v3.semantic_config('runners.drive.cards.week5_go1_two_reader',config)==config
    assert r.semantic_config('runners.drive.cards.week5_go1_two_reader',config)==dict(phase='GO1-score',reader='encoder',distractors=49)


def test_actual_go1_producer_continuation(tmp_path,monkeypatch):
    from runners.drive.cards import week5_go1_two_reader as go, week5_go1_two_reader_fixture as fixture
    from runners.drive.cards import week5_go_readers as readers
    monkeypatch.setattr(p,'ROOT',tmp_path)
    monkeypatch.setattr(r,'is_same_live_process',lambda value:False)
    monkeypatch.setattr(readers,'embeddings',fixture.vectors)
    docs=tmp_path/'docs.json';manifest=tmp_path/'manifest.json'
    put(docs,{'documents':fixture.rows()});put(manifest,{'constructed_only':True})
    inputs=dict(documents=str(docs),encoder_manifest=str(manifest))
    config=dict(phase='GO1-score',reader='encoder',distractors=49,max_new_texts=2,max_cpu_seconds=1800)
    old=tmp_path/'old';new=tmp_path/'new'
    plan=dict(module=go.MODULE,inputs=inputs,family='GO',campaign='S15-WEEK5',config=config,pins={str(docs):r.filehash(docs),str(manifest):r.filehash(manifest)})
    put(old/'PLAN.json',plan);put(old/'OWNER.json',dict(native={},plan_sha256=r.filehash(old/'PLAN.json')))
    assert go.execute(old/'output',inputs,config)['status']=='yielded'
    before=r.output_manifest(old/'output')
    put(old/'PAUSED.json',dict(status='PAUSED',checkpoint_validation_required=True,checkpoint_outputs=before))
    plan={**plan,'config':{**config,'max_new_texts':120,'max_cpu_seconds':41400},'resume':dict(root=str(old),plan_sha256=r.filehash(old/'PLAN.json'),paused_sha256=r.filehash(old/'PAUSED.json'))}
    r.copy_checkpoint(new,plan)
    result=go.execute(new/'output',inputs,plan['config']);assert result['rows']==60
    assert go.verify(new/'output',inputs,plan['config'])['verified']
    assert r.output_manifest(old/'output')==before
    for name,h in before.items():
        if name.endswith('.seal.json') or (name.startswith('vectors/') and name!='vectors/PROGRESS.json'):assert r.filehash(new/'output'/name)==h
