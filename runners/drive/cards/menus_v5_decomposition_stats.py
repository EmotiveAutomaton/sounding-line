"""V5.d pair-exact base-rate subtraction and real-writer paired uncertainty.

DESIGN CHECK: LESSONS3-5 read October18. Deterministic pure base rates make
observed and leave-pair-out expected agreements coincide, hence H_context=0.
Context plants must remain positive after subtraction; reversed consistency
must remain negative. Unequal graph degree does not obey the balanced variance
identity, and unequal endpoint marginals distinguish Cohen from pooled chance.
Empty leave-out samples, degenerate kappas and unsupported bootstrap draws are
undefined, not zeros. Fake controls retain the exact pair graph and bootstrap
real writer nodes together in both arms.
"""
from collections import Counter
import math
import numpy as np
from . import states_v2 as states

METRICS=('count','agreement','lean','left_accept','left_edit','left_dismiss','left_ignore',
         'right_accept','right_edit','right_dismiss','right_ignore')
GROUPS=('within_writer_cross_session','cross_writer','same_session')


class CheckpointYield(Exception):
    pass


def lean_expectation(left,right,truth,writer):
    count=int(writer.max())+1
    counts=np.bincount(writer*4+truth,minlength=count*4).reshape(count,4).astype(float)
    sizes=counts.sum(axis=1);a=writer[left];b=writer[right];same=a==b
    va=counts[a]-np.eye(4)[truth[left]];vb=counts[b]-np.eye(4)[truth[right]]
    va[same]-=np.eye(4)[truth[right[same]]];vb[same]-=np.eye(4)[truth[left[same]]]
    na=sizes[a]-1-same;nb=sizes[b]-1-same;valid=(na>0)&(nb>0)
    value=np.full(len(left),np.nan);value[valid]=np.sum(va[valid]*vb[valid],axis=1)/(na[valid]*nb[valid])
    return value,valid,counts


def aggregate(left,right,truth,writer,session,real_writer,nreal):
    """Group under current labels; index weights by immutable REAL writer IDs."""
    lean,valid,counts=lean_expectation(left,right,truth,writer)
    within=writer[left]==writer[right];same=session[left]==session[right]
    groups=np.where(same,2,np.where(within,0,1))
    a=real_writer[left];b=real_writer[right];index=a*nreal+b
    metrics=np.c_[np.ones(len(left)),truth[left]==truth[right],np.nan_to_num(lean),
                  np.eye(4)[truth[left]],np.eye(4)[truth[right]]]
    result=np.zeros((3,len(METRICS),nreal,nreal))
    for g in range(3):
        selected=valid&(groups==g)
        for m in range(len(METRICS)):
            result[g,m]=np.bincount(index[selected],weights=metrics[selected,m],minlength=nreal*nreal).reshape(nreal,nreal)
    return result,dict(unsupported_leave_pair_out=int((~valid).sum()),
                       unsupported_by_group={name:int(((groups==g)&~valid).sum()) for g,name in enumerate(GROUPS)},pairs=int(len(left)),
                       supported_pairs=int(valid.sum())),counts


def node_weights(nwriters,draws,seed):
    copies=np.random.default_rng(seed).multinomial(nwriters,np.full(nwriters,1/nwriters),size=draws)
    weights=copies[:,:,None]*copies[:,None,:]
    diagonal=np.arange(nwriters);weights[:,diagonal,diagonal]=copies
    return weights.reshape(draws,-1).astype(float)


def weighted(aggregates,weights):
    return (weights@aggregates.reshape(-1,weights.shape[1]).T).reshape(len(weights),3,len(METRICS))


