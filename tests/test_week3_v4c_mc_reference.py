import copy
import json
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week3_v4c_mc_reference as m
from runners.drive.cards import week3_v4c_mc_cost as cost
from runners.drive.cards import menus_v4_split_stats as split
from runners.drive.cards.menus_io import read,write
from tests.test_drive_cards_menus_v4_saved_diagnostics import fixture


def simple():
    rows=[dict(key=str(i),session='s',writer='w',open_at=float(i),resolved_at=float(i+2),handling='ignore',menu=['a','b']) for i in range(8)]
    base={r['key']:[.25]*4 for r in rows}
    model=dict(decay=.5,fit=dict(coefficients={'w':[np.log(3),2.]}))
    return rows,base,model


def test_generator_keeps_intercept_and_causal_habit_without_observed_labels():
    rows,base,model=simple();old=copy.deepcopy(rows)
    generated,trace=m.generate(rows,base,model,731)
    assert rows==old
    assert trace['0']['probabilities'][0]==pytest.approx(.5)
    assert trace['1']['probabilities'][0]==pytest.approx(.5)
    assert trace['0']['habit']==trace['1']['habit']==0
    expected=.5*((trace['0']['outcome']==0)-.25)
    assert trace['2']['habit']==pytest.approx(expected)
    assert generated[2]['previous_handling']==m.source.ACTIONS[trace['0']['outcome']]
    changed=copy.deepcopy(rows)
    for r in changed:r['handling']='accept'
    assert m.generate(changed,base,model,731)==(generated,trace)
    for before,after in zip(rows,generated):
        assert {k:v for k,v in before.items() if k not in ('handling','previous_handling')}=={k:v for k,v in after.items() if k not in ('handling','previous_handling')}


def test_known_bernoulli_law_and_zero_habit():
    rows,base,model=simple();model['fit']['coefficients']['w']=[np.log(3),0.]
    rows=[dict(rows[0],key=str(i),open_at=float(i),resolved_at=float(i)+.5) for i in range(10000)]
    base={r['key']:[.25]*4 for r in rows};_,trace=m.generate(rows,base,model,112)
    q=np.asarray([v['probabilities'] for v in trace.values()]);np.testing.assert_allclose(q,np.tile([.5,1/6,1/6,1/6],(len(q),1)),atol=1e-15)
    assert abs(np.mean([v['outcome']==0 for v in trace.values()])-.5)<.02
    with pytest.raises(ValueError,match='writer'):m.generate(rows,base,dict(model,fit=dict(coefficients={})),1)


def test_fitted_null_retains_writer_offsets_and_every_writer(tmp_path):
    inputs,config=fixture(tmp_path/'source');s=m.source.load(inputs,config)
    construction,saved=m.source.load_world(s,s['worlds'][0]);rows=m.source.rebuild(s['sessions'],construction,20261017)
    for r in rows:
        if r['writer']=='w0':r['handling']='accept'
        elif r['writer']=='w1':r['handling']='ignore'
    model=m.fit_null(rows,saved,s['base'])
    assert model['writer_count']==4 and set(model['fit']['coefficients'])=={'w0','w1','w2','w3'}
    assert model['fit']['coefficients']['w0'][0]>0>model['fit']['coefficients']['w1'][0]
    assert set(model['selection'])=={'0.5','0.8','0.95'}


def test_whole_pipeline_matches_original_rboth_statistic(tmp_path):
    inputs,config=fixture(tmp_path/'source');s=m.source.load(inputs,config)
    construction,saved=m.source.load_world(s,s['worlds'][0]);rows=m.source.rebuild(s['sessions'],construction,20261017)
    expected=split.split_world(rows,s['sessions'],saved,s['geometry'],s['base'],20261018,draws=100)
    actual=m.statistic(rows,s['sessions'],saved,s['geometry'],s['base'])
    assert actual['likelihood_ratio']==expected['readers']['R-both']['likelihood_ratio']
    for old,new in zip(expected['halves'],actual['halves']):assert old['audit']==new['audit'] and old['fits']['R-both']==new['fit']


def test_exact_complete_reference_denominator_and_ties():
    assert m.reference_probability(1.,np.zeros(199))==.005
    assert m.reference_probability(0.,np.zeros(199))==1.
    assert m.reference_probability(.5,np.r_[np.zeros(99),np.ones(100)])==101/200
    with pytest.raises(ValueError,match='199'):m.reference_probability(1.,np.zeros(198))
    with pytest.raises(ValueError,match='199'):m.reference_probability(1.,np.full(199,np.nan))


def test_complete_cost_handler_reentry_replay_tamper_and_scope(tmp_path):
    inputs,_=fixture(tmp_path/'source');out=tmp_path/'out';out.mkdir();write(out/'YIELD_REQUEST.json',{})
    assert cost.execute(out,inputs,cost.FIXTURE)['status']=='yielded'
    (out/'YIELD_REQUEST.json').unlink()
    result=cost.execute(out,inputs,cost.FIXTURE)
    assert result['cost_only'] and not result['scientific_admission'] and result['primary'] is None
    assert result['complete_pipeline_units']==2 and result['full_matrix_unrun']
    assert cost.execute(out,inputs,cost.FIXTURE)==result
    assert cost.verify(out,inputs,cost.FIXTURE)['fresh_generation_and_fit_replay']
    with pytest.raises(ValueError,match='mismatch'):cost.load(inputs,cost.CONFIG)
    p=next((out/'worlds').glob('*/GENERATED.json'));v=read(p);v[next(iter(v))]['habit']+=.01
    # Deliberately corrupt this disposable test output; the production writer
    # correctly refuses overwriting an immutable result.
    p.write_text(json.dumps(v),encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):cost.verify(out,inputs,cost.FIXTURE)
