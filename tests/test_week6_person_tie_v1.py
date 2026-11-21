"""Matching features reproduce strictly tied scores after equivalent arithmetic."""
import numpy as np
import pytest
from runners.drive.cards import week6_person_tie_v1 as study

@pytest.mark.parametrize('amplitude',[0,1e-15,5e-15,1e-14,2e-14])
def test_matching_equivalent_ratings(amplitude):
    rng=np.random.default_rng(31)
    x=rng.integers(0,5,(64,7)).astype(float)/3.
    x[4:20]=x[0]
    y=x+rng.uniform(-amplitude,amplitude,x.shape)
    first,second=study.ranking_feature(x),study.ranking_feature(y)
    np.testing.assert_array_equal(first,second)
    arms={'all':slice(None)}
    a,_=study.op.fold_hits(np.random.default_rng(3),first,first,arms)
    b,_=study.op.fold_hits(np.random.default_rng(3),second,second,arms)
    np.testing.assert_array_equal(a['all'],b['all'])

def test_diagnostic_keeps_verification_strict():
    with pytest.raises(ValueError,match='result.split.value'):
        study.verify_metric_tree({'split':{'value':.2}},{'split':{'value':.21}})
    study.verify_metric_tree({'unchanged':[1,2]},{'unchanged':[1,2]})

