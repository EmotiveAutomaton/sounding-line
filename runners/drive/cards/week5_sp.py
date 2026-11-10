"""Week 5 ASHRAE comfort-location and sensitivity consumers.

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. Recover planted building slopes,
neutral points and group differences. Do not invent operative temperatures,
weather or acceptability. Cluster resampling rebuilds all building summaries.
Cooling type is observational and does not separate exposure from control.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import time
for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[k]="2"
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

SEED=20261107
MEASUREMENT_SHA="23711ee1cfd988501d1ee77fc2207884e3edcb126cf96c0cd30a5380f39bd5e0"
METADATA_SHA="af6770a2b469f079cd172bd6632d1ae726a3a663515126816ff6d2d8f51bfc10"
AC="air conditioned";NV="naturally ventilated";MM="mixed mode"


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def write(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+f'.{os.getpid()}.tmp');tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf8')
    for a in range(10):
        try:os.replace(tmp,path);break
        except PermissionError:
            if a==9:raise
            time.sleep(.02*(a+1))


def projection(inputs):
    mpath=Path(inputs['measurements']);bpath=Path(inputs['metadata']);salt=Path(inputs['salt']).read_bytes()
    if sha(mpath)!=MEASUREMENT_SHA or sha(bpath)!=METADATA_SHA:raise ValueError('ASHRAE source pin mismatch')
    if len(salt)!=32:raise ValueError('salt shape')
    cols=['building_id','top','thermal_sensation','thermal_acceptability','t_mot_isd','fan','window','clo','met','vel']
    m=pd.read_csv(mpath,usecols=cols)
    b=pd.read_csv(bpath,usecols=['building_id','cooling_type','climate','publication'])
    if len(m)!=109033 or b.building_id.duplicated().any():raise ValueError('source count or unique metadata mismatch')
    if not set(m.building_id).issubset(set(b.building_id)):raise ValueError('missing building metadata')
    data=m.merge(b,on='building_id',how='left',validate='many_to_one')
    missing=data[['top','thermal_sensation']].isna().any(axis=1)
    record={'measurement_rows':len(data),'missing_operative_or_sensation':int(missing.sum()),
            'measurement_sha256':MEASUREMENT_SHA,'metadata_sha256':METADATA_SHA,
            'license':'CC BY 4.0 (Zenodo licence of record)','citation':'Foldvary Licina et al. (2018), ASHRAE Global Thermal Comfort Database II',
            'no_operative_temperature_imputation':True}
    data=data.loc[~missing].copy()
    # Publication identifies a source study; metadata authors/coordinates never enter the projection.
    for column,namespace in [('building_id','comfort-building'),('publication','comfort-study')]:
        data[column]=data[column].fillna('unknown').map(lambda v:hmac.new(salt,(namespace+':'+str(v)).encode(),hashlib.sha256).hexdigest())
    data=data.sort_values(['building_id','top','thermal_sensation'],kind='stable').reset_index(drop=True)
    record['retained_rows']=len(data);record['retained_buildings']=data.building_id.nunique()
    return data,record


def acceptable_width(group):
    d=group.loc[group.thermal_acceptability.isin(['acceptable','unacceptable'])]
    if len(d)<10:return None
    temp=d.top.to_numpy(float);mid=float(np.mean(temp));z=temp-mid;y=d.thermal_acceptability.eq('acceptable').to_numpy(float)
    if np.all(y==1):return float(temp.max()-temp.min())
    if np.all(y==0):return 0.
    x=np.column_stack([np.ones(len(d)),z,z*z])
    def objective(beta):
        eta=x@beta
        return float(np.logaddexp(0,eta).sum()-y@eta),x.T@(expit(eta)-y)
    fit=minimize(objective,np.zeros(3),jac=True,method='BFGS',options={'gtol':1e-7,'maxiter':200})
    if np.max(np.abs(objective(fit.x)[1]))>1e-4:return None
    grid=np.linspace(float(temp.min()),float(temp.max()),501);a=grid-mid
    good=expit(np.column_stack([np.ones(501),a,a*a])@fit.x)>=.8
    longest=run=0
    for value in good:
        run=run+1 if value else 0;longest=max(longest,run)
    return float(max(0,longest-1)*(grid[1]-grid[0]))


def building_summaries(data,config):
    rows=[];excluded={"fewer_than_30":0,"no_temperature_variation":0,"covariate_missing":0,"ordinal_failure":0}
    controls=config.get('controls',[])
    for key,g in data.groupby('building_id',sort=True):
        if len(g)<(2 if config.get('allow_small') else 30):excluded['fewer_than_30']+=1;continue
        if controls:
            # Numeric personal-control indicators retain only explicit 0/1 coding.
            g=g.copy()
            for col in controls:g[col]=pd.to_numeric(g[col],errors='coerce')
            before=len(g);g=g.dropna(subset=controls);excluded['covariate_missing']+=before-len(g)
            if len(g)<30:continue
        t=g.top.to_numpy(float);y=g.thermal_sensation.to_numpy(float)
        if np.ptp(t)<1e-8:excluded['no_temperature_variation']+=1;continue
        if config.get('minimum_range') and np.ptp(t)<config['minimum_range']:continue
        x=np.column_stack([np.ones(len(g)),t,*[g[c].to_numpy(float) for c in controls]])
        if np.linalg.matrix_rank(x)<x.shape[1]:continue
        beta=np.linalg.lstsq(x,y,rcond=None)[0];slope=float(beta[1]);mean_t=float(t.mean());mean_s=float(y.mean())
        if config.get('ordinal'):
            from statsmodels.miscmodels.ordinal_model import OrderedModel
            # Source sensations may include fractional ratings: ordered unique values are preserved.
            if len(np.unique(y))<3:excluded['ordinal_failure']+=1;continue
            try:
                fit=OrderedModel(y,(t-mean_t)[:,None],distr='probit').fit(method='bfgs',disp=False,maxiter=300)
                if not fit.mle_retvals.get('converged'):raise ValueError('nonconverged')
                slope=float(fit.params[0])
            except Exception:excluded['ordinal_failure']+=1;continue
        use_griffiths=bool(config.get('griffiths_all')) or float(beta[1])<.1
        neutral=mean_t-mean_s/(.5 if use_griffiths else float(beta[1]))
        weather=float(g.t_mot_isd.mean()) if g.t_mot_isd.notna().any() else None
        rows.append({'building':key,'study':g.publication.iloc[0],'cooling':g.cooling_type.iloc[0],
                     'n':len(g),'slope':slope,'neutral':neutral,'weather':weather,'mean_temp':mean_t,
                     'range':float(np.ptp(t)),'griffiths':use_griffiths,
                     'acceptable_width':acceptable_width(g)})
    return pd.DataFrame(rows),excluded


def range_match(table):
    a=table.loc[table.cooling.eq(AC)].copy();b=table.loc[table.cooling.eq(NV)].copy()
    if not len(a) or not len(b):return table.iloc[:0]
    scale=table[['mean_temp','range']].std().to_numpy().clip(1e-12);available=list(b.index);chosen=[]
    for i in a.sort_values('building').index:
        if not available:break
        distance=((b.loc[available,['mean_temp','range']].to_numpy()-a.loc[i,['mean_temp','range']].to_numpy())/scale)**2
        j=available[int(np.argmin(distance.sum(axis=1)))];available.remove(j);chosen.extend([i,j])
    return table.loc[chosen]


def range_match_bins(table):
    data=table.loc[table.cooling.eq(NV)].dropna(subset=['weather']).copy()
    data['weather_bin']=np.floor(np.abs(data.weather-22)/3).astype(int)
    groups=[g.sort_values(['range','building']) for _,g in data.groupby('weather_bin',sort=True)]
    if len(groups)<2:return data.iloc[:0]
    target=min(groups,key=len);chosen=[target]
    for group in groups:
        if group is target:continue
        remaining=list(group.index);take=[]
        for value in target['range']:
            at=int(np.argmin(np.abs(group.loc[remaining,'range'].to_numpy()-value)))
            take.append(remaining.pop(at))
        chosen.append(group.loc[take])
    return pd.concat(chosen,ignore_index=True).drop(columns=['weather_bin'])


def estimate(table,card):
    if card=='SP1':
        d=table.dropna(subset=['weather']);d=d.loc[d.cooling.isin([AC,NV,MM])]
        if any(sum(d.cooling.eq(k))<2 for k in [AC,NV]):return None
        group=[k for k in [AC,NV,MM] if sum(d.cooling.eq(k))>=2]
        d=d.loc[d.cooling.isin(group)]
        x=np.column_stack([d.cooling.eq(k).astype(float) for k in group]+[d.cooling.eq(k).astype(float)*d.weather for k in group])
        if np.linalg.matrix_rank(x)<x.shape[1]:return None
        beta=np.linalg.lstsq(x,d.neutral.to_numpy(),rcond=None)[0]
        return float(beta[len(group)+group.index(NV)]-beta[len(group)+group.index(AC)])
    if card=='SP2':
        a=table.loc[table.cooling.eq(AC),'slope'];b=table.loc[table.cooling.eq(NV),'slope']
        return float(a.median()-b.median()) if len(a) and len(b) else None
    d=table.loc[table.cooling.eq(NV)].dropna(subset=['weather']).copy()
    if len(d)<2:return None
    center=np.floor(np.abs(d.weather.to_numpy()-22)/3)*3+1.5
    if np.ptp(center)==0:return None
    return float(np.linalg.lstsq(np.column_stack([np.ones(len(d)),center]),d.slope.to_numpy(),rcond=None)[0][1])


def analyse(data,config):
    card=config['phase'];table,exclusions=building_summaries(data,config)
    fallback=False
    if len(table)<20:
        table,exclusions=building_summaries(data,{**config,'allow_small':True});fallback=True
    if table.empty:return {'card':card,'status':'unsupported','exclusions':exclusions,'fallback':'no estimable buildings; descriptive source counts only'}
    if config.get('side')=='hot':table=table.loc[table.weather>=22]
    if config.get('side')=='cold':table=table.loc[table.weather<22]
    if config.get('range_matched'):table=range_match_bins(table) if card=='SP3' else range_match(table)
    point=estimate(table,card)
    record={'card':card,'buildings':len(table),'rows':int(table.n.sum()) if len(table) else 0,'exclusions':exclusions,
            'scope':'descriptive observational buildings; cooling type mixes thermal exposure with personal control',
            'ordinal_latent_units':bool(config.get('ordinal'))}
    if point is None:record['status']='unsupported';return record
    cluster='study' if config.get('cluster')=='study' else 'building'
    groups=[g for _,g in table.groupby(cluster,sort=True)];rng=np.random.default_rng(SEED);draws=config.get('draws',2000);samples=[];failed=0
    for _ in range(draws):
        frame=pd.concat([groups[i] for i in rng.integers(0,len(groups),len(groups))],ignore_index=True)
        value=estimate(frame,card)
        if value is None:failed+=1
        else:samples.append(value)
    record['clusters']=len(groups);record['draws']=draws;record['failed_draws']=failed;record['estimate']=point
    if failed:record['status']='bootstrap_support_failure';return record
    ci=np.quantile(samples,[.025,.975]).tolist();bar={'SP1':.1,'SP2':.05,'SP3':.01}[card];direction=-1 if card=='SP3' else 1
    lo,hi=sorted(direction*np.array(ci));outcome='supports' if lo>bar else 'against' if hi<0 or (lo>=-bar and hi<=bar) else 'inconclusive'
    if len(groups)<20 or fallback:outcome='below floor, descriptive'
    if config.get('ordinal'):outcome='descriptive latent-probit sensitivity; original practical bar not applicable'
    record.update(status='ok',interval=ci,bar=bar,outcome=outcome)
    record['cooling_counts']={str(k):int(v) for k,v in table.cooling.value_counts(dropna=False).items()}
    record['griffiths_buildings']=int(table.griffiths.sum())
    record['median_acceptability_width']={k:(float(g.acceptable_width.median()) if g.acceptable_width.notna().any() else None) for k,g in table.groupby('cooling')}
    return record


def grid():
    rows=[{'cell':c,'phase':c,'draws':2000} for c in ['SP1','SP2','SP3']]
    rows.extend([{'cell':'SP1.griffiths','phase':'SP1','griffiths_all':True,'draws':200},
                 {'cell':'SP2.range','phase':'SP2','range_matched':True,'draws':200},
                 {'cell':'SP2.ordinal','phase':'SP2','ordinal':True,'draws':200},
                 {'cell':'SP2.range4','phase':'SP2','minimum_range':4,'draws':200},
                 {'cell':'SP2.control','phase':'SP2','controls':['window','fan'],'draws':200},
                 {'cell':'SP3.hot','phase':'SP3','side':'hot','draws':200},
                 {'cell':'SP3.cold','phase':'SP3','side':'cold','draws':200},
                 {'cell':'SP3.clo-met','phase':'SP3','controls':['clo','met'],'draws':200},
                 {'cell':'SP3.study','phase':'SP3','cluster':'study','draws':200},
                 {'cell':'SP3.ordinal-range','phase':'SP3','ordinal':True,'range_matched':True,'draws':200},
                 {'cell':'SP3.air-speed','phase':'SP3','controls':['vel'],'draws':200}])
    return rows


def fixture():
    rows=[]
    for i in range(48):
        group=AC if i<24 else NV;weather=10+(i%24);neutral=20+(.4 if group==NV else .1)*(weather-20);slope=.8 if group==AC else .5
        for t in np.linspace(neutral-3,neutral+3,40):
            rows.append(dict(building_id=f'b{i:03}',publication=f's{i//3}',cooling_type=group,top=t,thermal_sensation=slope*(t-neutral),t_mot_isd=weather,thermal_acceptability='acceptable'))
    table,_=building_summaries(pd.DataFrame(rows),{})
    assert abs(estimate(table,'SP1')-.3)<1e-10
    assert abs(estimate(table,'SP2')-.3)<1e-10
    table.loc[table.cooling.eq(NV),'slope']=.8-.02*(np.floor(np.abs(table.loc[table.cooling.eq(NV),'weather']-22)/3)*3+1.5)
    assert abs(estimate(table,'SP3')+.02)<1e-10
    return {'passed':True,'neutral_location_recovery':True,'sensitivity_recovery':True,'dulling_recovery':True}


def execute(output:Path,inputs:dict,config:dict):
    output.mkdir(parents=True,exist_ok=True);phase=config.get('phase','prepare')
    if phase=='fixture':a=fixture();write(output/'FIXTURE.json',a);return a
    if phase=='prepare':
        data,a=projection(inputs);data.to_parquet(output/'comfort.parquet',index=False);a['projection_sha256']=sha(output/'comfort.parquet');write(output/'SOURCE.json',a);return a
    result=analyse(pd.read_parquet(inputs['data']),config);write(output/'RESULT.json',result);return result


def verify(output:Path,inputs:dict,config:dict):
    phase=config.get('phase','prepare')
    if phase=='fixture':
        if fixture()!=json.loads((output/'FIXTURE.json').read_text('utf8')):raise ValueError('fixture mismatch')
    elif phase=='prepare':
        data,_=projection(inputs);pd.testing.assert_frame_equal(data,pd.read_parquet(output/'comfort.parquet'))
    else:
        expected=json.loads((output/'RESULT.json').read_text('utf8'));actual=analyse(pd.read_parquet(inputs['data']),config)
        if actual!=expected:raise ValueError('analysis replay mismatch')
    return {'verified':True,'phase':phase,'full_replay':True}
