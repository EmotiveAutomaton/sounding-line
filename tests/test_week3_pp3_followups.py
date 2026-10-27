import json
import numpy as np
import pytest
from runners.drive.cards import week3_pp3_followups as f


@pytest.mark.parametrize('family',['s','m','p'])
def test_known_answer_gates(family):
    assert f.known_answers(family)['constant_exact_null']


def test_tree_expands_absent_classes():
    x=np.zeros((60,2));y=np.ones(60,dtype=int)
    p=f.tree_probabilities(x,x[:3],y,3)
    assert np.array_equal(p,[[0,1,0]]*3)


def test_fixed_specification_and_ablation_masks():
    x,c,y,p,a=f.wide_fixture()
    d=f.designs(x,c,p,'m',1.)
    assert len(f.specifications('s'))==2
    assert all(arms[0][0].shape[1]==24 and arms[1][0].shape[1]==15 for _,_,_,arms in d)
    with pytest.raises(ValueError):f.specifications('new')


def test_exact_paired_null_and_direction():
    x,c,y,p,a=f.wide_fixture();z=np.zeros_like(x)
    real=f.evaluate(f.designs(z,np.zeros_like(c),p,'m',1),y,p,a)
    refs={k:np.repeat(np.repeat(v[None,None],200,axis=1),2,axis=0) for k,v in real.items()}
    w=f.m.resample_weights(a,p,'author',np.random.default_rng(4),2000)
    assert (f.primary_draws(real,refs,w,'m')==0).all()
    assert (f.primary_draws(real,refs,w,'s')==0).all()


@pytest.mark.parametrize('family',['s','m','p'])
def test_native_complete_reentry_and_corruption(tmp_path,family):
    out=tmp_path/family;cfg=dict(family=family,mode='constructed',permutations=8)
    result=f.execute(out,{},cfg)
    assert result['rows']==450 and not result['scientific_admission'] and 'variants' not in result
    assert f.verify(out,{},cfg)['all_models_references_and_bootstraps_replayed']
    d=json.loads((out/'SUMMARY.json').read_text());d['rows']-=1;(out/'SUMMARY.json').write_text(json.dumps(d))
    with pytest.raises(ValueError):f.verify(out,{},cfg)


def test_unknown_population_and_reduced_main_refused(tmp_path):
    with pytest.raises(ValueError):f.execute(tmp_path,{},dict(family='p',mode='main',permutations=8))
    with pytest.raises(ValueError):f.source({'fixture':'untrusted'},'constructed')
