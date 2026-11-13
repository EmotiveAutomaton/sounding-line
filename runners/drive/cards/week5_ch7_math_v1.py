"""CH7 frozen analytic units, own-player approximate null and cluster algebra.

DESIGN CHECK: fixed source scope and month-tail censoring; window references
carry across months. The null models three outcomes with feasible probabilities,
diagnoses positive update scales and never claims a Glicko-2 reconstruction.
"""
from collections import Counter,defaultdict
import math
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit
from .week5_ch_models import keep_columns,solve

SEED=20261111
MONTHS=('2017-04','2017-05','2017-06')
CONTROLS=('blitz','rapid')
# Compact numeric rows. NaN is private missing support, never a zero outcome.
PLAY,BELOW,ABOVE,GAMES,WIN,DRAW,STREAK,GAP,SIN,COS,TC,WB_BELOW,NEW_BEST,NEAR_BEST,GAIN,PACE,BEST_READY,PROV_START=range(18)
# Trace retains all games needed to simulate a full chronological source history.
T_TC,T_MONTH,T_START,T_RATING,T_OPP,T_DELTA,T_RESULT,T_KEEP,T_CENSORED,T_PACE,T_PROV=range(11)


def finite(value):return value is not None and math.isfinite(float(value))


def pace(game):
    shares=[row['think_time']/row['clock_before'] for row in game['rows']
            if finite(row.get('think_time')) and row['think_time']>0 and
            finite(row.get('clock_before')) and row['clock_before']>0]
    return float(np.median(shares)) if shares else float('nan')


def analytic_row(play,post,reference,best_before,number,result,losing,gap,hour,tc,gain,next_pace,ready,provisional):
    distance=(post-reference)/20.
    window=(post-max(best_before,post))/20.
    return [play,min(distance,0.),max(distance,0.),number,float(result==1),float(result==0),losing,
            gap/400.,math.sin(2*math.pi*hour/24),math.cos(2*math.pi*hour/24),tc,window,
            float(post>best_before),float(best_before-15<=post<=best_before),gain,next_pace,float(ready),float(provisional)]


def player_data(source_games):
    counts=Counter(games_before_restrictions=len(source_games));rows=[];trace=[];sessions={}
    for tc_index,tc in enumerate(CONTROLS):
        original=[g for g in source_games if g['time_control']==tc]
        counts['missing_start']+=sum(g['start'] is None for g in original)
        games=sorted((g for g in original if g['start'] is not None),key=lambda g:(g['start'],g['game']))
        groups=[]
        for game in games:
            if game['month'] not in MONTHS:raise ValueError('CH7 source month outside R2')
            if not finite(game.get('rating')) or not finite(game.get('opponent_rating')):
                raise ValueError('Source lacks authenticated pregame ratings')
            if not groups or groups[-1][-1]['month']!=game['month'] or game['start']-groups[-1][-1]['start']>=1800:
                groups.append([])
            groups[-1].append(game)
        bad={id(group):any(finite(g['rating_change']) and abs(g['rating_change'])>25 for g in group) for group in groups}
        counts['provisional_sessions_dropped']+=sum(bad.values())
        counts['provisional_session_games_dropped']+=sum(len(group) for group in groups if bad[id(group)])
        sessions[tc]=sum(not bad[id(group)] for group in groups)
        counts['eligible_sessions_'+tc]=sessions[tc]
        first_provisional=bool(games and finite(games[0]['rating_change']) and abs(games[0]['rating_change'])>25)
        counts['first_observed_provisional_'+tc]+=int(first_provisional)
        best=float('-inf');ordinal=0;index=0
        for group in groups:
            reference=group[0]['rating'];losing=0
            for number,game in enumerate(group,1):
                ordinal+=1
                best=max(best,game['rating'])
                result=game['result'];delta=game['rating_change']
                losing=losing+1 if result==-1 else 0
                next_game=games[index+1] if index+1<len(games) else None
                censored=next_game is None or next_game['month']!=game['month']
                play=False if censored else next_game['start']-game['start']<1800
                next_pace=pace(next_game) if play else float('nan')
                valid=finite(delta) and result in (-1,0,1)
                keep=not bad[id(group)] and valid
                trace.append([tc_index,MONTHS.index(game['month']),game['start'],game['rating'],game['opponent_rating'],
                              float(delta) if finite(delta) else float('nan'),float(result) if result in (-1,0,1) else float('nan'),
                              float(keep),float(censored),next_pace,float(first_provisional)])
                counts['right_censored_month_tail']+=int(censored)
                counts['missing_change_or_result']+=int(not valid)
                if keep and not censored:
                    post=game['rating']+delta
                    rows.append(analytic_row(int(play),post,reference,best,number,result,losing,
                        game['rating']-game['opponent_rating'],(game['start']/3600)%24,tc_index,delta,next_pace,
                        ordinal>30,first_provisional))
                    counts['playing_on_rows_'+tc]+=1
                    counts['pace_unavailable_rows']+=int(not math.isfinite(next_pace))
                if finite(delta):best=max(best,game['rating']+delta)
                index+=1
    return dict(rows=np.asarray(rows,float).reshape(-1,18),trace=np.asarray(trace,float).reshape(-1,11),
                sessions=sessions,counts=dict(counts))


