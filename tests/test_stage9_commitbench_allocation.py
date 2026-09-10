import pytest
from runners.stage9.commitbench_allocation import allocate


def test_old_exposure_cannot_be_relabelled_and_new_groups_fill_exact_reserve():
    groups={str(i) for i in range(100)}
    prior={str(i):{'train' if i<50 else 'development' if i<60 else 'reserve' if i<65 else 'discovery'} for i in range(70)}
    allocation,receipt=allocate(groups,groups,prior)
    assert receipt['reserve_target']==receipt['eligible_reserve_components']==30
    assert receipt['new_eligible_reserve_components']==25
    assert all(allocation[g] in roles for g,roles in prior.items())
    assert sum(allocation[g]=='discovery' for g in groups-set(prior))==5


def test_alias_of_reserved_and_fitted_source_loses_reserve_and_invalid_only_groups_do_not_count():
    groups={'fit','old_reserve','new1','new2','new3','invalid'}
    prior={'fit':{'train','reserve'},'old_reserve':{'reserve'}}
    allocation,receipt=allocate(groups,groups-{'invalid'},prior)
    assert allocation['fit']=='train'
    assert allocation['old_reserve']=='reserve'
    assert allocation['invalid']=='discovery'
    assert receipt['eligible_nonpilot_components']==5
    assert receipt['reserve_target']==2
    assert receipt['prior_reserve_components_lost_to_exposure']==1
    assert receipt['new_eligible_reserve_components']==1


def test_shortage_refuses_instead_of_promoting_old_examined_groups():
    with pytest.raises(ValueError,match='insufficient genuinely new'):
        allocate({'a','b','c'},{'a','b','c'},{'a':{'train'},'b':{'development'},'c':{'discovery'}})

