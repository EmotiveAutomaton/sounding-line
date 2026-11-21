"""Member-specific, locally authenticated person-slope projections."""
from pathlib import Path
import os
import numpy as np
import pandas as pd
from . import week6_person_ladder_v1 as base
from .batch_runtime import filehash,read
from .week6_lb3_source_v1 import PARENT_FEELINGS,CHILD_DISTRESS

STATUS_SMALL=tuple(k for k in base.STATUS if k not in ('int_excluded','int_lonely'))
STATUS_EVENTS=('interaction','status_criticised','status_ignored','status_sidelined','status_admired','status_upstaged')
SOLITARY=('occup_enthusiastic','occup_relaxed')
PARENT_EVENTS=('stressor_health','stressor_financial',*CHILD_DISTRESS)
SOURCES={
    '0056':(STATUS_SMALL,STATUS_EVENTS),
    '0057':((*base.STATUS,*SOLITARY),(*STATUS_EVENTS,'intellectual')),
    '0060':base.CONFIG['0060'],
    '0072':(PARENT_FEELINGS,PARENT_EVENTS),
    '0076':(('pa','energy','fidgety'),('interaction_playful','interaction_pleasant','stressed'))}

def source(member,root):
    root=Path(root)
    if root.drive.casefold()!=os.environ['SystemDrive'].casefold() or root.name!=base.ROOT_NAME:
        raise ValueError('Expected the verified temporary root on the system disk')
    manifest=root/'DRT1_MANIFEST.json'
    if filehash(manifest)!=base.MANIFEST:raise ValueError('Changed temporary manifest')
    pins={v['path']:v for v in read(manifest)['files']}
    def checked(name):
        key='open/openesm-'+member+'/'+name
        p=root/key;pin=pins[key]
        if p.stat().st_size!=pin['bytes'] or filehash(p)!=pin['sha256']:raise ValueError('Changed original source')
        return p
    record=read(checked('SOURCE.json'));checked('LICENCE_RECORD.json')
    if record['slug']!='openesm-'+member or record['class'] not in ('open-clean','open-tests-only'):raise ValueError('Unknown source')
    meta=read(checked('DOCUMENTED_METADATA.json'));features={v['name']:v for v in meta['features']}
    cols={'id','day',*SOURCES[member][0],*SOURCES[member][1]}
    if float(meta['n_days'])<7 or cols-features.keys():raise ValueError('Unbound dictionary')
    if member=='0072' and any(features[k]['transformation']!='recoded from (2,1) to (1,0)' for k in PARENT_EVENTS[:2]):raise ValueError('Unbound parent stress coding')
    table,=[v for v in read(checked('SCHEMA.json'))['files'] if v['file'].endswith('_ts.tsv')]
    if table['malformed_row_count'] or cols-{v['name'] for v in table['columns']}:raise ValueError('Original table layout differs')
    path=checked('raw/'+table['file'])
    if filehash(path)!=table['sha256']:raise ValueError('Source schema digest mismatch')
    return path,sorted(cols)

def above(series,floor=1):
    a=np.asarray(series,dtype=float)
    return np.where(np.isfinite(a),a>floor,np.nan)