def expected_score(gap):return expit(np.asarray(gap,float)*math.log(10)/400.)


def result_probabilities(expected,draw_fraction):
    p=np.asarray(expected,float)
    if np.any(~np.isfinite(p)) or np.any((p<0)|(p>1)) or not 0<=draw_fraction<=1:
        raise ValueError('Invalid result probabilities')
    draw=draw_fraction*2*np.minimum(p,1-p)
    probabilities=np.stack([1-p-draw/2,draw,p-draw/2],axis=-1) # loss, draw, win
    if np.any(probabilities<0) or not np.allclose(probabilities.sum(axis=-1),1,atol=1e-14):
        raise ValueError('Infeasible win/draw/loss probabilities')
    return probabilities


def fit_draw_fraction(expected,results):
    p=np.asarray(expected,float);is_draw=np.asarray(results)==0
    a=2*np.minimum(p,1-p)
    if np.any(is_draw & (a==0)):raise ValueError('Draw impossible under this expected-score model')
    def loss(value):
        q=value*a
        if np.any(is_draw & (q<=0)) or np.any(~is_draw & (q>=1)):return float('inf')
        return -float(np.log(q[is_draw]).sum()+np.log1p(-q[~is_draw]).sum())
    fit=minimize_scalar(loss,bounds=(0,1),method='bounded')
    candidates=[(loss(0.),0.),(loss(1.),1.)]
    if fit.success:candidates.append((float(fit.fun),float(fit.x)))
    value,fraction=min(candidates)
    if not math.isfinite(value):raise ValueError('Own-player draw fit unsupported')
    return dict(fraction=fraction,boundary=fraction in (0.,1.),negative_log_likelihood=value)


def nuisance_columns(number,result,hour):
    return np.array([1.,number,float(result==1),float(result==0),math.sin(2*math.pi*hour/24),math.cos(2*math.pi*hour/24)])


def fit_playing_on(rows):
    y=rows[:,PLAY]
    if not len(y):raise ValueError('No own-player playing-on outcomes')
    if np.all(y==y[0]):return dict(constant=float(y[0]),status='constant observed probability')
    x=np.column_stack([np.ones(len(rows)),rows[:,[GAMES,WIN,DRAW,SIN,COS]]])
    kept=keep_columns(x,required=1);x=x[:,kept]
    if len(x)<=len(kept):raise ValueError('Own-player nuisance fit has no residual support')
    scale=np.std(x,axis=0);scale[scale==0]=1.;z=x/scale
    def objective(beta):
        eta=z@beta;p=expit(eta)
        return float((np.logaddexp(0,eta)-y*eta).sum()),z.T@(p-y)
    fitted=minimize(objective,np.zeros(len(kept)),jac=True,method='BFGS',options={'gtol':1e-7,'maxiter':300})
    grad=objective(fitted.x)[1]
    if (not fitted.success and np.max(np.abs(grad))>1e-5) or np.max(np.abs(fitted.x))>30:
        raise ValueError('Own-player nuisance fit singular, separated or unconverged')
    p=expit(z@fitted.x);information=z.T@((p*(1-p))[:,None]*z)
    if np.linalg.matrix_rank(information,tol=1e-10)!=len(kept):
        raise ValueError('Own-player nuisance information is singular')
    return dict(status='own-player unpenalized logistic',kept=kept,scale=scale.tolist(),beta=fitted.x.tolist(),
                maximum_gradient=float(np.max(np.abs(grad))))


def fit_null(data,allowed=(0,)):
    fitted={}
    for tc in allowed:
        trace=data['trace'];trace=trace[(trace[:,T_TC]==tc)&(trace[:,T_KEEP]==1)]
        rows=data['rows'];rows=rows[rows[:,TC]==tc]
        if not len(trace):continue
        p=expected_score(trace[:,T_RATING]-trace[:,T_OPP]);score=(trace[:,T_RESULT]+1)/2
        error=score-p;den=float(error@error)
        if den<=1e-12:raise ValueError('Own-player update scale has no support')
        scale=float(error@trace[:,T_DELTA]/den)
        if not math.isfinite(scale) or scale<=0:
            raise ValueError('Own-player update scale is not positive; no clipping or borrowing')
        residual=trace[:,T_DELTA]-scale*error
        fitted[str(tc)]=dict(update_scale=scale,update_rmse=float(np.sqrt(np.mean(residual**2))),
            update_rows=len(trace),draw=fit_draw_fraction(p,trace[:,T_RESULT]),play=fit_playing_on(rows))
    if not fitted:raise ValueError('No supported own-player null')
    return fitted


