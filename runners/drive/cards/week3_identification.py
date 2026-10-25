"""WA0 session-summary identification references and GEN1 paired sensitivity.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-25.
Identical profiles tie at fractional chance and cannot pass. Prompt-only data
cannot beat their leave-writer-out context reference. Persistent person signal
can beat both context and the empirically rebuilt within-prompt label null.
Reversed matching must hurt. Missing fixed-gallery support invalidates a draw;
no redraw, successful-only probability or post-result population change.
Every arm uses the same session-mean operator, whole-prompt split, B-only
scaling/imputation and complete gallery. Only probe writers are bootstrapped.
The original pooled profiles are audit evidence, never the new control's ruler.
Fresh verification reconstructs every draw from the completed input binding.
"""
from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path
import time

import numpy as np
from scipy.stats import binom
from threadpoolctl import threadpool_limits

from . import timing_pmap_stats as pmap
from . import week3_identification_inputs as source
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_pmap_source import completed
from .timing_stats import bind,check_binding

CONFIG = dict(card='WA0',schema=1,mode='full',permutations=1000,
              genre_permutations=1000,bootstrap_draws=2000,seed=20261026)
CONSTRUCTED = dict(CONFIG,mode='constructed',permutations=64,genre_permutations=64,bootstrap_draws=200)
RESIDUALS = ('EV3.final','PMAP.final_style')


def finite_mean(x,axis=0):
    n=np.isfinite(x).sum(axis=axis)
    return np.divide(np.nansum(x,axis=axis),n,out=np.full(np.shape(n),np.nan),where=n>0)


def feature_matrix(rows):
    names=sorted(rows[0]['features']); slices={}; arrays=[];start=0
    for name in names:
        a=np.asarray([r['features'][name] for r in rows],float)
        if a.ndim!=2 or a.shape[1]==0 or np.isinf(a).any(): raise ValueError('invalid feature matrix')
        slices[name]=slice(start,start+a.shape[1]);start+=a.shape[1];arrays.append(a)
    if any(sorted(r['features'])!=names for r in rows):raise ValueError('feature roster changed')
    return np.column_stack(arrays),slices


def split(rows,assignment=None):
    halves,excluded=pmap.split_sessions(rows,assignment)
    writers=sorted(halves);index={r['session']:i for i,r in enumerate(rows)}
    if len(index)!=len(rows):raise ValueError('duplicate sessions')
    groups=np.full(len(rows),-1,dtype=int)
    saved={}
    for wi,w in enumerate(writers):
        saved[w]=[]
        for half,part in enumerate(halves[w]):
            if not part:raise ValueError('empty prompt half')
            ids=[index[r['session']] for r in part];groups[ids]=2*wi+half
            saved[w].append([r['session'] for r in part])
        if {r['prompt'] for r in halves[w][0]} & {r['prompt'] for r in halves[w][1]}:
            raise ValueError('prompt split leaked')
    return writers,groups,saved,excluded


def means(x,groups,writers):
    mask=groups>=0;x=x[mask];g=groups[mask]
    sums=np.zeros((2*len(writers),x.shape[1]));counts=np.zeros_like(sums)
    np.add.at(sums,g,np.nan_to_num(x,nan=0.));np.add.at(counts,g,np.isfinite(x))
    return np.divide(sums,counts,out=np.full_like(sums,np.nan),where=counts>0).reshape(len(writers),2,x.shape[1])


def context_rows(rows,x):
    """Prompt means exclude every session from the recipient's writer."""
    byprompt=defaultdict(list);bywriter=defaultdict(list)
    for i,r in enumerate(rows):byprompt[r['prompt']].append(i);bywriter[r['prompt'],r['writer']].append(i)
    out=np.full_like(x,np.nan)
    for prompt,ids in sorted(byprompt.items()):
        for writer in sorted({rows[i]['writer'] for i in ids}):
            own=bywriter[prompt,writer];excluded=set(own);donors=[i for i in ids if i not in excluded]
            if donors:out[own]=finite_mean(x[donors])
    return out


