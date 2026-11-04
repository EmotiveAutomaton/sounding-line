"""Variable offered-set adapter for the frozen T4 model, before human scoring.

DESIGN CHECK: LESSONS 3-5 read in current T4 build. Padding is an impossible
alternative under null and alternative, never a new choice. Exact compact/padded
probability invariance, full finite-difference gradient and invalid-choice refusal
precede the native fitted bank. Original model and its outcomes stay immutable.
"""
from types import FunctionType
import numpy as np
from scipy.special import softmax,logsumexp
from . import week4_t4_choice as base


def mask(data):
    m=data.get('mask',np.ones(data['x'].shape[:2],dtype=bool))
    if m.dtype!=np.bool_ or m.shape!=data['x'].shape[:2] or not m.any(axis=1).all():
        raise ValueError('Invalid offered-option mask')
    return m


def checked(data):
    writers=base.checked(data);m=mask(data);offered=data['y']<m.shape[1]
    if not m[np.flatnonzero(offered),data['y'][offered]].all():raise ValueError('Choice points to padding')
    if np.any(data['x'][~m]!=0):raise ValueError('Padded features must be zero')
    return writers


def logits(theta,data,individual):
    a=base.logits(theta,data,individual)
    a[:,:-1]=np.where(mask(data),a[:,:-1],-np.inf)
    return a


# Rebind only these interfaces; retain the original objective gradient, optimizer,
# deterministic starts, bounds, penalty and selection bytecode without mutation.
objective=FunctionType(base.objective.__code__,dict(base.__dict__,logits=logits),'objective')
fit=FunctionType(base.fit.__code__,dict(base.__dict__,objective=objective,checked=checked),'fit')


def known_answers():
    old=base.known_answers();rng=np.random.default_rng(88)
    x=rng.normal(size=(6,5,5));m=np.arange(5)[None,:]<np.array([1,2,3,4,5,2])[:,None];x[~m]=0
    data=dict(x=x,z=rng.normal(size=(6,2)),w=np.arange(6)%3,y=np.array([0,1,2,3,4,5]),mask=m)
    assert checked(data)==3
    for individual in (False,True):
        theta=rng.normal(size=7+3*(2 if individual else 1))*.2
        a=logits(theta,data,individual);p=softmax(a,axis=1)
        assert (p[:,:-1][~m]==0).all()
        for i in range(len(x)):
            compact=dict(x=x[i:i+1,m[i]],z=data['z'][i:i+1],w=data['w'][i:i+1])
            # Compute manually with the full writer parameterization: no relabeling.
            beta,gamma,delta,q=base.unpack(theta,3,individual)
            values=list(compact['x'][0]@beta/np.exp(q[data['w'][i]])+data['z'][i]@gamma)+[delta[data['w'][i]]]
            assert np.allclose(p[i,np.r_[np.flatnonzero(m[i]),5]],softmax(values),atol=1e-12,rtol=0)
        _,g=objective(theta,data,individual);numeric=[];eps=1e-6
        for i in range(len(theta)):
            hi=theta.copy();lo=theta.copy();hi[i]+=eps;lo[i]-=eps
            numeric.append((objective(hi,data,individual)[0]-objective(lo,data,individual)[0])/(2*eps))
        assert np.allclose(g,numeric,atol=2e-6,rtol=0)
        extended=dict(data,x=np.pad(x,((0,0),(0,2),(0,0))),mask=np.pad(m,((0,0),(0,2))),y=np.where(data['y']==5,7,data['y']))
        assert abs(objective(theta,extended,individual)[0]-objective(theta,data,individual)[0])<1e-12
        assert np.allclose(objective(theta,extended,individual)[1],g,atol=1e-12,rtol=0)
    data['y'][0]=4
    try:checked(data)
    except ValueError:pass
    else:raise AssertionError('Selected padding was accepted')
    return dict(old,compact_padding_probability=True,masked_gradient=True,extra_padding_invariant=True,selected_padding_refused=True)


def world(seed,individual):
    rng=np.random.default_rng(seed);writers=26
    beta=np.array([1.,-.5,.2,.1,.3]);gamma=np.array([.3,-.2]);delta=np.where((np.arange(writers)//2)%2,1.5,-1.5)
    q=np.where(np.arange(writers)%2,np.log(4.),np.log(.25)) if individual else np.zeros(writers)
    truth=np.concatenate((beta,gamma,delta,q));sets=[]
    for count in (80,200):
        w=np.repeat(np.arange(writers),count);x=rng.normal(size=(len(w),5,5));z=rng.normal(size=(len(w),2))
        m=np.arange(5)[None,:]<rng.integers(1,6,len(w))[:,None];x[~m]=0
        data=dict(x=x,z=z,w=w,y=np.zeros(len(w),dtype=int),mask=m)
        probabilities=softmax(logits(truth,data,True),axis=1)
        data['y']=(rng.random(len(w))[:,None]>np.cumsum(probabilities,axis=1)).sum(axis=1)
        sets.append((data,probabilities))
    train,_=sets[0];test,p=sets[1];real=train['x'][train['mask']]
    xm=real.mean(axis=0);xs=real.std(axis=0);zm=train['z'].mean(axis=0);zs=train['z'].std(axis=0)
    xs=np.where(xs>1e-12,xs,1.);zs=np.where(zs>1e-12,zs,1.)
    for data in (train,test):
        data['x']=(data['x']-xm)/xs;data['x'][~data['mask']]=0;data['z']=(data['z']-zm)/zs
    shared=fit(train,False);personal=fit(train,True)
    def score(model,ind):
        a=logits(np.asarray(model['theta']),test,ind);lp=a-logsumexp(a,axis=1)[:,None]
        lp=np.where(p>0,lp,0.)
        return float(np.mean(np.sum(p*lp,axis=1)))
    a,b=score(shared,False),score(personal,True);oracle=float(np.mean(np.sum(p*np.log(np.maximum(p,1e-300)),axis=1)))
    if max(a,b)>oracle+1e-10:raise ValueError('Fitted prediction exceeded expected oracle')
    return dict(seed=seed,regime='individual' if individual else 'shared',expected_gain=b-a,shared_expected_score=a,individual_expected_score=b,oracle_expected_score=oracle,
                temperature_correlation=float(np.corrcoef(np.log(personal['temperatures']),q)[0,1]) if individual else None,
                shared=shared,individual=personal)


def configuration(mode):
    return dict(base.configuration(mode),card='T4-variable')


run=FunctionType(base.run.__code__,dict(base.__dict__,configuration=configuration,known_answers=known_answers,world=world),'run',base.run.__defaults__)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
