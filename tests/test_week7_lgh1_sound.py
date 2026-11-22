import numpy as np
import pytest
from runners.drive.cards.week7_lgh1_sound_v1 import measures

RATE=16000
def tone(hz,seconds=.4):
    return np.sin(2*np.pi*hz*np.arange(round(RATE*seconds))/RATE)

def test_tone_and_level_ratios():
    m=measures(.5*tone(300),tone(150),RATE)
    assert m['relative_pitch_semitones']==pytest.approx(12,abs=.04)
    assert m['relative_level_db']==pytest.approx(-6.0206,abs=.03)
    assert m['bursts']==1 and m['voiced_fraction']==1 and m['pitch_iqr_semitones']<.04
    assert m['duration_seconds']==.4

def test_three_bursts():
    x=np.tile(np.r_[tone(200,.12),np.zeros(RATE//10)],3)
    assert measures(x,tone(200),RATE)['bursts']==3

def test_noise_and_silence():
    m=measures(np.random.default_rng(35).normal(size=RATE),tone(150),RATE)
    assert m['voiced_fraction']==0 and m['relative_pitch_semitones'] is None
    m=measures(np.zeros(RATE),tone(150),RATE)
    assert m['bursts']==0 and m['relative_level_db'] is None

def test_no_multichannel_input():
    with pytest.raises(ValueError,match='channel'):
        measures(np.ones((2,RATE)),tone(150),RATE)
