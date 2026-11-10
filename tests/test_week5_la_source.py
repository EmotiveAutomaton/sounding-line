import xml.etree.ElementTree as ET
from collections import Counter
from runners.drive.cards.week5_la_source import pointer,project_stream,NID,time_bounds


def nodes():
    return list(ET.fromstring('''<r xmlns:n="http://nite.sourceforge.net/">
    <w n:id="z" starttime="0" endtime="1">word</w>
    <vocalsound n:id="a" description="breath-laugh"/>
    <comment n:id="b" description="while laughing"/>
    <w n:id="q" starttime="2" endtime="3">laugh</w></r>'''))


def test_pointer_uses_document_order_not_lexical_identifier():
    selected=pointer('x.xml#id(z)..id(q)',nodes())
    assert len(selected)==4


def test_marks_removed_lexical_laugh_preserved_and_timing_rebuilt():
    counts=Counter();words,laughs=project_stream(nodes(),'m','s','ICSI',counts)
    assert [w['text'] for w in words]==['word','laugh']
    assert len(laughs)==2
    assert all(e['start']==1 and e['end']==2 and e['timing']=='adjacent_words' for e in laughs)
    assert {e['label'] for e in laughs}=={'vocal','speech_comment'}


def test_missing_time_is_unsupported_not_zero():
    node=ET.fromstring('<vocalsound description="laugh"/>')
    assert time_bounds([node],0)==(None,None,'missing')
