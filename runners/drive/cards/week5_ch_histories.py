"""CH4 reserve targets and CH6 stopping, on private sampled player histories.

DESIGN CHECK: LESSONS 2-5. Chronological train/test partitions prohibit test
medians, fitted targets, variances or session boundaries leaking into training.
Planted targets locate within 5% clock; source-window tails are censored.
Clock-forced responses are excluded by observed share, not centered reserve.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import json,math,sqlite3
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit
from .week5_ch_models import verdict,regress,keep_columns,demean
from .week5_ch_source import write_json,digest
from . import week5_ch_progress as progress

SEED=20261107


def load_histories(database,constructed=False):
    con=sqlite3.connect(database);result=defaultdict(list)
    try:
        if not constructed:
            states=con.execute('SELECT complete FROM checkpoints').fetchall()
            if not states or not all(row[0] for row in states):raise ValueError('Incomplete source histories')
        for month,ordinal,payload in con.execute('SELECT month,ordinal,payload FROM histories ORDER BY month,ordinal'):
            game=json.loads(payload);meta=game['meta']
            for player in sorted({r['player'] for r in game['rows']}):
                side=meta['players'].index(player)
                result[player].append(dict(game=game['game'],month=month,start=meta['start'],end=meta['end'],initial=meta['initial'],
                    increment=meta['increment'],time_control=meta['time_control'],rating_change=meta['rating_changes'][side],
                    result=(1 if meta['result']==('1-0' if side==0 else '0-1') else 0 if meta['result']=='1/2-1/2' else -1),
                    first_clock=game['first_clocks'][side],rows=[r for r in game['rows'] if r['player']==player]))
    finally:con.close()
    return result


def make_sessions(histories,gap_minutes=30,tc=None,year=None):
    rows=[];counts=Counter();session_counts={}
    for player in sorted(histories):
        original=histories[player];counts['games_before_restrictions']+=len(original)
        counts['missing_start_timestamp']+=sum(g['start'] is None for g in original)
        counts['other_time_control']+=sum(g['start'] is not None and tc is not None and g['time_control']!=tc for g in original)
        counts['other_year']+=sum(g['start'] is not None and (tc is None or g['time_control']==tc) and year is not None and not g['month'].startswith(str(year)) for g in original)
        games=[g for g in original if g['start'] is not None and (tc is None or g['time_control']==tc) and (year is None or g['month'].startswith(str(year)))]
        games.sort(key=lambda g:(g['start'],g['game']));sessions=0;net=0.;played=0;streak=0
        for i,game in enumerate(games):
            counts['eligible_games']+=1
            if i==0 or games[i-1]['month']!=game['month'] or game['start']-(games[i-1]['end'] if games[i-1]['end'] is not None else games[i-1]['start'])>=gap_minutes*60:
                sessions+=1;net=0.;played=0;streak=0
            played+=1
            if game['rating_change'] is None:net=float('nan');counts['missing_rating_change']+=1
            else:net+=game['rating_change']
            streak=streak+game['result'] if streak*game['result']>0 else game['result']
            if i+1==len(games) or games[i+1]['month']!=game['month']:
                counts['right_censored_window_tail']+=1;continue
            endpoint=game['end'] if game['end'] is not None else game['start']
            counts['direct_end_gap' if game['end'] is not None else 'start_time_gap_proxy']+=1
            stop=games[i+1]['start']-endpoint>=gap_minutes*60
            if not math.isfinite(net):continue
            rows.append(dict(player=player,stop=int(stop),net=net,positive=int(net>0),zero=int(net==0),last_result=game['result'],
                             games=played,hour=(game['start']/3600)%24,streak=streak,month=game['month']))
        session_counts[player]=sessions
    counts['players']=len(session_counts);counts['players_at_least_five_sessions']=sum(n>=5 for n in session_counts.values())
    return rows,dict(counts),session_counts


def fixed_logit(y,x,groups,within=True,maxiter=100):
    y=np.asarray(y,float);x=np.asarray(x,float);groups=np.asarray(groups);ids,index=np.unique(groups,return_inverse=True)
    if not within:x=np.column_stack([x,np.ones(len(x))]);index=np.zeros(len(x),dtype=int);ids=np.array(['pooled'])
    n=np.bincount(index);s=np.bincount(index,weights=y)
    keep=(s>0)&(s<n)
    if within:
        mask=keep[index];x=x[mask];y=y[mask];groups=groups[mask];ids,index=np.unique(groups,return_inverse=True)
        n=np.bincount(index);s=np.bincount(index,weights=y)
    if len(y)==0 or len(np.unique(y))<2:raise ValueError('No within-player stop variation')
    if within:
        centered=demean(y,x,groups)[1];kept=keep_columns(centered,required=1)
    else:kept=keep_columns(x,required=1)
    x=x[:,kept]
    # Scale nuisance without changing target's units; expose beta in original scale.
    scale=x.std(axis=0);scale[scale<1e-9]=1;x=x/scale
    beta=np.zeros(x.shape[1]);alpha=np.log((s+.5)/(n-s+.5)) if within else np.zeros(1)
    def objective(a,b):
        eta=(a[index] if within else 0)+x@b
        return float(np.sum(np.logaddexp(0,eta)-y*eta))
    prior=objective(alpha,beta);converged=False
    for iteration in range(maxiter):
        eta=(alpha[index] if within else 0)+x@beta;p=expit(eta);w=np.maximum(p*(1-p),1e-8);r=y-p
        if within:
            sw=np.bincount(index,weights=w);sr=np.bincount(index,weights=r)
            sx=np.column_stack([np.bincount(index,weights=w*x[:,j]) for j in range(x.shape[1])])
            xcenter=x-sx[index]/sw[index,None]
            h=xcenter.T@(w[:,None]*xcenter);g=xcenter.T@r
        else:h=x.T@(w[:,None]*x);g=x.T@r
        step=np.linalg.lstsq(h,g,rcond=1e-10)[0]
        astep=(sr-sx@step)/sw if within else np.zeros(1)
        factor=1.
        while factor>1/1024:
            candidate=objective(alpha+factor*astep,beta+factor*step)
            if candidate<=prior+1e-9:break
            factor/=2
        alpha+=factor*astep;beta+=factor*step
        if max(np.max(np.abs(factor*step)),np.max(np.abs(factor*astep)))<1e-6:converged=True;break
        prior=candidate
    if not converged:raise ValueError('Fixed logit did not converge')
    return dict(coefficients=(beta/scale).tolist(),kept_columns=kept,observations=len(y),players=len(ids),excluded_constant_players=int(np.sum(~keep)) if within else 0,iterations=iteration+1)


def stopping(histories,gap_minutes=30,tc=None,year=None,draws=2000,floor=10000,streak=False):
    # Compact per-player arrays bound memory; rich move histories never coexist
    # across players. The exact session function is shared with known answers.
    blocks=[];counts=Counter();session_numbers=[]
    for player in histories:
        rows,exposure,sessions=make_sessions({player:histories[player]},gap_minutes,tc,year)
        counts.update(exposure)
        if rows:
            blocks.append(np.array([[r[k] for k in ('stop','net','positive','zero','last_result','games','hour','streak')] for r in rows],float));session_numbers.append(sessions[player])
    within=sum(n>=5 for n in session_numbers)>=floor
    if within:blocks=[block for block,n in zip(blocks,session_numbers) if n>=5]
    counts=dict(counts)
    def design(rs,continuous=False):
        columns=[rs[:,1]/10 if continuous else rs[:,2],rs[:,3],rs[:,4],rs[:,5],np.sin(2*np.pi*rs[:,6]/24),np.cos(2*np.pi*rs[:,6]/24)]
        if streak:columns.append(rs[:,7])
        return np.column_stack(columns)
    if not blocks:return dict(card='CH6',status='unsupported',counts=counts,verdict='inconclusive')
    def assemble(indices):
        return np.concatenate([blocks[i] for i in indices]),np.concatenate([np.full(len(blocks[i]),copy,dtype=np.int32) for copy,i in enumerate(indices)])
    rows,groups=assemble(range(len(blocks)))
    try:
        point=fixed_logit(rows[:,0],design(rows),groups,within)
        secondary=fixed_logit(rows[:,0],design(rows,True),groups,within)
    except ValueError as exc:return dict(card='CH6',status='unsupported',reason=str(exc),counts=counts,verdict='inconclusive')
    values=[];continuous_values=[];invalid=0;rng=np.random.default_rng(SEED)
    checkpoint=progress.begin('CH6-whole-player-logistic',draws)
    for index in range(draws):
        sample,sample_groups=assemble(rng.integers(0,len(blocks),len(blocks)))
        def compute():
            try:
                primary=fixed_logit(sample[:,0],design(sample),sample_groups,within)['coefficients'][0]
                continuous=fixed_logit(sample[:,0],design(sample,True),sample_groups,within)['coefficients'][0]
                return [primary,continuous]
            except ValueError:return None
        result=progress.value(checkpoint,index,compute)
        if result is None:invalid+=1
        else:values.append(result[0]);continuous_values.append(result[1])
    ci=np.quantile(values,[.025,.975]).tolist() if not invalid and len(blocks)>=2 else None
    return dict(card='CH6',status='complete' if within else 'below floor, descriptive',counts=counts,point=point,log_odds=point['coefficients'][0],
                odds_ratio=math.exp(point['coefficients'][0]),interval_log=ci,interval_OR=None if ci is None else np.exp(ci).tolist(),
                verdict=verdict(ci,math.log(1.05)),routing_verdict=verdict(ci,math.log(1.05)) if within else 'inconclusive',bar_OR=1.05,draws=draws,invalid_draws=invalid,continuous_gain_per10=secondary['coefficients'][0],
                continuous_interval=None if ci is None else np.quantile(continuous_values,[.025,.975]).tolist(),
                session_gap_basis='direct end where available; start-to-start fallback otherwise',causal_claim=False)


def reserve_arrays(games,start_move=10,medians=None):
    values=[];counts=Counter()
    for game in games:
        counts['games_before_clock_restrictions']+=1;counts['moves_before_clock_restrictions']+=len(game['rows'])
        if game['first_clock'] is None:counts['missing_first_clock_games']+=1;continue
        if game['first_clock']<game['initial']:
            counts['subinitial_first_clock_games']+=1
            counts['exact_half_initial_games']+=abs(game['first_clock']-game['initial']/2)<1e-6
            continue
        for row in game['rows']:
            move=(row['ply']+1)//2
            if move<start_move:counts['before_start_move']+=1;continue
            counts['candidate_moves']+=1
            if row['clock_before'] is None or row['think_time'] is None or row['think_time']<=0:counts['unmeasured_moves']+=1;continue
            share=row['clock_before']/game['initial']
            if share<.15:counts['clock_floor_moves']+=1;continue
            values.append([math.log(row['think_time']),share,move,game['increment']])
    a=np.asarray(values,float).reshape(-1,4)
    if medians is None:medians={int(k):float(np.median(a[a[:,2]==k,1])) for k in sorted(set(a[:,2]))}
    if len(a)==0 or not medians:return a,np.empty(0),medians,dict(counts)
    knots=sorted(medians);baseline=np.interp(a[:,2],knots,[medians[k] for k in knots]);reserve=a[:,1]-baseline
    return a,reserve,medians,dict(counts)


def target_fit(y,base,reserve,band=False):
    if len(y)<20 or np.ptp(reserve)<.05:raise ValueError('Insufficient target variation')
    def at(target,width=0):
        x=np.column_stack([base,np.minimum(reserve-target+width,0),np.maximum(reserve-target-width,0)])
        b=np.linalg.lstsq(x,y,rcond=None)[0];err=y-x@b;return float(err@err),b
    low,high=np.quantile(reserve,[.1,.9]);grid=np.linspace(low,high,41);candidates=[]
    for width in ([0,.025,.05,.1,.15] if band else [0]):
        losses=[at(t,width)[0] for t in grid];i=int(np.argmin(losses))
        fit=minimize_scalar(lambda t:at(t,width)[0],bounds=(grid[max(0,i-1)],grid[min(len(grid)-1,i+1)]),method='bounded')
        loss,beta=at(fit.x,width);candidates.append((loss,float(fit.x),width,beta))
    loss,target,width,beta=min(candidates,key=lambda v:v[0]);variance=max(loss/len(y),1e-9)
    # Profile scale is secondary only: residual dependence makes this naive
    # likelihood interval unsuitable for an inferential claim about learning.
    profile=[float(t) for t in np.sort(np.append(grid,target)) if len(y)*math.log(max(at(t,width)[0],1e-9)/max(loss,1e-9))<=3.841458820694124]
    interval=[min(profile),max(profile)]
    return dict(target=target,width=width,beta=beta,variance=variance,profile_interval=interval)


def reserve_gain(train,test,start_move=10,band=False):
    a,z,medians,train_counts=reserve_arrays(train,start_move);b,zt,_,test_counts=reserve_arrays(test,start_move,medians)
    result=gain_from_arrays(a,z,b,zt,band)
    result.update(train_counts=train_counts,test_counts=test_counts)
    return result


def gain_from_arrays(a,z,b,zt,band=False):
    if len(a)<20 or len(b)<10:raise ValueError('Insufficient measured target moves')
    base=np.column_stack([np.ones(len(a)),a[:,1],a[:,2],a[:,3]]);testbase=np.column_stack([np.ones(len(b)),b[:,1],b[:,2],b[:,3]])
    target=target_fit(a[:,0],base,z,band);plain=np.linalg.lstsq(base,a[:,0],rcond=None)[0];plain_var=max(float(np.mean((a[:,0]-base@plain)**2)),1e-9)
    x=np.column_stack([testbase,np.minimum(zt-target['target']+target['width'],0),np.maximum(zt-target['target']-target['width'],0)])
    gain=.5*(np.log(plain_var/target['variance'])+(b[:,0]-testbase@plain)**2/plain_var-(b[:,0]-x@target['beta'])**2/target['variance'])
    return dict(gain=float(np.mean(gain)),moves=len(b),target=float(target['target']),width=float(target['width']),profile_interval=target['profile_interval'],profile_width=float(np.ptp(target['profile_interval'])),
                left_slope=float(target['beta'][1]+target['beta'][-2]),right_slope=float(target['beta'][1]+target['beta'][-1]))


def target_recovery(seed=SEED,players=200):
    rng=np.random.default_rng(seed);errors=[]
    for _ in range(players):
        z=rng.uniform(-.3,.3,800);target=rng.uniform(-.12,.12);base=np.column_stack([np.ones(len(z)),rng.uniform(.2,1.,len(z)),rng.integers(10,60,len(z)),rng.integers(0,5,len(z))])
        y=base@np.array([1,.2,.001,.01])+3*np.minimum(z-target,0)-2*np.maximum(z-target,0)+rng.normal(0,.03,len(z))
        fit=target_fit(y,base,z);errors.append(abs(fit['target']-target))
    return dict(players=players,max_absolute_target_error=float(max(errors)),pass_gate=max(errors)<=.05)


def reserve(histories,tc='blitz',start_move=10,draws=2000,floor=1000,threshold=.3,concentration_by='games',include_secondaries=True):
    from .week5_ch_reserve_secondaries import overshoot_player,concentration,bootstrap_mean,precision_difference
    per=[];counts=Counter();curves=[];curve_widths=[];bands=[];concentrations=[];slopes=[];overshoots=[];pooled_players=[]
    players=sorted(histories);checkpoint=progress.begin('CH4-per-player-targets-and-secondaries',len(players))
    for player_index,player in enumerate(players):
        original=histories[player];counts['games_before_restrictions']+=len(original)
        counts['other_time_control_games']+=sum(g['time_control']!=tc for g in original);counts['missing_start_games']+=sum(g['time_control']==tc and g['start'] is None for g in original)
        games=sorted([g for g in original if g['time_control']==tc and g['start'] is not None],key=lambda g:(g['start'],g['game']))
        counts['players_before_floor']+=1
        if len(games)<2:
            counts['under_two_games']+=1;progress.value(checkpoint,player_index,lambda:dict(status='under_two_games'));continue
        split=int(.7*len(games));train,test=games[:split],games[split:]
        a,z,medians,_=reserve_arrays(train,start_move);b,zt,_,_=reserve_arrays(test,start_move,medians)
        if len(a)>=20 and len(b)>=10:pooled_players.append(player)
        if len(games)<50:
            counts['under50_games']+=1;progress.value(checkpoint,player_index,lambda:dict(status='under50_games'));continue
        def compute():
            local_counts=Counter()
            try:
                fitted=reserve_gain(train,test,start_move);band=reserve_gain(train,test,start_move,True)
                result=dict(status='supported',fitted=fitted,band_gain=band['gain']-fitted['gain'],concentration=concentration(histories[player],concentration_by),slope=(fitted['left_slope']+fitted['right_slope'])/2,curve=None,widths=None,overshoot=None)
                if len(games)>=115:
                    try:
                        fits=[reserve_gain(train[:n],test,start_move) for n in (10,20,40,80)];result.update(curve=[f['gain'] for f in fits],widths=[f['profile_width'] for f in fits])
                    except ValueError:local_counts['learning_curve_unsupported_players']+=1
                if include_secondaries:
                    try:result['overshoot']=overshoot_player(player,train,test,start_move,threshold)
                    except ValueError:local_counts['overshoot_null_unsupported_players']+=1
            except ValueError:result=dict(status='insufficient_measured_target_support');local_counts['insufficient_measured_target_support']+=1
            result['counts']=dict(local_counts);return result
        result=progress.value(checkpoint,player_index,compute);counts.update(result['counts'])
        if result['status']=='supported':
            fitted=result['fitted'];per.append(dict(player=player,**fitted));bands.append(result['band_gain']);concentrations.append(result['concentration']);slopes.append(result['slope'])
            counts.update({'train_'+key:value for key,value in fitted['train_counts'].items()});counts.update({'test_'+key:value for key,value in fitted['test_counts'].items()})
            if result['curve'] is not None:curves.append(result['curve']);curve_widths.append(result['widths'])
            if result['overshoot'] is not None:overshoots.append(result['overshoot'])
    n=len(per);counts['supported_players']=n
    if n<floor:
        try:
            pooled=[]
            for player in pooled_players:
                games=sorted([g for g in histories[player] if g['time_control']==tc and g['start'] is not None],key=lambda g:(g['start'],g['game']));split=int(.7*len(games))
                a,z,medians,_=reserve_arrays(games[:split],start_move);b,zt,_,_=reserve_arrays(games[split:],start_move,medians);pooled.append((a,z,b,zt))
            combined=[np.concatenate([row[i] for row in pooled]) for i in range(4)]
            fallback=gain_from_arrays(*combined);gains=[];invalid=0;rng=np.random.default_rng(SEED)
            fallback_checkpoint=progress.begin('CH4-pooled-fallback-bootstrap',draws)
            for index in range(draws):
                selection=rng.integers(0,len(pooled),len(pooled))
                def compute():
                    try:return gain_from_arrays(*[np.concatenate([pooled[j][i] for j in selection]) for i in range(4)])['gain']
                    except ValueError:return None
                gain=progress.value(fallback_checkpoint,index,compute)
                if gain is None:invalid+=1
                else:gains.append(gain)
            ci=np.quantile(gains,[.025,.975]).tolist() if len(pooled)>=2 and not invalid else None
            return dict(card='CH4',status='below floor, descriptive',counts=dict(counts),pooled_players=len(pooled),pooled_fit=fallback,
                        interval=ci,verdict=verdict(ci,.005),routing_verdict='inconclusive',bar=.005,draws=draws,invalid_draws=invalid,
                        fallback='pooled target with each player training-only move medians; whole-player refits',
                        per_player_secondary_support=n)
        except ValueError:return dict(card='CH4',status='unsupported',counts=dict(counts),verdict='inconclusive',reason='Pooled fallback lacks measured target variation')
    gains=np.array([p['gain'] for p in per]);moves=np.array([p['moves'] for p in per]);rng=np.random.default_rng(SEED);samples=[]
    for _ in range(draws):
        indices=rng.integers(0,n,n);samples.append(float(np.average(gains[indices],weights=moves[indices])))
    ci=np.quantile(samples,[.025,.975]).tolist() if n>=2 else None
    return dict(card='CH4',status='complete',counts=dict(counts),gain=float(np.average(gains,weights=moves)),equal_player_gain_secondary=float(gains.mean()),weighting='held-out moves; whole players resampled',interval=ci,
                verdict=verdict(ci,.005),bar=.005,draws=draws,band_minus_point_gain=float(np.mean(bands)),
                learning_curve_mean=None if not curves else np.mean(curves,axis=0).tolist(),learning_curve_players=len(curves),
                learning_curve_profile_width_scale_only=None if not curve_widths else np.mean(curve_widths,axis=0).tolist(),
                by_construction=['sampling alone narrows target intervals','clock floor excludes forced fast moves'],
                precision=precision_difference(concentrations,slopes,draws),band_minus_point_interval=bootstrap_mean(bands,draws),
                learning_curve_slope=bootstrap_mean([np.polyfit(np.log2([10,20,40,80]),curve,1)[0] for curve in curves],draws),
                overshoot={side:bootstrap_mean([row['excess'][side] for row in overshoots if row['excess'][side] is not None],draws) for side in ('deficit','surplus')},
                overshoot_counts={kind:dict(sum((Counter(row[kind]) for row in overshoots),Counter())) for kind in ('observed','matched_null')},
                overshoot_null='fitted target dynamics plus training residual AR(1), 20 simulations per held-out game')


def execute_body(output,inputs,config):
    from .week5_ch_collection import verified_spec
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    path=verified_spec(inputs['histories'])
    if config.get('constructed_fixture'):
        con=sqlite3.connect(path)
        try:
            if con.execute("SELECT value FROM settings WHERE key='constructed_fixture'").fetchone()!=('true',):raise ValueError('History fixture bypass requires constructed database')
        finally:con.close()
    from .week5_ch_history_index import HistoryStore
    histories=HistoryStore(path,config.get('constructed_fixture',False))
    try:
        if config['card']=='CH6':result=stopping(histories,config.get('gap_minutes',30),config.get('time_control'),config.get('year'),config.get('draws',2000),config.get('floor',10000),config.get('streak',False))
        elif config['card']=='CH4':result=reserve(histories,config.get('time_control','blitz'),config.get('start_move',10),config.get('draws',2000),config.get('floor',1000),config.get('overshoot_threshold',.3),config.get('concentration_by','games'),config.get('include_secondaries',True))
        else:raise ValueError('Unknown history card')
    finally:histories.close()
    result['constructed_fixture']=bool(config.get('constructed_fixture'))
    write_json(output/'SCIENCE.json',result);return dict(status='complete',card=config['card'])


def execute(output,inputs,config):
    try:
        with progress.tracking(output,inputs,config):return execute_body(output,inputs,config)
    except progress.YieldRequested as exc:return dict(status='yielded',reason=str(exc),checkpoint=str(Path(output)/'CHECKPOINT.json'))


def verify(output,inputs,config):
    output=Path(output);execute(output/'replay',{k:v for k,v in inputs.items() if k!='resume_analysis'},config)
    if digest(output/'SCIENCE.json')!=digest(output/'replay/SCIENCE.json'):raise ValueError('History model replay differs')
    return dict(verified=True,complete_recalculation=True)
