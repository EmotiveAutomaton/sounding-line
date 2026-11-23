import hashlib
import wave
from zipfile import ZipFile
import pytest
from runners.drive.cards.week7_ami_channels import channel_map,complete_meetings,verified_channel,intervals

def test_corpus_assignment_precedes_headset_measurement(tmp_path):
    path=tmp_path/'made.zip'
    with ZipFile(path,'w') as z:
        z.writestr('corpusResources/meetings.xml','<root><meeting observation="A"><speaker nxt_agent="D" channel="3"/><speaker nxt_agent="B" channel="1"/></meeting></root>')
        z.writestr('words/A.D.words.xml','<root><w starttime="0" endtime="2"/><vocalsound type="laugh" starttime="2" endtime="3"/><vocalsound type="laugh"/><comment type="laugh"/></root>')
    mapping=channel_map(path)
    first='A/A.Headset-3.wav'
    assert mapping[first]==('A','D') and not complete_meetings(mapping,[first])
    assert complete_meetings(mapping,mapping)=={'A':sorted(mapping)}
    with ZipFile(path) as z:
        assert intervals(z,'A','D')==([(2.,3.)],[(0.,2.)],1)
        assert intervals(z,'A','B') is None

def test_digest_and_channel_count(tmp_path):
    path=tmp_path/'made.wav'
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,16000,0,'NONE','not compressed'))
        w.writeframes(bytes(32000))
    pin=dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert verified_channel(path,pin)==1.
    with pytest.raises(ValueError,match='digest'):verified_channel(path,dict(pin,sha256='0'*64))
