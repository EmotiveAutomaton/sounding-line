"""Fixed-design SP3 sensitivity preserving the parent's whole-frame bootstrap.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7. Five fixed signed doses,100 worlds
and2,000 exact building draws. The full building roster is resampled before
selecting weather-linked NV buildings. A failed draw is never dropped.
"""
from pathlib import Path
import hashlib,json,math,time
import numpy as np
import pandas as pd
from . import week5_sp as parent
from .week5_la2_ic import requested

SEED=20261107
BAR=.01
DOSES=(-2,-1,0,1,2)


def design(table):
    table=table.sort_values('building',kind='stable').reset_index(drop=True)
    if table.building.duplicated().any():raise ValueError('One summary per building required')
    mask=table.cooling.eq(parent.NV).to_numpy()&np.isfinite(pd.to_numeric(table.weather,errors='coerce').to_numpy(float))
    at=np.flatnonzero(mask);center=np.floor(np.abs(table.loc[mask,'weather'].to_numpy(float)-22)/3)*3+1.5
    x=np.column_stack([np.ones(len(at)),center]);y=table.slope.to_numpy(float)
    if not np.isfinite(y).all():raise ValueError('Nonfinite building slope')
    return table,at,x,y


def operators(table,draws=2000):
    table,at,x,y=design(table);n=len(table);matrix=np.zeros((draws,n));failures=[]
    if len(at)<2 or np.ptp(x[:,1])==0:return None,list(range(draws))
    rng=np.random.default_rng(SEED)
    for draw in range(draws):
        sampled=rng.integers(0,n,n);weight=np.bincount(sampled,minlength=n)[at]
        use=weight>0
        if use.sum()<2 or np.ptp(x[use,1])==0:failures.append(draw);continue
        matrix[draw,at]=np.linalg.solve(x.T@(weight[:,None]*x),x.T*weight)[1]
    return matrix,failures


def binding_for(table,source_sha,draws,worlds):
    rows=table[['building','cooling','weather','slope']].to_json(orient='split',double_precision=15)
    return hashlib.sha256((rows+source_sha+str((draws,worlds,BAR,DOSES,SEED))+parent.sha(__file__)+parent.sha(parent.__file__)).encode()).hexdigest()


