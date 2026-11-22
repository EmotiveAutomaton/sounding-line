"""Teacher and mentor agreement on matched occasions. Output contains only group statistics."""
import numpy as np
import pandas as pd

TRAITS = ('Openness','Conscientiousness','Extraversion','Agreeableness','Neuroticism')
SITUATIONS = ('Duty','Intellect','Adversity','Positivity','Negativity','Typicality','Humor')
ITEMS = (*TRAITS, *(s+'2' for s in TRAITS), *SITUATIONS)
RATERS = ('teacher','mentor')
COLUMNS = ['ID','timepoint',*(s+'_'+r for r in RATERS for s in ITEMS)]


def scales(frame):
    if frame[['ID','timepoint']].isna().any().any() or frame.duplicated(['ID','timepoint']).any():
        raise ValueError('Missing or duplicated teaching occasion')
    values = {}
    for rater in RATERS:
        for name in ITEMS:
            x = pd.to_numeric(frame[name+'_'+rater], errors='raise')
            if not x.dropna().isin([1,2,3,4,5]).all():
                raise ValueError('Unexpected rating code')
            values[name,rater] = 6-x if name=='Typicality' else x
        for trait in TRAITS:
            a,b=values[trait,rater],values[trait+'2',rater]
            values[trait+' state',rater]=((6-a)+b if trait=='Extraversion' else a+(6-b))/2
    return values


def agreement(ids, x, y, draws, seed):
    pair=pd.DataFrame({'id':ids,'x':x,'y':y}).dropna()
    history=pair.groupby('id',sort=True)
    means=history[['x','y']].mean()
    n=len(means)
    if n<2:
        return dict(people=n,repeat_people=int((history.size()>1).sum()),occasions=len(pair),estimates=None)
    dx,dy=(pair[['x','y']]-history[['x','y']].transform('mean')).to_numpy().T
    within=pd.DataFrame({'id':pair.id,'xx':dx*dx,'yy':dy*dy,'xy':dx*dy}).groupby('id',sort=True).sum()
    a,b=means.to_numpy().T
    statistics=np.column_stack((a,b,a*a,b*b,a*b,within.to_numpy()))
    rng=np.random.default_rng(seed)
    samples=[]
    for start in range(0,draws+1,64):
        w=rng.multinomial(n,np.full(n,1/n),min(64,draws+1-start))
        if start==0:w[0]=1
        ax,by,aa,bb,ab,xx,yy,xy=(w@statistics).T
        vx=aa-ax*ax/n
        vy=bb-by*by/n
        with np.errstate(divide='ignore',invalid='ignore'):
            between=np.where((vx>1e-10)&(vy>1e-10),(ab-ax*by/n)/np.sqrt(vx*vy),np.nan)
            inside=np.where((xx>1e-10)&(yy>1e-10),xy/np.sqrt(xx*yy),np.nan)
        samples.extend(np.column_stack((between,inside,between-inside,inside-between/2)))
    estimates={}
    for label,series in zip(('between','within','between_minus_within','within_minus_half_between'),np.array(samples).T):
        point=float(series[0]) if np.isfinite(series[0]) else None
        low,high=np.quantile(series[1:],[.025,.975]).tolist() if np.isfinite(series[1:]).all() else (None,None)
        estimates[label]=dict(point=point,lower=low,upper=high,finite_draws=int(np.isfinite(series[1:]).sum()))
    return dict(people=n,repeat_people=int((history.size()>1).sum()),occasions=len(pair),estimates=estimates)


def run(frame,draws=2000):
    key=['ID','timepoint']
    repeated=frame.duplicated(key,keep=False)
    excluded=dict(repeated_rows=int(repeated.sum()),ambiguous_keys=len(frame.loc[repeated,key].drop_duplicates()))
    frame=frame.loc[~repeated]
    values=scales(frame)
    quantities=(*ITEMS,*(s+' state' for s in TRAITS))
    results={name:agreement(frame.ID,values[name,'teacher'],values[name,'mentor'],draws,2026112206)
             for name in quantities}
    return {**results,'key_exclusions':excluded}
