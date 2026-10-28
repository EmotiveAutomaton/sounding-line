import copy
import runpy
from pathlib import Path
import pytest
from runners.drive.cards import week3_fic1_galleries_recovery as m
from runners.stage14.common import atomic
from runners.drive.cards.timing_p6 import gzip_equal


def fixture():return runpy.run_path(str(Path(__file__).with_name('test_week3_fic1_galleries.py')))['fixture']()


def sealed_sources(tmp_path):
    f=fixture();p=tmp_path/'prefix';c=tmp_path/'feature'
    for root in (p,c):(root/'output').mkdir(parents=True)
    m.freeze(c/'PLAN.json',dict(module='runners.drive.cards.week3_fic1_features',config=m.base.features.CONFIG))
    m.freeze(p/'PLAN.json',dict(module='runners.drive.cards.week3_fic1_prefixes',config=m.base.prefixes_source.CONFIG,inputs=dict(feature_completion=str(c/'COMPLETE.json'))))
    m.freeze(p/'output/SUMMARY.json',dict(exact_occurrence_replay=True,identification_computed=False))
    for root in (p,c):
        m.freeze(root/'output/DICTIONARY.json',f['dictionary'])
        m.freeze(root/'output/PROFILES.json',f['profiles'] if root==p else list(reversed(f['profiles'])))
    m.freeze(p/'output/PREFIX_FEATURES.json',f['prefixes']);index=[]
    for i,row in enumerate(f['rows']):
        rel=f'sessions/{i}.json.gz';path=c/'output'/rel;gzip_equal(path,row)
        index.append(dict(session=row['session'],file=rel,sha256=m.filehash(path)))
    m.freeze(c/'output/SESSION_INDEX.json',index)
    for root in (p,c):seal(root)
    return dict(prefix_completion=str(p/'COMPLETE.json'),feature_completion=str(c/'COMPLETE.json')),f


def seal(root):
    atomic(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():m.filehash(p) for p in root.rglob('*') if p.is_file() and p.name!='COMPLETE.json'}))


def test_actual_loader_accepts_only_order_difference_and_original_refuses(tmp_path):
    inputs,f=sealed_sources(tmp_path)
    with pytest.raises(ValueError,match='memberships differ'):m.base.load(inputs,m.CONFIG)
    data,_=m.load(inputs,m.CONFIG)
    assert data==f
    assert m.base.prepare(data,m.CONSTRUCTED)==m.base.prepare(f,m.CONSTRUCTED)


@pytest.mark.parametrize('bad',['duplicate','missing','field','session_order','seal','lineage','dictionary'])
def test_loader_preserves_seals_and_full_keyed_record_checks(tmp_path,bad):
    inputs,_=sealed_sources(tmp_path);root=Path(inputs['feature_completion']).parent
    path=root/'output/PROFILES.json';data=m.read(path)
    if bad=='duplicate':data.append(copy.deepcopy(data[0]))
    elif bad=='missing':data.pop()
    elif bad=='field':data[0]['full_typed_words']+=1
    elif bad=='session_order':data[0]['sessions'].reverse()
    elif bad=='dictionary':path=root/'output/DICTIONARY.json';data=m.read(path);data['words'].reverse()
    elif bad=='lineage':
        root=Path(inputs['prefix_completion']).parent;path=root/'PLAN.json';data=m.read(path);data['inputs']['feature_completion']='wrong'
    else:data[0]['full_typed_words']+=1
    atomic(path,data)
    if bad!='seal':seal(root)
    with pytest.raises(ValueError):m.load(inputs,m.CONFIG)


def test_unchanged_numerics_native_handler_reentry_and_replay(tmp_path):
    f=tmp_path/'fixture.json';m.freeze(f,fixture());inputs=dict(fixture=str(f))
    old=tmp_path/'old';new=tmp_path/'new'
    m.base.execute(old,inputs,m.CONSTRUCTED);m.execute(new,inputs,m.CONSTRUCTED)
    assert all((new/p.name).read_bytes()==p.read_bytes() for p in old.iterdir())
    assert m.verify(new,inputs,m.CONSTRUCTED)['all_galleries_recomputed']
    m.execute(new,inputs,m.CONSTRUCTED)
    assert all((new/p.name).read_bytes()==p.read_bytes() for p in old.iterdir())
