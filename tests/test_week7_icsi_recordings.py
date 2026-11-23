from zipfile import ZipFile

import numpy as np
import pytest
from runners.drive.cards import week7_icsi_recordings as study


MADE = b"""<Meeting Session="A01"><Participant Name="person" Channel="chan1"/>
<Participant Name="another" Channel="chan2"/><Transcript>
<Segment Participant="person" StartTime="1" EndTime="2"><VocalSound Description="laugh"/></Segment>
<Segment Participant="person" StartTime="2" EndTime="3"><VocalSound Description="laugh"/>speech</Segment>
<Segment Participant="another" StartTime="3" EndTime="4"><VocalSound Description="laugh"/><Pause/></Segment>
<Segment Participant="another" StartTime="4" EndTime="5">spoken words</Segment>
</Transcript></Meeting>"""


def test_unique_editions_and_mixed_marks(tmp_path):
    p=tmp_path/'test.zip'
    with ZipFile(p,'w') as z:
        z.writestr('transcripts/A01.mrt',MADE)
        z.writestr('copy/A01.mrt',MADE)
        z.writestr('transcripts/preambles.mrt',b'<Meeting/>')
    with ZipFile(p) as z:
        assert list(study.editions(z))==['A01']
    channels,marks,speech,refs,mixed,counts=study.transcript(MADE)
    assert counts['mixed_utterances']==2 and counts['mixed_marks']==2
    assert len(marks)==1 and marks[0]['start']==1 and marks[0]['end']==2
    assert mixed['person']=={'marks':2,'mixed':1}
    assert mixed['another']=={'marks':1,'mixed':1}
    assert len(channels)==2 and len(speech)==2 and refs['another']==[(4,5)]
    with ZipFile(p,'a') as z:
        z.writestr('competing/A01.mrt',MADE.replace(b'words',b'utterance'))
    with ZipFile(p) as z, pytest.raises(ValueError,match='Competing'):
        study.editions(z)


def test_reference_is_shared_without_changing_annotation_duration():
    rate=16000
    t=np.arange(rate)/rate
    audio=(20000*np.r_[np.sin(2*np.pi*150*t),np.sin(2*np.pi*300*t)]).astype('<i2')
    mark=dict(start=1.,end=2.)
    result,=study.channel_features(audio,rate,[(0,.7),(.5,1.)],[mark])
    assert result['relative_pitch_semitones']==pytest.approx(12,abs=.05)
    assert result['duration_seconds']==1 and result['voiced_fraction']==1


def test_provider_lettered_headsets_keep_the_original_file_labels():
    channels,*_=study.transcript(MADE.replace(b'chan1',b'chanA').replace(b'chan2',b'chanB'))
    assert set(channels.values())=={'chanA','chanB'}
    with pytest.raises(ValueError,match='Invalid ICSI channel'):
        study.transcript(MADE.replace(b'chan1',b'chanC'))
