"""Week 8 marital trajectories. Memberships and age bands stay in the sealed job."""
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

from runners.drive.cards.week6_sealed_support_v1 import ReadBudget, SealedFailure, write_tables
from runners.drive.sealed import week7_sld2_original as old
from independent_release import Entry, decide

STATUS=('A1PB17','B1PB19','C1PB19')
AGE='A1PRAGE_2019'
DATES=('PB23','PB25','PB28','PB29')
PAIRS=((0,1),(0,2),(1,2))
ITEMS=old.ITEMS


def fields(wave):
    cols=old.field_list(wave)+[STATUS[wave-1]]
    if wave==1:
        cols.append(AGE)
    elif wave==3:
        cols+=['C1PIDATE_MO','C1PIDATE_YR','C1PB22']
        cols+=['C1'+d+t for d in DATES for t in ('Y','M')]
    return list(dict.fromkeys(cols))


def load(root,pins):
    import pyreadstat
    from hashlib import file_digest
    frames=[]
    budget=ReadBudget(root)
    if len(pins)!=3:
        raise SealedFailure(13,'Wrong number of waves')
    for wave,(name,size,sha) in enumerate(pins,1):
        if name!=Path(name).name:
            raise SealedFailure(13,'Invalid original name')
        p=budget.reserve(Path(root)/name,passes=2)
        with p.open('rb') as stream:
            if p.stat().st_size!=size or file_digest(stream,'sha256').hexdigest()!=sha:
                raise SealedFailure(13,'Survey changed')
        cols=fields(wave)
        df,_=pyreadstat.read_sav(str(p),usecols=cols,user_missing=False,apply_value_formats=False)
        if set(df)!=set(cols) or df.M2ID.isna().any() or df.M2ID.duplicated().any():
            raise SealedFailure(13,'Missing fields or key')
        frames.append(df.set_index('M2ID'))
    return frames


def history(frame,prefix,lo,hi):
    flags=[]
    ambiguous=pd.Series(False,index=frame.index)
    for field,code,date in [('PB22',1,'PB23'),('PB22',2,'PB25'),('PB19',4,'PB29'),('PB19',3,'PB28')]:
        endorsed=frame[prefix+field].eq(code)
        m=old.month_index(frame[prefix+date+'Y'],frame[prefix+date+'M'])
        ambiguous|=endorsed & (m.isna() | m.eq(lo) | m.eq(hi))
        flags.append(endorsed & m.gt(lo) & m.lt(hi))
    return flags[0]|flags[2],flags[1]|flags[3],ambiguous


def membership(frames,known_counts):
    a,b,c=frames
    death,divorce=old.loss_flags(a,b)
    known={}
    for g,flag in enumerate([death|divorce,death,divorce],1):
        for mode in (1,2):
            waves=old.scored(frames,mode==2)
            waves[1]['role_loss']=flag.reindex(waves[1].person).to_numpy(int)
            cohort=old.projected(waves,ITEMS)
            people=frozenset(cohort.index)
            if len(people)!=known_counts[f'{g}-{mode}'] or cohort.family.isna().any():
                raise SealedFailure(14,'Previously released roster failed reconstruction')
            known[g,mode]=people
    index=a.index.intersection(b.index).intersection(c.index)
    obs=pd.DataFrame(index=index)
    for i,(frame,scored) in enumerate(zip(frames,old.scored(frames,False))):
        obs['p'+str(i)]=scored.set_index('person')[list(ITEMS)].mean(axis=1,skipna=False)
        obs['s'+str(i)]=frame[STATUS[i]]
    obs['age']=a[AGE].where(a[AGE].between(18,110))
    obs['family']=b.M2FAMNUM
    for df in (a,c):
        fam=df.M2FAMNUM.reindex(index)
        if (obs.family.notna() & fam.notna() & obs.family.ne(fam)).any():
            raise SealedFailure(12,'Inconsistent family link')
    dates=[old.month_index(df[p+'YR'],df[p+'MO']).reindex(index) for df,p in zip(frames,['A1PI_','B1PIDATE_','C1PIDATE_'])]
    good=dates[0].lt(dates[1])&dates[1].lt(dates[2])
    bflags=history(b.loc[index],'B1',dates[0],dates[1])
    cflags=history(c.loc[index],'C1',dates[1],dates[2])
    any3=history(c.loc[index],'C1',dates[0],dates[2])
    clear=~(bflags[0]|bflags[1]|bflags[2]|any3[0]|any3[1]|any3[2])
    pooled=known[1,1]
    age=obs.loc[list(pooled),'age']
    if age.isna().any():
        raise SealedFailure(12,'Unknown age for a loss member')
    complete=obs[['p0','p1','p2','age','family']].notna().all(axis=1)
    married=obs[['s0','s1','s2']].eq(1)
    comparison=frozenset(index[good & complete & clear & married.all(axis=1) & obs.age.between(age.min(),age.max())])
    later=frozenset(index[good & married[['s0','s1']].all(axis=1) & (cflags[0]|cflags[1]) &
                   ~index.isin(pooled) & obs[['p0','p1','age','family']].notna().all(axis=1)])
    return obs,known,comparison,later


