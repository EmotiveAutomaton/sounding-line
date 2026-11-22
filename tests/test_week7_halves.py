import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week7_halves_v1 as card

def frame():
    p=np.repeat(np.arange(30),16)
    event=np.tile([1,1,4,4],120)
    y=2+(p%4)*(event>1)
    return pd.DataFrame(dict(id=p,day=np.tile(np.repeat([1,4],8),30),interaction=1,
        int_proud=y,int_ashamed=y,status_admired=event,status_criticised=event))

@pytest.mark.parametrize('replay',[False,True])
def test_identical_slopes(replay):
    d=card.prepare(frame(),replay)
    v=card.evaluate(d,None,lambda:None,verify=replay)
    assert v['correlation']==pytest.approx(1)
    assert v['covariance']==pytest.approx(v['paired_proud_variance'])
    assert d.metadata['paired_people']==30

def test_no_cross_person_variance():
    f=frame();f.int_proud=np.where(f.status_admired.gt(1),5,1)
    assert card.evaluate(card.prepare(f,False),None,lambda:None)['correlation'] is None

def test_unavailable_support():
    f=frame();f.status_criticised=1
    d=card.prepare(f,False)
    assert d.metadata['paired_people']==0
    assert card.evaluate(d,None,lambda:None)['covariance'] is None

def test_invalid_rating():
    f=frame();f.loc[0,'int_ashamed']=9
    with pytest.raises(ValueError,match='Out-of-range'):card.prepare(f,False)