def quantities(sums):
    counts=sums[...,0];valid=counts>0
    agreement=np.divide(sums[...,1],counts,out=np.full_like(counts,np.nan),where=valid)
    lean=np.divide(sums[...,2],counts,out=np.full_like(counts,np.nan),where=valid)
    left=np.divide(sums[...,3:7],counts[...,None],out=np.full_like(sums[...,3:7],np.nan),where=valid[...,None])
    right=np.divide(sums[...,7:11],counts[...,None],out=np.full_like(sums[...,7:11],np.nan),where=valid[...,None])
    cohen=np.sum(left*right,axis=-1);pooled=np.sum(((left+right)/2)**2,axis=-1)
    def adjusted(chance):
        return np.divide(agreement-chance,1-chance,out=np.full_like(chance,np.nan),where=(1-chance)>1e-12)
    residual=agreement-lean
    return dict(agreement=agreement,lean=lean,residual=residual,chance_endpoint=cohen,chance_pooled=pooled,
        cohen_kappa=adjusted(cohen),pooled_mix_adjustment=adjusted(pooled),
        H=.5*(agreement[...,0]-agreement[...,1]),H_lean=.5*(lean[...,0]-lean[...,1]),
        H_context=.5*(residual[...,0]-residual[...,1]),
        H_same_session=.5*(agreement[...,2]-agreement[...,1]),
        H_same_lean=.5*(lean[...,2]-lean[...,1]),H_same_context=.5*(residual[...,2]-residual[...,1]),
        same_minus_cross_session_context=residual[...,2]-residual[...,0])


def interval(point,draws,config):
    values=np.asarray(draws,float);good=np.isfinite(values)
    valid=np.isfinite(point) and len(values)>1 and good.mean()>=1-config['maximum_undefined_fraction']
    if valid:
        lo,hi=np.quantile(values[good],[.025,.975]);se=float(values[good].std(ddof=1))
        p=math.erfc(abs(float(point)/se)/math.sqrt(2)) if se>0 else 1. if point==0 else 0.
    else:lo=hi=se=p=None
    point=float(point) if np.isfinite(point) else None
    return dict(effect=point,ci95=[lo,hi],standard_error=se,p_approx=p,
        state=states.contrast_state(point,lo,hi,valid=bool(valid)),supported_draws=int(good.sum()),draws=len(values))


def control_distribution(values,point):
    values=np.asarray(values,float);good=np.isfinite(values)
    if not good.all() or not np.isfinite(point):
        return dict(valid=False,draws=len(values),supported_draws=int(good.sum()),p_one_sided=None,
                    mean=None,sd=None,quantile95=None,biased_pipeline=None,
                    values=[float(v) if np.isfinite(v) else None for v in values])
    mean=float(values.mean());sd=float(values.std(ddof=1))
    return dict(valid=True,draws=len(values),supported_draws=len(values),
        p_one_sided=(1+int(np.sum(values>=point)))/(1+len(values)),mean=mean,sd=sd,
        quantile95=np.quantile(values,[.025,.975]).tolist(),biased_pipeline=bool(abs(mean)>.25*sd),
        values=values.tolist())


def balanced_identity(counts):
    sizes=counts.sum(axis=1);rates=counts[sizes>0]/sizes[sizes>0,None];n=len(rates)
    if n<2:return dict(valid=False)
    within=float(np.mean(np.sum(rates*rates,axis=1)))
    # Sampling two independent writer identities includes the same writer.
    independent=float(np.sum(rates.mean(axis=0)**2));variance=float(np.var(rates,axis=0).sum())
    distinct=float((np.sum(rates.sum(axis=0)**2)-np.sum(rates*rates))/(n*(n-1)))
    return dict(valid=True,writers=n,within=within,between_independent_writer_draws=independent,
        summed_population_variance=variance,identity_gap=(within-independent)-variance,
        between_distinct_writers=distinct,finite_writer_factor=n/(n-1),
        distinct_identity_gap=(within-distinct)-n/(n-1)*variance,
        scope='Balanced full-rate algebra, not the unequal-degree matched graph or pair-specific leave-two-out rates. Independent writer draws permit the same identity; distinct writers require n/(n-1).')


def primary_coefficients(aggregate):
    return np.asarray([aggregate[0,0],aggregate[0,1]-aggregate[0,2],aggregate[1,0],aggregate[1,1]-aggregate[1,2]])


def primary_from_coefficients(sums):
    a=np.divide(sums[...,1],sums[...,0],out=np.full(sums.shape[:-1],np.nan),where=sums[...,0]>0)
    b=np.divide(sums[...,3],sums[...,2],out=np.full(sums.shape[:-1],np.nan),where=sums[...,2]>0)
    return .5*(a-b)


