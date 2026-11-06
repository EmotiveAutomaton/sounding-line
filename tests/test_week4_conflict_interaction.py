import json
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week4_conflict_interaction as s
from runners.drive.cards import week4_conflict_stats as p
from runners.drive.cards.timing_stats import sufficient


@pytest.fixture(autouse=True)
def one_thread():
    with threadpool_limits(limits=1):yield


def test_known_signed_null_main_and_donor_worlds():
    values=s.known_answers()
    assert len(values)==6
    assert values['positive']['truth']['interaction']==.3
    assert values['negative']['truth']['interaction']==-.3
    assert values['main_only']['truth']['interaction']==0


def test_history_reference_rebuilds_product_independently():
    rows,_=s.world('combined');x,y,w=s.design(rows)
    a=np.random.default_rng(np.random.SeedSequence([20261102,0,1]))
    b=np.random.default_rng(np.random.SeedSequence([20261102,0,2]))
    refs=s.references(x,y,w,a,b);shuffled=refs[0][1]
    expected=np.empty(len(x))
    for writer in sorted(set(w)):
        ix=np.flatnonzero(w==writer)
        expected[ix]=(shuffled[ix,0]-sum(shuffled[ix,0])/len(ix))*(x[ix,10]-sum(x[ix,10])/len(ix))
    assert np.allclose(shuffled[:,-1],expected,rtol=0,atol=1e-14)
    assert not np.allclose(shuffled[:,-1],x[:,-1])
    assert np.array_equal(shuffled[:,1:12],x[:,1:12])
    assert np.array_equal(refs[0][2],y) and np.array_equal(refs[1][1],x)


def test_duplicate_clusters_and_exact_parent_comparator():
    rows,_=s.world('combined');x,y,w=s.design(rows);g=sufficient(x,y,w);base=sufficient(x[:,:12],y,w)
    ids=[0,0,1,3,3,4,6,8,9,10,11,12,13,14,14,15,17,18,19,19]
    names=sorted(set(w));copies=[]
    for ordinal,i in enumerate(ids):copies.extend(dict(r,writer=f'copy{ordinal:02}') for r in rows if r['writer']==names[i])
    value=s.paired_fit([g[i] for i in ids],[base[i] for i in ids])
    dense=s.dense_coefficients(copies,value['adjusted']['variance_ratio'])
    assert np.allclose(dense,[value['adjusted']['coefficients'][n] for n in s.NAMES],atol=2e-8,rtol=0)
    assert value['original']==p.adjusted_fit([base[i] for i in ids])


def test_focal_rank_loss_refuses():
    rows,_=s.world('positive');x,y,w=s.design(rows);x[:,-1]=1
    with pytest.raises(ValueError,match='not identifiable'):s.fit(sufficient(x,y,w))
    x[:,-1]=x[:,0]
    with pytest.raises(ValueError):s.fit(sufficient(x,y,w))


def test_timing_prefix_preserves_parent_draws_and_exact_reference():
    rows,truth=s.world('combined');v=s.run(rows,blocks=1);old=p.run(rows,blocks=1)
    assert v['bootstrap_draws']==200 and v['permutation_draws']==20 and not v['complete_banks']
    assert [r['original_own'] for r in v['bootstrap_values']]==[r['adjusted_own'] for r in old['bootstrap_values']]
    assert all(abs(r['interaction']-truth['interaction'])<2e-8 for r in v['bootstrap_values'])
    x,y,w=s.design(rows)
    refs=s.references(x,y,w,np.random.default_rng(np.random.SeedSequence([20261102,0,1])),np.random.default_rng(np.random.SeedSequence([20261102,0,2])))
    for name,a,b in refs:
        assert v['reference_values'][0][name]['effect']==s.fit(sufficient(a,b,w))['coefficients'][s.NAMES[-1]]
    with pytest.raises(ValueError,match='Incomplete'):s.calibration_check(v,truth)


def test_native_handler_replay_mutation_and_configuration_refusal(tmp_path):
    cfg=s.configuration('constructed');s.execute(tmp_path,{},cfg)
    assert s.verify(tmp_path,{},cfg)['full_fresh_replay']
    path=tmp_path/'SUMMARY.json';v=json.loads(path.read_text());v['human_scored']=True;path.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='Summary replay'):s.verify(tmp_path,{},cfg)
    cfg['reference_tail']='positive'
    with pytest.raises(ValueError,match='Frozen'):s.execute(tmp_path,{},cfg)
    with pytest.raises(ValueError):s.human_rows({},True)


def test_reference_missing_draw_suppresses_probability_and_signed_symmetry():
    assert s.null_summary([None,1,-1],0)['two_sided_p'] is None
    assert s.null_summary([-2,-1,0,1,2],1)['two_sided_p']==s.null_summary([-2,-1,0,1,2],-1)['two_sided_p']==5/6
