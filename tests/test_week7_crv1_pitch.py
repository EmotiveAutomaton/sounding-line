import io
import zipfile

import numpy as np
from scipy.io import wavfile
from runners.drive.cards.week7_crv1_pitch import annotation, compare, summarize_clip, aggregate

def grid(length):
    return ('File type = "ooTextFile"\nObject class = "TextGrid"\n\n0\n'
            +str(length)+'\n<exists>\n1\n"IntervalTier"\n"silences"\n0\n'
            +str(length)+'\n1\n0\n'+str(length)+'\n"sounding"\n').encode()

def waveform(hz):
    return np.sin(2*np.pi*hz*np.arange(8000)/8000)

def test_pitch_and_spread():
    low,_ = summarize_clip(8000,waveform(180),annotation(grid(1)))
    high,_ = summarize_clip(8000,waveform(360),annotation(grid(1)))
    assert abs((high-low)[0]-12)<.1 and abs((high-low)[1])<.1
    varying,_ = summarize_clip(8000,np.r_[waveform(180),waveform(360)],annotation(grid(2)))
    assert abs(varying[1]-12)<.2

def test_clock_and_voicing():
    assert summarize_clip(8000,waveform(180),annotation(grid(.5)))[1]=='clock'
    assert summarize_clip(8000,np.zeros(8000),annotation(grid(1)))[1]=='low_voicing'
    assert aggregate(np.zeros((22,2)))['contrasts']['pitch_height']['interval']==[0.,0.]

def test_zip_pairing(tmp_path):
    wav=tmp_path/'clips.zip'
    times=tmp_path/'times.zip'
    with zipfile.ZipFile(wav,'w') as a,zipfile.ZipFile(times,'w') as b:
        for key,hz in [('AAA01B',360),('AAA01D',180),('AAA02D',180)]:
            buf=io.BytesIO()
            wavfile.write(buf,8000,waveform(hz))
            a.writestr(key+'.wav',buf.getvalue())
            b.writestr(key+'.TextGrid',grid(1))
    result=compare(wav,times,lambda _:None)
    assert result=={'inventory_people':2,'exclusions':{'missing_partner':1},'paired':{'n':1,'status':'below_support'}}

