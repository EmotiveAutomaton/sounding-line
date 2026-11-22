"""Hawks diary projections, cross-event slope correlations and anxiety descriptions."""
from itertools import combinations
import numpy as np
import pandas as pd
from . import week6_bt_forms_v1 as forms
from . import week6_person_ladder_v1 as ladder
from . import week6_person_slopes_v1 as op
from . import week6_ld12_common_v1 as core
from .week6_lattice_diary_v1 import person_draw

EVENTS = ('argument_stress','let_pass_stress','friend_relative_stress','health_stress','other_stress')
FEELINGS = ('nervous','afraid','scared','distressed','worried')
SADNESS = 'sadness_extreme'
COLUMNS = ('id','day',*EVENTS,*FEELINGS,SADNESS)


def prepare(frame, replay):
    if frame.id.isna().any() or frame.day.isna().any() or (frame.day % 1 != 0).any():
        raise ValueError('Missing identity or invalid study day')
    ratings = frame.loc[:,[*EVENTS,*FEELINGS,SADNESS]]
    if ((~ratings.isin(range(1,6))) & ratings.notna()).any().any():
        raise ValueError('Undocumented Hawks item code')
    grades = {k:frame[k].to_numpy(float)-1 for k in EVENTS}
    data, _, half, gap = forms.project(frame, grades, (*FEELINGS,SADNESS))
    result = {}
    for feeling in (*FEELINGS,SADNESS):
        y=frame[feeling].to_numpy(float)
        # A common, fixed outcome unit for all halves and all three forms.
        by=frame[feeling].groupby(data['ids'])
        dof=int(frame[feeling].count()-by.count().gt(0).sum())
        sd=np.sqrt(((frame[feeling]-by.transform('mean'))**2).sum()/dof) if dof>0 else np.nan
        for event,grade in grades.items():
            result[event+'/'+feeling]={k:integer_halves(data['ids'],data['n'],grade,y,sd,split,
                    graded=k=='PST4',replay=replay) for k,split in [('PST1',half),('PST4',half),('PST5',gap)]}
    return result


def centered_products(x,y,replay):
    """Return n times the centered sums. All arithmetic here is on integer ratings."""
    if replay:
        i,j=np.triu_indices(len(x),1)
        dx=x[i]-x[j]
        return int(dx@dx),int(dx@(y[i]-y[j]))
    return int(len(x)*(x@x)-x.sum()**2),int(len(x)*(x@y)-x.sum()*y.sum())


def integer_halves(ids,n,grade,y,sd,split,*,graded,replay):
    halves=[]
    for half in (0,1):
        parts={k:np.full(n,np.nan) for k in ('b','L','S','n0','n1','sxx')}
        valid=(split==half)&np.isfinite(grade)&np.isfinite(y)
        for person in np.unique(ids[valid]):
            mask=valid&(ids==person)
            x=grade[mask].astype(np.int64);v=y[mask].astype(np.int64)
            low=v[x==0];above=v[x>0];nl=len(low);na=len(above)
            parts['n0'][person]=nl;parts['n1'][person]=na
            if min(nl,na)<2 or not np.isfinite(sd) or sd<=0:continue
            parts['L'][person]=int(low.sum())/nl/sd
            ss,_=centered_products(low,low,replay)
            parts['S'][person]=np.sqrt(ss/(nl*(nl-1)))/sd
            if graded:
                xx,xy=centered_products(x,v,replay)
                parts['sxx'][person]=xx/len(x)
                if len(np.unique(x[x>0]))<2:continue
                parts['b'][person]=(xy/xx)/sd
            else:
                parts['b'][person]=(int(above.sum())*nl-int(low.sum())*na)/(nl*na)/sd
        halves.append(parts)
    return halves


def pair_draws(groups, names, n, seed, replay):
    parts = [groups[k]['PST1'] for k in names]
    mask = np.logical_and.reduce([np.isfinite(h['b']) for p in parts for h in p])
    sides = [ladder.supported(p,mask) for p in parts]
    w = np.minimum.reduce([h['n1'] for pair in sides for h in pair])
    if len(w)<2:
        return len(w), None
    spread = [bool(op.wpearson(w,p[0]['S'],p[1]['S'])>=.30) for p in sides]
    rng = np.random.default_rng(seed)
    draws = []
    for start in range(0,2001,50):
        count = min(50,2001-start)
        W = op.boot_counts(rng,n,count-int(start==0))[:,mask]*w
        if start==0:
            W=np.vstack([w,W])
        valid = W.sum(axis=1)>0
        block = np.full((len(W),4),np.nan)
        if valid.any():
            weights=W[valid]
            residuals=[]
            variances=[]
            for pair,use in zip(sides,spread):
                slope=(pair[0]['b'],pair[1]['b'])
                covariates=[(pair[0]['L'],pair[1]['L'])]
                if use:
                    covariates.append((pair[0]['S'],pair[1]['S']))
                _,var,beta=op.adjust(weights,slope,covariates)
                variances.append(var)
                residuals.append(tuple(slope[i]-sum(beta[:,j,None]*x[i] for j,x in enumerate(covariates)) for i in (0,1)))
            def cov(x,y):
                xc=x-op.wmean(weights,x)[:,None]
                yc=y-op.wmean(weights,y)[:,None]
                return op.wmean(weights,xc*yc)
            a,b=residuals
            cross=(cov(a[0],b[1])+cov(a[1],b[0]))/2
            va,vb=variances
            good=(va>0)&(vb>0)
            corr=np.divide(cross,np.sqrt(np.where(good,va*vb,1)),where=good,out=np.full_like(va,np.nan))
            if replay:
                h1,h2=[dict(A=sides[0][i],B=sides[1][i]) for i in (0,1)]
                _,_,va,vb,reference=op.slope_block(weights,h1,h2,dict(zip(('A','B'),spread)))
                np.testing.assert_allclose(corr,reference,atol=1e-7,rtol=1e-7,equal_nan=True)
            block[valid]=np.column_stack([cross,corr,va,vb])
        draws.append(block)
    return len(w),np.concatenate(draws)


