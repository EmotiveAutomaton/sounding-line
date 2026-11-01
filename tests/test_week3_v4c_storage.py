import lzma
from pathlib import Path
from contextlib import ExitStack
import pytest
from runners.stage14.common import filehash,freeze
from runners.drive.cards import week3_v4c_storage as s,week3_v4c_mc_compressed as m,week3_v4c_storage_fixture as f


def test_bytes_digest_and_immutability(tmp_path):
    p=tmp_path/'worlds/a/null-000.json';data=b'{"x":-0.0,"y":1.2345678901234567}\n'
    s.retain_bytes(p,data);assert s.raw(p)==data
    plain=tmp_path/'plain';plain.write_bytes(data);assert s.logical_hash(p)==filehash(plain)
    s.retain_bytes(p,data)
    with pytest.raises(ValueError,match='Immutable'):s.retain_bytes(p,data+b' ')
    p.write_bytes(data)
    with pytest.raises(ValueError,match='Ambiguous'):s.raw(p)


def test_corruption_missing_and_wrong_path_refuse(tmp_path):
    p=tmp_path/'worlds/a/null-000.json';p.parent.mkdir(parents=True);Path(str(p)+'.xz').write_bytes(b'bad')
    with pytest.raises(lzma.LZMAError):s.raw(p)
    with pytest.raises(FileNotFoundError):s.raw(tmp_path/'worlds/a/null-001.json')
    with pytest.raises(ValueError,match='Only'):s.retain_bytes(tmp_path/'SUMMARY.json',b'{}')


def test_actual_orchestration_parity_and_fresh_replay(tmp_path):
    before=m.original.read,m.original.freeze,m.original.filehash
    assert f.execute(tmp_path,{},dict(references=199))['logical_parity']
    assert f.verify(tmp_path,{},dict(references=199))['full_199_reference_replay']
    assert before==(m.original.read,m.original.freeze,m.original.filehash)
    with pytest.raises(RuntimeError),m.lossless_io():raise RuntimeError('restore on failure')
    assert before==(m.original.read,m.original.freeze,m.original.filehash)


def test_tampered_seal_and_storage_binding_refuse(tmp_path):
    f.execute(tmp_path,{},dict(references=199));root=tmp_path/'packed'
    target=next(root.glob('worlds/*/null-000.json.xz'));target.write_bytes(lzma.compress(b'{}'))
    with ExitStack() as stack:
        ins,cfg=f.setup(tmp_path,stack,[])
        with pytest.raises(ValueError,match='seal'):m.execute(root,ins,cfg)
    (root/'STORAGE_BINDING.json').write_text('{}')
    with pytest.raises(ValueError,match='binding'):m.verify(root,{},m.CONFIG)


def test_pause_has_no_complete_summary(tmp_path):
    with ExitStack() as stack:
        ins,cfg=f.setup(tmp_path,stack,[]);out=tmp_path/'paused';freeze(out/'YIELD_REQUEST.json',{})
        assert m.execute(out,ins,cfg)['status']=='yielded'
        assert not (out/'SUMMARY.json').exists()


def test_compressed_collector_physical_binding_and_completeness(tmp_path,monkeypatch):
    from runners.drive.cards import week3_v4c_mc_collect_compressed as c
    from runners.stage14.common import read
    cells=m.source.roster()[:4]
    monkeypatch.setattr(m.source,'roster',lambda:cells)
    monkeypatch.setattr(m,'full_summary',lambda ws:{'ordered': [w['cell'] for w in ws]})
    inputs={}
    for i,cell in enumerate(cells):
        root=tmp_path/str(i);out=root/'output';base=out/'worlds'/m.source.world_name(cell)
        cfg=dict(m.CONFIG,shard_index=i);w=dict(cell=cell,reference_count=199,probability=1.,detected=False)
        freeze(root/'PLAN.json',dict(module=m.__name__,config=cfg,inputs={'source':'same'}))
        freeze(root/'VERIFIED.json',dict(full_fresh_generation_and_refit=True))
        freeze(out/'STORAGE_BINDING.json',m.storage_binding());freeze(out/'BINDING.json',dict(code={'core':'same'}))
        freeze(out/'SUMMARY.json',dict(config=cfg,worlds=[w]));freeze(base/'RESULT.json',w);freeze(base/'OBSERVED.json',dict(likelihood_ratio=0.))
        for j in range(199):s.freeze(base/f'null-{j:03d}.json',dict(statistic={'likelihood_ratio':0.}))
        freeze(out/'XZ_MANIFEST.json',m.physical_manifest(out))
        outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*.json')}
        freeze(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs=outputs));inputs[f'shard{i}']=str(root/'COMPLETE.json')
    assert c.gather(inputs,c.CONFIG)['summary']['ordered']==cells
    with pytest.raises(ValueError,match='four'):c.gather({k:v for k,v in inputs.items() if k!='shard3'},c.CONFIG)
    target=next((tmp_path/'0/output').rglob('*.xz'));target.write_bytes(b'bad')
    with pytest.raises(ValueError,match='manifest'):c.gather(inputs,c.CONFIG)


def test_migration_authenticates_prefix_and_reuses_exact_bytes(tmp_path,monkeypatch):
    import json
    from runners.stage14.common import read
    f.execute(tmp_path,{},dict(references=199))
    oldroot=tmp_path/'old';source=tmp_path/'plain';source.rename(oldroot/'output') if oldroot.exists() else None
    oldroot.mkdir(exist_ok=True)
    if source.exists():source.rename(oldroot/'output')
    monkeypatch.setattr(m.checkpoints,'native_identity',lambda pid:None)
    with ExitStack() as stack:
        ins,cfg=f.setup(tmp_path,stack,[])
        freeze(oldroot/'PLAN.json',dict(module=m.original.__name__,config=cfg,inputs=ins,pins={}))
        freeze(oldroot/'PAUSED.json',dict(status='PAUSED'))
        for name in ('OWNER.json','EXECUTE_NATIVE.json'):freeze(oldroot/name,dict(native={'pid':999999}))
        out=tmp_path/'retained';r=m.checkpoints.retain_prefix(oldroot,out,ins,cfg)
        assert r['retained_references']==199 and r['unsealed_old_references_not_admitted']==0
        for p in (oldroot/'output').glob('worlds/*/null-???.json'):assert s.raw(out/p.relative_to(oldroot/'output'))==p.read_bytes()
        assert m.execute(out,ins,cfg)['status']=='complete'
        p=next((oldroot/'output').glob('worlds/*/null-000.json.seal.json'));v=read(p);v['sha256']='0'*64;p.write_text(json.dumps(v))
        with pytest.raises(ValueError,match='seal'):m.checkpoints.retain_prefix(oldroot,tmp_path/'bad',ins,cfg)