def residualize(x,share,groups,slices):
    """Fit each nuisance on gallery-half sessions only, then apply to both halves."""
    y=x.copy();coefficients={};b=(groups>=0)&(groups%2==1)
    if not np.isfinite(share).all() or np.any((share<0)|(share>1)):raise ValueError('invalid accepted share')
    for name in RESIDUALS:
        if name not in slices:continue
        s=slices[name];coef=[]
        for j in range(s.start,s.stop):
            good=b&np.isfinite(x[:,j]);ss=share[good];yy=x[good,j]
            if not len(ss):coef.append(None);y[:,j]=np.nan;continue
            center=float(ss.mean());den=float(np.sum((ss-center)**2))
            slope=float(np.sum((ss-center)*(yy-yy.mean()))/den) if den>1e-14 else 0.
            intercept=float(yy.mean()-slope*center)
            y[:,j]=x[:,j]-intercept-slope*share
            y[np.abs(y[:,j])<1e-12,j]=0.
            coef.append(dict(intercept=intercept,slope=slope,gallery_sessions=int(good.sum())))
        coefficients[name]=coef
    return y,coefficients


def rosters_from_profiles(writers,profiles,slices,explicit=None):
    result={}
    for name,s in slices.items():
        available=[w for i,w in enumerate(writers) if np.isfinite(profiles[i,:,s]).any(1).all()]
        result[name]=explicit[name] if explicit and name in explicit else available
    return result


def identify(profiles,writers,roster,s):
    if len(roster)<3 or not set(roster)<=set(writers):return None
    ix=[writers.index(w) for w in roster];p=profiles[ix,:,s]
    if not np.isfinite(p).any(2).all():return None
    return pmap.identify(p[:,0,:],p[:,1,:])


def paired_interval(scores,config):
    value=pmap.interval(scores,config['bootstrap_draws'],config['seed'])
    value.pop('z',None);value.pop('approximate_two_sided_wald_p',None)
    return value


def null_summary(draws,observed):
    if not draws or any(x is None for x in draws):
        return dict(state='invalid',attempted=len(draws),invalid=sum(x is None for x in draws),
                    one_sided_p=None,reason='fixed support missing; no redraw or successful-only p')
    a=np.asarray(draws,float)
    return dict(state='complete',attempted=len(a),invalid=0,mean=float(a.mean()),
                q025=float(np.quantile(a,.025)),q975=float(np.quantile(a,.975)),
                one_sided_p=(1+int(np.count_nonzero(a>=observed)))/(len(a)+1))


def assignment(rows,rng):
    blocks=defaultdict(list)
    for r in rows:blocks[r['prompt']].append(r)
    out={}
    for prompt,block in sorted(blocks.items()):
        block=sorted(block,key=lambda r:r['session'])
        for row,writer in zip(block,rng.permutation([r['writer'] for r in block])):out[row['session']]=str(writer)
    return out


