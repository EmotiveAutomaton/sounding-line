"""WA0.h1 independent-writer context reference, curator-approved 2026-10-25.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-25.
Identical/prompt-only features cannot clear context; stable person fingerprints
can. Context donors never include any writer in that fold's probe or gallery,
so leaving out the target cannot encode its negative fingerprint. Three frozen
writer folds rotate calibration donors, probes and extra gallery candidates.
Every original eligible writer is scored once; no fold is dropped or redrawn.
Null labels shuffle within prompt and frozen role fold, with one assignment
reused across rotations. Under no person
signal the empirical null is the reference; under persistent person signal both
its upper tail and the context interval can be cleared. Missing fixed support
invalidates the entire affected variant. No old pooled result is revalidated.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from . import week3_identification as base
from . import week3_identification_inputs as source
from .timing_p6 import gzip_equal,write_equal,progress,gzread
from .timing_census import read
from .timing_stats import bind,check_binding

CONFIG=dict(base.CONFIG,card='WA0.h1',context_folds=3)
CONSTRUCTED=dict(base.CONSTRUCTED,card='WA0.h1',context_folds=3)


def writer_folds(rows,seed=20261026):
    writers=sorted({r['writer'] for r in rows})
    if len(writers)<6:raise ValueError('three disjoint writer roles require at least six writers')
    order=np.random.default_rng(seed).permutation(writers)
    return {str(w):i%3 for i,w in enumerate(order)}


def independent_context(donors,slices):
    """Return a provider whose calibration rows are fixed before any score."""
    dx,ds=base.feature_matrix(donors)
    if ds!=slices:raise ValueError('donor feature schema differs')
    groups=defaultdict(list)
    for i,r in enumerate(donors):groups[r['prompt']].append(i)
    donor_ids={r['writer'] for r in donors}
    def provide(rows,x,coefficients):
        if donor_ids&{r['writer'] for r in rows}:raise ValueError('context donor writer overlaps scored gallery')
        dd=dx.copy()
        if coefficients:
            share=np.asarray([r['accepted_share'] for r in donors])
            for name,coefs in coefficients.items():
                s=slices[name]
                for j,c in zip(range(s.start,s.stop),coefs):
                    if c is None:dd[:,j]=np.nan
                    else:
                        dd[:,j]=dx[:,j]-c['intercept']-c['slope']*share
                        dd[np.abs(dd[:,j])<1e-12,j]=0.
        means={p:base.finite_mean(dd[ix]) for p,ix in sorted(groups.items())}
        return np.asarray([means.get(r['prompt'],np.full(dx.shape[1],np.nan)) for r in rows])
    return provide


def scopes(rows,rosters,folds,calibration):
    donors=[r for r in rows if folds[r['writer']]==calibration]
    analysis=[r for r in rows if folds[r['writer']]!=calibration]
    galleries={name:[w for w in roster if folds[w]!=calibration] for name,roster in rosters.items()}
    probes={name:[w for w in roster if folds[w]==(calibration+1)%3] for name,roster in rosters.items()}
    return donors,analysis,galleries,probes


def role_assignment(rows,folds,index,seed):
    """One coherent draw across every overlapping gallery, conditional on roles."""
    rng=np.random.default_rng(np.random.SeedSequence([seed,index]))
    blocks=defaultdict(list)
    for row in rows:blocks[row['prompt'],folds[row['writer']]].append(row)
    out={}
    for key,block in sorted(blocks.items()):
        block=sorted(block,key=lambda r:r['session'])
        for row,writer in zip(block,rng.permutation([r['writer'] for r in block])):
            out[row['session']]=str(writer)
    return out


def real_scores(rows,rosters,folds):
    """Fast identical cross-fit galleries for the genre-label randomization."""
    values={name:{} for name in rosters}
    for f in range(3):
        _,rr,galleries,probes=scopes(rows,rosters,folds,f)
        x,slices=base.feature_matrix(rr);ww,groups,_,_=base.split(rr);pp=base.means(x,groups,ww)
        for name,roster in galleries.items():
            result=base.identify(pp,ww,roster,slices[name])
            if result is None:return {key:None for key in rosters}
            for w in probes[name]:values[name][w]=result['scores'][roster.index(w)]
    return {name:dict(scores=[values[name][w] for w in roster],
                      accuracy=float(np.mean([values[name][w] for w in roster]))) for name,roster in rosters.items()}


def analyze_group(rows,config,explicit=None,checkpoint=lambda *args:None,folds=None):
    rows=sorted(rows,key=lambda r:r['session']);x,slices=base.feature_matrix(rows)
    ww,groups,_,_=base.split(rows);rosters=base.rosters_from_profiles(ww,base.means(x,groups,ww),slices,explicit)
    folds=writer_folds(rows,config['seed']) if folds is None else folds
    if set(folds)!={r['writer'] for r in rows}:raise ValueError('cross-fit writer population differs')
    fold_detail=[]
    for f in range(3):
        donors,rr,galleries,probes=scopes(rows,rosters,folds,f)
        provider=independent_context(donors,slices)
        summary,detail=base.analyze_group(rr,config,galleries,
            lambda done,total:checkpoint(f,done,total),context_provider=provider,
            assignment_provider=lambda index:role_assignment(rows,folds,index,config['seed']))
        fold_detail.append(dict(calibration=f,donor_writers=sorted({r['writer'] for r in donors}),
                                probe_writers=probes,gallery_writers=galleries,
                                summary=summary,detail=detail))
    variants=fold_detail[0]['detail']['variants'];result={};joined={}
    for name in variants:
        original=name.removesuffix('.residual');roster=rosters[original]
        real={};context={};banks=[{} for _ in range(config['permutations'])];missing=[];sizes=[]
        for fold in fold_detail:
            v=fold['detail']['variants'][name];probes=fold['probe_writers'][original];gallery=v['writers'];sizes.append(len(gallery))
            if v['real'] is None or v['context'] is None:
                missing.append(dict(fold=fold['calibration'],reason='fixed real/context gallery absent'));continue
            for w in probes:
                if w in real:raise ValueError('probe writer counted more than once')
                j=gallery.index(w);real[w]=v['real']['scores'][j];context[w]=v['context']['scores'][j]
                for bank,source_scores in zip(banks,fold['detail']['null_probe_scores'][name]):
                    if source_scores is not None:bank[w]=source_scores[j]
        if missing or set(real)!=set(roster) or len(roster)<3:
            result[name]=dict(state='unsupported',pass_both=False,writers=len(roster),
                              reason='entire original probe roster required in independent context folds',missing=missing)
            joined[name]=dict(writers=roster,real=None,context=None);continue
        a=[real[w] for w in roster];b=[context[w] for w in roster]
        null_means=[float(np.mean([bank[w] for w in roster])) if set(bank)==set(roster) else None for bank in banks]
        null=base.null_summary(null_means,float(np.mean(a)))
        ci=base.paired_interval(np.asarray(a)-b,config)
        passed=null['state']=='complete' and null['one_sided_p']<.05 and ci['ci_low']>0
        state='invalid' if null['state']=='invalid' else 'positive' if passed else 'negative' if ci['ci_high']<0 else 'not_detected'
        result[name]=dict(state=state,pass_both=passed,writers=len(roster),
                         real=dict(accuracy=float(np.mean(a))),context=dict(accuracy=float(np.mean(b))),
                         permutation=null,real_minus_context=ci,fold_gallery_sizes=sizes,
                         chance=float(np.mean([1/len(fold_detail[(folds[w]-1)%3]['gallery_writers'][original]) for w in roster])))
        joined[name]=dict(writers=roster,real=dict(scores=a,accuracy=float(np.mean(a))),
                          context=dict(scores=b,accuracy=float(np.mean(b))),null_means=null_means)
    return result,dict(variants=joined,folds=fold_detail,writer_folds=folds,
                       rule='donor fold f; probe fold (f+1)%3; gallery both non-donor folds; every eligible writer scored once',
                       null='one shared assignment within prompt and fixed writer role; reused across all rotations')


def analyze(data,config,checkpoint=lambda *args:None):
    legacy=data['legacy']['pmap'];common=sorted(w for w,v in legacy.items() if all(base.pmap.supported(v,c) for c in ('lean','style')))
    explicit={'PMAP.'+c:common if c in ('lean','style') else sorted(w for w,v in legacy.items() if base.pmap.supported(v,c)) for c in source.CHANNELS}
    main,detail=analyze_group(data['rows'],config,explicit,
                            lambda fold,d,t:checkpoint('main-fold-'+str(fold),d,t))
    genres={};gd={};rr=data['genre_rows'];writers=sorted({r['writer'] for r in rr});gf=writer_folds(rr,config['seed'])
    rosters={name:writers for name in ('style','rhythm')}
    for g in ('creative','argumentative'):
        genres[g],gd[g]=analyze_group([r for r in rr if r['genre']==g],config,rosters,
            lambda fold,d,t:checkpoint(g+'-fold-'+str(fold),d,t),folds=gf)
    sensitivity,swaps=base.genre_sensitivity(rr,genres,gd,config,
        lambda d,t:checkpoint('genre-swap',d,t),real_scorer=lambda rows:real_scores(rows,rosters,gf))
    result=dict(card='WA0.h1',schema=1,primary='EV3.final.residual',primary_result=main['EV3.final.residual'],
                channels=main,genres=genres,genre_sensitivity=sensitivity,
                badge_licenses={label:all(main[name+s]['pass_both'] for s in ('','.residual'))
                                for label,name in [('habit','EV3.final'),('style','PMAP.final_style')]},
                method=data['method'],context='independent writer calibration pools; three frozen rotating roles',
                scope='same complete source population; each eligible writer probed once in a reduced fixed gallery; not original pooled estimand',
                original_diagnostic='WA0 literal leave-writer-out rule retained separately and licenses no claim',
                unsupported_channels=['PMAP.content_taste'],config=config)
    return result,dict(main=detail,genres=gd,genre_swaps=swaps)


def run(output,inputs,config,verification=False):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed approved independent-context configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    old=base.CONFIG if config['mode']=='full' else base.CONSTRUCTED
    data=base.load(inputs,old)
    def checkpoint(phase,done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('WA0.h1 stop/yield requested')
        if done%25==0 or done==total:progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,done=done,total=total))
    with threadpool_limits(limits=2):result,detail=analyze(data,config,checkpoint)
    if verification:
        check_binding(output,inputs,config)
        if read(output/'SUMMARY.json')!=result or gzread(output/'DETAIL.json.gz')!=detail:raise ValueError('full fresh WA0.h1 replay differs')
        return dict(verified=True,full_permutation_replay=True)
    write_equal(output/'SUMMARY.json',result);gzip_equal(output/'DETAIL.json.gz',detail)
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,['SUMMARY.json','DETAIL.json.gz'])
    return dict(status='complete',full_permutation_replay=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
