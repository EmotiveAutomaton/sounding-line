import pytest
from runners.drive import budget_week3 as b


def approval():
    return dict(campaign=b.CAMPAIGN, first_paid_cents=1000, nodes=list(b.CAPS),
                statement_verbatim='Authorized recorded statement', packet_sha256='a'*64)


def test_release_unused_before_next_node():
    old = dict(campaign_id=b.CAMPAIGN, invocation='first', node='PROC',
               status='RESERVED', reserved_cents=200, booked_cents=200)
    with pytest.raises(ValueError, match='Reconcile'):
        b.guard([old], 'VAL', 'next', 250, approval(), b.CUTOFF-1)
    settled = b.reconcile_row(old, 10, 'f'*64)
    b.guard([settled], 'VAL', 'next', 250, approval(), b.CUTOFF-1)
    assert settled['booked_cents'] == 10
    with pytest.raises(ValueError, match='exceeds'):
        b.reconcile_row(old, 201, 'f'*64)


def test_caps_cutoff_duplicates_and_reserve_refused():
    for node, cents in [('PROC',201),('VAL',251),('K',251),('AUTH',101),('GOAL',51),('P',51),('Reserve',1)]:
        with pytest.raises(ValueError): b.guard([], node, 'x', cents, approval(), b.CUTOFF-1)
    with pytest.raises(ValueError, match='cutoff'):
        b.guard([], 'PROC', 'x', 1, approval(), b.CUTOFF)
    row=dict(campaign_id=b.CAMPAIGN, invocation='x',node='PROC',booked_cents=1,status='RECONCILED')
    with pytest.raises(ValueError, match='Duplicate'):
        b.guard([row], 'PROC', 'x', 1, approval(), b.CUTOFF-1)


def test_unknown_reservation_is_not_released():
    old=dict(campaign_id=b.CAMPAIGN, invocation='x',node='PROC',booked_cents=200,status='UNKNOWN')
    with pytest.raises(ValueError, match='Reconcile'):
        b.guard([old], 'VAL', 'y', 1, approval(), b.CUTOFF-1)


def test_counted_cost_and_maximum_input():
    rows=[dict(custom_id='a',params=dict(max_tokens=32))]
    assert b.ceiling(rows, {'a':1000}) == 3
    with pytest.raises(ValueError): b.ceiling(rows, {'a':100000})
