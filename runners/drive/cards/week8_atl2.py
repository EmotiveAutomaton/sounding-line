"""Replay the 976 registered diary-family atlas rows in ten whole-person splits.

DESIGN CHECK (2026-11-27). Lessons read: LESSONS §§2–3 and CONTROLS §1.
Under the null, random halves can disagree or include zero. Under the
alternative, a reproducible event–feeling relationship gives the same signed
interval in both halves. Direction comes from the two estimates. Undefined
halves cannot count as agreement. Every split stays in the denominator of ten.
The case reaches the registered list at eight agreements, including equality.
"""
from collections import defaultdict
import csv
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from . import week8_gear as gear, week8_atlas_halves as model
from runners.stage14.common import atomic,filehash,freeze,read

HIST=gear.REPO/'.agent-state/drive-20261115/week7-phase1'
REG=HIST/'ATL_FOURTEEN_SOURCE'
PUBLIC=gear.REPO/'results/phase_2_4_stage_15/WEEK7/ATL_FOURTEEN_SOURCE_EXTENSION_pooled.csv'
INTERNAL=gear.ROOT.parent/'drive-week7-20261122/ATL-extended-0049-20261123'
UNIT='ATL2-frozen-atlas-halves'
STATIC_VOID={'scale endpoint undocumented','unbound occurrence floor','Different assessment schedules',
             'Grid floor absent from dictionary; separate registered mood comparison retained',
             'Unbound numeric or nominal contrast','fewer than 20 matched people','fewer than 20 with event variation'}


def originals():
    if str(HIST) not in sys.path:
        sys.path.insert(0,str(HIST))
    import atl_status,atl_other,adm_atl
    return atl_status,atl_other,adm_atl


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def frozen_roster():
    pooled=csv_rows(PUBLIC)
    if filehash(PUBLIC)!=filehash(REG/'pooled.csv'):
        raise ValueError('Pooled register differs from the filed table')
    order=[(r['event'],r['feeling'],r['scope']) for r in pooled]
    if len(order)!=976 or len(set(order))!=976:
        raise ValueError('Incomplete pooled table')
    groups=defaultdict(list)
    for r in csv_rows(REG/'items.csv'):
        k=(r['event_family'],r['feeling_family'])
        item=(r['member'],r['event'],r['feeling'],r['reason'])
        groups[(*k,'all')].append(item)
        if not r['historical_guess_overlap']:
            groups[(*k,'unread')].append(item)
    # This additional file has no entries in any public pooling denominator.
    if filehash(INTERNAL/'verify_INTERNAL.json')!=read(INTERNAL/'COMPLETE.json')['result_sha256']:
        raise ValueError('Internal register differs from the verified source')
    private=[]
    for key in sorted(read(INTERNAL/'verify_INTERNAL.json')):
        e,y=key.split('/')
        target=(e,y,'internal')
        private.append(target)
        groups[target].append(('0049',e,y,''))
    return order,private,groups


def design(unit):
    if unit!=UNIT:raise ValueError('Unknown atlas unit')
    s,o,a=originals()
    expected={}
    pins=[PUBLIC,REG/'items.csv',REG/'pooled.csv',REG/'inputs.json',INTERNAL/'verify_INTERNAL.json',INTERNAL/'COMPLETE.json',
          gear.REPO/'docs/design/stage-15/week8/ATL2.md',Path(model.__file__),HIST/'cal_shuffle.py',
          Path(s.__file__),Path(o.__file__),Path(a.__file__)]
    for member in ('0056','0057'):
        p,digest=s.source(member)
        expected[str(p)]=digest
        pins.append(p.parent.parent/'DOCUMENTED_METADATA.json')
    for member in o.MEMBERS:
        p,digest=o.source(member)
        expected[str(p)]=digest
        pins.append(o.D/(member+'.json'))
    for member in ('atus','couples'):
        _,extra=a.inputs(member)
        expected.update(extra)
    return dict(inputs=list(dict.fromkeys([*pins,*map(Path,expected)])),expected=expected,peak=2.0,cap=20000,
                operations=['execute'],source='frozen fourteen-source atlas and internal 0049')


def fixture():
    s,_,_=originals()
    rng=np.random.default_rng(44)
    u=np.repeat(np.arange(100),12)
    x=rng.integers(0,3,len(u)).astype(float)
    y=(rng.random(len(u))<1/(1+np.exp(2-2*x))).astype(float)
    owners=model.split_people(u,'invented',0)
    assert len(owners[0])==50 and not set(owners[0])&set(owners[1])
    a=model.fit_half(u,x,y,owners[0],890,draws=40,batch=8)
    b=model.fit_half(u,x,y,owners[0],890,draws=40,batch=13)
    assert np.array_equal(a,b) and min(a)>0
    keep=np.isin(u,owners[0])
    ids,X,n,yes=s.count_matrices(u[keep],x[keep],y[keep])
    w=np.vstack((np.ones(len(ids)),np.random.default_rng(890).multinomial(len(ids),np.full(len(ids),1/len(ids)),size=40)))
    want=np.array([s.fit(X,n@vec,yes@vec) for vec in w])
    assert np.allclose(want,a,atol=2e-8,rtol=0)
    assert model.fit_half(u,np.ones(len(u)),y,owners[0],890) is None
    assert model.direction(model.pooled([[a],[b]]))==1
    assert model.direction(model.pooled([[a],[-a]]))==0
    assert model.direction(None)==0
    order,private,_=frozen_roster()
    return dict(public_rows=len(order),internal_rows=len(private),original_operator_matches=True,whole_people=True,
                missing_distinct_from_zero=True,batching_independent=True)


