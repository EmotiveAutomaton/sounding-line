"""CH4 registered secondary readouts with a conditional AR(1) dynamic null.

DESIGN CHECK: LESSONS 3-5, CONTROLS 4-6. Never shuffle deviations: the null
retains fitted temporal persistence and the fitted target response. Counts
without excursions are unsupported, never zero-rate evidence. Simulated clock
paths obey the same clock floor and stopping/crossing definitions as observations.
"""
from __future__ import annotations
from collections import Counter
import hashlib,math
import numpy as np
from .week5_ch_histories import reserve_arrays,target_fit

SEED=20261107


def sequences(games,medians,start_move=10):
    output=[];knots=sorted(medians)
    if not knots:return output
    for game in games:
        if game['first_clock'] is None or game['first_clock']<game['initial']:continue
        sequence=[]
        for row in game['rows']:
            move=(row['ply']+1)//2
            if move<start_move:continue
            if row['clock_before'] is None or row['think_time'] is None or row['think_time']<=0 or row['clock_before']/game['initial']<.15:
                if sequence:output.append(sequence);sequence=[]
                continue
            median=float(np.interp(move,knots,[medians[k] for k in knots]))
            sequence.append(dict(share=row['clock_before']/game['initial'],move=move,increment=game['increment'],
                                 initial=game['initial'],median=median,logtime=math.log(row['think_time'])))
        if sequence:output.append(sequence)
    return output


def mean_response(item,model):
    deviation=item['share']-item['median']-model['target']
    x=np.array([1,item['share'],item['move'],item['increment'],min(deviation,0),max(deviation,0)])
    return float(x@model['beta'])


def fit_controller(train,start_move=10):
    a,z,medians,_=reserve_arrays(train,start_move)
    base=np.column_stack([np.ones(len(a)),a[:,1],a[:,2],a[:,3]])
    model=target_fit(a[:,0],base,z);pairs=[];residuals=[]
    for sequence in sequences(train,medians,start_move):
        r=[item['logtime']-mean_response(item,model) for item in sequence];residuals.extend(r);pairs.extend(zip(r[:-1],r[1:]))
    if len(pairs)<20:raise ValueError('Insufficient within-game residual transitions')
    pairs=np.asarray(pairs);den=pairs[:,0]@pairs[:,0]
    phi=float(pairs[:,0]@pairs[:,1]/den) if den else 0.
    if abs(phi)>=1:raise ValueError('Nonstationary fitted residual null')
    sigma=float(np.std(pairs[:,1]-phi*pairs[:,0]));model.update(medians=medians,phi=phi,sigma=sigma,residual_sd=float(np.std(residuals)))
    return model


def excursions(sequence,target,threshold=.3,horizon=10,settle_band=.05):
    counts=Counter();i=0
    while i<len(sequence):
        item=sequence[i];absolute_target=item['median']+target
        if absolute_target<=0:i+=1;continue
        deviation=item['share']-absolute_target;direction=-1 if deviation<-threshold*absolute_target else 1 if deviation>threshold*absolute_target else 0
        if not direction:i+=1;continue
        label='deficit' if direction<0 else 'surplus';counts[label+'_excursions']+=1;crossed=False;stable=0;j=i
        for j in range(i+1,min(len(sequence),i+horizon+1)):
            d=sequence[j]['share']-sequence[j]['median']-target
            crossed=crossed or direction*d<0
            stable=stable+1 if abs(d)<=settle_band else 0
            if stable>=2:break
        if crossed:counts[label+'_overshoots']+=1
        elif j==len(sequence)-1:counts[label+'_end_censored']+=1
        # Count one excursion, not every move spent in the same excursion.
        i=max(i+1,j+1)
    return counts


def simulate(sequence,model,rng):
    if not sequence:return []
    result=[];share=sequence[0]['share'];residual=rng.normal(0,model['residual_sd'])
    for original in sequence:
        if share<.15:break
        item=dict(original,share=share);residual=model['phi']*residual+rng.normal(0,model['sigma'])
        logtime=mean_response(item,model)+residual
        if logtime>50:break # effectively flagged; no finite-clock move is observed
        elapsed=math.exp(logtime);item['logtime']=logtime;result.append(item)
        share=share+(item['increment']-elapsed)/item['initial']
    return result


def overshoot_player(player,train,test,start_move=10,threshold=.3,simulations=20):
    model=fit_controller(train,start_move);actual=sequences(test,model['medians'],start_move)
    observed=Counter();null=Counter()
    seed=int.from_bytes(hashlib.sha256(f'{SEED}:overshoot:{player}'.encode()).digest()[:8],'little');rng=np.random.default_rng(seed)
    for seq in actual:
        observed.update(excursions(seq,model['target'],threshold))
        for _ in range(simulations):null.update(excursions(simulate(seq,model,rng),model['target'],threshold))
    excess={}
    for side in ('deficit','surplus'):
        n=observed[side+'_excursions']-observed[side+'_end_censored'];m=null[side+'_excursions']-null[side+'_end_censored']
        excess[side]=None if not n or not m else observed[side+'_overshoots']/n-null[side+'_overshoots']/m
    return dict(observed=dict(observed),matched_null=dict(null),excess=excess,phi=model['phi'],simulations=simulations)


def concentration(games,by='games'):
    if by=='games':counts=Counter(g['time_control'] for g in games)
    elif by=='days':
        pairs={(g['time_control'],int(g['start']//86400)) for g in games if g['start'] is not None};counts=Counter(tc for tc,_ in pairs)
    else:raise ValueError('Unknown concentration unit')
    return max(counts.values())/sum(counts.values()) if counts else None


def bootstrap_mean(values,draws=2000):
    values=np.asarray(values,float)
    if not len(values):return dict(status='unsupported',count=0,estimate=None,interval=None)
    if len(values)<2:return dict(status='below floor, descriptive',count=1,estimate=float(values[0]),interval=None)
    rng=np.random.default_rng(SEED);means=[float(np.mean(values[rng.integers(0,len(values),len(values))])) for _ in range(draws)]
    return dict(status='descriptive',count=len(values),estimate=float(np.mean(values)),interval=np.quantile(means,[.025,.975]).tolist())


def precision_difference(concentrations,slopes,draws=2000):
    concentrations=np.asarray(concentrations);slopes=np.asarray(slopes);n=len(slopes)
    def contrast(c,s):
        high=c>=np.quantile(c,.75)
        if not np.any(high) or np.all(high):raise ValueError('No concentration comparison')
        return float(np.median(s[high])-np.median(s[~high]))
    try:point=contrast(concentrations,slopes)
    except ValueError:return dict(status='unsupported',count=n,reason='No high/low concentration support')
    rng=np.random.default_rng(SEED);values=[];invalid=0
    for _ in range(draws):
        ix=rng.integers(0,n,n)
        try:values.append(contrast(concentrations[ix],slopes[ix]))
        except ValueError:invalid+=1
    return dict(status='descriptive' if not invalid else 'invalid uncertainty',count=n,estimate=point,
                interval=None if invalid else np.quantile(values,[.025,.975]).tolist(),invalid_draws=invalid)
