"""MNG1. Within-person activity appraisals in four American Time Use Surveys."""
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

from . import week8_gear as gear
from runners.stage14.common import filehash,freeze,read

YEARS=(2010,2012,2013,2021)
KEYS=['TUCASEID','TUACTIVITY_N']
ACTIVITIES=('child care','adult care and help','paid work','housework','eating and drinking','socializing','games and sport','television and movies','religious activities','volunteering','other activity')
COMPANY=('alone','with partner','with children','with friends','with co-workers','other company')
SOURCE=gear.REPO/'.agent-state/data_collection_root.json'


def sources():
    root=Path(read(SOURCE)['root'])
    wb=root/'open/atus-wellbeing'
    basic=root/'open/atus-activity-who'
    wbsource=read(wb/'SOURCE.json')
    spec={year:{} for year in YEARS}
    pins={}
    for item in wbsource['local_files']:
        path=root/item['path']
        for year in YEARS:
            if path.name in (f'wbact_{year}.zip',f'wbact-{year}.zip'):
                spec[year]['wb']=(path,f'wbact_{year}.dat')
                pins[path]=item['sha256']
        if path.name in ('wbmintcodebk.pdf','wbmintcodebk21.pdf'):
            pins[path]=item['sha256']
    for row in read(basic/'MANIFEST.json')['files']:
        year=int(row['year'])
        if year in spec and row['kind'] in ('act','who'):
            path=root/row['path']
            spec[year][row['kind']]=(path,row['member'])
            pins[path]=row['sha256']
    if not all(set(row)=={'wb','act','who'} for row in spec.values()) or len(pins)!=14:
        raise ValueError('Required annual archives or dictionaries absent')
    docs=[wb/'SOURCE.json',basic/'SOURCE.json',basic/'MANIFEST.json',basic/'REPORTING_R48.md',wb/'LICENCE.md',
          gear.REPO/'docs/design/stage-15/week8/MNG1.md']
    return spec,pins,docs


def design(unit):
    if unit!='MNG1-ATUS-four-years':raise ValueError('Unknown study')
    _,pins,docs=sources()
    return dict(inputs=[*pins,*docs],expected=pins,peak=1.5,cap=20000,operations=['execute','verify'],source='atus-wellbeing-activity-who')


