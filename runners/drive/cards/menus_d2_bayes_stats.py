"""Certified Laplace/quadrature hierarchical multinomial choice calculations.

DESIGN CHECK: LESSONS 3-5 read 2026-10-18. A continuous variance prior cannot
test zero variance. The explicit spike permits a zero lower credible bound;
known zero-information data must return its prior odds. An opposed-writer plant
must move mass away from zero. Nonfinite/uncertified modes, unstable quadrature,
or posterior mass near the slab cutoff invalidate the instrument, not the idea.
Twenty null worlds reject the calibration at >=4 detections: under Binomial
(20,.05), P(X>=4)=.01590 while P(X>=3)=.07548. Passing this coarse screen is
not proof that the population false-positive rate is <=.05. The exact interval
on that rate is always reported. Planted sensitivity requires >=4/5 at tau=1.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from scipy.stats import binom, beta as beta_distribution, norm

from . import states_v2 as states


def pack(matrices, truths, writers, random_columns):
    order=sorted(range(len(matrices)),key=lambda i:(writers[i],i))
    names=sorted(set(writers)); lookup={w:i for i,w in enumerate(names)}
    x=np.concatenate([np.asarray(matrices[i],float) for i in order]);sizes=np.array([len(matrices[i]) for i in order])
    starts=np.r_[0,np.cumsum(sizes)[:-1]];ys=np.array([truths[i] for i in order],int)
    menu_writer=np.array([lookup[writers[i]] for i in order]);option_writer=np.repeat(menu_writer,sizes)
    if not len(order) or np.any(sizes<2) or np.any(ys<0) or np.any(ys>=sizes) or not np.isfinite(x).all():
        raise ValueError('invalid hierarchical choice design')
    boundaries=np.r_[0,1+np.flatnonzero(np.diff(option_writer)),len(x)]
    menu_boundaries=np.r_[0,1+np.flatnonzero(np.diff(menu_writer)),len(sizes)]
    return dict(x=x,z=x[:,random_columns],sizes=sizes,starts=starts,selected=starts+ys,
                truths=ys,writer=option_writer,names=names,boundaries=boundaries,menu_boundaries=menu_boundaries)


def probability(parameters,data,tau):
    x,z=data['x'],data['z'];q=x.shape[1];p=z.shape[1]
    values=x@parameters[:q]
    if tau>0:
        deviations=parameters[q:].reshape(len(data['names']),p)
        values=values+tau*np.einsum('ij,ij->i',z,deviations[data['writer']])
    maximum=np.maximum.reduceat(values,data['starts'])
    exp=np.exp(values-np.repeat(maximum,data['sizes']))
    totals=np.add.reduceat(exp,data['starts']);prob=exp/np.repeat(totals,data['sizes'])
    nll=float(np.sum(maximum+np.log(totals)-values[data['selected']]))
    return nll,prob


def objective(parameters,data,tau,population_sd):
    q=data['x'].shape[1];nll,prob=probability(parameters,data,tau)
    residual=prob.copy();residual[data['selected']]-=1
    beta=parameters[:q];loss=nll+.5*float(beta@beta)/population_sd**2
    gradient=data['x'].T@residual+beta/population_sd**2
    if tau>0:
        deviations=parameters[q:];loss+=.5*float(deviations@deviations)
        slope_gradient=tau*np.add.reduceat(data['z']*residual[:,None],data['boundaries'][:-1],axis=0)
        gradient=np.r_[gradient,slope_gradient.ravel()+deviations]
    return loss,gradient


def blocks(parameters,data,tau,population_sd):
    q=data['x'].shape[1];p=data['z'].shape[1];_,prob=probability(parameters,data,tau)
    a=np.eye(q)/population_sd**2;bs=[];cs=[]
    for w in range(len(data['names'])):
        lo,hi=data['boundaries'][w:w+2];ml,mh=data['menu_boundaries'][w:w+2]
        features=data['x'][lo:hi]
        if tau>0:features=np.column_stack((features,tau*data['z'][lo:hi]))
        weighted=features*prob[lo:hi,None]
        means=np.add.reduceat(weighted,data['starts'][ml:mh]-lo,axis=0)
        hessian=features.T@weighted-means.T@means
        a+=hessian[:q,:q]
        if tau>0:bs.append(hessian[q:,q:]+np.eye(p));cs.append(hessian[:q,q:])
    return a,bs,cs


def schur(a,bs,cs):
    result=a.copy();logdet=0.;solved=[]
    for b,c in zip(bs,cs):
        factor=np.linalg.cholesky(b);logdet+=2*float(np.log(np.diag(factor)).sum())
        solve=np.linalg.solve(b,c.T);result-=c@solve;solved.append(solve)
    factor=np.linalg.cholesky(result);logdet+=2*float(np.log(np.diag(factor)).sum())
    return result,solved,logdet


def laplace(data,tau,config):
    q=data['x'].shape[1];p=data['z'].shape[1];w=len(data['names'])
    size=q+(w*p if tau>0 else 0);initial=np.zeros(size)
    result=minimize(objective,initial,args=(data,tau,config['population_sd']),jac=True,
        method='L-BFGS-B',options=dict(maxiter=config['maxiter'],ftol=1e-13,gtol=1e-8))
    parameters=result.x;loss,gradient=objective(parameters,data,tau,config['population_sd'])
    # Same strictly convex objective; Newton polishing has its own fixed cap,
    # gradient certificate and monotone line search, never relaxed convergence.
    steps=0
    while np.max(np.abs(gradient))>config['gradient_tolerance'] and steps<20:
        a,bs,cs=blocks(parameters,data,tau,config['population_sd']);s,solved,_=schur(a,bs,cs)
        rhs=gradient[:q].copy();other=[]
        for j,(b,c) in enumerate(zip(bs,cs)):
            v=np.linalg.solve(b,gradient[q+j*p:q+(j+1)*p]);rhs-=c@v;other.append(v)
        first=np.linalg.solve(s,rhs)
        direction=np.r_[first,*[v-bfirst@first for v,bfirst in zip(other,solved)]] if tau>0 else first
        fraction=1.;accepted=False
        for _ in range(30):
            candidate=parameters-fraction*direction
            value,g=objective(candidate,data,tau,config['population_sd'])
            if value<=loss-1e-4*fraction*float(gradient@direction):
                parameters=candidate;loss=value;gradient=g;accepted=True;break
            fraction*=.5
        if not accepted:break
        steps+=1
    gap=float(np.max(np.abs(gradient)))
    if not np.isfinite(loss) or gap>config['gradient_tolerance']:
        raise ValueError(f'uncertified hierarchical mode: {result.message}; gradient={gap}')
    a,bs,cs=blocks(parameters,data,tau,config['population_sd']);_,_,logdet=schur(a,bs,cs)
    # Noncentered deviations have unit Gaussian priors; all 2*pi terms cancel.
    evidence=-loss-q*math.log(config['population_sd'])-.5*logdet
    return dict(tau=float(tau),log_evidence=float(evidence),mode=parameters.tolist(),
                loss=loss,logdet=logdet,gradient_max=gap,lbfgs_iterations=int(result.nit),newton_steps=steps)


def quadrature(config,nodes):
    x,w=np.polynomial.legendre.leggauss(nodes);upper=config['slab_upper']
    tau=(x+1)*upper/2
    weights=w*upper/2*2*norm.pdf(tau,scale=config['slab_sd'])/(2*norm.cdf(upper/config['slab_sd'])-1)
    return tau,weights


def posterior(evidence,config,nodes):
    tau,weights=quadrature(config,nodes)
    if len(evidence)!=nodes+1 or evidence[0]['tau']!=0 or not np.allclose([v['tau'] for v in evidence[1:]],tau,rtol=0,atol=0):
        raise ValueError('quadrature grid changed')
    grid=np.r_[0,tau];prior=np.r_[config['spike_prior'],(1-config['spike_prior'])*weights]
    logs=np.array([v['log_evidence'] for v in evidence])+np.log(prior)
    mass=np.exp(logs-logsumexp(logs));cumulative=np.cumsum(mass)
    low,high=[float(grid[min(np.searchsorted(cumulative,a),len(grid)-1)]) for a in (.025,.975)]
    point=float(mass@grid);sd=math.sqrt(max(0,float(mass@grid**2)-point**2))
    return dict(effect=point,ci95=[low,high],posterior_sd=sd,standard_error=sd,
        p_approx=math.erfc(abs(point/sd)/math.sqrt(2)) if sd>0 else None,
        p_approx_scope='Descriptive Gaussian approximation to posterior spread, not a frequentist significance probability.',
        state=states.contrast_state(point,low,high),spike_posterior=float(mass[0]),
        variance_mean=float(mass@grid**2),tau=grid.tolist(),mass=mass.tolist(),
        tail_mass=float(mass[grid>=config['tail_start']].sum()))


def grid_summary(coarse,fine,config):
    a=posterior(coarse,config,config['quadrature_coarse']);b=posterior(fine,config,config['quadrature_fine'])
    mean_gap=abs(a['effect']-b['effect']);spike_gap=abs(a['spike_posterior']-b['spike_posterior'])
    stable=(mean_gap<=max(config['mean_absolute_tolerance'],config['mean_relative_tolerance']*b['effect'])
            and spike_gap<=config['spike_tolerance'] and a['state']==b['state'])
    tail_ok=b['tail_mass']<=config['maximum_tail_mass']
    return dict(primary=b,coarse=a,valid=bool(stable and tail_ok),
                stability=dict(mean_gap=mean_gap,spike_gap=spike_gap,stable=bool(stable),tail_ok=bool(tail_ok)))


def calibration(null,plant,config):
    n=len(null);detected=sum(r['primary']['ci95'][0]>0 for r in null)
    # Smallest count whose exact upper tail is <=5%; for n=20 this is four.
    reject_at=next((k for k in range(n+1) if binom.sf(k-1,n,.05)<=.05),n+1)
    interval=[0. if detected==0 else float(beta_distribution.ppf(.025,detected,n-detected+1)),
              1. if detected==n else float(beta_distribution.ppf(.975,detected+1,n-detected))]
    power=sum(r['primary']['ci95'][0]>0 for r in plant)
    valid=all(r['valid'] for r in null+plant) and detected<reject_at and power>=math.ceil(.8*len(plant))
    return dict(valid=bool(valid),null_detections=detected,null_worlds=n,null_reject_at=reject_at,
        null_band_tail_probability=float(binom.sf(reject_at-1,n,.05)),null_rate_ci95=interval,
        planted_detections=power,planted_worlds=len(plant),planted_required=math.ceil(.8*len(plant)),
        numerical_valid=all(r['valid'] for r in null+plant),
        scope='A coarse fixed diagnostic, not a proof of nominal size; simulated choices conditional on the observed designs and fitted zero-spread population mode.')
