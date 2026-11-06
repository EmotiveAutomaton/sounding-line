import json
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week4_conflict_spec as s
from runners.drive.cards import week4_conflict_stats as p
from runners.drive.cards.timing_stats import sufficient


@pytest.fixture(autouse=True)
def one_thread():
    with threadpool_limits(limits=1):yield


def test_known_null_signed_and_omitted_conflict_worlds():
    results=s.known_answers()
    assert len(results)==6
    targets=results['conflict_only']['targets']
    assert targets['entropy_only']['adjusted_own']==0
    assert targets['margin_only']['adjusted_own']==pytest.approx(.3)


def test_both_variants_reproduce_original_parent_comparator():
    rows,_=p.world('own_and_conflict');x,y,w=p.design(rows);groups=sufficient(x,y,w)
    for v in s.VARIANTS:
        assert s.paired_fit(groups,v)['original']==p.adjusted_fit(groups)


def test_retained_focal_rank_refuses_but_omission_is_deliberate():
    rows,_=s.world('own');x,y,w=p.design(rows)
    x[:,10]=1
    with pytest.raises(ValueError,match='Retained conflict'):s.fit_variant(sufficient(x,y,w),'entropy_only')
    value=s.fit_variant(sufficient(x,y,w),'margin_only')
    assert 'entropy' not in value['coefficients']
    x[:,0]=x[:,11]
    with pytest.raises(ValueError):s.fit_variant(sufficient(x,y,w),'margin_only')


def test_duplicate_clusters_equal_explicit_refit():
    rows,_=s.world('conflict_only');x,y,w=p.design(rows);groups=sufficient(x,y,w)
    ids=[0,0,1,3,3,4,6,8,9,10,11,12,13,14,14,15,17,18,19,19]
    names=sorted(set(w));copies=[]
    for ordinal,i in enumerate(ids):copies.extend(dict(r,writer=f'copy{ordinal}') for r in rows if r['writer']==names[i])
    for v in s.VARIANTS:
        fit=s.fit_variant([groups[i] for i in ids],v)
        dense=s.dense_coefficients(copies,v,fit['variance_ratio'])
        assert np.allclose(dense,[fit['coefficients'][p.NAMES[i]] for i in s.columns(v)],atol=2e-8,rtol=0)


def test_complete_cost_prefix_and_unchanged_streams():
    rows,targets=s.world('conflict_only')
    outputs=[s.run_variant(rows,v,blocks=1) for v in s.VARIANTS]
    for variant,value in zip(s.VARIANTS,outputs):
        assert value['bootstrap_draws']==200 and value['permutation_draws']==20
        assert value['state']=='cost_only' and not value['complete_banks']
        assert all(r['adjusted_own']==pytest.approx(targets[variant]['adjusted_own'],abs=2e-8) for r in value['bootstrap_values'])
    assert [r['original_own'] for r in outputs[0]['bootstrap_values']]==[r['original_own'] for r in outputs[1]['bootstrap_values']]
    original=p.run(rows,blocks=1)
    assert [r['original_own'] for r in outputs[0]['bootstrap_values']]==[r['adjusted_own'] for r in original['bootstrap_values']]
    with pytest.raises(ValueError,match='Incomplete'):s.calibration_check(outputs[0],targets['entropy_only'])


def test_native_replay_and_mutation_refusal(tmp_path):
    config=s.configuration('constructed');s.execute(tmp_path,{},config)
    assert s.verify(tmp_path,{},config)['full_fresh_replay']
    path=tmp_path/'SUMMARY.json';v=json.loads(path.read_text());v['human_scored']=True;path.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='Summary replay'):s.verify(tmp_path,{},config)


def test_frozen_configuration_and_dependency_refusal(tmp_path):
    config=s.configuration('constructed');config['variants'].reverse()
    with pytest.raises(ValueError,match='Frozen'):s.execute(tmp_path,{},config)
    with pytest.raises(ValueError):s.columns('best')
    with pytest.raises(ValueError):s.human_rows({},True)
