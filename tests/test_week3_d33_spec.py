from copy import deepcopy
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week3_d33_spec as card
from runners.drive.cards.timing_stats import sufficient
from runners.drive.cards.timing_p6 import write_equal
from runners.drive.cards.timing_census import read
from tests.test_drive_cards_timing_d33_supported import make_design


def fixture(inputs):
    rows=make_design()
    return rows,dict(coverage=dict(retained_words=len(rows),retained_writers=6),statistics=dict(constructed=True))


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return card.one_pass(output,inputs,config,loader=fixture)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return card.one_pass(output,inputs,config,True,fixture)


def test_all_settings_preserve_keys_values_and_original():
    rows=make_design();before=deepcopy(rows)
    for setting,omitted in card.SETTINGS.items():
        out=card.adjust(rows,setting)
        for a,b in zip(rows,out):
            assert set(a)==set(b)
            assert all(b[k]==(0. if k in omitted else a[k]) for k in a)
    assert rows==before


@pytest.mark.parametrize('beta',[-.8,0.,.8])
def test_signed_worlds_and_independent_reduced_gls(beta):
    for setting,omitted in card.SETTINGS.items():
        rows=card.adjust(make_design(beta),setting)
        x,y,w=card.stats.design(rows);actual=card.stats.fit(sufficient(x,y,w))
        keep=[j for j,n in enumerate(card.stats.NAMES) if n not in omitted]
        xx=x[:,keep];v=np.eye(len(y))
        for writer in set(w):
            ids=np.flatnonzero(w==writer);v[np.ix_(ids,ids)]+=actual['variance_ratio']
        weighted=np.linalg.solve(v,xx);b=np.linalg.solve(xx.T@weighted,weighted.T@y)
        assert actual['own']==pytest.approx(b[0],abs=1e-8)
        assert set(actual['omitted_columns'])==set(omitted)
        assert abs(actual['own']-beta)<.08


def test_complete_cost_handlers_replay_and_refuse_mutation(tmp_path):
    source=tmp_path/'FIXTURE.json';write_equal(source,dict(constructed=True))
    inputs=dict(parent_completion=str(source),parent_landing=str(source));out=tmp_path/'out'
    assert execute(out,inputs,card.configuration('cost'))['status']=='complete'
    assert verify(out,inputs,card.configuration('cost'))['full_fresh_replay']
    assert len(list((out/'inference').glob('*/block-00.json')))==3
    assert not (out/'SUMMARY.json').exists()
    p=out/'PROBE.json';saved=read(p);saved['blocks_per_setting']=2
    p.write_text(__import__('json').dumps(saved),encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):verify(out,inputs,card.configuration('cost'))


def test_bad_config_and_missing_source_refuse(tmp_path):
    with pytest.raises(ValueError,match='Frozen'):execute(tmp_path,{},dict(card.configuration('cost'),draws=100))
    with pytest.raises(ValueError,match='Exact parent'):card.load({})
