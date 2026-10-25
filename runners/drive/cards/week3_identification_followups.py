"""WA0.h1 one-generation specification, readout-attribution and reader checks.

DESIGN CHECK: LESSONS 2-5, CONTROLS 1-7, READER_HEURISTICS 6-10 reread
2026-10-25. NULL: identical/shared-prompt profiles cannot clear context; no
best partition or feature block is selected. ALTERNATIVE: stable independent
person patterns can clear the same two original gates. Removing the sole
planted feature block removes its signal; that is readout attribution only.
Every eligible writer, fixed gallery and original within-role null is retained.
Missing support stays unsupported; no redraws, successful-only pooling or next
generation. Full source bindings and every inference draw replay independently.
"""
from contextlib import contextmanager
from pathlib import Path
import math

import numpy as np
from threadpoolctl import threadpool_limits

from . import week3_identification as base
from . import week3_identification_crossfit as parent
from . import week3_identification_inputs as source
from .engine_habits_identification import FEATURES
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_pmap_source import completed
from .timing_stats import bind,check_binding

PRIMARY='EV3.final.residual'
FOLD_SEEDS=(20261026,20261027,20261028,20261029,20261030)
BLOCKS={'connectives':tuple(range(8)), 'punctuation':tuple(range(8,14)),
        'sentence_length':(14,15), 'quoted_share':(16,)}
CONFIGS={kind:dict(parent.CONFIG,card='WA0.h1.'+kind,followup=kind,
    generation=1,cpu_ceiling_seconds=5400) for kind in ('s','m','p')}
CONSTRUCTED={kind:dict(value,mode='constructed',permutations=64,bootstrap_draws=200)
             for kind,value in CONFIGS.items()}


def validate(config):
    if config not in [*CONFIGS.values(),*CONSTRUCTED.values()]:
        raise ValueError('fixed one-generation follow-up configuration required')


def correlation(a,b):
    """B-only preprocessing, row-centered unit profiles, neutral absent shape.

    A constant row has no direction: its similarity to every row is zero.
    This explicit extension retains zero-shape rows as uninformative; it does
    not turn them into missing writers or invent a Pearson coefficient.
    """
    a,b=np.asarray(a,float),np.asarray(b,float)
    if (a.shape!=b.shape or a.ndim!=2 or len(a)<2 or np.isinf(a).any() or np.isinf(b).any()
        or not np.isfinite(a).any(1).all() or not np.isfinite(b).any(1).all()):
        raise ValueError('absent channel or invalid paired gallery')
    have=np.isfinite(b).sum(0)
    mean=np.divide(np.nansum(b,axis=0),have,out=np.zeros(b.shape[1]),where=have>0)
    aa,bb=np.where(np.isfinite(a),a,mean),np.where(np.isfinite(b),b,mean)
    scale=bb.std(0);keep=(have>0)&(scale>1e-12)
    aa,bb=(aa[:,keep]-mean[keep])/scale[keep],(bb[:,keep]-mean[keep])/scale[keep]
    def shape(x):
        centered=x-x.mean(1,keepdims=True) if x.shape[1] else x
        norm=np.linalg.norm(centered,axis=1,keepdims=True)
        return np.divide(centered,norm,out=np.zeros_like(centered),where=norm>1e-12),int((norm<=1e-12).sum())
    aa,zero_a=shape(aa);bb,zero_b=shape(bb)
    distance=1-np.clip(aa@bb.T,-1.,1.)
    nearest=np.isclose(distance,distance.min(1)[:,None],atol=1e-12,rtol=1e-12)
    scores=nearest.diagonal()/nearest.sum(1)
    return dict(scores=scores.tolist(),accuracy=float(scores.mean()),chance=1/len(a),writers=len(a),
        missing_A=int((~np.isfinite(a)).sum()),missing_B=int((~np.isfinite(b)).sum()),
        features=len(mean),used_features=int(keep.sum()),absent_B_features=int((have==0).sum()),
        constant_features=int(((have>0)&~keep).sum()),tied_probes=int((nearest.sum(1)>1).sum()),
        neutral_shape_A=zero_a,neutral_shape_B=zero_b,
        standardization='B-only observed mean imputation and SD; row centering then unit norm; zero-shape similarity fixed at zero',
        reader='correlation distance on B-standardized profiles, with declared neutral zero-shape extension')


