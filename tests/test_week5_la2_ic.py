import numpy as np
import pytest
from runners.drive.cards import week5_la2_ic as ic


def rows(noise=.001):
    rng=np.random.default_rng(810);out=[]
    for m in range(24):
        for j in range(6):
            same=j%2;a,b=rng.uniform(0,.1,2)
            out.append(dict(meeting=f'constructed-{m}',same=same,rate_a=a,rate_b=b,
                joined=.4+.04*same+.1*a-.2*b+noise*rng.normal()))
    return out


def test_operator_matches_original_and_rank_rule():
    x,y,code,n=ic.design(rows());rng=np.random.default_rng(ic.SEED)
    for _ in range(40):
        indices=np.concatenate([np.flatnonzero(code==m) for m in rng.choice(n,n,replace=True)])
        assert abs(ic.operator(x,indices)@y-np.linalg.lstsq(x[indices],y[indices],rcond=1e-10)[0][0])<1e-12
    # Identifiable target survives an exactly redundant nuisance column.
    x[:,2]=2*x[:,1]
    assert abs(ic.operator(x,np.arange(len(y)))@y-np.linalg.lstsq(x,y,rcond=1e-10)[0][0])<1e-12
    x[:,0]=x[:,1]
    with pytest.raises(ValueError):ic.operator(x,np.arange(len(y)))


def test_floor_does_not_become_null():
    with pytest.raises(ValueError,match='twenty'):ic.design(rows()[:60])