def family(code):
    head=code//100
    if head in (301,302,303,401,402,403):return 0
    if head in (304,305,404,405):return 1
    if head==501:return 2
    if head==201:return 3
    if code//10000==11:return 4
    if head==1201:return 5
    if code==120307 or head==1301:return 6
    if code in (120303,120304):return 7
    return {14:8,15:9}.get(code//10000,10)


def company(codes):
    present={int(c) for c in codes if pd.notna(c) and 18<=int(c)<=62}
    alone=present & {18,19}
    if not present or (alone and present-{18,19}):return frozenset()
    if alone:return frozenset((0,))
    sets=({20,21},{22,27,40,52,57},{54},{59,60,61})
    groups={i for i,values in enumerate(sets,1) if present & values}
    if present.difference(*sets):groups.add(5)
    return frozenset(groups)


def read_source(spec,cols):
    archive,member=spec
    with ZipFile(archive) as z:
        if z.namelist().count(member)!=1:raise ValueError('Original data member differs')
        with z.open(member) as f:
            return pd.read_csv(f,usecols=cols,dtype={'TUCASEID':'string'})


def project(year,ratings,activity,who):
    weight='WUFNACTWT' if year==2021 else 'WUFNACTWTC'
    if ratings.duplicated(KEYS).any() or activity.duplicated(KEYS).any():
        raise ValueError('Ambiguous original episode')
    if ratings[KEYS].isna().any().any() or activity[KEYS].isna().any().any():
        raise ValueError('Missing original episode key')
    merged=ratings.merge(activity,on=KEYS,how='left',validate='one_to_one',indicator=True)
    if not merged['_merge'].eq('both').all():raise ValueError('Unmatched rated episode')
    valid=merged[['WUMEANING','WUHAPPY']].isin(range(7)).all(axis=1) & merged[weight].gt(0)
    use=merged.loc[valid].copy()
    group=use.groupby('TUCASEID',sort=True)
    use['difference']=(use.WUMEANING-group.WUMEANING.transform('mean'))-(use.WUHAPPY-group.WUHAPPY.transform('mean'))
    use['weight']=use[weight]/use[weight].sum()
    use['activity']=use.TRCODE.astype(int).map(family)
    w=who.merge(use[KEYS],on=KEYS,how='inner',validate='many_to_one')
    partners=w.groupby(KEYS,sort=False).TUWHO_CODE.agg(company).rename('company').reset_index()
    use=use.merge(partners,on=KEYS,how='left',validate='one_to_one')
    use['company']=[v if isinstance(v,frozenset) else frozenset() for v in use.company]
    return use,dict(year=year,matched=len(merged),eligible=len(use),unavailable_company=sum(not v for v in use.company),
            single_rated_people=int((use.groupby('TUCASEID').size()==1).sum()))


def contributions(frame):
    ids,inverse=np.unique(frame.TUCASEID.to_numpy(dtype=str),return_inverse=True)
    design=np.zeros((len(frame),len(ACTIVITIES)+len(COMPANY)),bool)
    design[np.arange(len(frame)),frame.activity.to_numpy(int)]=True
    for i,groups in enumerate(frame.company):
        for group in groups:design[i,len(ACTIVITIES)+group]=True
    weight=design*frame.weight.to_numpy()[:,None]
    totals=np.zeros((len(ids),design.shape[1]))
    numer=np.zeros_like(totals)
    np.add.at(totals,inverse,weight)
    np.add.at(numer,inverse,weight*frame.difference.to_numpy()[:,None])
    return numer,totals,design.sum(axis=0)


def summarize(parts,draws):
    rng=np.random.default_rng(2026112713)
    numerator=sum(v[0].sum(axis=0) for v in parts)
    denominator=sum(v[1].sum(axis=0) for v in parts)
    people=sum((v[1]>0).sum(axis=0) for v in parts)
    episodes=sum(v[2] for v in parts)
    result=np.full((draws+1,len(denominator)),np.nan)
    np.divide(numerator,denominator,where=denominator>0,out=result[0])
    for start in range(1,draws+1,24):
        size=min(24,draws+1-start)
        num=np.zeros((size,len(denominator)));den=np.zeros_like(num)
        for y,n,_ in parts:
            weights=np.vstack([np.bincount(rng.integers(len(y),size=len(y)),minlength=len(y)) for _ in range(size)])
            num+=weights@y;den+=weights@n
        np.divide(num,den,where=den>0,out=result[start:start+size])
    tables={}
    for index,name in enumerate(ACTIVITIES+COMPANY):
        if people[index]<11 or not np.isfinite(result[:,index]).all():
            continue
        low,high=np.quantile(result[1:,index],[.025,.975])
        tables[name]=dict(n=int(people[index]),episodes=int(episodes[index]),estimate=float(result[0,index]),
                          lower=float(low),upper=float(high))
    return tables


def fixture():
    ids=np.repeat([f'p{i}' for i in range(45)],2)
    rows=pd.DataFrame(dict(TUCASEID=ids,TUACTIVITY_N=np.tile([1,2],45),
        WUMEANING=np.tile([6,2],45),WUHAPPY=np.tile([2,4],45),WUFNACTWTC=1.,WUFNACTWT=3.))
    rows.loc[rows.TUCASEID=='p0',['WUMEANING','WUHAPPY']]=4
    act=rows[KEYS].copy();act['TRCODE']=np.tile([30101,50101],45)
    who=rows[KEYS].copy();who['TUWHO_CODE']=np.tile([22,61],45)
    add=who.iloc[::2].copy();add['TUWHO_CODE']=20
    who=pd.concat([who,who.iloc[::2],add])
    projected,counts=project(2010,rows,act,who)
    assert len(projected)==90 and all(v==frozenset((1,2)) for v in projected.company.iloc[::2])
    val=summarize([contributions(projected)],90)
    assert abs(val['child care']['estimate']-3*44/45)<1e-10 and abs(val['paid work']['estimate']+3*44/45)<1e-10
    assert val['with children']['n']==45 and val['with children']['episodes']==45
    assert company([18,20])==frozenset() and company([18,19])==frozenset((0,)) and not company([-1])
    rows.loc[0,'WUFNACTWT']=0.
    assert project(2021,rows,act,who)[1]['eligible']==89 and project(2012,rows,act,who)[1]['eligible']==90
    return dict(constructed=True,checks=['person centering','family direction and magnitude','concurrent and duplicate company','missing or conflicting company','corrected and 2021 weights','whole-person interval'])


def run(unit,d,mode):
    spec,_,_=sources()
    parts=[];status=[]
    for year,item in sorted(spec.items()):
        weight='WUFNACTWT' if year==2021 else 'WUFNACTWTC'
        ratings=read_source(item['wb'],[*KEYS,'WUMEANING','WUHAPPY',weight])
        activity=read_source(item['act'],[*KEYS,'TRCODE'])
        who=read_source(item['who'],[*KEYS,'TUWHO_CODE'])
        frame,meta=project(year,ratings,activity,who)
        parts.append(contributions(frame));status.append(meta)
    freeze(d/(mode+'_SUMMARY.json'),dict(years=status,draws=2000,tables=summarize(parts,2000)))


def check(unit,d):
    a,b=d/'execute_SUMMARY.json',d/'verify_SUMMARY.json'
    if a.read_bytes()!=b.read_bytes():raise ValueError('Independent re-read differs')
    return {p.name:filehash(p) for p in (a,b)}
