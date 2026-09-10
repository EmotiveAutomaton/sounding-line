import pytest
from runners.stage9 import queue
from runners.stage9.common import write, file_hash


def test_absent_or_paused_current_allocation_never_inherits_campaign_gear(tmp_path,monkeypatch):
    monkeypatch.setattr(queue,'ROOT',tmp_path)
    write(tmp_path/'CAMPAIGN.json',{'authorized_gear':2})
    assert queue.current_allocation()['gpu_available'] is False
    value={'version':1,'gear':1,'gpu_available':False,'basis':'owner requests Gear 1','recorded_at':'fixture'}
    write(tmp_path/'ALLOCATION.json',value)
    assert queue.current_allocation()=={**value,'sha256':file_hash(tmp_path/'ALLOCATION.json')}
    # Positive fixture exercises a later explicit allocation without any GPU use.
    value.update(gear=2,gpu_available=True,basis='isolated positive fixture')
    write(tmp_path/'ALLOCATION.json',value)
    assert queue.current_allocation()['gpu_available'] is True
    value['gpu_available']=False
    write(tmp_path/'ALLOCATION.json',value)
    assert queue.current_allocation()['gpu_available'] is False


@pytest.mark.parametrize('change',[{'gpu_available':True},{'gear':True},{'gear':3},
    {'gpu_available':1},{'basis':''},{'version':True},{'recorded_at':None}])
def test_invalid_or_contradictory_allocation_refuses(tmp_path,monkeypatch,change):
    monkeypatch.setattr(queue,'ROOT',tmp_path)
    value={'version':1,'gear':1,'gpu_available':False,'basis':'fixture','recorded_at':'fixture'}
    write(tmp_path/'ALLOCATION.json',value|change)
    with pytest.raises(ValueError,match='owner allocation'):
        queue.current_allocation()
