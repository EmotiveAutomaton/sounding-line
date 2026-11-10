import pytest
from runners.drive.cards import week5_bk_wd1 as card


def test_exact_original_roster():
    rows=card.roster()
    assert len(rows)==len(set(rows))==30
    assert [sum(f==g for f,_,_ in rows) for g in card.original.FAMILIES]==[10,10,5,5]


def test_partial_campaign_refused():
    with pytest.raises(ValueError,match='thirty'):
        card.campaign_result([])


def test_full_assignment_bank_required():
    bundle=dict(config=dict(permutation_draws=1000))
    with pytest.raises(ValueError,match='Missing complete'):
        card.world_result(bundle,[dict(binding=card.digest(bundle),records=[])])


def test_duplicate_assignment_refused():
    bundle=dict(config=dict(permutation_draws=1000));row=dict(index=0,status='invalid')
    with pytest.raises(ValueError,match='Duplicated'):
        card.world_result(bundle,[dict(binding=card.digest(bundle),records=[row,row])])
