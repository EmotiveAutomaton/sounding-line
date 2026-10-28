import copy
import numpy as np
import pytest
from scipy.stats import spearmanr
from runners.drive.cards import week3_tr4_comparison as c


def fixture(pattern='uniform',writers=6,sessions=24):
    rows=[]; split={}
    for w in range(writers):
        writer=str(w); split[writer]='discovery' if w<2 else 'test'
        for j in range(sessions):
            x=[250]*4 if pattern=='uniform' or j<sessions//2 else [850,50,50,50]
            rows.append(dict(writer=writer,session=f'{w}-{j}',prompt=str(j%2),half=split[writer],
                             start=j*3,end=j*3+1,counts=dict(zip(c.CLASSES,x))))
    return dict(rows=rows,split=dict(seed=c.SEED,writers=split,session_counts={w:sessions for w in split}))


def test_complete_uniform_pipeline_has_exact_zero_and_undefined_reliability():
    r,_=c.run_analysis(fixture(),3,4,20)
    p=r['primary']
    assert p['estimate']==0 and p['reference']['mean']==0 and p['reference_biased'] is False
    assert p['bootstrap']['interval']==[0,0] and p['probability']==1
    assert p['status']=='not_detected_sensitivity_unestablished'
    assert r['reliability']['real'] is None and r['reliability']['reference']['undefined']==4
    assert r['reliability']['paired_bootstrap']['undefined']==20
    assert r['counts']['all_sessions']==144 and len(r['retained'])==144


def test_complete_change_pipeline_tracks_but_does_not_bypass_bias():
    r,_=c.run_analysis(fixture('change'),3,4,20)
    assert r['primary']['estimate']>.05
    if r['primary']['reference_biased']: assert r['primary']['status']=='descriptive_only_biased_reference'
    assert r['counts']['scoreable_test_sessions']==32


def test_ambiguous_prefix_is_retained_and_invalidates_subsequent_targets():
    x=fixture(); x['rows'][24*2+5]['end']=x['rows'][24*2+6]['start']
    groups,rows=c.prepare(x); g=next(g for g in groups if g['writer']=='2')
    assert not g['mask'].any() and not g['reliability']
    assert len(rows)==144 and sum(r['writer']=='2' and r['reason']=='ambiguous_prefix' for r in rows)==18


@pytest.mark.parametrize('defect',['duplicate','split','counts','interval','census'])
def test_input_contract_refuses_corruption(defect):
    f=fixture();r=f['rows'][0]
    if defect=='duplicate': f['rows'].append(copy.deepcopy(r))
    if defect=='split': r['half']='test'
    if defect=='counts': r['counts']['accept']=-1
    if defect=='interval': r['end']=r['start']-1
    if defect=='census': f['split']['session_counts']['0']-=1
    with pytest.raises(ValueError): c.prepare(f)


def test_tuning_cannot_read_test_outcomes():
    f=fixture('change');a=c.tune(c.prepare(f)[0])
    for r in f['rows']:
        if r['half']=='test': r['counts']=dict(zip(c.CLASSES,[1,1,1,10000]))
    assert c.tune(c.prepare(f)[0])==a


def test_two_model_reference_matches_all_six_primary():
    gs,_=c.prepare(fixture('change')); p=c.tune(gs)
    for g in gs:
        assert c.primary(g)['gain']==c.primary(g,all_models=True,parameters=p)['gain']


def test_shuffle_preserves_missing_slots_and_moves_whole_vectors():
    f=fixture('change');f['rows'][0]['counts']=dict(zip(c.CLASSES,[0]*4))
    g=c.prepare(f)[0][0];x=c.outcome_shuffle(g,np.random.default_rng(42))
    assert not x[0].sum() and sorted(map(tuple,x))==sorted(map(tuple,g['data']))
    assert not np.array_equal(x,g['data'])


def test_reassignment_preserves_prompt_vectors_and_missing_slots():
    f=fixture('change'); f['rows'][1]['counts']=dict(zip(c.CLASSES,[0]*4))
    gs,_=c.prepare(f); xs=c.reassigned(gs,np.random.default_rng(10))
    for prompt in ('0','1'):
        before=[tuple(g['data'][j]) for g in gs for j,r in enumerate(g['rows']) if r['prompt']==prompt]
        after=[tuple(x[j]) for g,x in zip(gs,xs) for j,r in enumerate(g['rows']) if r['prompt']==prompt]
        assert sorted(before)==sorted(after)
    assert not xs[0][1].sum()


def test_rank_correlations_match_independent_scipy_with_ties():
    x=np.array([[[0,1],[0,3],[1,2],[2,2]],[[1,5],[2,4],[3,3],[4,2]]],float)
    assert np.allclose(c.correlations(x),[spearmanr(a[:,0],a[:,1]).statistic for a in x])


def test_paired_bootstrap_uses_same_real_writer_draws():
    real=np.array([[0,1],[1,3],[2,2],[4,5],[5,4]],float)
    fake=np.array([real,real[::-1]])
    # Both fake arms have the same profile-pair correlation and exactly the same
    # relation under each row draw for the first arm. Check by independent replay.
    a=c.paired_uncertainty(real,fake,31,seed=17);rng=np.random.default_rng(17);expected=[]
    for _ in range(31):
        ix=rng.integers(5,size=5)
        with np.errstate(invalid='ignore'):
            r=float(c.correlations(real[ix])); fs=[float(c.correlations(f[ix])) for f in fake]
        expected.append(r-np.mean(fs))
    assert a['paired_bootstrap']==c.distribution(expected)


def test_no_test_population_is_retained_as_unsupported():
    f=fixture(writers=2);r,_=c.run_analysis(f,2,2,5)
    assert r['primary']['status']=='unsupported' and r['counts']['all_sessions']==48
    assert r['reliability']['real'] is None


def test_reference_distribution_never_discards_undefined_values():
    d=c.distribution([1,float('nan'),2])
    assert d['undefined']==1 and d['mean'] is None and d['interval'] is None