def analyze_group(rows,config,explicit=None,checkpoint=lambda *args:None,context_provider=None,assignment_provider=None):
    rows=sorted(rows,key=lambda r:r['session']);x,slices=feature_matrix(rows)
    writers,groups,halves,excluded=split(rows)
    profiles=means(x,groups,writers);rosters=rosters_from_profiles(writers,profiles,slices,explicit)
    context=means(context_provider(rows,x,{}) if context_provider else context_rows(rows,x),groups,writers)
    variants={name:dict(real=identify(profiles,writers,rosters[name],s),
                       context=identify(context,writers,rosters[name],s),writers=rosters[name]) for name,s in slices.items()}
    share=np.asarray([r.get('accepted_share',0.) for r in rows]);coefficients={}
    if set(RESIDUALS)&set(slices):
        residual,coefficients=residualize(x,share,groups,slices)
        rp=means(residual,groups,writers)
        rc=means(context_provider(rows,residual,coefficients) if context_provider else context_rows(rows,residual),groups,writers)
        for name in RESIDUALS:
            if name in slices:variants[name+'.residual']=dict(real=identify(rp,writers,rosters[name],slices[name]),
                context=identify(rc,writers,rosters[name],slices[name]),writers=rosters[name])
    banks={name:[] for name in variants};bank_scores={name:[] for name in variants}
    rng=np.random.default_rng(config['seed']);assignments=[]
    for index in range(config['permutations']):
        labels=assignment_provider(index) if assignment_provider else assignment(rows,rng)
        ww,gg,_,_=split(rows,labels)
        pp=means(x,gg,ww)
        residual_pp=None
        if coefficients:residual_pp=means(residualize(x,share,gg,slices)[0],gg,ww)
        for name,item in variants.items():
            base=name.removesuffix('.residual');s=slices[base]
            result=identify(residual_pp if name.endswith('.residual') else pp,ww,item['writers'],s)
            banks[name].append(None if result is None else result['accuracy'])
            bank_scores[name].append(None if result is None else result['scores'])
        assignments.append([labels[r['session']] for r in rows]);checkpoint(index+1,config['permutations'])
    summaries={}
    for name,item in variants.items():
        real,ctx=item['real'],item['context']
        if real is None or ctx is None:
            summaries[name]=dict(state='unsupported',reason='complete fixed real/context gallery absent',writers=len(item['writers']),
                                 pass_both=False,real=real,context=ctx);continue
        null=null_summary(banks[name],real['accuracy'])
        ci=paired_interval(np.asarray(real['scores'])-ctx['scores'],config)
        passed=null['state']=='complete' and null['one_sided_p']<.05 and ci['ci_low']>0
        state='invalid' if null['state']=='invalid' else 'positive' if passed else 'negative' if ci['ci_high']<0 else 'not_detected'
        summaries[name]=dict(state=state,pass_both=passed,writers=len(item['writers']),
                             real={k:v for k,v in real.items() if k!='scores'},
                             context={k:v for k,v in ctx.items() if k!='scores'},permutation=null,real_minus_context=ci)
    detail=dict(variants=variants,banks=banks,null_probe_scores=bank_scores,assignments=assignments,sessions=[r['session'] for r in rows],
                halves=halves,excluded=excluded,nuisance_coefficients=coefficients)
    return summaries,detail


def paired_table(a,b):
    a,b=np.asarray(a,float),np.asarray(b,float)
    if a.shape!=b.shape or not np.isin(a,[0.,1.]).all() or not np.isin(b,[0.,1.]).all():
        return dict(state='unsupported',reason='fractional ties are not binary correctness; no invented discordant count')
    cells={f'{i}{j}':int(np.count_nonzero((a==i)&(b==j))) for i in (0,1) for j in (0,1)}
    discordant=cells['10']+cells['01'];p=1. if not discordant else min(1.,2*float(binom.cdf(min(cells['10'],cells['01']),discordant,.5)))
    return dict(state='complete',cells=cells,n=len(a),discordant=discordant,exact_two_sided_mcnemar_p=p,
                interpretation='rows creative correctness; columns argumentative correctness')


def mcnemar_power(n,p10,p01):
    q=p10+p01
    if q<0 or q>1 or min(p10,p01)<0:raise ValueError('infeasible joint distribution')
    if q==0:return 0.
    answer=0.
    for d in range(1,n+1):
        k=np.arange(d+1);reject=2*binom.cdf(np.minimum(k,d-k),d,.5)<.05
        answer+=float(binom.pmf(d,n,q)*binom.pmf(k[reject],d,p10/q).sum())
    return answer


