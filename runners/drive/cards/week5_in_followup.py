"""Prospective IN1 itemwise branches and fixed-design IN3/IN4 sensitivity.

DESIGN CHECK: preserve complete cluster dependence and the exact standardized
linear comparison. An injected minimum-size effect is tested for exclusion of
zero, separately from crossing the larger primary decision threshold.
"""
from pathlib import Path
import hashlib,json,time
import numpy as np
import pandas as pd
from . import week5_in as core


def matrix(generation,validation,task):
    if task=='IN3':
        arrays=[]
        for label in ['fear','anger']:
            d=generation.loc[generation.emotion.eq(label)];rage=float(label=='anger');z=core.standardize(d[['self_control','unpleasantness']].to_numpy())
            x=np.column_stack([np.ones(len(d)),np.full(len(d),rage),z[:,0],z[:,0]*rage,z[:,1],z[:,1]*rage])
            arrays.append((x,core.standardize(d.intensity.to_numpy()),d.prolific_id.to_numpy()))
        return np.concatenate([a[0] for a in arrays]),np.concatenate([a[1] for a in arrays]),np.concatenate([a[2] for a in arrays]),np.array([0,0,0,1,0,0.]),.15
    if task=='IN4':
        d=core.agreement_rows(generation,validation);d=d.loc[d.emotion.isin(core.PRIMARY)];x=np.column_stack([d.emotion.eq(k).astype(float) for k in core.PRIMARY])
        return x,d.contrast.to_numpy(),d.text.to_numpy(),np.ones(len(core.PRIMARY))/len(core.PRIMARY),.1
    raise ValueError('unregistered IN sensitivity parent')


def calibrate(x,y,clusters,contrast,bar,config,output):
    unique,code=np.unique(clusters,return_inverse=True);x=np.asarray(x,float);y=np.asarray(y,float);contrast=np.asarray(contrast,float)
    if np.linalg.matrix_rank(x)<x.shape[1]:return {'status':'design cannot test','reason':'fixed source design rank deficient'}
    if len(unique)<20:return {'status':'below floor, descriptive','clusters':len(unique),'reason':'fewer than twenty source clusters'}
    beta=np.linalg.lstsq(x,y,rcond=1e-12)[0];residual=y-x@beta
    # Delete precisely the contrast component while preserving every orthogonal
    # coefficient. Keep the observed residual vector intact within each cluster.
    null=beta-contrast*(contrast@beta)/(contrast@contrast);direction=contrast/(contrast@contrast)
    repetitions=int(config.get('worlds',100));draws=int(config.get('draws',2000));results=[];output.mkdir(parents=True,exist_ok=True);new=0;started=time.process_time()
    binding=hashlib.sha256(x.tobytes()+y.tobytes()+np.asarray(code).tobytes()+contrast.tobytes()+str((bar,repetitions,draws)).encode()+core.digest(Path(__file__)).encode()).hexdigest()
    for multiple in [-2,-1,0,1,2]:
        truth=multiple*bar;checks=[]
        for world in range(repetitions):
            path=output/'worlds'/f'{multiple}-{world:03d}.json'
            if path.exists():
                saved=json.loads(path.read_text('utf8'))
                if saved['binding']!=binding or core.digest(path)!=json.loads(path.with_suffix('.seal.json').read_text('utf8'))['sha256']:raise ValueError('IN sensitivity checkpoint changed')
                fit=saved['fit']
            else:
                from .week5_go1_pipeline import requested
                if new>=config.get('max_new_worlds',repetitions*5) or requested(output) or time.process_time()-started>=config.get('max_cpu_seconds',1e100):return {'status':'yielded','complete_card':False,'new_worlds':new,'new_cpu_seconds':time.process_time()-started}
                rng=np.random.default_rng(np.random.SeedSequence([core.SEED,world,713]));signs=rng.choice([-1.,1.],len(unique))
                constructed=x@(null+truth*direction)+residual*signs[code]
                fit=core.clustered_fit(x,constructed,clusters,contrast,draws,seed=core.SEED+world)
                core.write_json(path,{'binding':binding,'fit':fit});core.write_json(path.with_suffix('.seal.json'),{'sha256':core.digest(path)});new+=1
            if fit['status']!='ok':return {'status':'invalid sensitivity','reason':fit['status'],'effect_multiple':multiple,'world':world}
            estimate=fit['estimate'][0];lo,hi=fit['interval'][0]
            checks.append({'estimate':estimate,'interval':[lo,hi],'covers_truth':bool(lo-1e-10<=truth<=hi+1e-10),
                           'excludes_zero_expected_direction':bool(lo>1e-10 if multiple>0 else hi< -1e-10 if multiple<0 else lo>1e-10 or hi< -1e-10),
                           'primary_positive_support':core.classify(estimate,[lo,hi],bar)=='supports'})
            core.write_json(output/'PROGRESS.json',{'effect_multiple':multiple,'world':world+1,'worlds':repetitions,'draws':draws})
        results.append({'effect_multiple':multiple,'injected_contrast':truth,'worlds':repetitions,
                        'coverage':float(np.mean([r['covers_truth'] for r in checks])),
                        'zero_exclusion_rate':float(np.mean([r['excludes_zero_expected_direction'] for r in checks])),
                        'primary_positive_support_rate':float(np.mean([r['primary_positive_support'] for r in checks])),
                        'estimate_quantiles':np.quantile([r['estimate'] for r in checks],[.025,.5,.975]).tolist()})
    null_rate=results[2]['zero_exclusion_rate'];minimum=min(results[1]['zero_exclusion_rate'],results[3]['zero_exclusion_rate'])
    return {'status':'ok','clusters':len(unique),'rows':len(y),'draws':draws,'worlds_per_effect':repetitions,'practical_bar':bar,'effects':results,
            'sensitivity_pass':bool(null_rate<=.1 and minimum>=.8),'pass_rule':'null zero-exclusion<=0.10 and both signed one-bar zero-exclusion>=0.80',
            'scope':'fixed observed design and cluster-wild residual calibration; excludes zero is distinct from crossing the primary bar',
            'normalization':'original within-prompt standardized design and response units frozen before planting; no post-plant renormalization'}


