import copy
import json
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week4_conflict_spec as s
from runners.drive.cards import week4_conflict_spec_h1 as h
from runners.drive.cards import week4_conflict_stats as p
from runners.drive.cards.timing_stats import sufficient


@pytest.fixture(autouse=True)
def one_thread():
    with threadpool_limits(limits=1):yield


def test_exact_complete_cost_prefix_and_reuse():
    rows,_=s.world('conflict_only');cache=h.ParentFits()
    for variant in s.VARIANTS:
        assert h.run_variant(rows,variant,blocks=1,cache=cache)==s.run_variant(rows,variant,blocks=1)
    assert cache.calls==201 and cache.hits==201


def test_key_covers_all_sufficient_statistics_and_order():
    rows,_=s.world('own');groups=sufficient(*p.design(rows));key=h.cache_key(groups)
    assert h.cache_key(copy.deepcopy(groups))==key
    assert h.cache_key(list(reversed(groups)))!=key
    assert h.cache_key(groups+[groups[0]])!=key
    for field in ('n','xx','xy','yy','sx','sy'):
        changed=copy.deepcopy(groups)
        if field in ('xx','xy','sx'):changed[0][field].flat[0]+=.01
        else:changed[0][field]+=.01
        assert h.cache_key(changed)!=key


def test_fresh_handler_replay_and_tamper_refusal(tmp_path):
    config=h.configuration('constructed');h.execute(tmp_path,{},config)
    assert h.verify(tmp_path,{},config)['full_fresh_replay']
    path=tmp_path/'SUMMARY.json';value=json.loads(path.read_text());value['human_scored']=True;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='Summary replay'):h.verify(tmp_path,{},config)


def test_native_null_signed_omission_and_config_refusals(tmp_path):
    assert h.known_answers()['exact_comparator_reuse']
    with pytest.raises(ValueError,match='Frozen'):h.execute(tmp_path,{},s.configuration('constructed'))
    with pytest.raises(ValueError):h.human_rows({},True)
