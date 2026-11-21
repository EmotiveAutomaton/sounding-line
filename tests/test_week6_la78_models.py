import numpy as np
import pytest

from runners.drive.cards.week6_la78_models_v1 import role_direction, role_model, speaking_share, talk_crossproducts, talk_fit
from runners.drive.cards.week6_la78_targets_v1 import SpeakerFloor


def test_silence_and_simultaneous_talk_have_explicit_denominators():
    floors={s:SpeakerFloor([{"start":0,"end":n}]) for s,n in (("a",10),("b",5))}
    assert speaking_share("a",floors,0,60,"voiced")==pytest.approx(2/3)
    assert speaking_share("a",floors,0,60,"elapsed")==pytest.approx(1/6)
    assert speaking_share("a",floors,30,60,"voiced") is None


def test_whole_meeting_weighted_contrast_matches_raw_regression():
    rng=np.random.default_rng(662)
    blocks=[];xs=[];ys=[]
    for m in range(5):
        rows=[]
        for i in range(15):
            joined=bool(i%2);phase,before=rng.random(2)
            after=.3-.04*(not joined)+.1*phase+.2*before
            rows.append(dict(joined=joined,phase=phase,before=before,after=after))
            xs.extend([[1,int(not joined),phase,before]]*(m+1));ys.extend([after]*(m+1))
        blocks.append(talk_crossproducts(rows))
    direct=np.linalg.lstsq(xs,ys,rcond=None)[0][1]*100
    assert talk_fit(blocks,[1,2,3,4,5])==pytest.approx(direct)
    assert direct==pytest.approx(-4)
    assert talk_fit([talk_crossproducts([])],[1]) is None


def test_role_model_additive_null_reversal_and_singular_controls():
    x=np.array([[1,r,t,late] for r in (0,1) for t in (0,1) for late in (0,1)])
    exposure=np.arange(8)+1.
    y=exposure*np.exp(x@np.array([-.7,.2,-.1,.15]))
    assert role_model(exposure,y,x)==pytest.approx(y,abs=1e-6)
    assert role_model(exposure,y,np.column_stack((x,x[:,1]))) is None
    assert role_direction(.02,.01,-.01)=="sign reversal; no verdict"
    assert role_direction(0.,.01,-.01)=="descriptive"
