"""TRX1, first-period activity appraisals and the released Neuroticism score.

DESIGN CHECK (LESSONS 3–5). Check against pf_trait's constructed worlds.
Singular denominators and absent support stay undefined. No status diary is
accepted by this source binding.
"""
from itertools import combinations
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd

from . import week6_bt_pbk_v1 as source
from . import week6_person_ladder_v1 as ladder
from . import week6_person_slopes_v1 as ref
from .batch_runtime import filehash
from . import week6_lb_bank_v1 as bank, week6_ld12_common_v1 as core
from . import week6_person_small_v1 as old
from .batch_runtime import atomic, freeze, now, read
from .week6_ld_draws_v1 import RequestedYield

NEGATIVE = ('worried','fearful','sad')
FEELINGS = (*NEGATIVE,'cheerful','relaxed','unpleasant_mean')
COLUMNS = ('id','study_period','day','pleasantness',*FEELINGS[:-1])
STATIC_SHA = '159da00094e03bc1d078f300622324e7a7d11cbc9793fce6a704dfb973a1708f'


def sources(pointer):
    ts = source.local_source(pointer)
    static = ts.with_name('0010_geschwind_static.tsv')
    if filehash(static) != STATIC_SHA:
        raise ValueError('Unrecognized static trait table')
    return ts,static


def parts(frame, traits, replay=False):
    if tuple(traits.columns) != ('id','neuroticism') or traits.id.duplicated().any() or traits.id.isna().any():
        raise ValueError('Require one trait record per identified participant')
    people = frame.loc[frame.id.notna() & frame.study_period.eq(0)].copy()
    ids = sorted(people.id.unique())
    scores = pd.to_numeric(traits.set_index('id').neuroticism,errors='raise').reindex(ids).to_numpy(float)
    for c in COLUMNS[2:]:
        people[c]=pd.to_numeric(people[c],errors='raise')
    if any(not people[c].dropna().isin(range(1,8)).all() for c in FEELINGS[:-1]):
        raise ValueError('Feeling outside the documented scale')
    ratings=people.pleasantness.dropna()
    if ratings.empty or not ratings.isin(range(-4,4)).all():
        raise ValueError('Missing or undocumented appraisal scale')
    cut=float(np.quantile(ratings,1/3,method='inverted_cdf'))
    dated=people[people.day.notna()].copy()
    roster=pd.Categorical(dated.id,categories=ids).codes.astype(int)
    days=dated.groupby('id').day
    second=(dated.day>(days.transform('min')+days.transform('max'))/2).to_numpy(int)
    dated['unpleasant_mean']=dated[list(NEGATIVE)].mean(axis=1,skipna=False)
    ev=np.where(dated.pleasantness.notna(),dated.pleasantness.le(cut),np.nan)
    pairs,_=ladder.half_panel(dict(ids=roster,n=len(ids),feelings={k:dated[k].to_numpy(float) for k in FEELINGS},
        slopes={k:(ev,dated[k].to_numpy(float)) for k in FEELINGS}),second,replay)
    report=dict(people=len(ids),missing_trait_people=int((~np.isfinite(scores)).sum()),
        baseline_prompts=len(people),undated_prompts=int(people.day.isna().sum()),missing_appraisal_prompts=int(people.pleasantness.isna().sum()),
        cutoff=cut,low_appraisal_fraction=float((ratings<=cut).mean()),feelings={})
    for k,(a,b) in pairs.items():
        ok=np.isfinite(scores)&np.isfinite(a['b'])&np.isfinite(b['b'])
        report['feelings'][k]=dict(supported_people=int(ok.sum()),insufficient_half_support_people=int((np.isfinite(scores)&~ok).sum()))
    return scores,pairs,report


