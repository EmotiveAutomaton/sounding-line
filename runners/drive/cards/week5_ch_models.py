"""CH2/3/5 whole-player inference from complete independent-engine measurements.

DESIGN CHECK: LESSONS 3-5. Both planted signs and exact-zero truths are tested.
Fixed effects are removed within player; a bootstrap resamples whole players.
Rank failures remain invalid draws, never deleted. Floor failures take the
declared pooled descriptive route. Observational IV is not causal identification.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json, math, sqlite3
import numpy as np
from .week5_ch_source import write_json,digest
from . import week5_ch_progress as progress

SEED=20261107


def verdict(interval,bar):
    if interval is None:return 'inconclusive'
    lo,hi=interval
    if lo>bar:return 'supports'
    if hi<0 or (lo>=-bar and hi<=bar):return 'against'
    return 'inconclusive'


def demean(y,x,groups):
    ids,inverse=np.unique(groups,return_inverse=True);n=np.bincount(inverse).astype(float)
    ym=np.bincount(inverse,weights=y)/n
    xm=np.column_stack([np.bincount(inverse,weights=x[:,j])/n for j in range(x.shape[1])])
    return y-ym[inverse],x-xm[inverse],ids,inverse,n


def keep_columns(x,required=1):
    """Drop only redundant nuisance columns, preserving registered target order."""
    kept=[];basis=[]
    for j in range(x.shape[1]):
        v=x[:,j].copy();norm=np.linalg.norm(v)
        if norm:
            v/=norm
            for q in basis:v-=q@v*q
        residual=np.linalg.norm(v)
        if residual>1e-9:kept.append(j);basis.append(v/residual)
        elif j<required:raise ValueError('Primary target is not identifiable')
    return kept


def sufficient(y,x,groups,required=1,within=True):
    y=np.asarray(y,float);x=np.asarray(x,float);groups=np.asarray(groups)
    if not(np.isfinite(y).all() and np.isfinite(x).all()):raise ValueError('Nonfinite analytic input')
    if within:y,x,ids,inverse,n=demean(y,x,groups)
    else:ids,inverse=np.unique(groups,return_inverse=True);n=np.bincount(inverse).astype(float)
    kept=keep_columns(x,required);x=x[:,kept];p=x.shape[1]
    xx=np.empty((len(ids),p,p));xy=np.empty((len(ids),p))
    for i in range(p):
        xy[:,i]=np.bincount(inverse,weights=x[:,i]*y,minlength=len(ids))
        for j in range(p):xx[:,i,j]=np.bincount(inverse,weights=x[:,i]*x[:,j],minlength=len(ids))
    return dict(xx=xx,xy=xy,ids=ids,kept=kept,counts=n)


def solve(xx,xy):
    scale=np.sqrt(np.maximum(np.diag(xx),0))
    if np.any(scale<=1e-12):raise ValueError('No variation in resample')
    corr=xx/scale[:,None]/scale[None,:]
    if np.linalg.matrix_rank(corr,tol=1e-10)<len(scale):raise ValueError('Singular resample')
    return np.linalg.solve(corr,xy/scale)/scale


def regress(y,x,groups,bar,draws=2000,required=1,within=True,seed=SEED):
    try:s=sufficient(y,x,groups,required,within)
    except ValueError as exc:return dict(status='unsupported',reason=str(exc),interval=None,verdict='inconclusive',rows=len(y),players=len(set(groups)))
    n=len(s['ids']);point=solve(s['xx'].sum(axis=0),s['xy'].sum(axis=0));p=len(point)
    if n<2:return dict(status='below floor, descriptive',coefficient=float(point[0]),interval=None,verdict='inconclusive',rows=len(y),players=n)
    rng=np.random.default_rng(seed);samples=[];invalid=0
    # Counts weight each sampled player's complete within-player sufficient data.
    checkpoint=progress.begin('cluster-regression',draws)
    for index in range(draws):
        weights=np.bincount(rng.integers(0,n,n),minlength=n)
        def compute():
            try:return float(solve(np.tensordot(weights,s['xx'],axes=1),weights@s['xy'])[0])
            except ValueError:return None
        result=progress.value(checkpoint,index,compute)
        if result is None:invalid+=1
        else:samples.append(result)
    ci=np.quantile(samples,[.025,.975]).tolist() if not invalid else None
    return dict(status='complete' if not invalid else 'invalid uncertainty',coefficient=float(point[0]),
                coefficients=point.tolist(),kept_columns=s['kept'],interval=ci,verdict=verdict(ci,bar),
                rows=len(y),players=n,draws=draws,invalid_draws=invalid,bar=bar,within_player=within)


def controls(rows,variant='joint'):
    columns={'joint':[0,1,2,3,4,5],'stakes_only':[0,1,2,3,5],'complexity_only':[0,1,2,4,5],'neither':[0,1,2,5]}
    if variant not in columns:raise ValueError('Unregistered control variant')
    raw=np.asarray([[r['clock_before']/r['initial'],r['increment'],(r['ply']+1)/2,r['stakes'],r['legal_moves'],r['material']] for r in rows],float)
    return raw[:,columns[variant]]


def eligible(rows,tc=None):
    kept=[];counts=Counter(total_positions=len(rows))
    for row in rows:
        if tc is not None and row['time_control']!=tc:counts['other_control']+=1;continue
        if row.get('think_time') is None or row['think_time']<=0:counts['nonpositive_or_missing_time']+=1;continue
        if row.get('mate_sentinel_used'):counts['mating_score_not_centipawns']+=1;continue
        if row.get('clock_before') is None:counts['missing_prior_clock']+=1;continue
        kept.append(row)
    counts['supported_positions']=len(kept);counts['supported_players']=len({r['player'] for r in kept})
    return kept,dict(counts)


def closeness(rows,card='CH2',draws=2000,tc='blitz',measure='k50',floor=5000,critical=False,year=None,band_width=400,control_variant='joint'):
    source_count=len(rows)
    if year is not None:rows=[r for r in rows if r['month'].startswith(str(year))]
    selected,counts=eligible(rows,tc);selected=[r for r in selected if r.get(measure) is not None];per=Counter(r['player'] for r in selected)
    enough=sum(n>=20 for n in per.values())>=floor
    if not enough:selected,counts=eligible(rows,None)
    else:selected=[r for r in selected if per[r['player']]>=20]
    selected=[r for r in selected if r.get(measure) is not None]
    counts.update(source_positions_before_year_filter=source_count,positions_after_measure_filter=len(selected),players_after_measure_filter=len({r['player'] for r in selected}))
    if not selected:return dict(status='unsupported',counts=counts,reason='No measured choice/time rows',verdict='inconclusive')
    k=np.array([r[measure] for r in selected]);rating=np.array([((r['rating']//band_width+.5)*band_width-1600)/400 for r in selected])
    y=np.log([r['think_time'] for r in selected]);nuisance=controls(selected,control_variant)
    if card=='CH3':x=np.column_stack([k*rating,k,rating,nuisance]);bar=math.log(1.02)
    elif critical:
        indicator=np.array([r['stakes']<=50 for r in selected],float)
        x=np.column_stack([k*indicator,k,indicator,nuisance]);bar=math.log(1.03)
    else:x=np.column_stack([k,nuisance]);bar=math.log(1.03)
    if not enough:
        controls_present=sorted({r['time_control'] for r in selected})
        x=np.column_stack([x]+[np.array([r['time_control']==v for r in selected],float) for v in controls_present[1:]])
    result=regress(y,x,[r['player'] for r in selected],bar,draws,within=True)
    result.update(card=card,measure=measure,counts=counts,above_floor=enough,control_variant=control_variant,critical_slope_difference=critical,scope='within-player' if enough else 'below floor, descriptive; time controls pooled with player effects')
    if not enough:result['routing_verdict']='inconclusive'
    return result


def gap_breadth(rows,draws=2000,tc='blitz'):
    selected,counts=eligible(rows,tc);selected=[r for r in selected if r.get('best_gap') is not None]
    if not selected:return dict(status='unsupported',counts=counts)
    y=np.log([r['think_time'] for r in selected]);gap=np.array([r['best_gap']/100 for r in selected]);breadth=np.array([r['breadth'] for r in selected]);ctl=controls(selected);groups=[r['player'] for r in selected]
    return dict(breadth_beyond_gap=regress(y,np.column_stack([breadth,gap,ctl]),groups,math.log(1.03),draws),
                gap_beyond_breadth=regress(y,np.column_stack([gap,breadth,ctl]),groups,math.log(1.03),draws),counts=counts)


def book_rows(rows,database):
    con=sqlite3.connect(database);cache={};output=[]
    try:
        for row in rows:
            if row['ply']>10:continue
            key=(row['month'],row['time_control'],row['position'])
            if key not in cache:
                count=con.execute('SELECT n FROM opening_positions WHERE month=? AND tc=? AND position=?',key).fetchone()
                move=con.execute('SELECT move FROM openings WHERE month=? AND tc=? AND position=? ORDER BY n DESC,move LIMIT 1',key).fetchone()
                cache[key]=(count[0] if count else 0,move[0] if move else None)
            n,move=cache[key];output.append(dict(row,book=n>=500 and row['uci']==move,book_position_games=n))
    finally:con.close()
    return output


def book_rating(rows,database,draws=2000,tc='blitz'):
    selected,counts=eligible(book_rows(rows,database),tc)
    counts['book_moves']=sum(r['book'] for r in selected)
    books=[r for r in selected if r['book']]
    if not books:return dict(status='unsupported',counts=counts,reason='No book moves')
    x=np.column_stack([[(r['rating']-1600)/400 for r in books],controls(books)])
    fit=regress(np.log([r['think_time'] for r in books]),x,[r['player'] for r in books],math.log(1.02),draws,within=True)
    pooled=regress(np.log([r['think_time'] for r in books]),np.column_stack([x,np.ones(len(books))]),[r['player'] for r in books],math.log(1.02),draws,within=False)
    # Exact move-number strata, rather than a linear ply trend, match non-book
    # opportunities for the secondary book/non-book rating-slope contrast.
    move_numbers=sorted({(r['ply']+1)//2 for r in selected});rating=np.array([(r['rating']-1600)/400 for r in selected]);book=np.array([r['book'] for r in selected],float)
    matched=np.column_stack([book*rating,book,rating,controls(selected)]+[np.array([(r['ply']+1)//2==v for r in selected],float) for v in move_numbers[1:]])
    contrast=regress(np.log([r['think_time'] for r in selected]),matched,[r['player'] for r in selected],math.log(1.02),draws)
    return dict(within_player_fit=fit,pooled_descriptive_fit=pooled,book_minus_nonbook_rating_slope=contrast,counts=counts,scope='secondary book rating slope with explicit between-player descriptive companion')


def loo_expected_time(rows):
    """Exact leave-one-observation-out fixed-effect least squares residual."""
    y=np.log([r['think_time'] for r in rows]);groups=np.array([r['player'] for r in rows])
    band=np.array([int(r['rating']//400) for r in rows]);decile=np.array([(r['ply']//2)//10 for r in rows])
    tc=np.array([r['time_control'] for r in rows]);columns=[np.array([r['k50'] for r in rows],float)]
    for values in (band,decile,tc):
        for value in sorted(set(values))[1:]:columns.append((values==value).astype(float))
    raw=np.column_stack(columns);yd,xd,ids,inverse,n=demean(y,raw,groups);kept=keep_columns(xd,required=0);xd=xd[:,kept]
    if xd.shape[1]:
        beta=np.linalg.lstsq(xd,yd,rcond=None)[0];error=yd-xd@beta
        hat=np.einsum('ij,jk,ik->i',xd,np.linalg.pinv(xd.T@xd),xd)+1/n[inverse]
    else:error=yd;hat=1/n[inverse]
    if np.any(hat>=1-1e-9):raise ValueError('Expected-time leave-one-out has saturated row')
    return error/(1-hat)


def iv_fit(y,x,z,groups,required=2):
    yd,xd,ids,inverse,n=demean(np.asarray(y,float),x,np.asarray(groups));_,zd,_,_,_=demean(np.asarray(y,float),z,np.asarray(groups))
    # The first two columns are the endogenous regressors/excluded instruments.
    kept=keep_columns(xd,required);exog=[i for i in kept if i>=2];xd=xd[:,[0,1]+exog];zd=zd[:,[0,1]+exog]
    ols=np.linalg.lstsq(xd,yd,rcond=None)[0]
    if np.linalg.matrix_rank(zd)<zd.shape[1]:return dict(status='singular instrument',ols=float(ols[0]),iv=None,partial_F=[0.,0.])
    projected=zd@np.linalg.lstsq(zd,xd,rcond=None)[0]
    if np.linalg.matrix_rank(projected)<xd.shape[1]:return dict(status='singular instrument',ols=float(ols[0]),iv=None,partial_F=[0.,0.])
    beta=np.linalg.lstsq(projected,yd,rcond=None)[0];f=[]
    for j in (0,1):
        full=xd[:,j]-projected[:,j]
        restricted=xd[:,j]-(xd[:,2:]@np.linalg.lstsq(xd[:,2:],xd[:,j],rcond=None)[0] if xd.shape[1]>2 else 0.)
        rss=full@full;df=len(y)-len(ids)-zd.shape[1]
        f.append(float(((restricted@restricted-rss)/2)/(rss/df)) if rss>1e-12 and df>0 else 0.)
    return dict(status='valid' if min(f)>10 else 'weak instrument',ols=float(ols[0]),iv=float(beta[0]),partial_F=f)


def effort_point(rows):
    deviation=loo_expected_time(rows);rating=np.array([(r['rating']-1600)/400 for r in rows]);low=np.array([r['clock_before']<=10 for r in rows],float)
    ctl=controls(rows);smooth=(ctl[:,0]**2)[:,None];nuisance=np.column_stack([rating,ctl,smooth])
    x=np.column_stack([deviation*rating,deviation,nuisance]);z=np.column_stack([low*rating,low,nuisance])
    result=iv_fit([r['centipawn_loss'] for r in rows],x,z,[r['player'] for r in rows])
    result['ols_improvement']=-math.log(2)*result['ols'];result['iv_improvement']=None if result['iv'] is None else -math.log(2)*result['iv']
    return result


def effort(rows,draws=2000,tc=None,cap=None,max_stakes=None,floor=20):
    selected,counts=eligible(rows,tc)
    if cap is not None:selected=[dict(r,centipawn_loss=min(cap,r['centipawn_loss'])) for r in selected]
    if max_stakes is not None:selected=[r for r in selected if r['stakes']<max_stakes]
    groups={}
    for r in selected:groups.setdefault(r['player'],[]).append(r)
    keys=sorted(groups)
    if len(keys)<2:return dict(status='unsupported',counts=counts,verdict='inconclusive')
    if len(keys)<floor:
        try:
            deviation=loo_expected_time(selected);rating=np.array([(r['rating']-1600)/400 for r in selected])
            x=np.column_stack([-math.log(2)*deviation*rating,deviation,rating,controls(selected),np.ones(len(selected))])
            # coefficient on deviation/(-log2), not multiplied deviation, is the
            # cp improvement per doubling and 400 rating points.
            x[:,0]=deviation*rating/(-math.log(2))
            fallback=regress([r['centipawn_loss'] for r in selected],x,[r['player'] for r in selected],1.,draws,within=False)
            return dict(card='CH5',status='below floor, descriptive',pooled_ols=fallback,counts=counts,players=len(keys),routing_verdict='inconclusive',causal_claim=False)
        except ValueError as exc:return dict(card='CH5',status='unsupported',reason=str(exc),counts=counts,verdict='inconclusive')
    try:point=effort_point(selected)
    except ValueError as exc:return dict(status='unsupported',reason=str(exc),counts=counts,verdict='inconclusive')
    rng=np.random.default_rng(SEED);olss=[];ivs=[];invalid=0
    checkpoint=progress.begin('CH5-complete-nuisance-refit',draws)
    for index in range(draws):
        sample=[]
        for copy,cluster_index in enumerate(rng.integers(0,len(keys),len(keys))):
            sample.extend(dict(r,player=str(copy)) for r in groups[keys[cluster_index]])
        def compute():
            try:
                fit=effort_point(sample);return [fit['ols_improvement'],fit['iv_improvement']]
            except ValueError:return None
        fit=progress.value(checkpoint,index,compute)
        if fit is None:invalid+=1
        else:
            olss.append(fit[0])
            if fit[1] is None:invalid+=1
            else:ivs.append(fit[1])
    oci=np.quantile(olss,[.025,.975]).tolist() if len(olss)==draws else None
    ici=np.quantile(ivs,[.025,.975]).tolist() if len(ivs)==draws else None
    valid=point['status']=='valid' and ici is not None
    return dict(card='CH5',status='complete' if valid else 'OLS descriptive only',point=point,counts=counts,players=len(keys),
                interval=ici if valid else oci,iv_interval=ici,ols_interval=oci,invalid_draws=invalid,draws=draws,bar=1.,
                verdict=verdict(ici if valid else oci,1.),causal_claim=False,all_nuisance_refit=True)


def load_scores(path):
    rows=[]
    for file in sorted(Path(path).glob('*.json')):
        value=json.loads(file.read_text(encoding='utf8'));rows.append(dict(value['position'],**value['engine']))
    return rows


def execute_body(output,inputs,config):
    from .week5_ch_collection import load_complete
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config.get('constructed_fixture'):
        rows=load_scores(inputs['scores']['path'])
        if not all(json.loads(f.read_text()).get('constructed') for f in Path(inputs['scores']['path']).glob('*.json')):raise ValueError('Fixture bypass requires entirely constructed records')
    else:rows=load_complete(inputs)
    card=config['card']
    if card in ('CH2','CH3'):
        result=closeness(rows,card,config.get('draws',2000),config.get('time_control','blitz'),config.get('measure','k50'),config.get('floor',5000),config.get('critical',False),config.get('year'),config.get('band_width',400),config.get('control_variant','joint'))
        if config.get('include_secondaries',True) and card=='CH2':result['gap_breadth_secondary']=gap_breadth(rows,config.get('draws',2000),config.get('time_control','blitz'))
        if config.get('include_secondaries',True) and card=='CH3' and 'book_frame' in inputs:result['book_secondary']=book_rating(rows,inputs['book_frame']['path'],config.get('draws',2000),config.get('time_control','blitz'))
    elif card=='CH5':result=effort(rows,config.get('draws',2000),config.get('time_control'),config.get('loss_cap'),config.get('max_stakes'),config.get('floor',20))
    else:raise ValueError('Unsupported CH analysis')
    result['constructed_fixture']=bool(config.get('constructed_fixture'))
    write_json(output/'SCIENCE.json',result);return dict(status='complete',card=card)


def execute(output,inputs,config):
    try:
        with progress.tracking(output,inputs,config):return execute_body(output,inputs,config)
    except progress.YieldRequested as exc:return dict(status='yielded',reason=str(exc),checkpoint=str(Path(output)/'CHECKPOINT.json'))


def verify(output,inputs,config):
    output=Path(output);execute(output/'replay',{k:v for k,v in inputs.items() if k!='resume_analysis'},config)
    if digest(output/'SCIENCE.json')!=digest(output/'replay/SCIENCE.json'):raise ValueError('Independent source-based statistical replay differs')
    return dict(verified=True,complete_recalculation=True)