def correlation_identify(profiles,writers,roster,s):
    if len(roster)<3 or not set(roster)<=set(writers):return None
    p=profiles[[writers.index(w) for w in roster],:,s]
    if not np.isfinite(p).any(2).all():return None
    return correlation(p[:,0,:],p[:,1,:])


@contextmanager
def reader(kind):
    """Process-local substitution; originals restored even on refusal."""
    previous=base.identify
    if kind=='correlation':base.identify=correlation_identify
    elif kind!='euclidean':raise ValueError('unknown frozen reader')
    try:yield
    finally:base.identify=previous


def rosters(data):
    rows=data['rows'];x,slices=base.feature_matrix(rows);ww,g,_,_=base.split(rows)
    legacy=data['legacy']['pmap']
    common=sorted(w for w,v in legacy.items() if all(base.pmap.supported(v,c) for c in ('lean','style')))
    explicit={'PMAP.'+c:common if c in ('lean','style') else sorted(w for w,v in legacy.items() if base.pmap.supported(v,c)) for c in source.CHANNELS}
    return base.rosters_from_profiles(ww,base.means(x,g,ww),slices,explicit)


def compact(detail):
    """Retain every joined null draw and role/split proof, not redundant arrays."""
    return dict(variants=detail['variants'],writer_folds=detail['writer_folds'],
        rule=detail['rule'],null=detail['null'],folds=[dict(calibration=f['calibration'],
            donor_writers=f['donor_writers'],probe_writers=f['probe_writers'],gallery_writers=f['gallery_writers'],
            halves=f['detail']['halves'],excluded=f['detail']['excluded'],
            nuisance_coefficients=f['detail']['nuisance_coefficients']) for f in detail['folds']],
        replay='all original whole-prompt assignments reconstructed; joined null accuracy for every draw retained')


def projected(rows,drop):
    if drop not in BLOCKS:raise ValueError('unknown frozen EV3 feature block')
    keep=[i for i in range(len(FEATURES)) if i not in BLOCKS[drop]]
    output=[]
    for r in rows:
        v=r['features']['EV3.final']
        if len(v)!=17:raise ValueError('frozen seventeen-feature engine schema differs')
        output.append(dict(r,features={'EV3.final':[v[i] for i in keep]}))
    return output


def paired_change(original,changed,config):
    out={}
    for key,item in changed['variants'].items():
        before=original['variants'][key]
        if item['writers']!=before['writers']:raise ValueError('paired comparison writer roster changed')
        if any(v[arm] is None for v in (before,item) for arm in ('real','context')):
            out[key]=dict(state='unsupported',reason='entire original fixed support required');continue
        a=np.asarray(before['real']['scores']);b=np.asarray(item['real']['scores'])
        ca=np.asarray(before['context']['scores']);cb=np.asarray(item['context']['scores'])
        out[key]=dict(baseline_minus_variant_accuracy=base.paired_interval(a-b,config),
            baseline_minus_variant_context_gap=base.paired_interval((a-ca)-(b-cb),config),
            scope='paired probe-writer resampling with every complete gallery fixed; descriptive, not a causal feature effect')
    return out


def expected_points(summary,expected,exact=False):
    """Bind the baseline to completed parent levels even in cost-only pilots."""
    for name,value in summary.items():
        old=expected[name]
        if value['writers']!=old['writers']:raise ValueError('completed parent roster count changed')
        for arm in ('real','context'):
            if value.get(arm)!=old.get(arm):raise ValueError('completed parent baseline level changed')
        if value.get('fold_gallery_sizes')!=old.get('fold_gallery_sizes'):
            raise ValueError('completed parent gallery size changed')
    if exact and summary!=expected:
        raise ValueError('complete original parent baseline differs')


