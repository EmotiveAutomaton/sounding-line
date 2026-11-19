"""Pooled conditional logit, chronological train/test, player-mean held-out gain.

DESIGN CHECK: LESSONS 3-5. Prior-only options prevent future leakage. Null count
worlds must show no held-out recency gain; preferences alone can produce a count
coefficient and never establish learning. Singular/separated/nonconvergent fits
are retained as invalid, not redrawn. Independent scalar arithmetic replays the
vectorized likelihood and gradients. No fitted coefficient is the primary.
V2 isolates each comparison's required fits; a failed secondary does not suppress
a valid primary. Invalidity retains observed support and never becomes a null.
"""
from collections import Counter
import math
import numpy as np
from scipy.optimize import minimize
from .week6_ch_riders_fields_v3 import opening_choices


def prepare(players,check=lambda:None):
    names=[]; choices=[]; census=Counter()
    for name in sorted(players):
        check();rows,counts=opening_choices(players[name]);census.update(counts)
        if not rows:continue
        index=len(names);names.append(name)
        for row in rows:
            row['person']=index;choices.append(row)
    offsets=[];features=[];selected=[];person=[];train=[];week=[]
    for row in choices:
        offsets.append(len(features));selected.append(len(features)+row['chosen'])
        x=np.asarray(row['features'],float)
        # The same shift is subtracted from every option in a choice. Its
        # softmax probabilities are mathematically unchanged; physical inputs
        # were preserved in the source projection and chronological census.
        x-=x.mean(axis=0)
        features.extend(x.tolist());person.append(row['person']);train.append(row['train']);week.append(row['week_break'])
    return dict(names=names,x=np.asarray(features,float).reshape(-1,3),
        starts=np.asarray(offsets,int),selected=np.asarray(selected,int),
        person=np.asarray(person,int),train=np.asarray(train,bool),week=np.asarray(week,bool),
        census=dict(census))


def subset(prepared, mask, columns):
    stops=np.r_[prepared['starts'][1:],len(prepared['x'])]
    index=np.flatnonzero(mask);starts=[];selected=[];x=[]
    for row in index:
        begin=prepared['starts'][row];end=stops[row]
        starts.append(len(x));selected.append(len(x)+prepared['selected'][row]-begin)
        x.extend(prepared['x'][begin:end][:,columns].tolist())
    starts=np.asarray(starts,int);x=np.asarray(x,float).reshape(-1,len(columns))
    lengths=np.diff(np.r_[starts,len(x)])
    return dict(x=x,starts=starts,lengths=lengths,selected=np.asarray(selected,int),
                person=prepared['person'][index],week=prepared['week'][index])


def likelihood(data,beta,weights,reference=False,need_hessian=False):
    x=data['x']; n=len(data['starts']); p=len(beta)
    if not n:return None
    w=np.asarray(weights,float)[data['person']]
    total=float(w.sum())
    if not total:return None
    if reference:
        ll=[];g=np.zeros(p);h=np.zeros((p,p));stops=np.r_[data['starts'][1:],len(x)]
        for i,(begin,end) in enumerate(zip(data['starts'],stops)):
            local=x[begin:end];u=[math.fsum(float(a*b) for a,b in zip(row,beta)) for row in local]
            peak=max(u);terms=[math.exp(v-peak) for v in u];denom=math.fsum(terms)
            probabilities=np.asarray([v/denom for v in terms]);chosen=data['selected'][i]-begin
            ll.append(u[chosen]-peak-math.log(denom))
            expected=np.asarray([math.fsum(float(probabilities[k]*local[k,j]) for k in range(len(local))) for j in range(p)])
            g+=w[i]*(local[chosen]-expected)
            if need_hessian:
                centered=local-expected
                for k in range(len(local)):h+=w[i]*probabilities[k]*np.outer(centered[k],centered[k])
        return np.asarray(ll),g/total,h/total
    utility=x@beta;maximum=np.maximum.reduceat(utility,data['starts'])
    terms=np.exp(utility-np.repeat(maximum,data['lengths']))
    denominator=np.add.reduceat(terms,data['starts']);probability=terms/np.repeat(denominator,data['lengths'])
    means=np.add.reduceat(probability[:,None]*x,data['starts'],axis=0)
    ll=utility[data['selected']]-maximum-np.log(denominator)
    gradient=np.einsum('i,ij->j',w,x[data['selected']]-means)/total
    hessian=np.zeros((p,p))
    if need_hessian:
        centered=x-np.repeat(means,data['lengths'],axis=0)
        hessian=np.einsum('i,ij,ik->jk',probability*np.repeat(w,data['lengths']),centered,centered)/total
    return ll,gradient,hessian


