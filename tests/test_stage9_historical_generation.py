import pytest
from runners.stage9 import historical_generation as historical
from runners.stage9.common import digest,read,write
from runners.stage9.generation_analysis import summarize
from runners.stage9.neural_operations import generation_settings
from runners.stage9.generation_policy import LEGACY


def test_actual_archived_distribution_and_reference_reproduce():
    worlds,scores,source=historical.archived_worlds()
    assert len(worlds)==len(scores)==40 and len(source['files'])==42
    assert sorted(scores)[8]==read(historical.ARCHIVE/'E04/metrics.json')['real_percentile_value']
    assert generation_settings('broad_historical')==(336,LEGACY)
    result=summarize(worlds,[{'accepted':False}]*40,scores,population='historical_replay',scope='scientific')
    assert result['expected_attempts']==40 and not result['comparison']['criterion_pass']
    with pytest.raises(ValueError,match='full assigned'):
        summarize(worlds,[{'accepted':False}]*40,scores,population='original',scope='scientific')


def test_actual_historical_preparation_preserves_role_and_refuses_tampering(tmp_path,monkeypatch):
    monkeypatch.setenv('S9_CELL_IDENTITY','d'*64)
    monkeypatch.setattr(historical,'inside',lambda p:p.resolve())
    out=tmp_path/'historical';done=historical.prepare(out,'pilot')
    cases,role,sha,plan=historical.checked_inputs(out,'pilot')
    assert len(cases)==2 and role=='pilot' and done['original_worlds']==40
    assert plan['previously_exposed'] and not plan['confirmation_eligible']
    before=digest(read(out/'COMPLETE.json'));historical.prepare(out,'pilot')
    assert digest(read(out/'COMPLETE.json'))==before
    with pytest.raises(ValueError,match='identity'):historical.checked_inputs(out,'scientific')
    plan['reference_scores'][0]+=1;write(out/'WORLD_PLAN.json',plan)
    with pytest.raises(ValueError,match='closure'):historical.checked_inputs(out,'pilot')