def analyze(data,config,checkpoint=lambda *args:None,expected=None):
    kind=config['followup'];rr=data['rows'];fixed=rosters(data)
    folds=parent.writer_folds(rr,parent.CONFIG['seed'])
    main,full=parent.analyze_group(rr,config,fixed,lambda f,n,t:checkpoint('baseline',f,n,t),folds=folds)
    if expected is not None:expected_points(main,expected,exact=all(
        config[k]==parent.CONFIG[k] for k in ('permutations','bootstrap_draws','seed')))
    baseline=compact(full);del full
    members={'baseline':main};details={'baseline':baseline};changes={}
    if kind=='s':
        for seed in FOLD_SEEDS[1:]:
            label='fold_seed_'+str(seed)
            result,dd=parent.analyze_group(rr,config,fixed,
                lambda f,n,t:checkpoint(label,f,n,t),folds=parent.writer_folds(rr,seed))
            members[label]=result;details[label]=compact(dd);del dd
        curve={}
        for name in main:
            values=[v[name] for v in members.values()]
            complete=all(v['state'] not in ('unsupported','invalid') for v in values)
            curve[name]=dict(specifications=len(values),passing=sum(v['pass_both'] for v in values),
                all_supported=complete,all_pass=complete and all(v['pass_both'] for v in values),
                accuracy_range=[min(v['real']['accuracy'] for v in values),max(v['real']['accuracy'] for v in values)] if complete else None,
                context_gap_range=[min(v['real_minus_context']['effect'] for v in values),max(v['real_minus_context']['effect'] for v in values)] if complete else None,
                scope='all frozen balanced partitions shown; no best partition, pooled permutation probability or successful-subset aggregate')
    elif kind=='p':
        with reader('correlation'):
            result,dd=parent.analyze_group(rr,config,fixed,
                lambda f,n,t:checkpoint('correlation',f,n,t),folds=folds)
        members['correlation']=result;details['correlation']=compact(dd)
        changes['correlation']=paired_change(baseline,details['correlation'],config);del dd
        curve=None
    elif kind=='m':
        for block in BLOCKS:
            label='without_'+block
            result,dd=parent.analyze_group(projected(rr,block),config,{'EV3.final':fixed['EV3.final']},
                lambda f,n,t:checkpoint(label,f,n,t),folds=folds)
            members[label]=result;details[label]=compact(dd)
            changes[label]=paired_change(baseline,details[label],config);del dd
        curve=None
    else:raise ValueError('unregistered follow-up')
    return dict(card=config['card'],schema=1,generation=1,primary=PRIMARY,members=members,
        specification_curve=curve,paired_changes=changes,config=config,
        feature_blocks={k:[FEATURES[i] for i in ix] for k,ix in BLOCKS.items()} if kind=='m' else None,
        corpus_sessions=len(rr),primary_writers=len(fixed['EV3.final']),
        source_measurement=data['method'],genre_branch='unchanged; GEN1.ic is not re-run or extended by these main-channel follow-ups',
        scope='conditional identification/readout robustness; no automatic attention, value, causal mechanism or personal-preference inference',
        control='same independent donors, fixed galleries, within-prompt-and-role null, p<.05 and paired gap CI lower>0; all probabilities descriptive',
        followups_authorized=False),dict(members=details)


def load(inputs,config):
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('constructed fixture required')
        return base.load(inputs,base.CONSTRUCTED),None
    if set(inputs)!={'source_completion','parent_completion'}:raise ValueError('complete original inputs and corrected parent required')
    root=Path(inputs['parent_completion']).resolve().parent
    for name in ('PLAN.json','output/SUMMARY.json','output/DETAIL.json.gz'):
        completed(inputs['parent_completion'],root/name)
    plan=read(root/'PLAN.json');old=read(root/'output/SUMMARY.json')
    if plan['module']!='runners.drive.cards.week3_identification_crossfit' or plan['config']!=parent.CONFIG:
        raise ValueError('completed approved original corrected control required')
    if Path(plan['inputs']['source_completion']).resolve()!=Path(inputs['source_completion']).resolve():
        raise ValueError('parent and follow-up source identity differs')
    if old['card']!='WA0.h1' or old['primary']!=PRIMARY:raise ValueError('wrong completed parent')
    return base.load({'source_completion':inputs['source_completion']},base.CONFIG),old['channels']


def run(output,inputs,config,verification=False):
    validate(config);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    data,expected=load(inputs,config)
    def checkpoint(member,fold,done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('follow-up stop/yield requested')
        if done%25==0 or done==total:progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',member=member,fold=fold,done=done,total=total))
    with threadpool_limits(limits=2):result,detail=analyze(data,config,checkpoint,expected)
    if verification:
        check_binding(output,inputs,config)
        if read(output/'SUMMARY.json')!=result or gzread(output/'DETAIL.json.gz')!=detail:raise ValueError('complete fresh follow-up replay differs')
        return dict(verified=True,full_permutation_replay=True)
    write_equal(output/'SUMMARY.json',result);gzip_equal(output/'DETAIL.json.gz',detail)
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,['SUMMARY.json','DETAIL.json.gz'])
    return dict(status='complete',full_permutation_replay=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
