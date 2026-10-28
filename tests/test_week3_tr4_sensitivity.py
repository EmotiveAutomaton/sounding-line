import json
import numpy as np
import pytest
from runners.drive.cards import week3_tr4_sensitivity as s
from runners.drive.cards import week3_tr4_comparison as p


def test_stationary_truth_and_oracle_are_exact_null():
    world=s.construct(0.,s.SEEDS[0]);assert world['oracle_old_probability_penalty']==0
    for w in range(18):
        values=world['truth'][w*24:(w+1)*24]
        assert all(x['probabilities']==values[0]['probabilities'] and x['variation_from_initial']==0 for x in values)


@pytest.mark.parametrize('dose',[.15,.30])
def test_planted_truth_has_declared_variation_and_positive_oracle_penalty(dose):
    world=s.construct(dose,s.SEEDS[0]);assert world['oracle_old_probability_penalty']>0
    for i,row in enumerate(world['truth']):
        assert np.isclose(row['variation_from_initial'],dose if i%24>=12 else 0,rtol=0,atol=1e-15)
        assert min(row['probabilities'])>0
    groups,retained=p.prepare(world['census'])
    assert len(retained)==432 and len(groups)==18 and sum(g['half']=='test' for g in groups)==14
    assert all(g['reliability'] and g['mask'].sum()==8 for g in groups)


def test_paired_doses_reuse_prechange_counts_and_seed_replay_is_exact():
    a=s.construct(0.,s.SEEDS[1]);b=s.construct(.3,s.SEEDS[1]);assert b==s.construct(.3,s.SEEDS[1])
    for i,(x,y) in enumerate(zip(a['census']['rows'],b['census']['rows'])):
        if i%24<12:assert x==y
        assert sum(x['counts'].values())==sum(y['counts'].values())==100
    assert s.digest(a)!=s.digest(b) and s.digest(a)!=s.digest(s.construct(0.,s.SEEDS[2]))


def test_actual_handler_reentry_and_tamper_refusal(tmp_path):
    landing=tmp_path/'parent.json';landing.write_text(json.dumps(dict(full_write_through=True,id='S15-TR4-20261027')))
    output=tmp_path/'run';inputs={'parent_landing':str(landing)};config=s.CONFIGS['constructed']
    s.execute(output,inputs,config);before=(output/'cells/00.json').read_bytes()
    assert s.verify(output,inputs,config)['complete_input_replay']
    assert (output/'cells/00.json').read_bytes()==before
    cell=json.loads(before);cell['world']['dose']=0;(output/'cells/00.json').write_text(json.dumps(cell))
    with pytest.raises(ValueError,match='cell replay'):s.verify(output,inputs,config)


def test_refuses_unapproved_configuration_and_missing_parent(tmp_path):
    with pytest.raises(ValueError,match='configuration'):s.execute(tmp_path,{},dict(s.CONFIGS['constructed'],outcomes=1))
    with pytest.raises(ValueError,match='bindings'):s.execute(tmp_path,{},s.CONFIGS['constructed'])
