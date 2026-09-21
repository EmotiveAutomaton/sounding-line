"""Frozen native production knowledge crossed with objective inversion.

DESIGN CHECK: LESSONS 3-5; CONTROLS 3,6. NULL identical laws give balanced
posteriors; disjoint laws give zero oracle loss. ALTERNATIVE learned knowledge
can help or hurt without voiding. Source/replay/ruler errors fail closed.
No new fit, human claim, outcome selection or silent probability clipping.
"""
from itertools import product
import numpy as np
from . import native_math as N, native_shared as S
from .common import read, freeze, filehash

OBJECTIVES=('functional','presentation')
REWARDS=(S.SUCCESS,np.array([float(a[2]) for a in S.ARTIFACTS]))
ARMS=('untrained','declarative','active','replay','demonstration','oracle')


def policy(kernel,reward):
    if kernel.shape!=S.SHAPE or not np.isfinite(kernel).all() or (kernel<0).any():
        raise ValueError('invalid transition model')
    S.close(kernel.sum(-1),np.ones(S.SHAPE[:-1]))
    values=np.zeros((4,2,8,8));values[3]=reward[None,:,None]
    selected=np.zeros(S.SHAPE[:-2],dtype=int)
    for step,ctx,ai,previous in product((2,1,0),range(2),range(8),range(8)):
        q=kernel[step,ctx,ai,previous]@values[step+1,ctx,:,ai]
        goal=int(np.flatnonzero(q>=q.max()-1e-12)[0])
        selected[step,ctx,ai,previous]=goal
        values[step,ctx,ai,previous]=q[goal]
    return selected


def endpoints(kernel,pi):
    result=np.zeros((2,8))
    for ctx,initial in enumerate(S.INITIAL):
        mass=np.zeros((8,8));mass[initial,initial]=1.
        for step in range(3):
            following=np.zeros_like(mass)
            for a,previous in product(range(8),repeat=2):
                following[:,a]+=mass[a,previous]*kernel[step,ctx,a,previous,pi[step,ctx,a,previous]]
            mass=following
        result[ctx]=mass.sum(1)
    S.close(result.sum(-1),np.ones(2))
    return result


def observed(laws,quality):
    # laws: objective, context, endpoint; lexicographic artifact indexing.
    if quality=='intact':return laws.copy()
    if quality!='hide-evidence':raise ValueError('unknown observation channel')
    out=np.zeros((2,2,4))
    for i,a in enumerate(S.ARTIFACTS):out[:,:,2*a[0]+a[2]]+=laws[:,:,i]
    return out


def posterior(laws):
    total=laws.sum(0)
    out=np.full_like(laws,.5)
    np.divide(laws,total[None],out=out,where=total[None]>0)
    return out,total==0


def score(truth,predicted):
    p,unsupported=posterior(predicted)
    joint=truth/4.  # balanced objectives and initial contexts
    S.close(np.array(joint.sum()),np.array(1.))
    by=[]
    for goal in range(2):
        loss=.5*((p[0]-(goal==0))**2+(p[1]-(goal==1))**2)
        weights=truth[goal]/2.;positive=weights>0
        zeros=positive&(p[goal]==0)
        log=None if zeros.any() else float(-np.sum(weights[positive]*np.log(p[goal][positive])))
        by.append(dict(half_brier=float((weights*loss).sum()),log_loss=log,
            zero_probability_mass=float(weights[zeros].sum()),unsupported_mass=float(weights[unsupported].sum())))
    return dict(half_brier=float(np.mean([r['half_brier'] for r in by])),
        log_loss=None if any(r['log_loss'] is None for r in by) else float(np.mean([r['log_loss'] for r in by])),
        log_loss_infinite=any(r['log_loss'] is None for r in by),by_objective=by,
        zero_probability_mass=float(np.mean([r['zero_probability_mass'] for r in by])),
        unsupported_mass=float(np.mean([r['unsupported_mass'] for r in by])))


def controls():
    same=np.full((2,2,8),1/8.)
    S.close(np.array(score(same,same)['half_brier']),np.array(.25),0)
    disjoint=np.zeros((2,2,8));disjoint[0,:,0]=1;disjoint[1,:,7]=1
    S.close(np.array(score(disjoint,disjoint)['half_brier']),np.array(0.),0)
    wrong=score(disjoint,disjoint[::-1])
    if not wrong['log_loss_infinite'] or wrong['zero_probability_mass']!=1:raise ValueError('confident error did not fail')
    absent=np.zeros_like(disjoint);fallback=score(disjoint,absent)
    if fallback['unsupported_mass']!=1 or fallback['half_brier']!=.25:raise ValueError('unsupported mass disappeared')
    # Degradation collapses distinct evidence bits while retaining valid states.
    colliding=np.zeros_like(disjoint);colliding[0,:,0]=1;colliding[1,:,2]=1
    if score(observed(colliding,'hide-evidence'),observed(colliding,'hide-evidence'))['half_brier']!=.25:
        raise ValueError('channel did not remove evidence')
    return dict(balanced_null=True,disjoint_ceiling=True,infinite_error=True,unsupported_retained=True,degradation=True)