class OriginalDiaries:
    @lru_cache(maxsize=16)
    def load(self,member):
        status,other,adm=originals()
        if member in ('0056','0057'):
            f,events,ys,features=status.projection(member)
            results={y:above_floor(f[y],1) for y in ys if int(features[y]['answer_categories'])==6}
        elif member in ('atus','couples'):
            root,_=adm.inputs(member)
            f,keys,ys=adm.load_frame(member,root)
            events={k:pd.to_numeric(f[k]).to_numpy(float) for k in keys}
            results={y:above_floor(adm.codes(f[y],range(7)),0) for y in ys}
        else:
            meta=read(other.D/(member+'.json'))['fields']
            keys,ys,floor=other.group(member,meta)
            path,_=other.source(member)
            cols=list(dict.fromkeys(['id',*keys,*ys]))
            f=pd.read_csv(path,sep='\t',dtype=str,keep_default_na=False,usecols=cols)
            f=f.loc[~f.id.isin(['','NA'])].reset_index(drop=True)
            def number(k):
                val=f[k].replace({'TRUE':'1','FALSE':'0','True':'1','False':'0'})
                z=pd.to_numeric(val,errors='coerce')
                return None if (z.isna()&~val.isin(['','NA','NaN','nan'])).any() else z.to_numpy(float)
            events={}
            for k in keys:
                val=number(k)
                if k=='interaction_type' and member=='0076' and val is not None:
                    for i in range(5):
                        events[k+'='+str(i)]=np.where(np.isfinite(val),val==i,np.nan)
                elif k=='helping_effort' and val is not None:
                    events[k]=np.where(number('helping_binary')==1,val,np.nan)
                elif k not in ('company','social_company') and val is not None:
                    events[k]=val
            results={}
            for y in ys:
                val=number(y)
                if val is not None:
                    results[y]=above_floor(val,0 if member=='0060' and y=='lonely' else floor)
        _,person=np.unique(f.id.astype(str),return_inverse=True)
        return person,events,results

    @lru_cache(maxsize=200)
    def halves(self,member,split):
        return model.split_people(self.load(member)[0],member,split)


def above_floor(a,floor):
    a=np.asarray(a,dtype=float)
    return np.where(np.isfinite(a),(a>floor).astype(float),np.nan)


def measure(diaries,items,split,side,batch):
    groups=defaultdict(list)
    for member,event,feeling,reason in items:
        if reason in STATIC_VOID:
            continue
        person,events,feelings=diaries.load(member)
        if event not in events or feeling not in feelings:
            continue
        samples=model.fit_half(person,events[event],feelings[feeling],diaries.halves(member,split)[side],
                               model.seed(member,split,side,'bootstrap'),batch=batch)
        if samples is not None and np.isfinite(samples).all():
            groups[member].append(samples)
    return model.pooled(groups.values())


def analyze(diaries,items,batch):
    fits=[]
    for split in range(10):
        a,b=[measure(diaries,items,split,side,batch) for side in range(2)]
        fits.append((a,b))
    valid=sum(a is not None and b is not None for a,b in fits)
    signs=[model.direction(a) if model.direction(a)==model.direction(b) else 0 for a,b in fits]
    return dict(splits=10,defined_both=valid,same_clear=sum(v!=0 for v in signs),
                both_positive=signs.count(1),both_negative=signs.count(-1),paired_intervals=fits)


def run(unit,d,mode):
    if unit!=UNIT or mode!='execute':
        raise ValueError('Unrecognized atlas operation')
    order,private,groups=frozen_roster()
    # Each finished checkpoint has both independent fits, including the source
    # decoder. Use the original table order, interleaving the internal-only file.
    sequence=[]
    for i,key in enumerate(order):
        if i<len(private):sequence.append(private[i])
        sequence.append(key)
    first,second=OriginalDiaries(),OriginalDiaries()
    dest=d/'verified_cells';dest.mkdir(exist_ok=True)
    for i,key in enumerate(sequence):
        path=dest/(str(i).zfill(4)+'.json')
        if path.exists():raise ValueError('Unexpected existing cell')
        data=analyze(first,groups[key],16)
        replay=analyze(second,groups[key],11)
        if data!=replay:raise ValueError('Independent atlas cell replay differs')
        freeze(path,dict(event=key[0],feeling=key[1],scope=key[2],**data))
        atomic(d/'ATLAS_PROGRESS.json',dict(verified=i+1,planned=len(sequence)))
    freeze(d/'ATLAS_COMPLETE.json',dict(public_rows=len(order),internal_rows=len(private),
           checksums={p.name:filehash(p) for p in sorted(dest.glob('*.json'))}))


def check(unit,d):
    p=d/'ATLAS_COMPLETE.json'
    obj=read(p)
    if obj['public_rows']!=976 or len(obj['checksums'])!=obj['public_rows']+obj['internal_rows']:
        raise ValueError('Incomplete atlas')
    if any(filehash(d/'verified_cells'/p)!=h for p,h in obj['checksums'].items()):
        raise ValueError('Changed verified atlas cell')
    return {p.name:filehash(p)}
