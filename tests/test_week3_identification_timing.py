"""Whole-design timing is cost-only and preserves the shared CPU ceiling evidence."""
import json
import pytest
from runners.drive.cards import week3_identification_timing as card
from runners.drive.cards import week3_identification_crossfit as h1
from tests.test_week3_identification_crossfit import prepared_fixture
from tests.test_week3_identification import rows


def test_known_answer_full_thousand_draw_empirical_reference():
    result,detail=h1.analyze_group(rows('identity',writers=12),dict(h1.CONSTRUCTED,permutations=1000))
    assert result['x']['pass_both'] and result['x']['permutation']['attempted']==1000
    assert all(len(f['detail']['assignments'])==1000 for f in detail['folds'])


def test_cost_only_whole_design_and_fresh_verify(tmp_path):
    path=tmp_path/'fixture.json';path.write_text(json.dumps(prepared_fixture()),encoding='utf8')
    inputs=dict(fixture=str(path));out=tmp_path/'out'
    assert card.execute(out,inputs,card.CONSTRUCTED)['cost_only']
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    report=card.read(out/'FORECAST.json');work=card.read(out/'WORK.json')
    assert not report['scientific_admission'] and report['total_projected_cpu_seconds']>0
    assert set(work['work_counts'])=={'literal','independent'}
    assert not (out/'SUMMARY.json').exists() and not (out/'DETAIL.json.gz').exists()
    assert work['work_counts']['independent']['channels']==11
    data=card.read(out/'WORK.json');data['work_counts']['literal']['draws']=1
    (out/'WORK.json').write_text(json.dumps(data),encoding='utf8')
    # A changed deterministic work receipt fails before a new clock receipt write.
    with pytest.raises(ValueError):card.verify(out,inputs,card.CONSTRUCTED)
