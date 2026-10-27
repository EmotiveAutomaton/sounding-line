import copy
import json
import pytest
from runners.stage9.coauthor import suggestions
from runners.drive.cards import week3_tr3_candidates as original
from runners.drive.cards import week3_tr3_candidates_recovery as m
from tests.test_week3_tr3_candidates import fixture as text_fixture


def fixture():
    f=text_fixture()
    for u in f['units'].values():
        for d in u['displays']:
            # Exercise the canonical producer, not a second invented schema.
            d['options']=suggestions([dict(index=i+5,original=' '+t,trimmed=t) for i,t in enumerate(d['options'])]) if d['options'] else []
    return f


def test_canonical_counts_exactly_match_equivalent_display_text():
    f=fixture();old=text_fixture()
    for r in f['census']['roster'][:2]:
        assert m.prepare(f['units'][r['session']],r)==original.prepare(old['units'][r['session']],r)
    assert f['units']['a']['displays'][0]['options'][0]['original'].startswith(' ')


@pytest.mark.parametrize('fault',['original','index','missing','duplicate-index','plain-text'])
def test_canonical_schema_and_reopen_metadata_refuse(fault):
    f=copy.deepcopy(fixture());u=f['units']['a'];options=u['displays'][1]['options']
    if fault=='original':options[0]['original']='different metadata'
    elif fault=='index':options[0]['index']=80
    elif fault=='missing':options[0].pop('trimmed')
    elif fault=='duplicate-index':options[1]['index']=options[0]['index']
    else:u['displays'][0]['options']=['wrong schema']
    with pytest.raises(ValueError):m.prepare(u,f['census']['roster'][0])


def test_complete_recovery_serialization_and_tamper(tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(fixture()),encoding='utf8')
    config=dict(mode='constructed',seed=20261026);inputs=dict(fixture=str(f));out=tmp_path/'output'
    result=m.execute(out,inputs,config);assert m.execute(out,inputs,config)==result
    assert m.verify(out,inputs,config)['complete_candidate_replay']
    assert original.prepare is m._original_prepare
    (out/'CANDIDATES.json').write_text('{}')
    with pytest.raises(ValueError):m.verify(out,inputs,config)
    assert original.prepare is m._original_prepare
