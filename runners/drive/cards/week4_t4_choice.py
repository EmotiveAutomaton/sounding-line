"""Prospective T4 shared/individual temperature models and constructed bank.

DESIGN CHECK: LESSONS 3-5 reread November 2. Exact probabilities, full gradient
and zero-feature invariance must hold under null and alternative. Oracle expected
log score dominates fitted predictions under both. Planted temperatures should
improve held-out expectation; shared temperatures should not manufacture material
gain. Calibration failure is retained, never a license to tune human criteria.
"""
from pathlib import Path
import time
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from .timing_p6 import read, write_equal, progress


RIDGE=1e-5


def checked(data):
    x,z,w,y=data['x'],data['z'],data['w'],data['y']
    if x.ndim!=3 or z.shape!=(len(x),2) or x.shape[2]!=5 or w.shape!=y.shape or w.shape!=(len(x),):
        raise ValueError('Malformed choice data')
    if not np.isfinite(x).all() or not np.isfinite(z).all() or not np.issubdtype(w.dtype,np.integer) or not np.issubdtype(y.dtype,np.integer):
        raise ValueError('Nonfinite/noninteger choice data')
    if len(x)==0 or np.any(w<0) or set(w)!=set(range(int(w.max())+1)) or np.any(y<0) or np.any(y>x.shape[1]):
        raise ValueError('Unsupported writer or choice')
    return int(w.max())+1


def unpack(theta, writers, individual):
    beta=theta[:5];gamma=theta[5:7];delta=theta[7:7+writers]
    q=theta[7+writers:] if individual else np.zeros(writers)
    if len(theta)!=7+writers*(2 if individual else 1):raise ValueError('Wrong parameter size')
    log_temperature=q-q.mean()
    return beta,gamma,delta,log_temperature


def logits(theta,data,individual):
    writers=int(data['w'].max())+1;b,g,d,q=unpack(theta,writers,individual)
    options=np.einsum('nkd,d->nk',data['x'],b)*np.exp(-q[data['w']])[:,None]+(data['z']@g)[:,None]
    return np.column_stack((options,d[data['w']]))


def objective(theta,data,individual):
    w=data['w'];writers=int(w.max())+1;b,g,d,q=unpack(theta,writers,individual)
    a=logits(theta,data,individual);n=len(a);prob=softmax(a,axis=1)
    value=float(np.mean(logsumexp(a,axis=1)-a[np.arange(n),data['y']])+RIDGE*.5*np.dot(theta,theta))
    residual=prob;residual[np.arange(n),data['y']]-=1;residual/=n
    ro=residual[:,:-1];scale=np.exp(-q[w]);gradient=np.zeros_like(theta)
    gradient[:5]=np.einsum('nk,nkd,n->d',ro,data['x'],scale)
    gradient[5:7]=data['z'].T@ro.sum(axis=1)
    gradient[7:7+writers]=np.bincount(w,weights=residual[:,-1],minlength=writers)
    if individual:
        xb=np.einsum('nkd,d->nk',data['x'],b)
        dq=np.bincount(w,weights=-(ro*xb*scale[:,None]).sum(axis=1),minlength=writers)
        gradient[7+writers:]=dq-dq.mean()
    gradient+=RIDGE*theta
    return value,gradient


def projected_gradient(theta,gradient,bounds):
    g=gradient.copy()
    for i,(lo,hi) in enumerate(bounds):
        if lo is not None and theta[i]<=lo+1e-10 and g[i]>0:g[i]=0
        if hi is not None and theta[i]>=hi-1e-10 and g[i]<0:g[i]=0
    return float(np.max(np.abs(g)))


def fit(data,individual):
    writers=checked(data);size=7+writers*(2 if individual else 1)
    bounds=[(None,None)]*(7+writers)+([(-3.,3.)]*writers if individual else [])
    starts=[]
    for sign in (0.,-1.,1.):
        t=np.zeros(size)
        t[:5]=sign*.1*np.asarray([1.,-.5,.2,.1,.3])
        if individual:t[7+writers:]=sign*.2*np.where(np.arange(writers)%2,1.,-1.)
        starts.append(t)
    receipts=[];candidates=[]
    for start in starts:
        result=minimize(objective,start,args=(data,individual),method='L-BFGS-B',jac=True,bounds=bounds,
                        options=dict(maxiter=1500,gtol=1e-8,ftol=1e-12,maxls=40))
        value,gradient=objective(result.x,data,individual);gap=projected_gradient(result.x,gradient,bounds)
        certified=np.isfinite(value) and np.isfinite(result.x).all() and gap<=1e-5
        receipt=dict(objective=value,projected_gradient=gap,iterations=int(result.nit),status=int(result.status),certified=bool(certified))
        receipts.append(receipt)
        if certified:candidates.append((value,result.x))
    if not candidates:raise ValueError('No numerically certified choice fit: '+str(receipts))
    value,theta=min(candidates,key=lambda x:x[0]);b,g,d,q=unpack(theta,writers,individual)
    return dict(theta=theta.tolist(),objective=value,attempts=receipts,temperatures=np.exp(q).tolist(),
                boundary_coordinates=int(np.sum(np.abs(theta[7+writers:])>=3-1e-8)) if individual else 0)


