import numpy as np
import pytest
from runners.drive.cards import week4_t4_history as h

def test_brute_force_strict_past_population_and_zero_norm():
    assert all(h.known_answers().values())

def test_future_change_cannot_change_current_prototype():
    hs=[dict(session='a',writer='a',end_at=1,count=1,total=np.array([1.,0.])),dict(session='b',writer='b',end_at=2,count=1,total=np.array([0.,1.]))]
    baseline=h.prototypes(h.Prefix(hs).at(3),'a')
    hs.append(dict(session='future',writer='a',end_at=3,count=1,total=np.array([-900.,100.])))
    actual=h.prototypes(h.Sweep(hs).at(3),'a')
    assert actual[2]==baseline[2]
    assert all(np.array_equal(a,b) for a,b in zip(actual[:2],baseline[:2]))

def test_chronology_and_nonmonotone_queries_refuse():
    with pytest.raises(ValueError,match='chronology'):
        h.prepare_histories([dict(session='x',writer='a',timestamp=2,end_at=1,sequences=[])],None)
    selector=h.Sweep([]);selector.at(2)
    with pytest.raises(ValueError,match='Nonmonotone'):selector.at(1)

def test_native_interface_and_tamper(tmp_path):
    cfg=h.configuration('constructed');h.execute(tmp_path,{},cfg)
    assert h.verify(tmp_path,{},cfg)['complete_history_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):h.verify(tmp_path,{},cfg)
