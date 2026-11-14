"""Constructed RF1 numerical checks; no retrieved comments or inferred UID."""
import math
import numpy as np
import pytest
from runners.drive.cards import week5_rf_statistics_v2 as s
from runners.drive.cards import week5_rf_math_fixture_v2 as f


def test_three_read_world_hand_entropy_margin_and_truth_coefficients():
    result=f.check(full_draws=False)
    assert result['hand_TWO_A_margin']>.09
    rows=f.planted_rows();x,names=s.design(rows,'THREE','signed_rates')
    y=np.array([r['later_support'] for r in rows]);n=np.full(len(rows),1000)
    fit=s.fit_binomial(x,y,n,np.ones(len(rows)))
    coefficients=dict(zip((names[i] for i in fit['selected']),fit['coefficients']))
    assert coefficients['trust_signed']==pytest.approx(math.log(4),abs=1e-8)
    assert coefficients['liking_signed']==pytest.approx(-math.log(4),abs=1e-8)


def test_identical_probability_null_has_no_model_gain():
    result=s.election_losses(f.planted_rows(null=True),'signed_rates')
    assert result['primary']==pytest.approx(0,abs=1e-14)


def test_all_elections_for_candidate_share_fold_and_bootstrap_weight():
    rows=f.planted_rows();ids=[r['candidate'] for r in rows];fold=s.folds(ids);weights=s.bootstrap_weights(ids,1999)
    for start in range(0,len(rows),8):
        assert len(set(fold[start:start+8]))==1 and len(set(weights[start:start+8]))==1
    assert sum(weights[::8])==40
    assert np.array_equal(weights,s.bootstrap_weights(ids,1999))


def test_nonconstant_rank_deficiency_and_no_training_support_refuse():
    x=np.array([[1,0,0],[1,1,1],[1,2,2]],float)
    with pytest.raises(s.Unsupported):s.fit_binomial(x,np.array([2,5,8]),np.full(3,10),np.ones(3))
    fit=s.fit_binomial(np.array([[1,0],[1,0]],float),np.array([3,7]),np.array([10,10]),np.ones(2))
    with pytest.raises(s.Unsupported):s.predict_eta(np.array([[1,1]],float),fit)


def test_prospective_representation_required_and_uncertainty_not_fabricated():
    with pytest.raises(ValueError):s.design(f.planted_rows(),'THREE','unreviewed')
    point=s.election_losses(f.planted_rows(),'signed_rates')
    assert s.uncertainty(point,[])['interval'] is None


def test_twelve_hand_comments_preserve_presence_mentions_and_overlap():
    from runners.drive.cards import week5_rf_cp_fixture_v1 as literal
    from runners.drive.cards import week5_rf_cp_markers_v1 as markers
    comments=[{'markers':markers.rf_counts(text)} for text,_ in literal.RF_CASES]
    early=s.early_counts(comments)
    assert early['comments']==12
    assert early['reads']['respect']==dict(for_comments=3,against_comments=3,overlap_comments=0,for_mentions=6,against_mentions=4)
    assert early['reads']['trust']==dict(for_comments=4,against_comments=4,overlap_comments=1,for_mentions=8,against_mentions=5)
    assert early['reads']['liking']==dict(for_comments=2,against_comments=3,overlap_comments=0,for_mentions=4,against_mentions=5)
    rates=s.index_rates(early)
    assert rates['trust']['for']-rates['trust']['against']==0
    assert rates['liking']['for']-rates['liking']['against']==pytest.approx(-1/12)


def test_three_versus_two_columns_and_polarity_sensitivity_are_distinct():
    rows=f.planted_rows()
    three,names=s.design(rows,'THREE')
    assert names[-3:]==['respect_signed','trust_signed','liking_signed'] and three.shape[1]==5
    for model in s.MODELS[:3]:assert s.design(rows,model)[0].shape[1]==4
    assert s.design(rows,'THREE','separate_polarities')[0].shape[1]==8
    rows[0]['early']['reads']['trust']['overlap_comments']=1
    with pytest.raises(ValueError):s.design(rows,'THREE')
