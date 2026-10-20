"""Exact crossed REML objective with analytic derivatives and stable residuals.

DESIGN CHECK: LESSONS 3-5 read October 19. Same fixed/random model, variance
ceiling, start, tolerances and iteration cap as timing_d30_crossed. Stable
penalized residual evaluation avoids subtracting large nearly equal quadratics;
analytic derivatives avoid finite-difference cancellation. Dense covariance,
finite-difference derivative and contrast-reversal fixtures must agree. Undefined
zero residual variance, nonidentifiability and ceiling hits still refuse.
"""
import math
import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.sparse.linalg import splu
from . import timing_d30_crossed as original


def prepare(x,y,writers,markers):
    p=original.prepare(x,y,writers,markers)
    x=np.asarray(x,float);y=np.asarray(y,float)
    keep=p['kept_columns']; scale=x.std(0)
    a=np.column_stack([(x[:,keep]-x[:,keep].mean(0))/scale[keep],np.ones(len(x))])
    wl,ml=sorted(set(writers)),sorted(set(markers));nw=len(wl)
    wi,mi={v:i for i,v in enumerate(wl)},{v:i for i,v in enumerate(ml)}
    z=sparse.coo_matrix((np.ones(2*len(y)),(np.repeat(np.arange(len(y)),2),
        np.column_stack([[wi[v] for v in writers],[nw+mi[v] for v in markers]]).ravel())),
        shape=(len(y),nw+len(ml))).tocsc()
    h=np.column_stack([a,y]);g=(z.T@z).tocsc()
    p.update(a=a,y=y,z=z,ztz=g,g_dense=g.toarray(),zth=np.asarray(z.T@h),hth=h.T@h)
    return p


def evaluate(p,theta):
    ratios=np.expm1(theta);nw,nm=p['writer_levels'],p['marker_levels']
    d=np.sqrt(np.r_[np.repeat(ratios[0],nw),np.repeat(ratios[1],nm)])
    diagonal=sparse.diags(d,format='csc')
    factor=splu(sparse.eye(nw+nm,format='csc')+diagonal@p['ztz']@diagonal)
    u=d[:,None]*p['zth']; cross=p['hth']-u.T@factor.solve(u)
    information=cross[:-1,:-1];sign,logdet=np.linalg.slogdet(information)
    if sign<=0:raise ValueError('undefined crossed information')
    beta=np.linalg.solve(information,cross[:-1,-1])
    residual=p['y']-p['a']@beta
    latent=factor.solve(d*np.asarray(p['z'].T@residual).ravel())
    remainder=residual-p['z']@(d*latent)
    rss=float(remainder@remainder+latent@latent);df=p['n']-p['p']
    if not math.isfinite(rss) or rss<=0:raise ValueError('undefined crossed residual variance')
    objective=float(np.log(np.abs(factor.U.diagonal())).sum()+logdet+df*math.log(rss/df))
    dg=d[:,None]*p['g_dense']
    diagonal_zvz=p['ztz'].diagonal()-np.sum(dg*factor.solve(dg),axis=0)
    zvh=p['zth']-p['ztz']@(d[:,None]*factor.solve(u))
    zvx=zvh[:,:-1];zvr=zvh[:,-1]-zvx@beta
    pdiag=diagonal_zvz-np.sum(zvx*np.linalg.solve(information,zvx.T).T,axis=1)
    gradients=np.array([pdiag[:nw].sum()-df/rss*(zvr[:nw]@zvr[:nw]),
                        pdiag[nw:].sum()-df/rss*(zvr[nw:]@zvr[nw:])])*np.exp(theta)
    value=dict(objective=objective,effect=float(beta[0]/p['target_scale']),residual_variance=rss/df,
               writer_variance_ratio=float(ratios[0]),marker_variance_ratio=float(ratios[1]))
    return value,gradients


def fit(x,y,writers,markers):
    p=prepare(x,y,writers,markers)
    def objective(theta):
        value,gradient=evaluate(p,theta)
        return value['objective'],gradient
    result=minimize(objective,np.log1p([.1,.1]),jac=True,method='L-BFGS-B',
        bounds=[(0.,math.log1p(original.MAX_RATIO))]*2,
        options=dict(maxiter=200,maxls=50,ftol=1e-10,gtol=1e-6))
    ratios=np.expm1(result.x)
    if not result.success or not np.isfinite(result.fun) or np.any(ratios>=original.MAX_RATIO*.999):
        raise ValueError('stable crossed REML convergence/variance ceiling: '+str(result.message))
    answer,_=evaluate(p,result.x)
    answer.update(converged=True,iterations=int(result.nit),objective_evaluations=int(result.nfev),
        observations=p['n'],writers=p['writer_levels'],markers=p['marker_levels'],kept_columns=p['kept_columns'],
        estimator='crossed random-intercept Gaussian REML, same objective; stable residual and analytic derivative')
    return answer