def estimates(obs,group,control,pairs,draws):
    if len(group)<11 or len(control)<11 or group & control:
        return []
    ids=sorted(group|control)
    d=obs.loc[ids]
    if d.family.isna().any() or d.age.isna().any():
        return []
    g=d.index.isin(group)
    band=np.asarray(d.age//10,int)
    bands=np.unique(band[g])
    masks=[(g & (band==v),~g & (band==v)) for v in bands]
    if any(not c.any() for _,c in masks):
        return []
    _,cluster=np.unique(d.family,return_inverse=True)
    nf=cluster.max()+1
    rng=np.random.default_rng(2026112705)
    scores=d[['p0','p1','p2']].to_numpy()
    signals=[]
    for wave,end in pairs:
        x,y=scores[:,wave],scores[:,end]
        signals.append(np.column_stack([np.ones(len(x)),x,y,x*x,x*y]))
    def evaluate(w):
        value=[]
        for signal in signals:
            # Sufficient cross-products after centering outcome, exposure and covariate within decade.
            total=change=sgg=sgx=sgy=sxx=sxy=0.
            for gm,cm in masks:
                ng,xc,yc,xxc,xyc=w[gm]@signal[gm]
                nc,xr,yr,xxr,xyr=w[cm]@signal[cm]
                if ng==0:
                    continue
                if nc==0:
                    return np.full(2*len(signals),np.nan)
                scale=ng/nc
                mean_x=(xc+scale*xr)/(2*ng)
                mean_y=(yc+scale*yr)/(2*ng)
                total+=ng
                change+=yc-xc-scale*(yr-xr)
                sgg+=ng/2
                sgx+=xc-ng*mean_x
                sgy+=yc-ng*mean_y
                sxx+=xxc+scale*xxr-2*ng*mean_x**2
                sxy+=xyc+scale*xyr-2*ng*mean_x*mean_y
            den=sgg*sxx-sgx**2
            value.extend([change/total if total else np.nan,
                          (sgy*sxx-sgx*sxy)/den if den>1e-10 else np.nan])
        return np.asarray(value)
    point=evaluate(np.ones(len(d)))
    bank=np.array([evaluate(np.bincount(rng.integers(nf,size=nf),minlength=nf)[cluster]) for _ in range(draws)])
    rows=[]
    for k,v in enumerate(point):
        if not np.isfinite(v) or not np.isfinite(bank[:,k]).all():
            continue
        low,high=np.quantile(bank[:,k],[.025,.975])
        rows.append(dict(transition=k//2+1,form=k%2+1,estimate=v,lower=low,upper=high,n=len(group)))
    return rows


def calculate(frames,known_counts,draws):
    obs,known,comp,later=membership(frames,known_counts)
    entries=[]
    for g,group in [(1,known[1,1]),(2,known[2,1]),(3,known[3,1]),(4,later)]:
        if g==4 and len(group)<20:
            continue
        # n counts the people whose change is benchmarked. Check both the
        # fixed reference and its contributing people without releasing an age count.
        bands=set(obs.loc[list(group),'age']//10)
        positive=frozenset(p for p in comp if obs.at[p,'age']//10 in bands)
        for row in estimates(obs,group,comp,PAIRS if g<4 else PAIRS[:1],draws):
            entries.append(Entry(dict(group=g,**row),group,(comp,positive)))
    allowed,_=decide([(1,'purpose',entries)],frozenset(frames[0].index),tuple(known.values()))
    if not allowed:
        raise SealedFailure(12,'No disclosable contrast')
    return allowed


def run(root,out,config):
    first=calculate(load(root,config['files']),config['known'],config['draws'])
    if first!=calculate(load(root,config['files']),config['known'],config['draws']):
        raise SealedFailure(14,'Fresh source replay differs')
    write_tables(out,first)
