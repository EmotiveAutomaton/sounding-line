"""RF1 hand-specified three-read world, no public source or election inference."""
import itertools
import math
import numpy as np
from . import week5_rf_statistics_v1 as model


def planted_rows(candidates=40,null=False):
    rows=[]
    for person in range(candidates):
        for index,(respect,trust,liking) in enumerate(itertools.product((0,1),repeat=3)):
            # Hand probabilities: .8 for trust-only, .2 for liking-only, .5 otherwise.
            support=500 if null or trust==liking else 800 if trust else 200
            rows.append({'candidate':f'constructed-candidate-{person:03d}','election':f'constructed-{person}-{index}',
                'year':2010,'early_support':.5,'later_support':support,'later_oppose':1000-support,
                'rates':{key:{'for':value,'against':0} for key,value in zip(model.READS,(respect,trust,liking))}})
    return rows


def hand_margin():
    entropy=-.8*math.log(.8)-.2*math.log(.2)
    return .5*(math.log(2)-entropy)


def check(full_draws=False):
    rows=planted_rows();point=model.election_losses(rows,'separate_polarities')
    margin=point['mean_election_log_losses']['TWO-A']-point['mean_election_log_losses']['THREE']
    if abs(margin-hand_margin())>1e-10:raise ValueError('Hand-specified TWO-A loss margin failed')
    draws=[];candidates=[r['candidate'] for r in rows]
    for index in range(2000 if full_draws else 0):
        try:value=model.election_losses(rows,'separate_polarities',model.bootstrap_weights(candidates,index))
        except model.Unsupported as exc:value={'primary':None,'unsupported':str(exc)}
        draws.append({'index':index,**value})
    return {'by_construction':True,'hand_TWO_A_margin':hand_margin(),'point':point,'draws':draws,
        'uncertainty':model.uncertainty(point,draws),'real_source_used':False,'scientific_admission':False}
