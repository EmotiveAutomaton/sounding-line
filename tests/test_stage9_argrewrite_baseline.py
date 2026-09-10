import pytest
from runners.stage9.argrewrite_baseline import features, fit_predict


def test_features_reject_outcome_and_state_difference():
    with pytest.raises(ValueError):features({'text':'allowed','truth':'claim'})
    same=features({'before':'one two','after':'one two'})
    changed=features({'before':'one two','after':'one three'})
    assert same['change:5']==0 and changed['change:5']>0


def test_classifier_learns_planted_signal_and_retains_all_classes():
    training=[{'unit':str(i),'truth':'evidence' if i%2 else 'claim',
               'artifact':{'text':'observed data' if i%2 else 'we claim'}} for i in range(80)]
    test=[{'artifact':{'text':'observed data'}},{'artifact':{'text':'we claim'}}]
    p=fit_predict(training,test,'artifact')
    assert p[0]['evidence']>p[0]['claim'] and p[1]['claim']>p[1]['evidence']
    assert all(len(v)==9 and abs(sum(v.values())-1)<1e-10 and min(v.values())>0 for v in p)