def pool_pairs(qualified):
    result=dict(qualifying_pairs=len(qualified),reading='no verdict',first_factor_share=None)
    if not qualified:
        return result
    matrix=np.stack(list(qualified.values()))
    if not np.isfinite(matrix).all():
        return dict(result,reason='Missing indexed correlation draw')
    var=matrix[:,1:].var(axis=1,ddof=1)
    if len(matrix)>1 and (var<=0).any():
        return dict(result,reason='Undefined inverse variance')
    w=1/var if len(matrix)>1 else np.ones(1)
    pooled=np.average(matrix,weights=w,axis=0)
    p=float(pooled[0])
    s=ladder.stat(p,pooled[1:])
    lo,hi=s['interval']
    result.update(pooled=s,reading='one' if p>=.5 and lo>.3 else 'several' if p<.3 and hi<.5 else 'undecided',
                  Q=float(w@(matrix[:,0]-p)**2),df=len(w)-1)
    names=sorted({k for pair in qualified for k in pair})
    if len(qualified)==len(names)*(len(names)-1)//2:
        corr=np.eye(len(names))
        for (a,b),vals in qualified.items():
            i,j=names.index(a),names.index(b)
            corr[i,j]=corr[j,i]=vals[0]
        eig=np.linalg.eigvalsh(corr)
        if eig[0]>=-1e-10:result['first_factor_share']=float(eig[-1]/len(names))
    return result


def different_events(panels,rows,n,replay,guard):
    pairs={};qualified={}
    for left,right in combinations((k for k in panels if k.split('/')[1] in FEELINGS),2):
        if left.split('/')[0]==right.split('/')[0]:continue
        label=left+' / '+right
        mask=np.logical_and.reduce([np.isfinite(p['b']) for k in (left,right) for p in panels[k]['PST1']])
        item=pairs[label]=dict(people=int(mask.sum()),status='single-slope variance gate did not pass')
        if not all(rows[k]['PST1']['reading']=='stable' for k in (left,right)):continue
        guard()
        people,draws=pair_draws(panels,(left,right),n,[20261121,3,47],replay)
        assert people==item['people']
        if draws is None:
            item['status']='insufficient common support'
            continue
        stats=[ladder.stat(x[0],x[1:]) for x in draws.T]
        item.update(status='common-support variance or correlation unidentified',covariance=stats[0],correlation=stats[1],variances=stats[2:])
        if all(v['interval'] and v['interval'][0]>0 for v in stats[2:]) and np.isfinite(draws[0,1]):
            qualified[left,right]=draws[:,1]
            item['status']='estimable pair'
    return dict(pairs=pairs,pool=pool_pairs(qualified))


def anxiety(frame,replay,guard):
    roster,ids=np.unique(frame.id.astype(str),return_inverse=True)
    result={}
    within,_,linear=core.arithmetic(replay)
    for outcome in ('nervous','worried'):
        complete=frame[['afraid',outcome]].notna().all(axis=1).to_numpy()
        group=ids[complete];xy=frame.loc[complete,['afraid',outcome]].to_numpy(float)
        estimates=[]
        for i in range(-1,2000):
            if i%50==0:guard()
            w=np.ones(len(roster)) if i<0 else person_draw(np.arange(len(roster)),source_seed=202611190003,draw=i)
            weight=w[group]
            if not weight.sum():
                estimates.append(np.nan);continue
            try:
                z=within(xy,group,weight)[0]
                estimates.append(float(linear(z[:,:1],z[:,1],weight)[0]))
            except (core.fits.InvalidFit,np.linalg.LinAlgError):
                estimates.append(np.nan)
        s=ladder.stat(estimates[0],estimates[1:])
        result[outcome]=dict(people=len(np.unique(group)),rows=len(group),slope=s,
                             explained_fraction=float(s['estimate']**2) if s['estimate'] is not None else None)
    return result

