"""T4.h1 fused evaluation of the immutable objective and its gradient.

DESIGN CHECK: LESSONS 3-5 reread in the November 2 build. Under null and
alternative, pointwise objective/gradient must match the retained implementation.
No fastmath, parallel sum, changed estimator, starts or certificate. A cost hold
does not authorize human scoring; the entire original bank remains mandatory.
"""
from types import FunctionType
import numba
import llvmlite
import numpy as np
import scipy
from . import week4_t4_variable as variable
from . import week4_t4_choice as base


@numba.njit(cache=False,fastmath=False)
def kernel(theta,x,z,w,y,mask,individual):
    n=x.shape[0]; options=x.shape[1]; writers=int(w.max())+1
    gradient=np.zeros(len(theta)); dq=np.zeros(writers); qmean=0.
    if individual:
        for j in range(writers):qmean+=theta[7+writers+j]/writers
    total=0.
    for i in range(n):
        writer=w[i]; scale=np.exp(-(theta[7+writers+writer]-qmean)) if individual else 1.
        state=z[i,0]*theta[5]+z[i,1]*theta[6]
        dismissal=theta[7+writer]; largest=dismissal
        utility=np.empty(options); products=np.empty(options)
        for j in range(options):
            products[j]=0.
            if mask[i,j]:
                for k in range(5):products[j]+=x[i,j,k]*theta[k]
                utility[j]=products[j]*scale+state
                if utility[j]>largest:largest=utility[j]
            else:utility[j]=-np.inf
        denominator=np.exp(dismissal-largest)
        for j in range(options):
            if mask[i,j]:denominator+=np.exp(utility[j]-largest)
        selected=dismissal if y[i]==options else utility[y[i]]
        total+=(largest-selected+np.log(denominator))/n
        state_residual=0.
        for j in range(options):
            if mask[i,j]:
                residual=(np.exp(utility[j]-largest)/denominator-(1. if y[i]==j else 0.))/n
                state_residual+=residual
                for k in range(5):gradient[k]+=residual*x[i,j,k]*scale
                if individual:dq[writer]-=residual*products[j]*scale
        gradient[5]+=state_residual*z[i,0];gradient[6]+=state_residual*z[i,1]
        gradient[7+writer]+=(np.exp(dismissal-largest)/denominator-(1. if y[i]==options else 0.))/n
    if individual:
        avg=0.
        for j in range(writers):avg+=dq[j]/writers
        for j in range(writers):gradient[7+writers+j]=dq[j]-avg
    for j in range(len(theta)):
        total+=base.RIDGE*.5*theta[j]*theta[j]
        gradient[j]+=base.RIDGE*theta[j]
    return total,gradient


def objective(theta,data,individual):
    return kernel(theta,data['x'],data['z'],data['w'],data['y'],variable.mask(data),individual)


_fit=FunctionType(base.fit.__code__,dict(base.__dict__,objective=objective,checked=variable.checked),'fit')


def fit(data,individual):
    result=_fit(data,individual);theta=np.asarray(result['theta']);writers=variable.checked(data)
    value,gradient=variable.objective(theta,data,individual)
    bounds=[(None,None)]*(7+writers)+([(-3.,3.)]*writers if individual else [])
    gap=base.projected_gradient(theta,gradient,bounds)
    if abs(value-result['objective'])>1e-9 or gap>1e-5:
        raise ValueError('Selected fit failed original-implementation certificate')
    return dict(result,reference_objective=value,reference_projected_gradient=gap)


world=FunctionType(variable.world.__code__,dict(variable.__dict__,fit=fit),'world')


def known_answers():
    checks=variable.known_answers();rng=np.random.default_rng(20261102)
    for zero in (False,True):
        for extreme in (1.,1000.):
            mask=np.arange(5)[None,:]<np.array([1,2,5,3,2,1,4,5,3])[:,None]
            x=rng.normal(size=(9,5,5))*extreme; x[~mask]=0
            if zero:x[:]=0
            data=dict(x=x,z=rng.normal(size=(9,2)),w=np.array([0,0,0,0,1,1,2,2,2]),
                y=np.array([0,1,5,2,1,5,3,4,0]),mask=mask)
            variable.checked(data)
            for individual in (False,True):
                theta=rng.normal(size=7+3*(2 if individual else 1))
                if individual:theta[-3:]=[-3.,0.,3.]
                expected,eg=variable.objective(theta,data,individual);actual,ag=objective(theta,data,individual)
                if abs(expected-actual)>1e-9 or not np.allclose(eg,ag,atol=1e-10,rtol=0):
                    raise ValueError('Compiled objective or gradient differs')
    data=dict(x=rng.normal(size=(60,3,5)),z=rng.normal(size=(60,2)),w=np.arange(60)%3,y=np.arange(60)%4)
    for individual in (False,True):
        old=variable.fit(data,individual);new=fit(data,individual)
        if abs(old['objective']-new['objective'])>1e-8:raise ValueError('Independent fitted objectives differ')
        for result in (old,new):
            assert any(a['certified'] for a in result['attempts'])
    return dict(checks,fused_objective_agrees=True,full_gradient_agrees=True,independent_fitted_objectives_agree=True)


def configuration(mode):
    versions=dict(numba=numba.__version__,llvmlite=llvmlite.__version__,numpy=np.__version__,scipy=scipy.__version__)
    expected=dict(numba='0.66.0',llvmlite='0.48.0',numpy='2.4.6',scipy='1.17.1')
    if versions!=expected:raise ValueError('Compiled runtime versions changed')
    return dict(base.configuration(mode),card='T4.h1-kernel',runtime_versions=versions)


run=FunctionType(base.run.__code__,dict(base.__dict__,configuration=configuration,known_answers=known_answers,world=world),'run',base.run.__defaults__)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
