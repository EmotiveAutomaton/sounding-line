"""Consecutive answered-prompt slopes. All bootstrap weights are whole-person counts."""
import numpy as np
import pandas as pd
from .week6_lattice_diary_v1 import InvalidFit, logit_fit
from .week7_answered_v1 import chronology, reading


def clock(frame, member):
    if member in ('0056', '0057'):
        return chronology(frame)
    f = frame[['id','day']].copy()
    if member == '0063':
        f = f.loc[frame.missing_beep.eq(0)]
        time = pd.to_datetime(frame.datetime, utc=True, errors='coerce')
    elif member == '0073':
        time = pd.to_datetime(frame.completed, errors='coerce')
    elif member == '0060':
        hours = pd.to_numeric(frame.hour, errors='coerce')
        mins = pd.to_numeric(frame.minute, errors='coerce')
        minutes = (hours*60+mins).where(hours.between(0,23) & mins.between(0,59))
    elif member in ('0003','0049'):
        name = 'study_time' if member == '0003' else 'ema_time'
        hours = pd.to_numeric(frame[name], errors='coerce')
        minutes = hours.where((hours >= 0) & (hours < 24)) * 60
    else:
        raise ValueError('Unbound within-day clock')
    if member in ('0063','0073'):
        minutes = (time - time.dt.normalize()).dt.total_seconds() / 60
    f['minute'] = minutes
    f['day'] = pd.to_numeric(f.day, errors='coerce')
    bad = f.minute.isna() | f.day.isna() | f.duplicated(['id','day','minute'],keep=False)
    excluded = bad.groupby(f.id).transform('any')
    people = f.id.nunique()
    f = f.loc[~excluded].sort_values(['id','day','minute'],kind='stable')
    f['gap'] = f.groupby(['id','day']).minute.diff()
    f['block'] = np.floor(f.minute/240)
    gaps = f.gap.dropna()
    q = gaps.quantile([0,.25,.5,.75,.90,.95,1]).tolist() if len(gaps) else [None]*7
    cap = None if q[2] is None else 2*q[2]
    return f[['id','gap','block']],dict(people=people,clock_excluded_people=people-f.id.nunique(),
        all_pairs=len(gaps),paired_people=f.loc[f.gap.notna(),'id'].nunique(),cap_minutes=cap,
        gap_minutes=dict(zip(('min','p25','median','p75','p90','p95','max'),q)),
        pairs_by_band=np.histogram(gaps,bins=[0,30,60,120,240,480,np.inf])[0].tolist(),
        band_edges_minutes_left_inclusive=[0,30,60,120,240,480],short_pairs=int((gaps<=cap).sum()) if cap else 0)


def fit_panel(person, predictors, target, block):
    ids, inv = np.unique(person, return_inverse=True)
    count = np.bincount(inv)
    means = np.column_stack([np.bincount(inv,weights=v)/count for v in predictors.T])
    centered = predictors-means[inv]
    varying = np.bincount(inv,weights=centered[:,0]**2)>1e-12
    if varying.sum()<20:
        raise InvalidFit('Fewer than 20 people vary on the current event')
    # Drop exactly redundant nuisance columns while retaining the original fitted span.
    nuisance = np.column_stack((np.ones(len(inv)),centered[:,1:],means[inv],
                                *(block==b for b in np.unique(block)[1:])))
    keep = []
    for col in nuisance.T:
        trial = np.column_stack([*keep,col])
        if np.linalg.matrix_rank(trial)>len(keep):
            keep.append(col)
    design = np.column_stack([centered[:,0],*keep])
    if np.linalg.matrix_rank(design)!=design.shape[1]:
        raise InvalidFit('Current event aliased with controls')
    return ids, inv, design, target


def cell(timing, support, x, y, floor, same, seed, draws=2000):
    x = np.asarray(x,float)[timing.index]; y = np.asarray(y,float)[timing.index]
    roster = np.unique(timing.id)
    samples = np.random.default_rng(seed).multinomial(len(roster),np.full(len(roster),1/len(roster)),size=draws) if len(roster) else []
    dest = np.flatnonzero(timing.gap.notna())
    output = {}
    for key in ('all','short'):
        t = dest if key=='all' else dest[timing.gap.to_numpy()[dest]<=support['cap_minutes']] if len(dest) else dest
        s = t-1
        complete = np.isfinite(x[s]) & np.isfinite(x[t]) & np.isfinite(y[s]) & np.isfinite(y[t])
        s,t = s[complete],t[complete]
        people = timing.id.to_numpy()[s]
        result=dict(people=len(np.unique(people)),pairs=len(t),estimate=None,interval=None,ratio=None)
        output[key]=result
        try:
            if result['people']<20:raise InvalidFit('Fewer than 20 matched people')
            ids,inv,X,yy=fit_panel(people,np.column_stack((x[s],y[s],x[t])),
                                   (y[t]>floor).astype(float),timing.block.to_numpy()[s])
            # One pooled within-person standard deviation, reestimated under each draw.
            def estimate(w):
                return float(logit_fit(X,yy,w)[0]*np.sqrt(np.average(X[:,0]**2,weights=w)))
            result['estimate']=estimate(np.ones(len(t)))
            result['ratio']=result['estimate']/same
            positions=np.searchsorted(roster,ids)[inv]
            bank=[]
            for draw in samples:
                try:bank.append(estimate(draw[positions]))
                except InvalidFit:pass
            result['valid_draws']=len(bank)
            if len(bank)==draws:
                result['interval']=np.quantile(bank,[.025,.975]).tolist()
        except InvalidFit as error:
            result['reason']=str(error)
    output['reading']=reading(output['all'],output['short'])
    return output


