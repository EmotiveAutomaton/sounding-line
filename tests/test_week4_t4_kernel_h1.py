import numpy as np
import pytest
from runners.drive.cards import week4_t4_kernel_h1 as h
from runners.drive.cards import week4_t4_variable as v


def test_objective_gradient_and_independent_fits():
    assert all(h.known_answers().values())


def test_compiled_gradient_finite_differences_and_padding():
    rng=np.random.default_rng(81);m=np.arange(5)[None,:]<np.array([1,2,5,4,3,1])[:,None]
    x=rng.normal(size=(6,5,5));x[~m]=0
    d=dict(x=x,z=rng.normal(size=(6,2)),w=np.arange(6)%3,y=np.array([0,1,5,3,2,5]),mask=m)
    for individual in (False,True):
        t=rng.normal(size=7+3*(2 if individual else 1))*.3
        value,g=h.objective(t,d,individual);numeric=[]
        for j in range(len(t)):
            hi=t.copy();lo=t.copy();hi[j]+=1e-6;lo[j]-=1e-6
            numeric.append((h.objective(hi,d,individual)[0]-h.objective(lo,d,individual)[0])/2e-6)
        assert np.allclose(g,numeric,atol=2e-6,rtol=0)
        extended=dict(d,x=np.pad(x,((0,0),(0,2),(0,0))),mask=np.pad(m,((0,0),(0,2))),y=np.where(d['y']==5,7,d['y']))
        assert abs(h.objective(t,extended,individual)[0]-value)<1e-12
        assert np.allclose(h.objective(t,extended,individual)[1],g,atol=1e-12,rtol=0)


def test_native_replay_and_tamper(tmp_path):
    config=h.configuration('constructed');h.execute(tmp_path,{},config)
    assert h.verify(tmp_path,{},config)['complete_fitted_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):h.verify(tmp_path,{},config)
