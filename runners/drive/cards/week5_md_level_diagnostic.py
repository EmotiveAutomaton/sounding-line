"""Immutable MD12 completion addendum: multiple correlation and gate sensitivity.

DESIGN CHECK: the adjacent 0.9 wording permits gamma and correlation readings.
The prospectively frozen gamma rule and pooled primary remain unchanged.
Report the alternative R filter and joint filter as labelled companions only.
"""
from pathlib import Path
import json
import numpy as np
from . import week5_md as md
from .week5_md_analysis import load_verified

README_SHA='528ff1c960b419e62c6e4679f728dbb2a838e4016cae17e4c697a95384f6a78c'
SCRIPT_SHA='c5b252de7eb9b3924c2441e99a66f9f88b6583f6413cd5ad0523c909980c7b70'


def multiple_r(features):
    a=np.asarray(features,float);a=a-a.mean(axis=0);x=a[:,:4];y=a[:,4]
    total=float(y@y)
    if total<=1e-18:return {'r':None,'aliased':True,'constant_level':True}
    scale=np.sqrt(np.mean(x*x,axis=0)).clip(1e-15);z=x/scale
    residual=y-z@np.linalg.lstsq(z,y,rcond=1e-12)[0];fraction=max(0.,float(residual@residual)/total)
    return {'r':float(np.sqrt(max(0.,1-min(1.,fraction)))),'aliased':bool(fraction<=1e-12),'constant_level':False}


def summary(records):
    values=[r['r'] for r in records if r['r'] is not None]
    return {'participants':len(records),'defined':len(values),'constant_level':sum(r['constant_level'] for r in records),
            'aliased':sum(r['aliased'] for r in records),'above_point9':sum(v>.9 for v in values),
            'quantiles_0_25_50_75_100':np.quantile(values,[0,.25,.5,.75,1]).tolist() if values else None}


def blocks(directory):
    out=[];end=0
    for path in sorted(Path(directory).glob('block-*.npz')):
        if md.sha(path)!=json.loads(path.with_suffix('.sha256.json').read_text('utf8'))['sha256']:raise ValueError('completed per-person block changed')
        with np.load(path,allow_pickle=False) as a:
            if int(a['start'])!=end:raise ValueError('noncontiguous per-person blocks')
            end=int(a['end']);out.append({k:a[k].copy() for k in ['mse','beta','gamma','valid']})
    if not out:raise ValueError('saved per-person arm missing')
    return {k:np.concatenate([r[k] for r in out]) for k in out[0]}


def compute(plays,gamma,base,time_model,level):
    n=len(plays)
    if any(len(a['valid'])!=n for a in [base,time_model,level]):raise ValueError('per-person arm population mismatch')
    x,y=md.rating_history(plays,gamma);centered,_,keep=md.center_training(x,y)
    pooled=multiple_r(centered[:,:10,:5].reshape(-1,5))
    at_pooled=[multiple_r(row[:10,:5]) for row in x[keep]]
    per_person=[None]*n
    for value in np.unique(time_model['gamma'][time_model['valid']]):
        use=np.flatnonzero(time_model['valid'] & np.isclose(time_model['gamma'],value))
        xx,_=md.rating_history(plays[use],float(value))
        for index,row in zip(use,xx):per_person[index]=multiple_r(row[:10,:5])
    valid=base['valid'] & time_model['valid'] & level['valid']
    eligible=np.array([bool(valid[i]) and r is not None and r['r'] is not None and r['r']<=.9 and not r['aliased'] for i,r in enumerate(per_person)])
    previous=valid & (time_model['gamma']<=.9)
    joint=previous & eligible
    result={'pooled_training_multiple_r':pooled,'within_participant_at_pooled_gamma':summary(at_pooled),
            'per_person_arm_at_own_M0_gamma':summary([r for i,r in enumerate(per_person) if valid[i] and r is not None]),
            'valid_per_person_models':int(valid.sum()),'eligible_by_multiple_r':int(eligible.sum()),
            'excluded_by_multiple_r_or_alias':int((valid&~eligible).sum()),
            'previous_gamma_gate_eligible':int(previous.sum()),'gamma_gate_disagreements':int((previous!=eligible).sum()),
            'multiple_r_filtered_median_level_weight':float(np.median(level['beta'][eligible,-1])) if eligible.any() else None,
            'frozen_gamma_gate_median_level_weight':float(np.median(level['beta'][previous,-1])) if previous.any() else None,
            'joint_filter_eligible':int(joint.sum()),'joint_filtered_median_level_weight':float(np.median(level['beta'][joint,-1])) if joint.any() else None,
            'interpretation':'preserve frozen gamma<=0.9 rule; R<=0.9 and joint filters are separately labelled descriptive companions, not replacements',
            'training_ratings':10,'pooled_gamma':float(gamma),'pooled_nonconstant_mood_participants':int(keep.sum()),
            'alias_definition':'level residual SSE / centered level SST <= 1e-12; constant level separately counted'}
    return result


def execute(output:Path,inputs:dict,config:dict):
    from .week5_at_source import authenticate
    root=authenticate(inputs['md12_root']);upstream=json.loads((root/'output/RESULT.json').read_text('utf8'))
    data=load_verified(inputs['task']);plays=data['first']
    if upstream['analysed_first_plays']!=len(plays):raise ValueError('declare the exact sampled source before diagnostic')
    order=np.random.default_rng(md.SEED).permutation(len(plays));split=min(5000,len(plays)//3);main=plays[np.sort(order[split:])]
    arms=[blocks(root/'output/companions'/name) for name in ['arm-2','arm-3','arm-4']]
    result=compute(main,upstream['pooled']['gamma'],*arms)
    readme=Path(inputs['source'])/'README_Rutledge_GBE_risk_data.md';script=Path(inputs['source'])/'Rutledge_GBE_risk_data_code.m'
    if md.sha(readme)!=README_SHA or md.sha(script)!=SCRIPT_SHA:raise ValueError('source software documentation changed')
    result.update(card='MD12.level-diagnostic',scope='completed first-play main cohort; training ratings only; aggregate identification diagnostic',
                  source_first_plays=len(plays),exploratory_excluded=split,upstream_result_sha256=md.sha(root/'output/RESULT.json'),
                  README_MATLAB_check={'readme_sha256':README_SHA,'script_sha256':SCRIPT_SHA,
                    'readme_numeric_output_targets':False,'conditional_requirement':'not applicable: README points to code but specifies no numerical output targets',
                    'script_comments_have_other_numeric_examples':True,'script_executed':False,
                    'source_counts':'verified separately in the source receipt; historical happiness-weight block check remains in completed MD12'},
                  pooled_primary_unchanged=True)
    md.save_json(output/'RESULT.json',result);return result


def verify(output:Path,inputs:dict,config:dict):
    result=execute(output/'independent-replay',inputs,config)
    if result!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('level diagnostic replay differs')
    return {'verified':True,'complete_training_correlation_and_saved_fit_replay':True}
