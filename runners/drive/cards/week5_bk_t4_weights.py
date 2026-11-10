"""Identified T4 texture: unit writer feature directions and relative temperatures.

The original primary is unchanged. Direction norm one and centered log
temperature separate direction from scale; common positive magnitude is free.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax,logsumexp
from . import week4_t4_variable as original
from . import week4_t4_choice as base


def directions(angles):
    a,b,c,d=np.asarray(angles).T
    sa,sb,sc,sd=np.sin(a),np.sin(b),np.sin(c),np.sin(d)
    ca,cb,cc,cd=np.cos(a),np.cos(b),np.cos(c),np.cos(d)
    u=np.c_[ca,sa*cb,sa*sb*cc,sa*sb*sc*cd,sa*sb*sc*sd]
    j=np.stack([np.c_[-sa,ca*cb,ca*sb*cc,ca*sb*sc*cd,ca*sb*sc*sd],
                np.c_[np.zeros(len(a)),-sa*sb,sa*cb*cc,sa*cb*sc*cd,sa*cb*sc*sd],
                np.c_[np.zeros(len(a)),np.zeros(len(a)),-sa*sb*sc,sa*sb*cc*cd,sa*sb*cc*sd],
                np.c_[np.zeros(len(a)),np.zeros(len(a)),np.zeros(len(a)),-sa*sb*sc*sd,sa*sb*sc*cd]],axis=1)
    return u,j


def angles_of(vector):
    v=np.asarray(vector,float);norm=np.linalg.norm(v)
    if norm<1e-12:v=np.ones(5)/np.sqrt(5)
    else:v=v/norm
    return np.array([np.arctan2(np.linalg.norm(v[1:]),v[0]),np.arctan2(np.linalg.norm(v[2:]),v[1]),
                     np.arctan2(np.linalg.norm(v[3:]),v[2]),np.arctan2(v[4],v[3])])


def unpack(theta,writers):
    if len(theta)!=3+6*writers:raise ValueError('Wrong identified texture parameter size')
    magnitude=np.exp(theta[0]);gamma=theta[1:3];delta=theta[3:3+writers];rawq=theta[3+writers:3+2*writers]
    u,j=directions(theta[3+2*writers:].reshape(writers,4))
    return magnitude,gamma,delta,rawq,rawq-rawq.mean(),u,j


def logits(theta,data):
    w=int(data['w'].max())+1;m,g,d,rawq,q,u,j=unpack(theta,w)
    v=m*np.exp(-q[data['w']])[:,None]*np.einsum('nkd,nd->nk',data['x'],u[data['w']])+(data['z']@g)[:,None]
    v=np.where(original.mask(data),v,-np.inf)
    return np.column_stack((v,d[data['w']]))


def objective(theta,data):
    ids=data['w'];w=int(ids.max())+1;m,g,d,rawq,q,u,j=unpack(theta,w)
    a=logits(theta,data);n=len(a);res=softmax(a,axis=1);res[np.arange(n),data['y']]-=1;res/=n
    ro=res[:,:-1];scale=m*np.exp(-q[ids]);projection=np.einsum('nkd,nd->nk',data['x'],u[ids]);v=projection*scale[:,None]
    penalty=m*m+g@g+d@d+rawq@rawq
    value=float(np.mean(logsumexp(a,axis=1)-a[np.arange(n),data['y']])+base.RIDGE*.5*penalty)
    grad=np.zeros_like(theta);grad[0]=np.sum(ro*v)+base.RIDGE*m*m
    grad[1:3]=data['z'].T@ro.sum(1)+base.RIDGE*g
    grad[3:3+w]=np.bincount(ids,weights=res[:,-1],minlength=w)+base.RIDGE*d
    dq=np.bincount(ids,weights=-(ro*v).sum(1),minlength=w)
    grad[3+w:3+2*w]=dq-dq.mean()+base.RIDGE*rawq
    perrow=np.einsum('nk,nkd,n->nd',ro,data['x'],scale);vectors=np.zeros((w,5));np.add.at(vectors,ids,perrow)
    grad[3+2*w:]=np.einsum('wd,wjd->wj',vectors,j).reshape(-1)
    return value,grad


def fit(data,baseline):
    w=original.checked(data);beta,gamma,delta,q=base.unpack(np.asarray(baseline['theta']),w,True)
    magnitude=max(float(np.linalg.norm(beta)),np.exp(-12));angle=angles_of(beta)
    initial=np.r_[np.log(magnitude),gamma,delta,q,np.tile(angle,w)]
    bounds=[(-12.,12.),(None,None),(None,None)]+[(None,None)]*w+[(-3.,3.)]*w+[(0.,np.pi),(0.,np.pi),(0.,np.pi),(-np.pi,np.pi)]*w
    starts=[]
    for sign in (0.,-1.,1.):
        candidate=initial.copy();perturb=sign*.15*np.where(np.arange(w)%2,1.,-1.)[:,None]*np.array([1.,-.5,.3,-.2])[None,:]
        aa=candidate[3+2*w:].reshape(w,4)+perturb
        aa[:,:3]=np.clip(aa[:,:3],0,np.pi);aa[:,3]=np.clip(aa[:,3],-np.pi,np.pi);candidate[3+2*w:]=aa.reshape(-1)
        starts.append(candidate)
    attempts=[];valid=[]
    for start in starts:
        out=minimize(objective,start,args=(data,),method='L-BFGS-B',jac=True,bounds=bounds,
                     options=dict(maxiter=1500,gtol=1e-8,ftol=1e-12,maxls=40))
        value,gradient=objective(out.x,data);gap=base.projected_gradient(out.x,gradient,bounds)
        certified=np.isfinite(value) and np.isfinite(out.x).all() and gap<=1e-5
        attempts.append(dict(objective=value,projected_gradient=gap,certified=bool(certified),iterations=int(out.nit),status=int(out.status)))
        if certified:valid.append((value,out.x))
    if not valid:raise ValueError('No certified identified-weight texture fit: '+str(attempts))
    value,theta=min(valid,key=lambda pair:pair[0]);m,g,d,r,q,u,j=unpack(theta,w)
    return dict(theta=theta.tolist(),objective=value,attempts=attempts,temperatures=np.exp(q).tolist(),
                unit_directions=u.tolist(),common_magnitude=float(m),
                identification='unit direction; common magnitude; centered log temperature',
                boundary_coordinates=int(sum((lo is not None and abs(t-lo)<1e-8) or (hi is not None and abs(t-hi)<1e-8) for t,(lo,hi) in zip(theta,bounds))))


def score(result,data,probabilities=None):
    a=logits(np.asarray(result['theta']),data);lp=a-logsumexp(a,axis=1)[:,None]
    if probabilities is None:return float(np.mean(lp[np.arange(len(lp)),data['y']]))
    return float(np.mean(np.sum(probabilities*np.where(probabilities>0,lp,0.),axis=1)))


def known_answers():
    rng=np.random.default_rng(20261107);w=3;theta=np.r_[.1,rng.normal(size=2)*.1,rng.normal(size=w)*.1,rng.normal(size=w)*.1,np.tile([1.,1.1,.9,.7],w)]
    data=dict(x=rng.normal(size=(18,5,5)),z=rng.normal(size=(18,2)),w=np.arange(18)%3,y=np.arange(18)%6,mask=np.ones((18,5),bool))
    value,gradient=objective(theta,data);numeric=[]
    for i in range(len(theta)):
        hi=theta.copy();lo=theta.copy();hi[i]+=1e-6;lo[i]-=1e-6
        numeric.append((objective(hi,data)[0]-objective(lo,data)[0])/2e-6)
    if not np.allclose(gradient,numeric,atol=2e-6,rtol=0):raise ValueError('Identified texture gradient failed')
    m,g,d,r,q,u,j=unpack(theta,w)
    if not np.allclose((u*u).sum(1),1.,atol=1e-14):raise ValueError('Direction normalization failed')
    if abs(q.sum())>1e-14:raise ValueError('Temperature gauge failed')
    reconstructed=np.array([directions(angles_of(v)[None,:])[0][0] for v in u])
    if not np.allclose(reconstructed,u,atol=1e-14):raise ValueError('Direction coordinate coverage failed')
    manual=[]
    for i in range(len(data['w'])):
        writer=data['w'][i];manual.append([m/np.exp(q[writer])*np.dot(x,u[writer])+np.dot(data['z'][i],g) for x in data['x'][i]]+[d[writer]])
    if not np.allclose(logits(theta,data),manual,atol=1e-12):raise ValueError('Direct texture probability oracle failed')
    return dict(full_gradient=True,unit_directions=True,centered_temperature=True,direct_probability=True)
