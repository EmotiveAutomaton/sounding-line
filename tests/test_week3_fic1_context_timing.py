import pytest
from runners.drive.cards import week3_fic1_context_timing as m
from tests.test_week3_fic1_context import fixture


def test_complete_timing_handler_replays_and_reentry_is_immutable(tmp_path):
    fp=tmp_path/'fixture.json';m.freeze(fp,fixture());inputs=dict(fixture=str(fp));out=tmp_path/'output'
    m.execute(out,inputs,m.CONSTRUCTED)
    assert m.verify(out,inputs,m.CONSTRUCTED)['all_inputs_replayed']
    hashes={p.name:m.filehash(p) for p in out.iterdir() if p.name!='PROGRESS.json'}
    m.execute(out,inputs,m.CONSTRUCTED)
    assert hashes=={p.name:m.filehash(p) for p in out.iterdir() if p.name!='PROGRESS.json'}
    assert not m.read(out/'SUMMARY.json')['identification_computed']
    m.atomic(out/'CONTEXT.json',{})
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONSTRUCTED)


def test_population_gap_refused_before_preparation(tmp_path):
    f=fixture();f['units'].pop();fp=tmp_path/'fixture.json';m.freeze(fp,f)
    with pytest.raises(ValueError,match='complete original population'):
        m.execute(tmp_path/'out',dict(fixture=str(fp)),m.CONSTRUCTED)


def test_full_path_requires_sealed_predecessors(tmp_path):
    with pytest.raises(ValueError):m.execute(tmp_path,dict(fixture='unused'),m.CONFIG)


def test_changed_configuration_refused(tmp_path):
    with pytest.raises(ValueError,match='fixed context timing'):
        m.execute(tmp_path,{},dict(m.CONSTRUCTED,writers=3))