def fit(data,weights,reference=False,check=lambda:None):
    p=data['x'].shape[1]
    if not len(data['starts']) or not np.asarray(weights)[data['person']].sum():
        return dict(status='unsupported',reason='No training choices')
    beta=np.zeros(p);w=np.asarray(weights)[data['person']];total=w.sum()
    if reference:
        for iteration in range(100):
            check();ll,g,h=likelihood(data,beta,weights,True,True)
            if np.linalg.matrix_rank(h,tol=1e-10)!=p:return dict(status='invalid',reason='Unidentifiable choice model')
            if max(abs(g))<1e-11:break
            direction=np.linalg.solve(h,g);before=float(w@ll/total);step=1.
            while step>=2**-24:
                candidate=beta+step*direction
                new=likelihood(data,candidate,weights,True)[0]
                if float(w@new/total)>=before+1e-4*step*float(g@direction):break
                step/=2
            if step<2**-24:return dict(status='invalid',reason='Independent Newton line search failed')
            beta=candidate
    else:
        def objective(value):
            check();ll,g,_=likelihood(data,value,weights)
            return -float(w@ll/total),-g
        solved=minimize(objective,beta,jac=True,method='BFGS',options=dict(gtol=1e-11,maxiter=300))
        beta=solved.x
    ll,g,h=likelihood(data,beta,weights,reference,True)
    if (not np.isfinite(beta).all() or max(abs(beta))>30 or not np.isfinite(ll).all() or
            max(abs(g))>1e-6 or np.linalg.matrix_rank(h,tol=1e-10)!=p):
        return dict(status='invalid',reason='Unconverged, separated or unidentified conditional logit')
    return dict(status='complete',beta=beta.tolist(),mean_training_log_likelihood=float(w@ll/total),
                max_gradient=float(max(abs(g))),minimum_information_eigenvalue=float(np.linalg.eigvalsh(h).min()))


def model_sets(prepared):
    return {name:(subset(prepared,prepared['train'],cols),subset(prepared,~prepared['train'],cols))
            for name,cols in [('count',[0]),('hours',[0,1]),('games',[0,2])]}


def draw(prepared,sets,weights,reference=False,check=lambda:None):
    fits={name:fit(train,weights,reference,check) for name,(train,test) in sets.items()}
    result=dict(fits=fits,gains={})
    # A registered secondary cannot silently become an admission gate on the
    # primary. Each comparison requires its own arm and the shared count fit.
    logs={name:likelihood(test,np.asarray(fits[name]['beta']),weights,reference)[0]
          for name,(train,test) in sets.items() if fits[name]['status']=='complete'}
    test=sets['count'][1];n=len(prepared['names'])
    for arm in ('hours','games'):
        statuses={name:fits[name]['status'] for name in ('count',arm)}
        status=('invalid' if 'invalid' in statuses.values() else
                'unsupported' if 'unsupported' in statuses.values() else 'complete')
        if any(value not in ('invalid','unsupported','complete') for value in statuses.values()):
            raise ValueError('Unknown conditional fit status')
        gain=logs[arm]-logs['count'] if status=='complete' else None
        for label,mask in [('',np.ones(len(test['person']),bool)),('_week_break',test['week'])]:
            counts=np.bincount(test['person'][mask],minlength=n)
            ok=counts>0
            denominator=float(np.asarray(weights)[ok].sum())
            point=None
            if gain is not None and denominator:
                totals=np.bincount(test['person'][mask],weights=gain[mask],minlength=n)
                means=np.divide(totals,counts,out=np.zeros(n),where=ok)
                point=float(np.asarray(weights)[ok]@means[ok]/denominator)
            result['gains'][arm+label]=dict(point=point,
                players=int(ok.sum()),choices=int(counts.sum()),
                comparison_status=status,required_fits=statuses)
    return result


def result(prepared,point,draws):
    summary={}
    for name in ('hours','games','hours_week_break','games_week_break'):
        original=point['gains'][name]
        valid=[d['gains'][name]['point'] for d in draws if d['gains'][name]['point'] is not None]
        ci=np.quantile(valid,[.025,.975]).tolist() if (original['comparison_status']=='complete' and
            original['point'] is not None and original['players']>=20 and len(valid)==len(draws) and valid) else None
        value=original['point']
        label=('invalid fit' if original['comparison_status']=='invalid' else
            'below floor, descriptive' if original['players']<20 else
            'unsupported training comparison' if original['comparison_status']=='unsupported' else
            'uncertainty unavailable' if ci is None else
            'gain beyond bar' if value>=.003 and ci[0]>0 else 'count-only better' if ci[1]<0 else
            'inside practical band' if ci[0]>=-.003 and ci[1]<=.003 else 'inconclusive')
        summary[name]=dict(original,interval=ci,valid_draws=len(valid),invalid_draws=len(draws)-len(valid),
            classification=label if name=='hours' else 'descriptive secondary',required_players=20)
    return dict(card='CH14',bar=.003,primary='hours',gains=summary,fit=point['fits'],census=prepared['census'],
        players=len(prepared['names']),draws=len(draws),
        split='floor(2*n/3) eligible choices per player train, remaining choices test',
        limitations=['Predictive weighting rule only: a preference that drifts looks like recency.',
            'A positive count coefficient alone is not evidence that use raises readiness.',
            'Novel choices outside the past option set are counted and excluded, then update later history.',
            'Week-break rows use the same prior training fit; they are a held-out subset, not a new restricted fit.'])
