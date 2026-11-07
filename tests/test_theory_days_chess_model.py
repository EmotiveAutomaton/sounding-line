import numpy as np
from runners.theory_days.chess_model import constructed,calculate,sufficient,fit,unpack

def test_planted_signs_and_weak_instrument():
    for sign,expected in [(1,'supports'),(-1,'against'),(0,'inconclusive')]:
        values,groups=constructed(sign);result=calculate(values,groups,draws=64)
        assert result['verdict']==expected
        assert min(result['fit']['first_stage_partial_F'])>10
    values[:,3]=0
    assert calculate(values,groups,draws=64)['status']=='design cannot test'

def test_sufficient_fit_matches_direct_linear_solve():
    values,groups=constructed(1);stats=sufficient(values,groups);xx,zz,zx,xy,zy,_,_=unpack(stats.sum(axis=0))
    result=fit(stats.sum(axis=0))
    two_stage=np.linalg.solve(zx.T@np.linalg.solve(zz,zx),zx.T@np.linalg.solve(zz,zy))
    assert abs(result['iv_product']-two_stage[3])<1e-10
    assert abs(result['ols_product']-np.linalg.lstsq(xx,xy,rcond=None)[0][3])<1e-10
