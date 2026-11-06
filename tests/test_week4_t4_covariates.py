import copy
import math
import numpy as np
import pytest
from runners.drive.cards import week4_t4_covariates as m


def test_known_answers():
    assert m.known_answers()['verified']


def test_scalar_original_distance_oracle():
    a=np.array([[1.,7.,np.nan],[4.,7.,3.],[5.,7.,-1.]])
    b=np.array([[2.,7.,0.],[4.,7.,1.],[6.,7.,np.nan]])
    expected=[]
    means=[4.,7.,.5];filled=[[2.,7.,0.],[4.,7.,1.],[6.,7.,.5]]
    scales=[math.sqrt(8/3),0.,math.sqrt(1/6)]
    for i,row in enumerate(a):
        ds=[]
        for other in filled:
            ds.append(sum((((means[k] if np.isnan(row[k]) else row[k])-other[k])/scales[k])**2 for k in (0,2)))
        expected.append(min(d for j,d in enumerate(ds) if j!=i)-ds[i])
    assert np.allclose(m.distances(a,b)[0],expected,rtol=1e-13,atol=1e-13)


def test_gallery_only_scaling_and_missing_profile():
    a=np.array([[1.],[2.],[3.]]);b=a.copy()
    before=m.distances(a,b)[0]
    a[0,0]=100.
    assert m.distances(a,b)[0][1:]==before[1:]
    with pytest.raises(ValueError,match='absent channel'):
        m.distances([[np.nan],[1.]],[[0.],[1.]])


def test_complete_windows_and_missing_auxiliary_preserved():
    rows=[dict(writer='a',session='a',windows=[dict(hesitancy=1.),dict(hesitancy=3.)]),
          dict(writer='a',session='b',windows=[dict(hesitancy=8.)])]
    r=m.join(['a','b'],{},rows)
    assert r[0]['mean_hesitancy']==4. and r[0]['eligible_windows']==3
    assert r[1]['mean_hesitancy'] is None and r[0]['missing_identification']
    assert m.join(['a','b'],{},rows[::-1])==r


def test_duplicate_and_invalid_support_refused():
    row=dict(writer='a',session='s',windows=[])
    with pytest.raises(ValueError,match='Duplicate'):
        m.join(['a'],{},[row,row])
    with pytest.raises(ValueError,match='canonical'):
        m.join(['a','a'],{},[])
    row['windows']=[dict(hesitancy=float('nan'))]
    with pytest.raises(ValueError,match='Invalid eligible'):
        m.join(['a'],{},[row])


def test_handler_replay_and_changed_output_refused(tmp_path):
    c=m.configuration('constructed');m.execute(tmp_path,{},c)
    assert m.verify(tmp_path,{},c)['full_fresh_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):
        m.verify(tmp_path,{},c)