def known_answers():
    rng=np.random.default_rng(99);data=dict(x=rng.normal(size=(12,3,5)),z=rng.normal(size=(12,2)),w=np.arange(12)%3,y=np.arange(12)%4)
    for individual in (False,True):
        t=rng.normal(size=7+3*(2 if individual else 1))*.2
        v,g=objective(t,data,individual);eps=1e-6;numeric=[]
        for i in range(len(t)):
            a=t.copy();b=t.copy();a[i]+=eps;b[i]-=eps
            numeric.append((objective(a,data,individual)[0]-objective(b,data,individual)[0])/(2*eps))
        if not np.allclose(g,numeric,atol=2e-6,rtol=0):raise ValueError('Analytic gradient fails finite differences')
        beta,gamma,delta,q=unpack(t,3,individual);manual=[]
        for x,z,w in zip(data['x'],data['z'],data['w']):
            values=[sum(float(xi[j])*float(beta[j]) for j in range(5))/np.exp(q[w])+float(np.dot(z,gamma)) for xi in x]+[delta[w]]
            e=np.exp(np.asarray(values)-max(values));manual.append(e/e.sum())
        assert np.allclose(softmax(logits(t,data,individual),axis=1),manual,atol=1e-12,rtol=0)
    zeros=dict(data,x=np.zeros_like(data['x']),z=np.zeros_like(data['z']))
    t=np.zeros(13);t[7:10]=[-1.,0.,1.];original=logits(t,zeros,True);t[10:]=[-2.,1.,1.]
    assert np.array_equal(original,logits(t,zeros,True))
    assert checked(data)==3
    return dict(direct_probability=True,finite_difference_gradient=True,zero_feature_temperature_invariance=True)


def world(seed,individual):
    rng=np.random.default_rng(seed);writers=26;beta=np.asarray([1.,-.5,.2,.1,.3]);gamma=np.asarray([.3,-.2])
    # Dismissal varies in blocks of two; temperature alternates, crossing the two.
    delta=np.where((np.arange(writers)//2)%2,1.5,-1.5)
    q=np.where(np.arange(writers)%2,np.log(4.),np.log(.25)) if individual else np.zeros(writers)
    truth=np.concatenate((beta,gamma,delta,q))
    sets=[]
    for count in (80,200):
        w=np.repeat(np.arange(writers),count);x=rng.normal(size=(len(w),3,5));z=rng.normal(size=(len(w),2))
        data=dict(x=x,z=z,w=w,y=np.zeros(len(w),dtype=int))
        probabilities=softmax(logits(truth,data,True),axis=1)
        data['y']=(rng.random(len(w))[:,None]>np.cumsum(probabilities,axis=1)).sum(axis=1)
        sets.append((data,probabilities))
    train,_=sets[0];test,p=sets[1]
    # Identical scaling from training observations for both fitted models.
    xm=train['x'].mean(axis=(0,1));xs=train['x'].std(axis=(0,1));zm=train['z'].mean(axis=0);zs=train['z'].std(axis=0)
    xs=np.where(xs>1e-12,xs,1.);zs=np.where(zs>1e-12,zs,1.)
    for data in (train,test):data['x']=(data['x']-xm)/xs;data['z']=(data['z']-zm)/zs
    shared=fit(train,False);personal=fit(train,True)
    score=lambda model,ind:float(np.mean(np.sum(p*(logits(np.asarray(model['theta']),test,ind)-logsumexp(logits(np.asarray(model['theta']),test,ind),axis=1)[:,None]),axis=1)))
    a,b=score(shared,False),score(personal,True);oracle=float(np.mean(np.sum(p*np.log(np.maximum(p,1e-300)),axis=1)))
    if max(a,b)>oracle+1e-10:raise ValueError('Fitted prediction exceeded expected oracle')
    return dict(seed=seed,regime='individual' if individual else 'shared',expected_gain=b-a,shared_expected_score=a,individual_expected_score=b,oracle_expected_score=oracle,
                temperature_correlation=float(np.corrcoef(np.log(personal['temperatures']),q)[0,1]) if individual else None,
                shared=shared,individual=personal)


def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown validation scope')
    return dict(card='T4-choice',mode=mode,seed=20261102,worlds=20,probe=3,ridge=RIDGE)


def run(output,inputs,config,verification=False):
    if inputs or config!=configuration(config['mode']):raise ValueError('Constructed frozen choice validation only')
    output=Path(output);start=time.process_time();checks=known_answers();bank=[]
    count=0 if config['mode']=='constructed' else 3 if config['mode']=='timing' else 20
    for i in range(count):
        for individual in (False,True):bank.append(world(config['seed']+i,individual))
        progress(output/'PROGRESS.json',dict(phase='verify-models' if verification else 'models',done=i+1,total=count))
    summary=dict(mode=config['mode'],checks=checks,worlds=len(bank),human_scoring=False,scientific_admission=False)
    if count:
        gains={kind:float(np.mean([r['expected_gain'] for r in bank if r['regime']==kind])) for kind in ('shared','individual')}
        summary.update(mean_expected_gains=gains,boundary_fits=sum(r['individual']['boundary_coordinates']>0 for r in bank),
                       complete_bank=count==20,bank_gate=(gains['individual']>.02 and gains['shared']<=.005) if count==20 else None)
    values={'SUMMARY.json':summary,'WORLDS.json':bank}
    for n,v in values.items():
        if verification:
            old=read(output/n)
            def equal(a,b):
                if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
                if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
                if isinstance(a,float):return abs(a-b)<=1e-10
                return a==b
            if not equal(old,v):raise ValueError('Independent fitted replay differs')
        else:write_equal(output/n,v)
    if not verification and count:write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start,full_forecast_cpu_seconds=3*(time.process_time()-start)*20/count))
    return dict(verified=True,complete_fitted_replay=True) if verification else dict(status='complete')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
