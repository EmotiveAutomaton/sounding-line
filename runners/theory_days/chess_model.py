"""Frozen B4 observational interaction and just-identified IV diagnostic.

DESIGN CHECK: LESSONS 3-5. Signed and zero planted interactions exercise both
stages; absent/weak instruments refuse. Bootstrap failures are not discarded.
The low-clock exclusion restriction is not established by numerical checks.
"""
from pathlib import Path
import numpy as np
from runners.stage14.common import read,freeze,filehash


def standardize(x):
    scale=x.std()
    if not np.isfinite(scale) or scale<=1e-12:raise ValueError('No predictor variation')
    return (x-x.mean())/scale


def sufficient(values,groups):
    if not np.isfinite(values).all():raise ValueError('Nonfinite feature')
    y,r,t,low,middle,late,difficulty=values.T
    r=standardize(r);t=standardize(t);product=standardize(r*t);difficulty=standardize(difficulty)
    x=np.column_stack([np.ones(len(y)),r,t,product,middle,late,difficulty])
    z=np.column_stack([np.ones(len(y)),r,low,low*r,middle,late,difficulty])
    unique,inverse=np.unique(groups,return_inverse=True);n=len(unique);parts=[]
    for a,b in ((x,x),(z,z),(z,x)):
        for i in range(7):
            for j in range(7):parts.append(np.bincount(inverse,weights=a[:,i]*b[:,j],minlength=n))
    for a in (x,z):
        for i in range(7):parts.append(np.bincount(inverse,weights=a[:,i]*y,minlength=n))
    parts.extend([np.bincount(inverse,weights=y*y,minlength=n),np.bincount(inverse,minlength=n)])
    return np.column_stack(parts)


def unpack(s):
    return s[:49].reshape(7,7),s[49:98].reshape(7,7),s[98:147].reshape(7,7),s[147:154],s[154:161],s[161],s[162]


def fit(s):
    xx,zz,zx,xy,zy,y2,n=unpack(s)
    if np.linalg.matrix_rank(xx)!=7:return dict(status='singular_OLS')
    ols=np.linalg.solve(xx,xy)
    if np.linalg.matrix_rank(zz)!=7 or np.linalg.matrix_rank(zx)!=7:return dict(status='singular_instrument',ols_product=float(ols[3]))
    iv=np.linalg.solve(zx,zy);fstats=[];ex=[0,1,4,5,6]
    for target in (2,3):
        ss=xx[target,target]
        full=ss-zx[:,target]@np.linalg.solve(zz,zx[:,target])
        restricted=ss-xx[ex,target]@np.linalg.solve(xx[np.ix_(ex,ex)],xx[ex,target])
        if full<=1e-10 or n<=7:return dict(status='invalid_first_stage_residual',ols_product=float(ols[3]))
        fstats.append(float(((restricted-full)/2)/(full/(n-7))))
    return dict(status='valid' if min(fstats)>10 else 'weak_instrument',ols_product=float(ols[3]),iv_product=float(iv[3]),first_stage_partial_F=fstats)


def calculate(values,groups,draws=2000):
    games=len(np.unique(groups));n=len(values)
    if games<1000 or n<10000:return dict(status='design cannot test',games=games,moves=n,reason='Source case floor')
    try:stats=sufficient(values,groups)
    except ValueError as exc:return dict(status='design cannot test',games=games,moves=n,reason=str(exc))
    point=fit(stats.sum(axis=0));result=dict(games=games,moves=n,fit=point,draws=draws,causal_claim=False)
    if point['status']!='valid':return dict(result,status='design cannot test',reason='Instrument/rank gate',verdict='inconclusive')
    rng=np.random.default_rng(20261106);iv=[];ols=[];invalid=0
    for start in range(0,draws,16):
        totals=rng.multinomial(games,np.full(games,1/games),size=min(16,draws-start))@stats
        for total in totals:
            f=fit(total)
            if f['status'] not in ('valid','weak_instrument'):invalid+=1;continue
            iv.append(f['iv_product']);ols.append(f['ols_product'])
    if invalid:return dict(result,status='invalid uncertainty',invalid_draws=invalid,verdict='inconclusive',interval=None)
    ci=np.quantile(iv,[.025,.975]).tolist();ols_ci=np.quantile(ols,[.025,.975]).tolist()
    verdict='supports' if ci[0]>1 else 'against' if ci[1]<=0 else 'inconclusive'
    return dict(result,status='complete',interval=ci,ols_interval=ols_ci,invalid_draws=0,verdict=verdict)


def constructed(sign,seed=20261106):
    rng=np.random.default_rng(seed);n=12000
    rating=rng.normal(1500,250,n);low=rng.binomial(1,.2,n);logtime=2-1.2*low+rng.normal(0,.3,n)
    phase=rng.integers(0,3,n);difficulty=rng.exponential(100,n)
    product=standardize(standardize(rating)*standardize(logtime))
    y=-50+5*sign*product+.1*standardize(logtime)+rng.normal(0,1,n)
    return np.column_stack([y,rating,logtime,low,phase==1,phase==2,difficulty]),np.repeat(np.arange(1200),10)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config.get('constructed'):
        result={str(sign):calculate(*constructed(sign),draws=64) for sign in (-1,0,1)}
        assert result['1']['verdict']=='supports' and result['-1']['verdict']=='against' and result['0']['verdict']!='supports'
    else:
        p=Path(inputs['source']['path']);assert filehash(p)==inputs['source']['sha256']
        with np.load(p) as source:result=calculate(source['values'],source['groups'],config.get('draws',2000))
    freeze(output/'SCIENCE.json',result);return dict(status='complete',constructed=bool(config.get('constructed')))


def verify(output,inputs,config):
    output=Path(output)
    if config.get('constructed'):result={str(sign):calculate(*constructed(sign),draws=64) for sign in (-1,0,1)}
    else:
        p=Path(inputs['source']['path']);assert filehash(p)==inputs['source']['sha256']
        with np.load(p) as source:result=calculate(source['values'],source['groups'],config.get('draws',2000))
    assert read(output/'SCIENCE.json')==result
    return dict(verified=True,complete_recalculation=True)