def analyze(truth,writer,session,pairs,config,unit=None):
    if unit is None:unit=lambda kind,index,build:build()
    nw=int(writer.max())+1;weights=node_weights(nw,config['bootstrap_draws'],config['seed'])
    left,right=pairs['left'],pairs['right'];curves=[];primary_graph=None;primary_point=None;primary_draws=None
    for cutoff in (.6,.7,.8,.9):
        mask=pairs['similarity']>=cutoff;a=left[mask];b=right[mask]
        graph,support,counts=aggregate(a,b,truth,writer,session,writer,nw)
        point=quantities(graph.sum(axis=(-1,-2)));draws=quantities(weighted(graph,weights))
        reported={k:interval(point[k],draws[k],config) for k in ('H','H_lean','H_context','H_same_session','H_same_lean','H_same_context','same_minus_cross_session_context')}
        if support['unsupported_leave_pair_out']:
            # Never relabel a supported-subgraph statistic as the exact saved-pair estimand.
            for key in ('H_lean','H_context','H_same_lean','H_same_context','same_minus_cross_session_context'):
                reported[key]=interval(np.nan,np.full(len(weights),np.nan),config)
            point['H_context']=np.nan;draws['H_context']=np.full(len(weights),np.nan)
        groups={}
        for g,name in enumerate(GROUPS):
            groups[name]=dict(pairs=int(graph[g,0].sum()),**{k:float(point[k][g]) if np.isfinite(point[k][g]) else None
                for k in ('agreement','lean','residual','chance_endpoint','chance_pooled','cohen_kappa','pooled_mix_adjustment')})
        curves.append(dict(cutoff=cutoff,contrasts=reported,groups=groups,support=support))
        if cutoff==.8:primary_graph=(a,b);primary_point=float(point['H_context']);primary_draws=draws['H_context']
    a,b=primary_graph;rng=np.random.default_rng(config['seed']);permutations=[];fake=[];fake_coefficients=[]
    by_writer=[np.flatnonzero(writer==i) for i in range(nw)]
    for number in range(config['permutations']):
        labels=truth.copy()
        for indices in by_writer:labels[indices]=rng.permutation(labels[indices])
        def build_permutation():
            graph,support,_=aggregate(a,b,labels,writer,session,writer,nw)
            value=float(quantities(graph.sum(axis=(-1,-2)))['H_context'])
            return dict(value=value if np.isfinite(value) and not support['unsupported_leave_pair_out'] else None)
        saved=unit('outcome',number,build_permutation)
        permutations.append(np.nan if saved['value'] is None else saved['value'])
    session_ids=np.unique(session);session_writer=np.array([writer[np.flatnonzero(session==s)[0]] for s in session_ids])
    if not np.array_equal(session_ids,np.arange(len(session_ids))):raise ValueError('session encoding must be contiguous')
    rng=np.random.default_rng(config['seed'])
    for number in range(config['permutations']):
        labels=rng.permutation(session_writer)[session]
        def build_fake():
            graph,support,_=aggregate(a,b,truth,labels,session,writer,nw)
            return dict(coefficients=primary_coefficients(graph).tolist(),valid=not bool(support['unsupported_leave_pair_out']))
        saved=unit('fake',number,build_fake);coeff=np.asarray(saved['coefficients'])
        if not saved['valid']:coeff=coeff*np.nan
        fake_coefficients.append(coeff);fake.append(float(primary_from_coefficients(coeff.sum(axis=(-1,-2)))))
    coefficients=np.asarray(fake_coefficients)
    sums=(weights@coefficients.reshape(config['permutations']*4,nw*nw).T).reshape(len(weights),config['permutations'],4)
    fake_draws=primary_from_coefficients(sums)
    # Unsupported assignments invalidate a draw rather than silently changing its fake average.
    paired=primary_draws-fake_draws.mean(axis=1);fake_point=float(np.mean(fake))
    primary=next(row for row in curves if row['cutoff']==.8)['contrasts']['H_context']
    return dict(primary=primary,state=primary['state'],curves=curves,
        outcome_permutations=control_distribution(permutations,primary_point),
        fake_writers=control_distribution(fake,primary_point),
        own_minus_fake=interval(primary_point-fake_point,paired,config),
        balanced_lean_check=balanced_identity(counts)),dict(fake_coefficients=coefficients)