def power_curve(table):
    if table['state']!='complete':return dict(state='unsupported',reason=table['reason'])
    n=table['n'];c=table['cells'];pa=(c['10']+c['11'])/n;pb=(c['01']+c['11'])/n
    denom=math.sqrt(pa*(1-pa)*pb*(1-pb))
    if denom==0:return dict(state='unsupported',reason='observed correctness has zero variance; paired dependence unidentified')
    phi=(c['11']/n-pa*pb)/denom;grid=[]
    for ia in range(40,91,5):
        for ib in range(40,91,5):
            a,b=ia/100,ib/100;both=a*b+phi*math.sqrt(a*(1-a)*b*(1-b))
            feasible=max(0.,a+b-1)-1e-12<=both<=min(a,b)+1e-12
            power=mcnemar_power(n,max(0.,a-both),max(0.,b-both)) if feasible else None
            grid.append(dict(creative_accuracy=a,argumentative_accuracy=b,difference=a-b,
                             feasible=bool(feasible),power=power,
                             discordance=a+b-2*both if feasible else None))
    eligible=[abs(r['difference']) for r in grid if r['power'] is not None and r['power']>=.8]
    return dict(state='complete',n=n,dependence='fixed empirical binary phi correlation',phi=phi,grid=grid,
                minimum_grid_absolute_difference_at_80_percent=min(eligible) if eligible else None,
                infeasible_cells='reported, not clipped; holding correlation fixed may violate Frechet bounds',
                scope='exact two-sided McNemar planning power at fixed gallery; not a universal detection threshold')


def genre_sensitivity(rows,genre_results,genre_details,config,checkpoint=lambda *args:None,real_scorer=None):
    rows=sorted(rows,key=lambda r:r['session']);writers=sorted({r['writer'] for r in rows})
    observed={};draws={k:[] for k in ('style','rhythm')};rng=np.random.default_rng(config['seed']+1)
    for name in draws:
        first=genre_details['creative']['variants'][name];second=genre_details['argumentative']['variants'][name]
        if first['writers']!=second['writers'] or first['real'] is None or second['real'] is None:
            observed[name]=None;continue
        a,b=first['real']['scores'],second['real']['scores'];table=paired_table(a,b)
        observed[name]=dict(difference=float(np.mean(np.asarray(a)-b)),paired_table=table,power=power_curve(table),
                            interval=paired_interval(np.asarray(a)-b,config))
    for i in range(config['genre_permutations']):
        flipped={w:bool(rng.integers(2)) for w in writers};scores={}
        for g in ('creative','argumentative'):
            selected=[r for r in rows if (r['genre']==g)!=flipped[r['writer']]]
            if real_scorer:
                scores[g]=real_scorer(selected)
            else:
                x,slices=feature_matrix(selected);ww,groups,_,_=split(selected);pp=means(x,groups,ww)
                scores[g]={name:identify(pp,ww,genre_details[g]['variants'][name]['writers'],slices[name]) for name in draws}
        for name in draws:
            aa,bb=scores['creative'][name],scores['argumentative'][name]
            draws[name].append(None if aa is None or bb is None else aa['accuracy']-bb['accuracy'])
        checkpoint(i+1,config['genre_permutations'])
    for name,value in observed.items():
        if value is None:observed[name]=dict(state='unsupported');continue
        bank=draws[name]
        if any(x is None for x in bank):value.update(state='invalid',genre_swap_p=None)
        else:
            p=(1+sum(abs(v)>=abs(value['difference'])-1e-12 for v in bank))/(len(bank)+1)
            valid=all(genre_results[g][name]['pass_both'] for g in genre_results)
            value.update(state='invalid_identification' if not valid else 'difference_detected' if p<.05 else 'not_detected',
                         genre_swap_p=p,identification_controls_pass=valid,
                         wording='Use measured paired power grid; no fixed 31-point statement inferred from marginal totals')
    return observed,draws


