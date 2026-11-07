import numpy as np
import pytest
from runners.theory_days import mind_sensitivity as m
from runners.theory_days.emotions import mind_contrast

def test_exact_parent_loop_and_bank():
    pairs=[('z',0,11,1,13),('a',2,23,1,17),('z',3,31,0,19),('single',1,5,0,7)]
    w=m.bank(pairs,64)
    assert np.all(w[:,3]==1) and np.all(w[:,[0,2]].sum(axis=1)==2)
    assert m.summarize(np.array([r[1:] for r in pairs]),w)==mind_contrast(pairs,64)

def test_full_states_and_immutable_handlers(tmp_path):
    r=m.fixtures()
    assert r['states']['zero']['interval']==[0.,0.]
    assert np.allclose(r['states']['negative']['interval'],[-.75,-.75],rtol=0,atol=1e-15)
    assert r['states']['negative']['verdict']=='supports'
    assert r['states']['undefined']['relative_difference'] is None
    m.execute(tmp_path,{},dict(constructed=True));before=(tmp_path/'CALIBRATION.json').read_bytes()
    assert m.verify(tmp_path,{},dict(constructed=True))['complete_recalculation']
    m.execute(tmp_path,{},dict(constructed=True));assert (tmp_path/'CALIBRATION.json').read_bytes()==before

def test_binomial_counts_and_sign():
    n=np.tile([1000,1000],(2000,1));r=m.world(n,.2,-.4,np.random.default_rng(12))
    assert np.all(r[:,[0,2]]<=n)
    assert abs(r[:,0].sum()/r[:,2].sum()-.6)<.01
    r=m.world(np.array([[5,7]]),1.,-1.,np.random.default_rng(1))
    assert r.tolist()==[[0,5,7,7]]
    with pytest.raises(ValueError):m.world(n,.9,.2,np.random.default_rng(1))
    with pytest.raises(ValueError):m.world(np.array([[1.5,2]]),.1,0,np.random.default_rng(1))

def test_finite_count_uncertainty():
    assert m.wilson(0,100)[1]>.03 and m.wilson(100,100)[0]<.97
    assert np.allclose(m.wilson(50,100),[.40383153,.59616847])
    with pytest.raises(ValueError):m.wilson(2,1)

def test_full_denominators_and_corruption(tmp_path):
    pairs=[('one',0,2,1,2)]
    r=m.calibration(pairs,3,32,0)
    for cell in r['doses'].values():
        assert len(cell['records'])==3
        assert sum(cell['counts'][s] for s in ('supports','against','inconclusive'))==3
        assert all(v<=3 for v in cell['counts'].values())
    with pytest.raises(ValueError):m.summarize(np.array([[2,1,0,1]]),np.ones((2,1),dtype=int))
    path=tmp_path/'source';path.write_text('changed')
    with pytest.raises(AssertionError):m.calculate({'go_emotions':dict(path=str(path),sha256='bad')},{})
