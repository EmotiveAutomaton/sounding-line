"""Signed, identical, held-out and cluster uncertainty AT controls."""
import numpy as np
import pytest
from runners.drive.cards.week5_at_analysis import outcome,folds,gaussian_predictions,at2,at3,at4
from runners.drive.cards.week5_at_scoring import ENGINE_MODELS


def rows():
    rng=np.random.default_rng(8);out=[]
    for w in range(15):
        for j in range(24):
            surprise,entropy=rng.normal(size=2);length=float(rng.integers(2,12));freq=float(rng.normal())
            y=.2*surprise+.3*entropy+.04*length+rng.normal(scale=.3)
            out.append(dict(writer=str(w),pause_seconds=float(np.exp(y)),fast=float(1/(1+np.exp(3*y))),
                length=length,log_frequency=freq,sentence_start=j%7==0,paragraph_start=j==0,
                position=j,population_surprisal=float(rng.normal()),scores={m:dict(surprisal_nats=float(surprise),
                entropy_nats=float(entropy)) for m in ENGINE_MODELS}))
    return out


def test_exhaustive_outcome_bands_and_exact_zero():
    assert outcome(0,[0]*20,.01)['state']=='against'
    assert outcome(.2,[.18,.2,.22],.01)['state']=='supports'
    assert outcome(-.2,[-.18,-.2,-.22],.01)['state']=='against'
    assert outcome(.01,[-.03,.01,.05],.01)['state']=='inconclusive'


def test_fold_predictions_never_fit_heldout_outcomes():
    rng=np.random.default_rng(9);w=np.repeat(np.arange(10),10);x=rng.normal(size=(100,2));y=x[:,0]+rng.normal(size=100)
    f=folds(w);p,_=gaussian_predictions(x,y,w,f);y2=y.copy();y2[f==0]+=100
    p2,_=gaussian_predictions(x,y2,w,f)
    assert np.array_equal(p[f==0],p2[f==0])
    assert set(w[f==0]).isdisjoint(set(w[f!=0]))


def test_at2_pair_replay_and_selection_in_uncertainty():
    value=at2(rows(),list(ENGINE_MODELS),20)
    assert value['secondary'][ENGINE_MODELS[0]]==value['secondary'][ENGINE_MODELS[1]]
    assert value['primary']['effect']==value['secondary'][ENGINE_MODELS[0]]['effect']
    assert value['selected_model']==min(ENGINE_MODELS)


def test_at3_signed_plants_and_collinearity_refusal():
    value=at3(rows(),ENGINE_MODELS[0],30)
    assert value['primary']['state']=='supports'
    r=rows()
    for row in r:
        row['scores'][ENGINE_MODELS[0]]['entropy_nats']=row['scores'][ENGINE_MODELS[0]]['surprisal_nats']
    with pytest.raises(ValueError,match='identifiable'):
        at3(r,ENGINE_MODELS[0],20)


def test_at4_complete_auc_and_replay():
    value=at4(rows(),ENGINE_MODELS[0],20)
    assert value['full_auc']>value['baseline_auc']
    assert value==at4(rows(),ENGINE_MODELS[0],20)
