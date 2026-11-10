"""Texture-only optimizer continuation; unchanged primary solver preserved."""
from types import FunctionType
from scipy.optimize import minimize
from . import week4_t4_kernel_h1 as original


def continued_minimize(*args,**kwargs):
    options=dict(kwargs['options'])
    if options.get('maxiter')!=1500:raise ValueError('Original comparator iteration policy changed')
    options['maxiter']=6000
    return minimize(*args,**dict(kwargs,options=options))


_fit=FunctionType(original._fit.__code__,dict(original._fit.__globals__,minimize=continued_minimize),
                  original._fit.__name__,original._fit.__defaults__,original._fit.__closure__)
fit=FunctionType(original.fit.__code__,dict(original.fit.__globals__,_fit=_fit),
                 original.fit.__name__,original.fit.__defaults__,original.fit.__closure__)