def itemwise(generation,channel,draws):
    if channel not in ['anger','disgust']:raise ValueError('only landed supported RAGE/DISGUST branches are commissioned')
    d=generation.loc[generation.emotion.eq(channel)];controls=core.standardize(np.column_stack([d.unpleasantness,d.confidence,d[core.STYLE].mean(axis=1)]));y=core.standardize(d.intensity.to_numpy());result={}
    for item,sign in core.PROFILES[channel].items():
        x=np.column_stack([np.ones(len(d)),sign*core.standardize(d[item].to_numpy()),controls]);c=np.array([0,1,0,0,0.])
        fit=core.clustered_fit(x,y,d.prolific_id.to_numpy(),c,draws)
        if fit['status']=='ok':fit['outcome']='below floor, descriptive' if fit['clusters']<20 or len(d)<300 else core.classify(fit['estimate'][0],fit['interval'][0],.1)
        result[item]={'signed_direction':sign,**fit}
    return {'card':'IN1.w.'+channel,'items':result,'rows':len(d),'all_profile_items_reported':True,'scope':'registered itemwise descriptive decomposition, controls and prompt retained'}


def execute(output:Path,inputs:dict,config:dict):
    generation=pd.read_parquet(inputs['generation']);task=config['phase']
    if task=='IN1.w':result=itemwise(generation,config['channel'],config.get('draws',2000))
    elif task in ['IN3.ic','IN4.ic']:
        validation=pd.read_parquet(inputs['validation']) if task=='IN4.ic' else None
        result=calibrate(*matrix(generation,validation,task.split('.')[0]),config,output);result['card']=task
    else:raise ValueError('unregistered followup')
    if result.get('status')!='yielded':core.write_json(output/'RESULT.json',result)
    return result


def verify(output:Path,inputs:dict,config:dict):
    actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return {**actual,'verified':False}
    if actual!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('complete IN followup replay differs')
    return {'verified':True,'all_worlds_and_cluster_draws_replayed':True}
