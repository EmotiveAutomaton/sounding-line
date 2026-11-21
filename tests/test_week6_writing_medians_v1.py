"""Constructed checks for registered writer-level timing ratios."""
import numpy as np
import pytest
from runners.drive.cards import week6_writing_medians_v1 as w


def capture(cursor=1,time=4000):
    return [dict(eventName='system-initialize',eventTimestamp=1000,currentDoc='\n'),
            dict(eventName='text-insert',eventTimestamp=2000,eventSource='user',textDelta={'ops':[{'insert':'a'}]}),
            dict(eventName='suggestion-get',eventTimestamp=time,currentCursor=cursor)]


def test_request_on_fixed_clock():
    rows,omitted=w.request_pauses(capture())
    assert rows==[('within_word',2.)] and not omitted


def test_unbound_or_reversed_clock():
    assert w.request_pauses(capture(12))[1]['cursor_unavailable']==1
    with pytest.raises(ValueError,match='chronology'):w.request_pauses(capture(time=1900))


def test_ratio_then_median():
    groups={'a':{('creative','before_sentence'):[4]*90,('creative','before_word'):[2]*10},
            'b':{('creative','before_sentence'):[8],('creative','before_word'):[2]}}
    values,counts=w.writer_ratios(groups,{},'WLG1')
    assert counts['included_writers']==2 and np.median(values)==3


def test_same_place_and_genre():
    groups={'a':{('creative','within_word'):[1,3],('creative','before_word'):[9]}}
    req={'a':[(('creative','within_word'),4),(('argumentative','within_word'),99)]}
    v,c=w.writer_ratios(groups,req,'WLG2')
    assert list(v)==[2] and c['unmatched_requests']==1


def test_replay_every_draw():
    values=np.array([.25,.8,1.,1.5,2.,4.])
    first=w.compute(values,900,False)
    assert first==w.compute(values,900,True) and len(first[1])==2000


def test_bo_separate_allowances_and_campaign_ceiling():
    from runners.drive.cards import week6_writing_policy_v1 as wp
    used=dict.fromkeys(wp.FAMILY_CEILINGS,0.)
    used['KP']=90000
    assert wp.room_from_charges('WLG',10000,0,123,used)==9877
    used['ES']=wp.CEILING-90000-19999
    with pytest.raises(RuntimeError,match='both independent'):wp.room_from_charges('WLG',10000,0,0,used)
    assert wp.card_identity('WLG2')==('WLG','WLG2',10000)
