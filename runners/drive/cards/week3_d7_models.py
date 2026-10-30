"""D7 chronological completed-duration model core; no scientific admission.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 read 2026-10-29. Exact constant
NULL gives identical predictions; signed novelty ALTERNATIVES can improve
held-out prediction in either direction. Training-only transforms and selection
must be invariant to changed test responses. Censoring/support stays explicit.
"""
from collections import defaultdict
import math
import numpy as np

PENALTIES=(.001,.01,.1)
COSTS=('none','ordinal','elapsed')
RESPONSES=('duration','acceptance')


def partition(rows):
    if not rows or len({r['writer'] for r in rows})!=1 or len({r['key'] for r in rows})!=len(rows):
        raise ValueError('One writer and unique keys required')
    sessions={}
    for r in rows:
        clock=(r['session_start'],r['session_end'])
        if not all(math.isfinite(t) for t in clock) or clock[1]<clock[0]:raise ValueError('Invalid clock')
        if r['session'] in sessions and sessions[r['session']]!=clock:raise ValueError('Session clocks disagree')
        sessions[r['session']]=clock
    order=sorted(sessions,key=lambda k:(sessions[k][0],k));n=len(order);a=int(.6*n);b=int(.8*n)
    if min(a,b-a,n-b)<1 or a<3:return None,'session_support'
    names=(order[:a],order[a:b],order[b:])
    if max(sessions[k][1] for k in names[0])>=min(sessions[k][0] for k in names[1]) or max(sessions[k][1] for k in names[1])>=min(sessions[k][0] for k in names[2]):return None,'overlapping_time_ranges'
    groups=[np.array([i for i,r in enumerate(rows) if r['session'] in group and r['dwell_observed']],int) for group in names]
    if any(len(ids)<minimum for ids,minimum in zip(groups,(10,2,2))):return None,'observed_menu_support'
    return groups,None


def weights(rows,ids):
    count=defaultdict(int)
    for i in ids:count[rows[i]['session']]+=1
    return np.array([1/(len(count)*count[rows[i]['session']]) for i in ids])


def features(rows,train,response,cost,full,labels):
    if response not in RESPONSES or cost not in COSTS:raise ValueError('Unknown setting')
    prompts=sorted({rows[i]['prompt'] for i in train})
    columns=[]
    for i,r in enumerate(rows):
        v=[math.log1p(r['mean_option_characters']),r['menu_size']]
        if cost!='none':v.append(math.log1p(r['menu_ordinal'] if cost=='ordinal' else r['elapsed_seconds']))
        v.extend(float(r['prompt']==p) for p in prompts)
        if response=='duration':v.append(float(labels[i,1]))
        else:v.append(r['mean_novelty'])
        if full:v.append(r['mean_novelty'] if response=='duration' else labels[i,0])
        columns.append(v)
    x=np.asarray(columns,float)
    if not np.isfinite(x).all():raise ValueError('Nonfinite feature')
    mu=x[train].mean(0);sd=x[train].std(0);sd=np.where(sd<1e-12,1.,sd)
    return np.c_[np.ones(len(rows)),(x-mu)/sd]


def fit(x,y,weight,penalty):
    if x.ndim!=2 or len(x)!=len(y) or len(y)!=len(weight) or not np.isfinite(y).all():raise ValueError('Invalid fitting arrays')
    if np.all(y==y[0]):return np.r_[y[0],np.zeros(x.shape[1]-1)]
    h=x.T@(weight[:,None]*x);h+=np.diag(np.r_[0.,np.full(x.shape[1]-1,penalty)])
    b=x.T@(weight*y);beta=np.linalg.solve(h,b)
    if np.max(np.abs(h@beta-b))>1e-8:raise ValueError('Ridge solution uncertified')
    return beta


def label_array(rows):
    a=np.array([[math.log1p(r['dwell_seconds']),float(r['accepted'])] for r in rows])
    if not np.isfinite(a).all() or np.any(a[:,0]<0) or not np.isin(a[:,1],[0,1]).all():raise ValueError('Invalid labels')
    return a


def compare(rows,response,cost,labels=None):
    groups,reason=partition(rows)
    if reason:raise ValueError('Unsupported writer: '+reason)
    labels=label_array(rows) if labels is None else np.asarray(labels,float)
    if labels.shape!=(len(rows),2) or not np.isfinite(labels).all() or np.any(labels[:,0]<0) or not np.isin(labels[:,1],[0,1]).all():raise ValueError('Invalid label matrix')
    train,cal,test=groups;y=labels[:,RESPONSES.index(response)];wt=weights(rows,train);wc=weights(rows,cal);we=weights(rows,test)
    predictions=[];fits=[]
    def predict(x,b):
        values=x@b
        return np.clip(values,0,1) if response=='acceptance' else values
    # Half the sum across the two binary classes equals (p - y)**2.
    def loss(a,b):return (a-b)**2
    for full in (False,True):
        x=features(rows,train,response,cost,full,labels);candidates=[]
        for penalty in PENALTIES:
            beta=fit(x[train],y[train],wt,penalty);value=float(wc@loss(predict(x[cal],beta),y[cal]));candidates.append((value,penalty,beta))
        value,penalty,beta=min(candidates,key=lambda t:(t[0],t[1]));pred=predict(x[test],beta)
        predictions.append(pred);fits.append(dict(penalty=penalty,calibration_loss=value,coefficients=beta.tolist()))
    losses=[loss(p,y[test]) for p in predictions];delta=losses[0]-losses[1]
    return dict(response=response,cost=cost,test_keys=[rows[i]['key'] for i in test],train_keys=[rows[i]['key'] for i in train],calibration_keys=[rows[i]['key'] for i in cal],test_truth=y[test].tolist(),predictions=[p.tolist() for p in predictions],fits=fits,losses=[float(we@x) for x in losses],gain=float(we@delta),weight=we.tolist())


def world(seed=20261026,writers=12,sessions=10,menus=12,dose=.8):
    rng=np.random.default_rng(seed);rows=[]
    for w in range(writers):
        for s in range(sessions):
            start=s*100000+w*1000
            for j in range(menus):
                novelty=rng.uniform(0,1);accepted=bool(rng.integers(2));duration=2+.3*accepted+dose*(novelty-.5)+rng.normal(0,.08)
                rows.append(dict(key=f'{w}:{s}:{j}',writer=str(w),session=f'{w}:{s}',prompt=str(s%2),session_start=start,session_end=start+900,open_at=start+j*10,menu_ordinal=j,elapsed_seconds=j*10,mean_option_characters=30+int(rng.integers(10)),menu_size=5,mean_novelty=novelty,dwell_seconds=math.expm1(duration),dwell_observed=True,accepted=accepted))
    return rows


def writers(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['writer']].append(r)
    return {w:sorted(groups[w],key=lambda r:(r['open_at'],r['key'])) for w in sorted(groups)}
