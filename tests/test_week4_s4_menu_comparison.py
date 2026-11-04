import copy
import pytest
from runners.drive.cards import week4_s4_menu_comparison as m


def test_equal_positive_reversed_and_reliability():
    for d in (0.,.25,-.25):
        rows=m.fixture(d,4,140);v=m.estimate(rows);m.scalar_check(rows,v)
        assert v['summary']['effect']==d and v['summary']['effect_ci95']==[d,d]
        assert abs(v['summary']['reliability']-1)<1e-12
    assert abs(m.correlation([0.,.5,1.],[1.,.5,0.])+1)<1e-12
    assert abs(m.correlation([0.,.5,1.],[1.,0.,1.]))<1e-12


def test_writer_weight_not_menu_weight_and_canonical_option():
    rs=m.fixture(.25,3,40)
    for r in rs:
        if r['writer']=='1' and r['navigation']['arm']=='pointer':r['option_own_cosines'][1]=.25
        if r['writer']=='2' and r['navigation']['arm']=='pointer':r['option_own_cosines'][1]=0.
    extra=[dict(r,key=r['key']+':repeat') for r in rs if r['writer']=='0'];v=m.estimate(rs+extra)
    assert v['summary']['effect']==0.


def test_all_arms_and_missing_history_remain_in_census():
    rs=m.fixture(0.,3,40)
    rs[0]['navigation']['arm']='both';rs[1]['navigation']['arm']='neither'
    rs[2]['option_own_cosines']=None
    rs[3]['handling']='dismiss';rs[3]['canonical_choice']=2
    v=m.estimate(rs)
    assert sum(v['summary']['browsing_counts'].values())==len(rs)
    assert v['summary']['browsing_counts']['both']==v['summary']['browsing_counts']['neither']==1
    assert v['writers'][0]['excluded']=={'no_earlier_history':1,'not_a_chosen_option':1}


def test_unsupported_and_degenerate_are_not_zero_or_dropped_draws():
    rs=m.fixture(0.,3,40)
    for r in rs:r['navigation']['arm']='pointer'
    v=m.estimate(rs)
    assert v['summary']['effect'] is None and v['summary']['reliability'] is None
    rs=m.fixture(0.,3,40);v=m.estimate(rs)
    assert v['summary']['reliability_undefined_bootstraps']>0
    assert v['summary']['reliability_ci95'] is None and len(v['reliability_bootstraps'])==2000


def test_duplicate_nonfinite_and_false_canonical_refuse():
    rs=m.fixture(0.,3,40)
    with pytest.raises(ValueError):m.estimate(rs+[rs[0]])
    rs[0]['option_own_cosines'][0]=float('nan')
    with pytest.raises(ValueError):m.estimate(rs)
    rs=m.fixture(0.,3,40);rs[0]['canonical_choice']=2
    with pytest.raises(ValueError):m.estimate(rs)