def run(out,card,pulse,raw):
    checks=controls();root,cfg=S.packet(card,S.PRACTICE,pulse)
    if card['episodes']!=512 or max(cfg['budgets'])!=512:raise ValueError('checkpoint differs')
    records=[];arrays={};max_replay=0.;models=0
    declarative=S.production_kernel(dict(action_rate=.75,goal_strength=1.,routine_strength=.2))
    for lineage in cfg['lineages']:
        true=S.production_kernel(N.law(lineage))
        S.close(true,N.arrays(root/'evaluator'/f'law-{lineage}.npz')['kernel'],1e-12)
        true_policies=[policy(true,r) for r in REWARDS]
        truth=np.array([endpoints(true,p) for p in true_policies])
        for draw,seed,condition in product(cfg['training_draws'],cfg['policy_seeds'],('matched-start','restricted-start')):
            pulse(phase='expertise-complete-rivals',lineage=lineage,draw=draw,seed=seed,condition=condition)
            kernels=dict(untrained=np.full(S.SHAPE,1/8.),declarative=declarative,oracle=true)
            tables={}
            for arm in ('active','replay','demonstration'):
                stem=f'{lineage}-{draw}-{seed}-{condition}-512-{arm}'
                a=N.arrays(root/'models'/f'{stem}.npz');tables[arm]=a['counts']
                kernels[arm]=a['counts']/a['counts'].sum(-1,keepdims=True);models+=1
            max_replay=max(max_replay,S.close(tables['active'],tables['replay'],0))
            base=f'{lineage}-{draw}-{seed}-{condition}'
            production={};forecast={}
            for arm in ARMS:
                chosen=[policy(kernels[arm],r) for r in REWARDS]
                predicted=np.array([endpoints(kernels[arm],p) for p in chosen])
                actual=np.array([endpoints(true,p) for p in chosen])
                success=np.array([actual[g]@r for g,r in enumerate(REWARDS)])
                production[arm]=success;forecast[arm]=predicted
                arrays[base+'-'+arm+'-predicted']=predicted
                arrays[base+'-'+arm+'-production']=actual
                arrays[base+'-'+arm+'-policy']=np.array(chosen)
            S.close(forecast['active'],forecast['replay'],0);S.close(production['active'],production['replay'],0)
            arrays[base+'-truth']=truth
            for quality in ('intact','hide-evidence'):
                target=observed(truth,quality);oracle=score(target,target)
                if quality=='intact':oracle_intact=oracle['half_brier']
                elif oracle['half_brier']<oracle_intact-1e-12:raise ValueError('oracle improved after information loss')
                for arm in ARMS:
                    guessed=observed(forecast[arm],quality);result=score(target,guessed)
                    if result['half_brier']<oracle['half_brier']-1e-12:raise ValueError('reader beats known conditional oracle')
                    records.append(dict(lineage=lineage,draw=draw,policy_seed=seed,condition=condition,quality=quality,arm=arm,
                        episodes=512 if arm in ('active','replay','demonstration') else 0,
                        acquired_transitions=1536 if arm in ('active','demonstration') else 0,
                        processed_transitions=1536 if arm in ('active','replay','demonstration') else 0,
                        production_by_objective=production[arm].tolist(),**result))
    expected=len(cfg['lineages'])*len(cfg['training_draws'])*len(cfg['policy_seeds'])*2*2*len(ARMS)
    if len(records)!=expected:raise ValueError('incomplete rival roster')
    competence=[]
    for lineage,condition,arm in product(cfg['lineages'],('matched-start','restricted-start'),('active','replay','demonstration')):
        def success(a):return np.mean([r['production_by_objective'] for r in records if
            (r['lineage'],r['condition'],r['arm'],r['quality'])==(lineage,condition,a,'intact')],axis=0)
        delta=success(arm)-success('untrained')
        competence.append(dict(lineage=lineage,condition=condition,arm=arm,
            improvement_by_objective=delta.tolist(),admitted=bool((delta.mean(-1)>1e-12).all())))
    destination=out/'PREDICTIONS.npz'
    if destination.exists():
        prior=N.arrays(destination)
        if set(prior)!=set(arrays):raise ValueError('saved prediction roster changed')
        for name,value in arrays.items():S.close(value,prior[name],0)
    else:np.savez_compressed(destination,**arrays)
    freeze(out/'ROWS.json',records);freeze(out/'COMPETENCE.json',competence)
    checks.update(source_bound=True,full_rivals=True,exact_replay=max_replay==0,oracle_dominance=True,oracle_information_loss=True)
    return dict(status='complete',kind='scientific',rows=len(records),lineages=len(cfg['lineages']),frozen_tables=models,
        controls=checks,competence_admitted={a:all(r['admitted'] for r in competence if r['arm']==a) for a in ('active','replay','demonstration')},
        scope='descriptive shared native development contrast; exact-program readers; fixed optimal maker assumption; no human or neural claim',
        files={n:filehash(out/n) for n in ('ROWS.json','COMPETENCE.json','PREDICTIONS.npz')})