def simulate(data,fitted,seed):
    rng=np.random.default_rng(seed);rows=[]
    trace=data['trace']
    for key,parameters in sorted(fitted.items()):
        tc=int(key);games=trace[trace[:,T_TC]==tc]
        rating=games[0,T_RATING];reference=rating;best=rating;number=0;losing=0;previous_play=False;previous_month=None
        for ordinal,game in enumerate(games,1):
            if previous_month!=game[T_MONTH] or not previous_play:number=0;reference=rating
            number+=1
            gap=rating-game[T_OPP];expected=float(expected_score(gap))
            probabilities=result_probabilities(expected,parameters['draw']['fraction'])
            result=int(rng.choice([-1,0,1],p=probabilities))
            delta=parameters['update_scale']*((result+1)/2-expected);post=rating+delta
            losing=losing+1 if result==-1 else 0;hour=(game[T_START]/3600)%24
            playfit=parameters['play']
            if 'constant' in playfit:probability=playfit['constant']
            else:
                x=nuisance_columns(number,result,hour)[playfit['kept']]/np.asarray(playfit['scale'])
                probability=float(expit(x@playfit['beta']))
            play=bool(rng.random()<probability)
            if game[T_KEEP] and not game[T_CENSORED]:
                rows.append(analytic_row(int(play),post,reference,best,number,result,losing,gap,hour,tc,delta,
                            float('nan'),ordinal>30,bool(game[T_PROV])))
            best=max(best,post);rating=post;previous_play=play;previous_month=game[T_MONTH]
    return np.asarray(rows,float).reshape(-1,18)


def design(rows,kind='recent',gain_levels=None):
    nuisance=rows[:,[GAMES,WIN,DRAW,STREAK,GAP,SIN,COS,TC]]
    if kind in ('recent','pace'):
        return np.column_stack([rows[:,[BELOW,ABOVE]],nuisance]),2
    if kind=='window_slope':return np.column_stack([rows[:,WB_BELOW],nuisance]),1
    if kind=='new_best':
        extra=[(rows[:,GAIN]==gain).astype(float) for gain in (gain_levels or [])[1:]]
        return np.column_stack([rows[:,NEW_BEST],nuisance,*extra]),1
    raise ValueError('Unregistered CH7 estimand')


def subset(rows,kind):
    if kind=='pace':return rows[np.isfinite(rows[:,PACE])]
    if kind=='window_slope':return rows[rows[:,BEST_READY]==1]
    if kind=='new_best':return rows[(rows[:,BEST_READY]==1)&(rows[:,WIN]==1)&((rows[:,NEW_BEST]+rows[:,NEAR_BEST])>0)]
    if kind=='provisional_start':return rows[rows[:,PROV_START]==1]
    return rows


def sufficient_blocks(blocks,kind='recent'):
    blocks=[subset(block,kind) for block in blocks]
    gain_levels=None
    if kind=='new_best':
        levels=defaultdict(set)
        for block in blocks:
            for row in block:levels[row[GAIN]].add(row[NEW_BEST])
        gain_levels=sorted(gain for gain,classes in levels.items() if classes=={0.,1.})
        blocks=[block[np.isin(block[:,GAIN],gain_levels)] for block in blocks]
    actual_kind='recent' if kind=='provisional_start' else kind
    designs=[design(block,actual_kind,gain_levels)[0] for block in blocks]
    required=2 if actual_kind in ('recent','pace') else 1
    width=designs[0].shape[1] if designs else 0
    xx=np.zeros((len(blocks),width,width));xy=np.zeros((len(blocks),width));rows_count=0
    for i,(block,x) in enumerate(zip(blocks,designs)):
        if not len(block):continue
        y=block[:,PACE] if kind=='pace' else 1-block[:,PLAY] if kind=='new_best' else block[:,PLAY]
        x=x-x.mean(axis=0);y=y-y.mean();xx[i]=x.T@x;xy[i]=x.T@y;rows_count+=len(y)
    # Column selection from a square-root factor preserves rank without all rows.
    eigenvectors,eigenbasis=np.linalg.eigh(xx.sum(axis=0))
    if not len(eigenvectors):raise ValueError('No CH7 analytical rows')
    root=np.sqrt(np.maximum(eigenvectors,0))[:,None]*eigenbasis.T
    kept=keep_columns(root,required)
    return dict(xx=xx[:,kept][:,:,kept],xy=xy[:,kept],kept=kept,rows=rows_count,
                players_with_rows=sum(len(b)>0 for b in blocks),gain_levels=gain_levels)


def coefficients(statistics,weights=None):
    if weights is None:return solve(statistics['xx'].sum(axis=0),statistics['xy'].sum(axis=0))
    return solve(np.tensordot(weights,statistics['xx'],axes=1),weights@statistics['xy'])


def contrast(beta):return float(abs(beta[0])-abs(beta[1]))


def working_bar(stop_probability,null_contrasts):
    if len(null_contrasts)!=20 or not np.isfinite(null_contrasts).all():
        return None
    return max(.1*stop_probability,2*float(np.mean(np.abs(null_contrasts)))+3*float(np.std(null_contrasts,ddof=1)))


def pattern(interval,left,right,bar):
    if bar is None or any(value is None for value in (interval,left,right)):return 'mixed'
    inside=lambda value:value[0]>=-bar and value[1]<=bar
    outside=lambda value:value[0]>bar or value[1]<-bar
    if interval[0]>bar and inside(right):return 'floor'
    if outside(left) and outside(right) and inside(interval):return 'ladder'
    return 'mixed'
