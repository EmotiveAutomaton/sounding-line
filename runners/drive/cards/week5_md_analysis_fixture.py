"""Constructed whole MD1/MD2 execution and independent bootstrap replay.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Three hundred synthetic tasks provide
all actual task fields, signed level plants, and nondegenerate offer variation.
No fixture observation comes from a participant. Every complete numerical
handler, including ridge tuning and historical sign companions, is exercised.
"""
from pathlib import Path
import json
import numpy as np
from . import week5_md as base
from . import week5_md_analysis as analysis


def constructed(sign=1,n=300):
    rng=np.random.default_rng(435);p=np.zeros((n,30,15));p[:,:,0]=np.arange(1,31)
    p[:,:,2]=rng.choice([-3.,0.,3.],(n,30));p[:,:,3]=rng.uniform(1,10,(n,30));p[:,:,4]=-rng.uniform(1,10,(n,30))
    p[:,:,6]=rng.integers(0,2,(n,30));win=rng.integers(0,2,(n,30))
    p[:,:,7]=np.where(p[:,:,6],np.where(win,p[:,:,3],p[:,:,4]),p[:,:,2])
    p[:,:,8]=1.;p[:,:,11]=1.;p[:,:,13]=2.;p[:,:,9]=np.nan
    ii=np.array([0,3,5,8,11,13,16,18,21,24,26,29]);p[:,ii,9]=50.
    x,_=base.rating_history(p,.5)
    y=x[:,:,:4]@np.array([.6,.4,.8,-.05])+sign*.12*x[:,:,4]+rng.normal(0,.25,(n,12))
    p[:,ii,9]=50+y
    for play in p:base.validate_play(play)
    return p


def run(output:Path,draws=2000):
    source=output/'constructed-source';source.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(source/'task.npz',first=constructed())
    base.save_json(source/'SOURCE.json',{'task_sha256':base.sha(source/'task.npz'),'constructed_only':True})
    base.save_json(source/'VERIFIED.json',{'verified':True,'constructed_only':True})
    inputs={'task':str(source/'task.npz')};config={'phase':'MD12','draws':draws}
    result=analysis.execute(output/'run',inputs,config)
    if result['pooled']['MD1']['level_weight']<=0 or result['companions']['historical_sign_diagnostic']['blocks']!=1:
        raise ValueError('whole MD known-answer direction or companion failed')
    checked=analysis.verify(output/'run',inputs,config)
    if not checked['verified']:raise ValueError('whole MD replay failed')
    # Both signed task plants also pass the actual pooled estimator, not just OLS.
    for sign in (-1,1):
        fit=base.pooled(constructed(sign),output/f'sign-{sign}',draws=30)
        if sign*fit['MD1']['level_weight']<=0:raise ValueError('actual pooled signed plant failed')
    receipt={'passed':True,'constructed_only':True,'whole_MD12_execute_verify':True,'primary_draws':draws,
             'signed_pooled_plants':True,'ridge_and_historical_companions':True}
    base.save_json(output/'FIXTURE.json',receipt);return receipt


def execute(output:Path,inputs:dict,config:dict):return run(output,config.get('draws',2000))


def verify(output:Path,inputs:dict,config:dict):
    result=run(output/'fixture-replay',config.get('draws',2000))
    if result!=json.loads((output/'FIXTURE.json').read_text('utf8')):raise ValueError('complete fixture replay differs')
    return {'verified':True,'whole_fixture_replayed':True}