def analyze(data,config,checkpoint=lambda *args:None):
    # Preserve original PMAP channel support, including its common lean/style roster.
    legacy=data['legacy']['pmap'];common=sorted(w for w,v in legacy.items() if all(pmap.supported(v,c) for c in ('lean','style')))
    explicit={'PMAP.'+c:common if c in ('lean','style') else sorted(w for w,v in legacy.items() if pmap.supported(v,c)) for c in source.CHANNELS}
    main,detail=analyze_group(data['rows'],config,explicit,lambda d,t:checkpoint('main',d,t))
    gg={};gd={}
    genre_rows=data['genre_rows'];writers=sorted({r['writer'] for r in genre_rows})
    for g in ('creative','argumentative'):
        gg[g],gd[g]=analyze_group([r for r in genre_rows if r['genre']==g],config,
            {c:writers for c in ('style','rhythm')},lambda d,t:checkpoint(g,d,t))
    sensitivity,swaps=genre_sensitivity(genre_rows,gg,gd,config,lambda d,t:checkpoint('genre-swap',d,t))
    audit={}
    for c in source.CHANNELS:
        roster=explicit['PMAP.'+c]
        audit['PMAP.'+c]=pmap.identify([legacy[w][0][c] for w in roster],[legacy[w][1][c] for w in roster]) if len(roster)>=3 else None
    for g in gg:
        v=data['legacy']['genre'][g]
        for c in ('style','rhythm'):
            audit['GEN1.'+g+'.'+c]=pmap.identify([v[w][0][c] for w in writers],[v[w][1][c] for w in writers])
    result=dict(card='WA0',schema=1,primary='EV3.final.residual',primary_result=main['EV3.final.residual'],
                channels=main,genres=gg,genre_sensitivity=sensitivity,
                badge_licenses={'habit':False,'style':False},
                claim_licensing=False,
                control_defect='Literal leave-writer-out means can encode an omitted-writer fingerprint; retained diagnostic only; use approved WA0.h1',
                method=data['method'],original_results_preserved=True,
                original_pooled_comparison_scope='audit only; session-summary controls do not retroactively validate pooled estimands',
                unsupported_channels=['PMAP.content_taste'],
                control_rule='within-prompt writer-label permutation p<0.05 AND real-minus-context writer CI lower>0',
                bootstrap_scope='probe writers only; gallery fixed',config=config)
    return result,dict(main=detail,genres=gd,genre_swaps=swaps,original_pooled_audit=audit)


def load(inputs,config):
    if config==CONSTRUCTED and set(inputs)=={'fixture'}:
        data=read(inputs['fixture'])
        if not 6<=len({r['writer'] for r in data['rows']})<=30:
            raise ValueError('bounded constructed writer population required')
        return data
    if set(inputs)!={'source_completion'} or config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed WA0 analysis required')
    complete=Path(inputs['source_completion']).resolve();root=complete.parent
    for name in ('PLAN.json','output/INPUTS.json.gz','output/SOURCE_BINDINGS.json','output/SUMMARY.json'):
        completed(complete,root/name)
    plan=read(root/'PLAN.json')
    if plan['module']!='runners.drive.cards.week3_identification_inputs' or plan['config'] not in (source.CONFIG,source.CONSTRUCTED):
        raise ValueError('wrong completed source preparation')
    if (config['mode']=='full')!=(plan['config']['mode']=='full'):raise ValueError('constructed/real scope mismatch')
    if any(filehash(p)!=h for p,h in read(root/'output/SOURCE_BINDINGS.json').items()):raise ValueError('original source binding changed')
    return gzread(root/'output/INPUTS.json.gz')


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    data=load(inputs,config)
    def checkpoint(phase,done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('WA0 stop/yield requested')
        if done%25==0 or done==total:progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,done=done,total=total))
    with threadpool_limits(limits=2):result,detail=analyze(data,config,checkpoint)
    if verification:
        check_binding(output,inputs,config)
        if read(output/'SUMMARY.json')!=result or gzread(output/'DETAIL.json.gz')!=detail:raise ValueError('full fresh WA0 replay differs')
        return dict(verified=True,full_permutation_replay=True)
    write_equal(output/'SUMMARY.json',result);gzip_equal(output/'DETAIL.json.gz',detail)
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,['SUMMARY.json','DETAIL.json.gz'])
    return dict(status='complete',full_permutation_replay=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
