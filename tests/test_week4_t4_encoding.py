import pytest
from runners.drive.cards import week4_t4_encoding as e

def test_exact_cache_hit_new_text_and_role_separation():
    data=e.inventory(*e.fixture())
    assert len(data['jobs'])==2 and data['menus'][0]['options'][0]['cached']==0
    assert data['histories'][0]['sequences'][0]==data['menus'][0]['options'][1]
    assert data['histories'][0]['timestamp']==1000 and data['histories'][0]['end_at']==2000

def test_bad_cache_alias_refuses():
    menus,histories,cache=e.fixture();cache[0]['role']='context'
    with pytest.raises(ValueError,match='binding'):e.inventory(menus,histories,cache)

def test_actual_constructed_interface_and_tamper(tmp_path):
    c=e.configuration('constructed');e.execute(tmp_path,{},c)
    assert e.verify(tmp_path,{},c)['complete_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):e.verify(tmp_path,{},c)