def project(frame,member):
    if member=='0060':
        data=base.project(frame,member)
        intellect=data['slopes']['curiosity'][0]
        y=data['feelings'];data['slopes']['contentment']=(intellect,y['content'])
        data['slopes']['curiosity_minus_contentment']=(intellect,y['curious']-y['content'])
        return data
    ids_ok=~frame.id.isin(['','NA'])
    f=frame.loc[ids_ok].copy()
    roster,unit=np.unique(f.pop('id').astype(str),return_inverse=True)
    for col in f:
        x=pd.to_numeric(f[col].replace({'':np.nan,'NA':np.nan}),errors='raise').astype(float)
        low=0 if col in PARENT_EVENTS[:2] or col=='day' else 1
        hi=(np.inf if col=='day' else 1 if col in PARENT_EVENTS[:2] else 2 if col=='interaction'
            else 7 if member=='0072' else 5 if member=='0076' else 6)
        if (((x<low)|(x>hi)|(x%1!=0))&x.notna()).any():raise ValueError('Unexpected item coding '+col)
        f[col]=x
    keep=f.day.notna().to_numpy(copy=True)
    duplicates=np.zeros(len(f),dtype=bool)
    if member=='0072':
        duplicates=pd.DataFrame(dict(person=unit,day=f.day.to_numpy())).duplicated(keep=False).to_numpy()&keep
        keep &= ~duplicates
    if member=='0056':keep &= f.interaction.eq(1).to_numpy()
    if member=='0057':keep &= f.interaction.isin([1,2]).to_numpy()
    if member=='0076':keep &= f[['interaction_playful','interaction_pleasant','stressed']].notna().all(axis=1).to_numpy()
    f=f.loc[keep].reset_index(drop=True);unit=unit[keep]
    ratings={}
    for col in SOURCES[member][0]:
        values=f[col]
        if member in ('0056','0057'):
            values=values.where(f.interaction.eq(2 if col.startswith('occup_') else 1))
        ratings[col]=base.scale(values,unit)
    slopes={};unpleasant=[]
    def add(key,event,rating,negative=False):
        slopes[key]=(event,rating)
        if negative:unpleasant.append(key)
    if member in ('0056','0057'):
        ev={k.removeprefix('status_'):above(f[k].where(f.interaction.eq(1))) for k in STATUS_EVENTS[1:]}
        anger=(ratings['int_angry']+ratings['int_resentful'])/2
        for name in ('criticised','ignored','sidelined'):add(name+'_anger',ev[name],anger,True)
        for name in ('criticised','ignored'):add(name+'_shame',ev[name],ratings['int_ashamed'],True)
        add('upstaged_envy',ev['upstaged'],ratings['int_envious'],True)
        for name in ('proud','relaxed'):add('admired_'+name,ev['admired'],ratings['int_'+name])
        add('admired_proud_minus_relaxed',ev['admired'],ratings['int_proud']-ratings['int_relaxed'])
        if member=='0057':
            event=above(f.intellectual.where(f.interaction.eq(2)))
            for name in SOLITARY:add('intellectual_'+name,event,ratings[name])
            add('intellectual_enthusiastic_minus_relaxed',event,ratings[SOLITARY[0]]-ratings[SOLITARY[1]])
    elif member=='0072':
        health,money=(f[k].to_numpy() for k in PARENT_EVENTS[:2])
        ev=np.where((health==1)|(money==1),1.,np.where((health==0)&(money==0),0.,np.nan))
        child=above(f[list(CHILD_DISTRESS)].mean(axis=1,skipna=False))
        fear,worry,anger=[ratings['parent_'+k] for k in ('afraid','worried','angry')]
        for name,rating in [('fear',fear),('worry',worry),('anger',anger)]:add('stressor_'+name,ev,rating,True)
        add('stressor_fear_worry_minus_anger',ev,(fear+worry)/2-anger)
        add('child_distress_worry',child,worry,True);add('child_distress_anger',child,anger,True)
        add('child_distress_worry_minus_anger',child,worry-anger)
    else:
        add('stress_playfulness',above(f.stressed),base.scale(f.interaction_playful,unit))
    d=f.day.groupby(unit);mid=(d.transform('min')+d.transform('max'))/2
    return dict(ids=unit,n=len(roster),feelings=ratings,slopes=slopes,unpleasant=tuple(unpleasant),
                splits=dict(time=(f.day>mid).to_numpy(int),odd_even=(f.day%2==0).to_numpy(int)),
                counts=dict(source_reports=len(frame),source_people=len(roster),dated_context_reports=len(f),duplicate_day_rows=int(duplicates.sum()),missing_identity=int((~ids_ok).sum())))

