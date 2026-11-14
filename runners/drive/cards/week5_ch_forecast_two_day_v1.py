"""Frozen independent player split and ordered loss/draw/win forecast.

DESIGN CHECK: split rehash explicitly approved before outcomes; the original
history population stays intact. Calibration must have all three outcomes.
Empty deciles, unconverged fits and unsupported controls remain explicit.
"""
import hashlib
import math
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

SPLIT_PREFIX = 'SG1-forecast|20261112|'


def calibration(player):
    return hashlib.sha256((SPLIT_PREFIX + player).encode()).hexdigest()[0] in '012'


def probabilities(parameters, x):
    """Proportional-odds logistic model; category order is loss, draw, win."""
    x = np.asarray(x,float)
    cut1, log_distance, gap, black = np.asarray(parameters,float)
    distance = np.exp(log_distance)
    eta = x @ np.array([gap,black])
    lower = expit(cut1-eta)
    upper = expit(cut1+distance-eta)
    return np.column_stack((lower,upper-lower,1-upper))


def probabilities_reference(parameters, x):
    """Separate odds arithmetic for independent formula replay."""
    cut1, log_distance, gap, black = map(float,parameters)
    x = np.asarray(x,float)
    score = gap*x[:,0]+black*x[:,1]
    low_z = cut1-score
    high_z = cut1+math.exp(log_distance)-score
    # tanh identity avoids overflow and is independently coded from expit.
    low = .5*(1+np.tanh(low_z/2))
    high = .5*(1+np.tanh(high_z/2))
    return np.array([low, high-low, 1-high]).T


def fit(x, y, reference=False, check=lambda:None):
    x,y=np.asarray(x,float),np.asarray(y,int)
    if x.ndim!=2 or x.shape[1]!=2 or len(x)!=len(y) or not np.isfinite(x).all():
        raise ValueError('Invalid ordered forecast rows')
    if set(y.tolist()) != {0,1,2}:
        raise ValueError('Ordered forecast needs loss, draw and win calibration outcomes')
    if np.linalg.matrix_rank(np.column_stack((np.ones(len(x)),x)))!=3:
        raise ValueError('Ordered forecast calibration design has no rank')
    law = probabilities_reference if reference else probabilities
    def objective(p):
        with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
            q=law(p,x)[np.arange(len(y)),y]
            if not np.isfinite(q).all() or np.any(q<=0):return float('inf')
            return -float(np.mean(np.log(q)))
    fitted=minimize(objective,np.array([-1.,math.log(2.),1.,0.]),method='BFGS',
                    options=dict(gtol=1e-7,maxiter=500),callback=lambda p:check())
    gradient=float(np.max(np.abs(fitted.jac)))
    if not np.isfinite(fitted.fun) or not np.isfinite(fitted.x).all() or gradient>1e-5:
        raise ValueError('Ordered forecast fit unconverged')
    if np.max(np.abs(fitted.x))>30:
        raise ValueError('Ordered forecast is separated or numerically unsupported')
    return dict(parameters=fitted.x.tolist(),objective=float(fitted.fun),maximum_gradient=gradient,
                optimizer_success=bool(fitted.success),n=len(y),category_counts=np.bincount(y,minlength=3).tolist())


def expectation(parameters,x,reference=False):
    p=(probabilities_reference if reference else probabilities)(parameters,x)
    return p[:,2]+.5*p[:,1]


def decile_calibration(expected, score):
    expected,score=np.asarray(expected,float),np.asarray(score,float)
    if not len(expected):raise ValueError('No analysis players for forecast validation')
    cuts=np.quantile(expected,np.arange(1,10)/10)
    bins=np.searchsorted(cuts,expected,side='right')
    counts=np.bincount(bins,minlength=10)
    means=np.divide(np.bincount(bins,weights=expected,minlength=10),counts,
                    out=np.full(10,np.nan),where=counts>0)
    observed=np.divide(np.bincount(bins,weights=score,minlength=10),counts,
                       out=np.full(10,np.nan),where=counts>0)
    off=abs(means-observed)
    use=bool(np.any(off[np.isfinite(off)]>.03))
    return dict(cuts=cuts.tolist(),n=counts.tolist(),expected=[float(x) if math.isfinite(x) else None for x in means],
                observed=[float(x) if math.isfinite(x) else None for x in observed],
                use_decile_calibration=use,empty_deciles=int((counts==0).sum()),
                calibration_uses_analysis_outcomes=True,
                qualification='Packet-prescribed aggregate recalibration on analysis players; no out-of-sample calibration claim')