def calibrate(table,output,config,source_sha):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if int(config.get('draws',2000))!=2000 or int(config.get('worlds',100))!=100:raise ValueError('Full fixed SP3 sensitivity grid required')
    table,at,x,y=design(table);draws=2000;worlds=100
    support=dict(full_frame_buildings=len(table),analytic_buildings=len(at))
    if len(at)<2 or np.ptp(x[:,1])==0:return dict(status='design cannot test',reason='No analytic distance variation',**support)
    beta=np.linalg.lstsq(x,y[at],rcond=None)[0];residual=y[at]-x@beta
    if len(table)<20 or len(at)<20:return dict(status='below floor, descriptive',pooled_slope=float(beta[1]),**support)
    matrix,failures=operators(table,draws)
    if failures:return dict(status='invalid sensitivity',reason='bootstrap_support_failure',failed_draws=failures,total_draws=draws,**support)
    binding=binding_for(table,source_sha,draws,worlds);started=time.monotonic();maximum=float(config.get('max_wall_seconds',900))
    if not math.isfinite(maximum) or maximum<=0:raise ValueError('Positive finite wall quantum required')
    directory=output/'worlds';directory.mkdir(exist_ok=True);completed=0;results=[]
    prior_count=len(list(directory.glob('*.npz')))
    for multiple in DOSES:
        truth=multiple*BAR;checks=[]
        for world in range(worlds):
            path=directory/f'{multiple}-{world:03d}.npz';seal=path.with_suffix('.sha256.json')
            if path.exists():
                saved=json.loads(seal.read_text('utf8'))
                if saved['binding']!=binding or saved['sha256']!=parent.sha(path):raise ValueError('SP3 sensitivity checkpoint changed')
                with np.load(path,allow_pickle=False) as arrays:
                    samples=arrays['values'];point=float(arrays['point'])
                if samples.shape!=(draws,) or not np.isfinite(samples).all() or not np.isfinite(point):raise ValueError('Invalid saved draw array')
            else:
                if requested(output) or time.monotonic()-started>=maximum:
                    return dict(status='yielded',complete_card=False,phase='sensitivity_worlds',completed=completed,total=500)
                rng=np.random.default_rng(np.random.SeedSequence([SEED,world,881]))
                signs=rng.choice([-1.,1.],len(table));constructed=y.copy()
                constructed[at]=beta[0]+truth*x[:,1]+residual*signs[at]
                point=float(np.linalg.lstsq(x,constructed[at],rcond=None)[0][1]);samples=matrix@constructed
                np.savez_compressed(path,values=samples,point=point)
                parent.write(seal,dict(binding=binding,sha256=parent.sha(path)))
            interval=np.quantile(samples,[.025,.975]);lo,hi=map(float,interval)
            checks.append(dict(point=point,covers_truth=lo-1e-10<=truth<=hi+1e-10,
                excludes_zero=(lo>1e-10 if multiple>0 else hi< -1e-10 if multiple<0 else lo>1e-10 or hi< -1e-10),
                parent_negative_support=hi<-BAR))
            completed+=1;parent.write(output/'PROGRESS.json',dict(phase='sensitivity_worlds',completed=completed,total=500))
            if prior_count<25 and completed==25:
                return dict(status='yielded',complete_card=False,phase='sensitivity_worlds',completed=completed,total=500,reason='first five percent world pilot')
        results.append(dict(effect_multiple=multiple,injected_slope=truth,worlds=worlds,
            estimate_quantiles=np.quantile([c['point'] for c in checks],[.025,.5,.975]).tolist(),
            interval_coverage=float(np.mean([c['covers_truth'] for c in checks])),
            zero_exclusion_rate=float(np.mean([c['excludes_zero'] for c in checks])),
            original_negative_support_rate=float(np.mean([c['parent_negative_support'] for c in checks]))))
    return dict(status='ok',card='SP3.ic',**support,worlds_per_effect=worlds,draws=draws,practical_bar=BAR,
        effects=results,sensitivity_pass=results[2]['zero_exclusion_rate']<=.10 and min(results[1]['zero_exclusion_rate'],results[3]['zero_exclusion_rate'])>=.80,
        failed_draws=[],source_sha256=source_sha,
        scope='Fixed observed building design, cluster-wild slope residuals; all original full-frame building bootstrap multiplicities retained')


def execute(output,inputs,config):
    if set(config)-{'phase','draws','worlds','max_wall_seconds'} or config.get('phase')!='SP3.ic':raise ValueError('Registered primary instrument config required')
    data=pd.read_parquet(inputs['data']);table,exclusions=parent.building_summaries(data,{})
    fallback=len(table)<20
    if fallback:table,exclusions=parent.building_summaries(data,{'allow_small':True})
    if table.empty:result=dict(status='design cannot test',reason='No eligible building summaries')
    elif fallback:
        _,at,_,_=design(table)
        result=dict(status='below floor, descriptive',pooled_slope=parent.estimate(table,'SP3'),
                    full_frame_buildings=len(table),analytic_buildings=len(at),original_small_building_fallback=True)
    else:result=calibrate(table,Path(output),config,parent.sha(inputs['data']))
    if result.get('status')!='yielded':
        result['source_rows']=len(data);result['source_buildings']=int(data.building_id.nunique());result['exclusions']=exclusions
        parent.write(Path(output)/'RESULT.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output);result=execute(output/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return {**result,'verified':False}
    if result!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('Full SP3 sensitivity summary differs')
    for path in sorted((output/'worlds').glob('*.npz')):
        with np.load(path,allow_pickle=False) as left,np.load(output/'independent-replay/worlds'/path.name,allow_pickle=False) as right:
            if set(left.files)!=set(right.files):raise ValueError('SP3 draw keys differ')
            for key in left.files:
                if not np.array_equal(left[key],right[key]):raise ValueError('SP3 full draw replay differs')
    return dict(verified=True,all_worlds_and_draws_replayed=True)
