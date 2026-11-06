"""WD1.h3 exact zero-column compression of the frozen h2 calibration.

DESIGN CHECK: LESSONS3-5 and CONTROLS1-7 read2026-11-04.
NULL and ALTERNATIVE worlds, gates and full reference banks unchanged.
An all-zero ridge coefficient has exact optimum0 under either. Remove only
columns identically zero in training; restore zeros and certify the full
original objective. Refuse nonzero omissions, changed model or failed gradient.
"""
import types
import numpy as np
from . import week3_sdt_newton as original
from . import week4_wd1_calibration_h2 as base


def logistic_fit(x,y,penalty=1.):
    x=np.asarray(x,float);y=np.asarray(y,float)
    if x.ndim!=2 or x.shape[1]<1:raise ValueError('Invalid original design')
    keep=np.any(x!=0,axis=0);keep[0]=True
    def solve(hessian,gradient):
        step=np.zeros(x.shape[1])
        step[keep]=np.linalg.solve(hessian[np.ix_(keep,keep)],gradient[keep])
        return step
    # Preserve original full-shape objective/gradient/Hessian arithmetic and
    # line search. Compress only the independent block-diagonal Newton solve.
    linear=types.SimpleNamespace(**{**vars(np.linalg),'solve':solve})
    numerical=types.SimpleNamespace(**{**vars(np),'linalg':linear})
    fitted=clone(original.logistic_fit_with_certificate,np=numerical)
    beta,_=fitted(x,y,penalty)
    regularizer=np.full(x.shape[1],float(penalty));regularizer[0]=0.
    gradient=x.T@(original.expit(x@beta)-y)+regularizer*beta
    if not np.isfinite(beta).all() or np.max(np.abs(gradient))>1e-3:
        raise ValueError('Original full gradient certificate failed')
    return beta


def clone(function,**replacements):
    scope=dict(function.__globals__);scope.update(replacements)
    return types.FunctionType(function.__code__,scope,function.__name__,function.__defaults__,function.__closure__)


reference_scores=clone(original.reference_scores,logistic_fit=logistic_fit)
evaluate=clone(original.evaluate,reference_scores=reference_scores)
proxy=types.SimpleNamespace(**{**vars(original),'evaluate':evaluate})
evaluate_world=clone(base.evaluate_world,old=proxy)
calculate=clone(base.calculate,evaluate_world=evaluate_world,__file__=__file__)
configuration=base.configuration
execute=clone(base.execute,calculate=calculate)
verify=clone(base.verify,calculate=calculate)
