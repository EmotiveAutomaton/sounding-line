import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week4_timing_ruler as r

def test_known_three_components_and_writer_speed_invariance():
    with threadpool_limits(limits=1):
        model,a=r.writer_ruler(r.known_items());scaled,b=r.writer_ruler(r.known_items(13))
    assert model['state']==scaled['state']=='fitted'
    pa=np.array([[x['fast'],x['hesitation'],x['slowest']] for x in a]);pb=np.array([[x['fast'],x['hesitation'],x['slowest']] for x in b])
    assert np.allclose(pa,pb,atol=1e-8)
    assert (pa[:240].argmax(1)==0).mean()>.98
    assert (pa[240:360].argmax(1)==1).mean()>.98 and (pa[360:].argmax(1)==2).mean()>.98
    assert not any(x['stop'] for x in a[:200]) and all(x['stop'] for x in a[360:])

def test_stretch_excludes_first_onset_but_keeps_internal_breaks():
    x=lambda gap,fast:dict(onset=True,interval_seconds=gap,fast=fast)
    assert r.stretch_hesitancy([x(100,0),x(.2,.9),x(.2,.9)])['hesitancy']==pytest.approx(.1)
    assert r.stretch_hesitancy([x(.1,.9),x(61,0)])['state']=='break'
    assert r.stretch_hesitancy([x(.1,.9),x(60,0)])['state']=='eligible'
    assert r.stretch_hesitancy([x(1,.2)])['state']=='unsupported'

def test_ties_and_missing_ruler_remain_explicit():
    labels,_=r.thirds([.1]*20);assert set(labels)=={'middle'}
    assert r.writer_ruler([dict(x,location='before_word') for x in r.known_items()])[0]['state']=='unsupported'
    with pytest.raises(ValueError):r.fit_mixture([0.]*100)
