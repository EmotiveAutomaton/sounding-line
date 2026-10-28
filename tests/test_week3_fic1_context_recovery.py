import pytest
from runners.drive.cards import week3_fic1_context_recovery as m
from tests.test_week3_fic1_context import fixture


def source(tmp):
    fp=tmp/'fixture.json';m.freeze(fp,fixture());root=tmp/'source';root.mkdir()
    config=m.original.CONSTRUCTED;inputs=dict(fixture=str(fp))
    m.original.execute(root/'output',inputs,config);m.original.verify(root/'output',inputs,config)
    m.freeze(root/'PLAN.json',dict(module='runners.drive.cards.week3_fic1_context_timing',config=config,inputs=inputs,pins={str(fp):m.filehash(fp)}))
    m.freeze(root/'COMPLETE.json',dict(fresh_process_verified=True))
    manifest=tmp/'resume.json';m.freeze(manifest,dict(source_root=str(root),terminal_name='COMPLETE.json',
        terminal_sha256=m.filehash(root/'COMPLETE.json'),plan_sha256=m.filehash(root/'PLAN.json'),
        files={name:m.filehash(root/'output'/name) for name in m.FILES}))
    return root,dict(resume_manifest=str(manifest)),config


def test_retained_execution_is_no_compute_and_fresh_replay_reconstructs(tmp_path,monkeypatch):
    root,inputs,config=source(tmp_path);actual=m.original.context.prepare
    monkeypatch.setattr(m.original.context,'prepare',lambda *a,**k:(_ for _ in ()).throw(AssertionError('recomputed during retention')))
    out=tmp_path/'out';m.execute(out,inputs,config);m.execute(out,inputs,config)
    monkeypatch.setattr(m.original.context,'prepare',actual)
    assert m.verify(out,inputs,config)['retained_construction_freshly_replayed']
    assert all((out/n).read_bytes()==(root/'output'/n).read_bytes() for n in m.FILES)


@pytest.mark.parametrize('bad',['source','input','destination','incomplete'])
def test_changed_evidence_refused(tmp_path,bad):
    root,inputs,config=source(tmp_path);out=tmp_path/'out'
    if bad=='source':(root/'output/CONTEXT.json').write_bytes(b'{}')
    elif bad=='input':(tmp_path/'fixture.json').write_bytes(b'{}')
    elif bad=='destination':out.mkdir();(out/'CONTEXT.json').write_bytes(b'{}')
    else:
        p=tmp_path/'resume.json';v=m.read(p);v['files'].pop('SUMMARY.json');p.write_text(__import__('json').dumps(v))
    with pytest.raises(ValueError):m.execute(out,inputs,config)


def test_full_configuration_cannot_use_constructed_source(tmp_path):
    root,inputs,config=source(tmp_path)
    with pytest.raises(ValueError,match='configuration'):m.execute(tmp_path/'out',inputs,m.original.CONFIG)
