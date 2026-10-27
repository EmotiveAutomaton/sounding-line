import copy
import json
import pytest
from runners.drive.cards import week3_tr3_candidates_recovery as first
from runners.drive.cards import week3_tr3_candidates_recovery2 as m
from tests.test_week3_tr3_candidates_recovery import fixture as prior_fixture


def fixture():
    f=prior_fixture();f['units']['a']['displays'].append(dict(ordinal=3,origin=1,reopened=True,options=[],empty_display_event=True))
    return f


def test_prior_representable_counts_identical_and_empty_reopen_adds_no_offer():
    f=prior_fixture()
    for r in f['census']['roster'][:2]:
        assert m.prepare(f['units'][r['session']],r)==first.prepare(f['units'][r['session']],r)
    f=fixture();r=f['census']['roster'][0];u=f['units']['a']
    with pytest.raises(ValueError):first.prepare(u,r)
    actual=m.prepare(u,r);u['displays'].pop();expected=first.prepare(u,r)
    expected['empty_displays']+=1;assert actual==expected


@pytest.mark.parametrize('fault',['flag','origin','order','nonempty'])
def test_invalid_empty_reopen_refused(fault):
    f=fixture();d=f['units']['a']['displays'][-1]
    if fault=='flag':d.pop('empty_display_event')
    elif fault=='origin':d['origin']=99
    elif fault=='order':d['ordinal']=2
    else:d['options']=[dict(index=0,original='changed',trimmed='changed')]
    with pytest.raises(ValueError):m.prepare(f['units']['a'],f['census']['roster'][0])


def test_every_empty_display_counted_including_empty_open_and_reopen():
    f=fixture();u=f['units']['a'];r=f['census']['roster'][0]
    for d in u['displays']:
        d['options']=[];d['empty_display_event']=True
    result=m.prepare(u,r)
    assert result['empty_displays']==3 and result['offers']==0 and result['feature_counts']=={}


def test_serialized_complete_replay_and_tamper(tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(fixture()),encoding='utf8')
    config=dict(mode='constructed',seed=20261026);inputs=dict(fixture=str(f));out=tmp_path/'output'
    result=m.execute(out,inputs,config);assert m.execute(out,inputs,config)==result
    assert m.verify(out,inputs,config)['complete_candidate_replay']
    (out/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError):m.verify(out,inputs,config)