def effect(scores, halves, draws):
    a,b=halves
    keep=np.isfinite(scores)&np.isfinite(a['b'])&np.isfinite(b['b'])
    out=np.full(len(draws),np.nan)
    if keep.sum()<2:return out
    tr=scores[keep]
    pr=lambda k:(a[k][keep],b[k][keep])
    base=np.minimum(*pr('n1'))
    weights=draws[:,keep]*base
    use=weights.sum(axis=1)>0
    if not use.any():return out
    w=weights[use]
    slopes=pr('b')
    X=[pr('L')]
    with np.errstate(divide='ignore',invalid='ignore'):
        if ref.wpearson(base,*pr('S'))>=.30:X.append(pr('S'))
        _,_,beta=ref.adjust(w,slopes,X)
        covariances=np.stack([ref.wcov(w,tr,(x+y)/2) for x,y in X],axis=-1)
        avg=(slopes[0]+slopes[1])/2
        den=np.sqrt(ref.wcov(w,tr,tr))*np.abs(ref.wmean(w,avg))
        num=ref.wcov(w,tr,avg)-(covariances*beta).sum(axis=-1)
        out[use]=np.divide(num,den,out=np.full(len(w),np.nan),where=den>ref.EPS)
    return out


def calculate(scores, panels, counts):
    v={k:effect(scores,p,counts) for k,p in panels.items()}
    for left,right in combinations(NEGATIVE,2):
        v[left+'_minus_'+right]=v[left]-v[right]
    return v


def binding(card,member,root):
    if (card,member)!=('TRX1','0010'):
        raise ValueError('Only the baseline clinical appraisal is bound')
    pointer=read(Path.cwd()/'.agent-state/data_collection_root.json')
    if Path(root)!=Path(pointer['root']):raise ValueError('Unexpected root')
    ts,_=sources(pointer)
    return ts,source.SHA


def evaluate(data,weights,guard,*,verify=False):
    guard()
    counts=core.multiplicities(data.people,weights)[None,:]
    results=calculate(*data.panels['trait'],counts)
    return {k:(float(a[0]) if np.isfinite(a[0]) else None) for k,a in results.items()}


def operate(output,inputs,config,replay):
    path,sha=binding(config['card'],config['member'],inputs['data_root'])
    static=path.with_name('0010_geschwind_static.tsv')
    if sha!=inputs['source_sha256'] or inputs['manifest_sha256']!=old.MANIFEST or filehash(static)!=STATIC_SHA:
        raise ValueError('Source changed')
    frame=pd.read_csv(path,sep='\t',usecols=COLUMNS,dtype={'id':str})
    traits=pd.read_csv(static,sep='\t',usecols=['id','neuroticism'],dtype={'id':str})[['id','neuroticism']]
    scores,panels,report=parts(frame,traits,replay)
    data=core.Prepared(len(scores),report)
    data.panels['trait']=(scores,panels)
    data.specs={k:{} for k in [*FEELINGS,*(a+'_minus_'+b for a,b in combinations(NEGATIVE,2))]}
    directory=Path(output)/('verify' if replay else 'execute')
    start=time.monotonic()
    def guard():
        if time.monotonic()-start>=config['max_wall_seconds'] or any((Path(output)/k).exists() for k in ('YIELD_REQUEST.json','STOP_REQUEST.json')):
            raise RequestedYield('runtime limit')
    def progress(n,t):
        atomic(directory/'DRAW_PROGRESS.json',dict(at=now(),committed_draws=n,elapsed=t))
    try:
        result=bank.run(directory,sys.modules[__name__],data,member='0010',source_digest=sha,seed=202611190010,
            guard=guard,verify=replay,execute_dir=Path(output)/'execute',limit=config['max_new_draws'],progress=progress)
    except RequestedYield as exc:
        return dict(status='yielded',verified=False,reason=str(exc))
    dest=directory/'ENGINE_RESULT.json'
    if dest.exists():
        if read(dest)!=result:raise ValueError('Changed result')
    else:freeze(dest,result)
    return dict(status='verified' if replay else 'computed',verified=replay,engine_sha256=filehash(dest),draw_count=2000)


def execute(output,inputs,config):
    return operate(output,inputs,config,False)


def verify(output,inputs,config):
    return operate(output,inputs,config,True)
