import json
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week4_conflict_fixed as f
from runners.drive.cards import week4_conflict_stats as p
from runners.drive.cards.timing_stats import sufficient


@pytest.fixture(autouse=True)
def one_thread():
    with threadpool_limits(limits=1):yield


def test_all_known_worlds_and_dense_dummies():
    assert len(f.known_answers())==6


def test_writer_offsets_do_not_change_slopes():
    rows,_=p.world('own_and_conflict');x,y,w=p.design(rows)
    original=f.fixed_fit(sufficient(x,y,w))
    changed=y+np.array([int(name[1:])*2 for name in w])
    other=f.fixed_fit(sufficient(x,changed,w))
    for k,v in original['coefficients'].items():assert other['coefficients'][k]==pytest.approx(v,abs=2e-8)


def test_duplicated_writer_resample_matches_explicit_refit():
    rows,_=p.world('own');x,y,w=p.design(rows);groups=sufficient(x,y,w)
    ids=[0,0,1,4,6,8,8,9,10,13,13,14,15,16,16,17,18,19,19,19]
    fitted=f.fixed_fit([groups[i] for i in ids]);names=sorted(set(w));copies=[]
    for ordinal,i in enumerate(ids):copies.extend(dict(r,writer=f'copy{ordinal}') for r in rows if r['writer']==names[i])
    dense=f.dense_coefficients(copies)
    for k,v in fitted['coefficients'].items():assert dense[k]==pytest.approx(v,abs=2e-8)


def test_constant_and_collinear_focal_terms_refuse():
    rows,_=p.world('own');x,y,w=p.design(rows)
    for index in (0,10,11):
        changed=x.copy();changed[:,index]=1.
        with pytest.raises(ValueError):f.fixed_fit(sufficient(changed,y,w))
    changed=x.copy();changed[:,10]=changed[:,0]
    with pytest.raises(ValueError):f.fixed_fit(sufficient(changed,y,w))


def test_paired_comparator_is_original_full_conflict_model():
    rows,_=p.world('conflict_only');x,y,w=p.design(rows);groups=sufficient(x,y,w)
    result=f.paired_fit(groups,[])
    assert result['original']==p.adjusted_fit(groups)
    assert result['adjusted_own']==pytest.approx(0,abs=2e-8)


def test_native_complete_replay_and_tamper_refusal(tmp_path):
    config=f.configuration('constructed');f.execute(tmp_path,{},config)
    assert f.verify(tmp_path,{},config)['full_fresh_replay']
    path=tmp_path/'SUMMARY.json';record=json.loads(path.read_text());record['native_known_answers']=False
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='summary differs'):f.verify(tmp_path,{},config)


def test_cost_bank_complete_prefix_and_configuration_refusal():
    rows,_=p.world('reverse');value=f.run(rows,blocks=1)
    assert value['state']=='cost_only' and value['bootstrap_draws']==200 and value['permutation_draws']==20
    assert value['point']['adjusted_own']==pytest.approx(-.4,abs=2e-8)
    assert all(r['adjusted_own']==pytest.approx(-.4,abs=2e-8) for r in value['bootstrap_values'])
    with pytest.raises(ValueError):f.run(rows,blocks=2)
    with pytest.raises(ValueError):f.human_rows({},True)
