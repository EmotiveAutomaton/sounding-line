import copy
import numpy as np
import pytest
from runners.drive.cards import week4_s4_menu_source as m


def test_known_answers():
    assert all(m.known_answers().values())


def test_open_snapshot_is_not_pointer_and_missing_target_still_is_event():
    events=m.fixture()[:3]
    assert m.navigation(events,1,3)['arm']=='neither'
    events.insert(2,dict(eventName='suggestion-hover',eventTimestamp=1500,currentHoverIndex=None))
    assert m.navigation(events,1,4)['arm']=='pointer'


def test_keyboard_only_and_all_boundary_positions():
    for name,expected in [('suggestion-up','keyboard'),('suggestion-down','keyboard'),('suggestion-hover','pointer')]:
        events=[dict(eventName=n,eventTimestamp=i) for i,n in enumerate(['suggestion-open',name,'suggestion-close',name,'suggestion-reopen',name,'suggestion-select',name])]
        for independent in (False,True):
            r=m.navigation(events,0,8,independent)
            assert r['arm']==expected and r['hidden_navigation_ordinals']==[3]
            assert (r['hover_ordinals'] or r['keyboard_ordinals'])==[1,5]


def test_invalid_boundary_clock_and_hidden_selection_refuse():
    e=m.fixture()
    with pytest.raises(ValueError):m.navigation(e,0,9)
    e[5]['eventTimestamp']=0
    with pytest.raises(ValueError):m.navigation(e,1,9)
    e=m.fixture(); e[3]['eventName']='suggestion-select'
    with pytest.raises(ValueError):m.navigation(e,1,9)


def test_equal_future_other_writer_and_zero_history():
    hs=[dict(session='old',writer='a',end_at=1,count=1,total=np.array([1.,0.])),
        dict(session='equal',writer='a',end_at=2,count=1,total=np.array([0.,1.])),
        dict(session='other',writer='b',end_at=0,count=1,total=np.array([0.,1.]))]
    p=m.history.Prefix(hs)
    assert m.own_options(p.at(2),'a',[0,1],lambda r:np.eye(2)[r])[0]==[1.,0.]
    assert m.own_options(p.at(0),'a',[0],lambda r:np.eye(2)[r])[0] is None
    assert m.own_options(({'a':np.zeros(2)},{'a':2},{'a':['one','two']}),'a',[0],lambda r:np.eye(2)[r])[0] is None


def test_split_is_whole_session_seeded_and_outcome_independent():
    ss=[dict(session=str(i),writer=str(i//5)) for i in range(10)]
    a=m.halves(ss,20261102)
    assert a==m.halves(list(reversed(ss)),20261102)
    assert all(sum(a[s['session']] for s in ss if s['writer']==w)==2 for w in ('0','1'))
    with pytest.raises(ValueError):m.halves(ss+[ss[0]],20261102)


def test_serialized_handler_reentry_and_mutation_refusal(tmp_path):
    c=m.configuration('constructed')
    m.execute(tmp_path,{},c);m.verify(tmp_path,{},c);m.execute(tmp_path,{},c)
    p=tmp_path/'SUMMARY.json';p.write_text('{}')
    with pytest.raises(ValueError):m.verify(tmp_path,{},c)