def rows_for_fit(games):
    usable=[r for r in games if r.get('score') in (0.,.5,1.) and r.get('rating') is not None and r.get('opponent_rating') is not None]
    return np.asarray([[(r['rating']-r['opponent_rating'])/100.,float(r['colour']=='black'),2*r['score']]
                       for r in usable],float).reshape(-1,3)


def prepare(store,check=lambda:None,reference=False):
    parts={};counts=Counter()
    for player in store:
        check()
        group='calibration' if calibration(player) else 'analysis'
        counts[group+'_players']+=1
        by_tc={}
        for row in store[player]:by_tc.setdefault(row['time_control'],[]).append(row)
        for tc,games in by_tc.items():
            values=rows_for_fit(games)
            counts[group+'_excluded_rows']+=len(games)-len(values)
            if len(values):parts.setdefault((tc,group),[]).append(values)
    output={}
    for tc in sorted({key[0] for key in parts}):
        check()
        if (tc,'calibration') not in parts or (tc,'analysis') not in parts:
            output[tc]=dict(status='unsupported',reason='No calibration or analysis rows')
            continue
        train=np.concatenate(parts[(tc,'calibration')]);test=np.concatenate(parts[(tc,'analysis')])
        try:
            fitted=fit(train[:,:2],train[:,2],reference,check)
            expected=expectation(fitted['parameters'],test[:,:2],reference)
            output[tc]=dict(status='complete',fit=fitted,
                           calibration=decile_calibration(expected,test[:,2]/2))
        except ValueError as exc:output[tc]=dict(status='unsupported',reason=str(exc))
    return dict(split_prefix=SPLIT_PREFIX,calibration_digits='012',counts=dict(counts),controls=output,
                approximation='ordered proportional-odds logistic forecast; no reconstruction of the rating system')


def predict(row,forecast,reference=False):
    spec=forecast['controls'].get(row['time_control'])
    if (not spec or spec['status']!='complete' or row.get('score') is None
            or row.get('rating') is None or row.get('opponent_rating') is None):return None
    x=[[(row['rating']-row['opponent_rating'])/100.,float(row['colour']=='black')]]
    expected=float(expectation(spec['fit']['parameters'],x,reference)[0])
    cal=spec['calibration']
    if cal['use_decile_calibration']:
        index=int(np.searchsorted(cal['cuts'],expected,side='right'))
        expected=cal['observed'][index]
    return expected


def enrich(games,forecast,reference=False):
    groups={}
    for r in games:
        if r['start'] is not None:groups.setdefault((r['time_control'],r['month']),[]).append(dict(r))
    output=[]
    for key in sorted(groups):
        rows=sorted(groups[key],key=lambda r:(r['start'],r['game']))
        session_sizes=Counter(r['session_id'] for r in rows)
        prior_surprise=0.;losing=0;last_session=None
        for index,row in enumerate(rows):
            expected=predict(row,forecast,reference)
            if row['session_id']!=last_session:prior_surprise=0.;losing=0
            row['E']=expected
            row['surprise']=None if expected is None or row['score'] is None else row['score']-expected
            row['form_before']=prior_surprise
            row['losing_streak']=losing+1 if row['score']==0 else 0
            row['previous_start_gap']=None if index==0 else row['start']-rows[index-1]['start']
            row['next_row']=dict(rows[index+1]) if index+1<len(rows) else None
            row['remaining_games']=session_sizes[row['session_id']]-row['index_in_session']
            if row['surprise'] is None:prior_surprise=float('nan')
            else:prior_surprise+=row['surprise']
            losing=row['losing_streak'];last_session=row['session_id'];output.append(row)
    return output
