import pytest
from runners.stage9 import generation_cases as cases
from runners.stage9.common import digest,read,write
from runners.stage9.recipes import parameter_partition


def first(domain,population,sample):
    for index in range(100):
        row=cases.make_attempt(index,domain,'pilot',population,sample)
        if row['selected']:return row
    raise AssertionError('actual discarded population not realized')


def test_actual_original_and_expanded_sources_replay_and_keep_partition():
    for domain in ('essay','workshop_doc'):
        for population in ('original','expanded'):
            reader=first(domain,population,'reader');reference=first(domain,population,'reference')
            assert parameter_partition(reader['world'])=='training'
            assert reader['content_sha256']!=reference['content_sha256']
            if population=='original':assert not reader['world']['trajectory']['changes']


def test_real_preparation_roundtrip_and_changed_reference_refusal(tmp_path,monkeypatch):
    monkeypatch.setenv('S9_CELL_IDENTITY','c'*64)
    monkeypatch.setattr(cases,'inside',lambda p:p.resolve())
    root=tmp_path/'source';done=cases.prepare(root,role='pilot',population='expanded')
    selected,role,sha,plan=cases.checked_inputs(root,'pilot','expanded')
    assert role=='pilot' and len(selected)==done['reader_worlds']==2 and done['reference_worlds']==2
    assert len(plan['reference_scores'])==2 and done['distinct_source_worlds']==4
    with pytest.raises(ValueError,match='borrow pilot'):cases.checked_inputs(root,'scientific','expanded')
    before=digest(read(root/'COMPLETE.json'));cases.prepare(root,role='pilot',population='expanded')
    assert digest(read(root/'COMPLETE.json'))==before
    plan['reference_scores'][0]+=1.;write(root/'WORLD_PLAN.json',plan)
    with pytest.raises(ValueError,match='closure differs'):cases.checked_inputs(root,'pilot','expanded')
