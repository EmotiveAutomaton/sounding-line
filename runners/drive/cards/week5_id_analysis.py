"""ID1 chronological case census and exposure-matched logit-scale comparison.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Steady preference is defined only in
the first global scenario half. Quantity response uses Random cases in the
second half. Exact first-half exposure is matched; level is not the slope.
Separation/rank failure remains unsupported, not quantity insensitivity.
"""
from collections import Counter
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.special import expit
from . import week5_go as core


def cases(frame,companion=False):
    rows=[];counts=Counter()
    for person,g in frame.groupby('person',sort=True):
        counts['source_fingerprints']+=1
        if companion:
            if int(g.sessions.iloc[0])<2:continue
            seed=int(person[:16],16) if all(c in '0123456789abcdef' for c in person[:16]) else sum(map(ord,person))
            order=np.random.default_rng(np.random.SeedSequence([core.SEED,seed])).permutation(len(g));half=len(g)//2
            first=g.iloc[order[:half]];second=g.iloc[order[half:]]
        else:
            if not bool(g.primary_session.iloc[0]):counts['not_single_complete_session']+=1;continue
            first=g.loc[g.order<=6];second=g.loc[g.order>=7]
        classification=first.loc[first.kind.eq('Species')];exposure=len(classification)
        counts['first_species_exposure_'+str(exposure)]+=1
        if exposure<3:counts['below_B2_three_scenario_exposure']+=1;continue
        steady=bool(classification.human_saved.eq(1).all());targets=second.loc[second.kind.eq('Random')]
        if targets.empty:counts['no_second_half_random_case']+=1;continue
        for r in targets.itertuples(index=False):
            rows.append({'person':person,'exposure':exposure,'steady':steady,'log_ratio':float(np.log2(r.pets/r.humans)),
                         'human_saved':int(r.human_saved),'outnumbered':r.pets>r.humans})
    result=pd.DataFrame(rows,columns=['person','exposure','steady','log_ratio','human_saved','outnumbered'])
    if len(result):
        valid=[k for k,g in result.groupby('exposure') if g.steady.nunique()==2]
        counts['unmatched_exposure_rows']=int((~result.exposure.isin(valid)).sum());result=result.loc[result.exposure.isin(valid)].reset_index(drop=True)
    counts['matched_rows']=len(result);counts['matched_fingerprints']=int(result.person.nunique())
    counts['steady_outnumbered_cases']=int((result.steady.astype(bool)&result.outnumbered.astype(bool)).sum()) if len(result) else 0
    return result,dict(counts)


def fit_logit(x,y,weight=None,max_iter=150):
    x=np.asarray(x,float);y=np.asarray(y,float);w=np.ones(len(y)) if weight is None else np.asarray(weight,float)
    active=np.sum(w[:,None]*x*x,axis=0)>1e-12
    if not active[-3:].all():return None
    z=x[:,active]
    if np.linalg.matrix_rank(z*np.sqrt(w)[:,None])<z.shape[1]:return None
    beta=np.zeros(z.shape[1]);loss=np.inf
    for _ in range(max_iter):
        eta=z@beta;prob=expit(eta);gradient=z.T@(w*(prob-y));hessian=(z*(w*prob*(1-prob))[:,None]).T@z
        if np.linalg.cond(hessian)>1e12:return None
        delta=np.linalg.solve(hessian,gradient);step=1.
        while step>1e-9:
            next_beta=beta-step*delta;linear=z@next_beta;next_loss=float(w@(np.logaddexp(0,linear)-y*linear))
            if next_loss<=loss+1e-9:break
            step*=.5
        beta=next_beta;loss=next_loss
        if np.max(np.abs(beta))>40:return None
        if np.max(np.abs(z.T@(w*(expit(z@beta)-y))))/max(1,w.sum())<1e-8:
            all_beta=np.zeros(x.shape[1]);all_beta[active]=beta;return all_beta
    return None


def analyse(frame,draws=2000,companion=False):
    count=int((frame.steady&frame.outnumbered).sum()) if len(frame) else 0
    if count<500:return {'status':'design cannot test','steady_outnumbered_cases':count,'required':500,'scope':'descriptive counts only'}
    keys,code=np.unique(frame.person.to_numpy(),return_inverse=True);exposures=sorted(frame.exposure.unique())
    steady=frame.steady.to_numpy(float);ratio=frame.log_ratio.to_numpy(float)
    x=np.column_stack([frame.exposure.eq(k).to_numpy(float) for k in exposures]+[steady,ratio,steady*ratio]);y=frame.human_saved.to_numpy(float)
    b=fit_logit(x,y)
    if b is None:return {'status':'unsupported','reason':'separation, rank or likelihood convergence','steady_outnumbered_cases':count}
    rng=np.random.default_rng(core.SEED);bootstrap=[]
    for draw in range(draws):
        weights=np.bincount(rng.integers(0,len(keys),len(keys)),minlength=len(keys));value=fit_logit(x,y,weights[code])
        if value is None:return {'status':'bootstrap_fit_failure','draw':draw,'reason':'no resample is discarded or redrawn'}
        bootstrap.append([float(value[-1]),float(value[-2]),float(value[-2]+value[-1]),float(value[-3])])
    interval=np.quantile(bootstrap,[.025,.975],axis=0).T.tolist();lo,hi=interval[0]
    outcome='supports' if lo>.2 else 'against' if hi<0 or (lo>=-.2 and hi<=.2) else 'inconclusive'
    if len(keys)<20:outcome='below floor, descriptive'
    if companion:outcome='non-temporal descriptive companion; no temporal-stability claim'
    return {'status':'ok','fingerprints':len(keys),'rows':len(frame),'steady_outnumbered_cases':count,'exposure_strata':[int(k) for k in exposures],
            'slope_difference_steady_minus_others':float(b[-1]),'others_slope':float(b[-2]),'steady_slope':float(b[-2]+b[-1]),
            'steady_level_log_odds_for_scale':float(b[-3]),'intervals_difference_others_steady_level':interval,'draws':draws,'outcome':outcome,
            'flatter_interpretation_applicable':bool(abs(b[-2]+b[-1])<abs(b[-2])),
            'scope':'exact first-half Species exposure matched; fingerprint clustered; quantity slopes on logit scale'}


def execute(output:Path,inputs:dict,config:dict):
    output.mkdir(parents=True,exist_ok=True)
    if config['phase']=='cases':
        frame=pd.read_parquet(inputs['source']);primary,a=cases(frame);companion,b=cases(frame,True)
        primary.to_parquet(output/'primary.parquet',index=False);companion.to_parquet(output/'companion.parquet',index=False)
        result={'source_only':True,'chronological_primary':a,'non_temporal_companion':b,
                'primary_sha256':core.sha(output/'primary.parquet'),'companion_sha256':core.sha(output/'companion.parquet')}
        core.write(output/'CASE.json',result);return result
    frame=pd.read_parquet(inputs['cases']);result=analyse(frame,config.get('draws',2000),config.get('companion',False));result['card']='ID1'
    core.write(output/'RESULT.json',result);return result


def verify(output:Path,inputs:dict,config:dict):
    actual=execute(output/'independent-replay',inputs,config);name='CASE.json' if config['phase']=='cases' else 'RESULT.json'
    if actual!=json.loads((output/name).read_text('utf8')):raise ValueError('ID1 complete case/statistic replay differs')
    return {'verified':True,'full_replay':True}
