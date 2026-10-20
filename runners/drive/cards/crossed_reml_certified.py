"""Continue an abnormal REML line search to the original gradient tolerance.

DESIGN CHECK: LESSONS 3-5, especially certified solutions and unchanged numeric
accuracy. Successful old fits are byte-identical. Only ABNORMAL line-search
termination permits continuation at its last iterate, never another start.
Positive/reversed/exact-null answers stay unchanged; undefined information,
variance ceilings, iteration exhaustion and indefinite curvature still refuse.
Both original gradient and function tolerances certify any recovered solution.
"""
import math
import numpy as np
from scipy.optimize import minimize
from . import crossed_reml_stable as old

GTOL=1e-6
FTOL=1e-10
MAXITER=200


def projected_gradient(x,g,upper):
    return np.where(((x<=0)&(g>0))|((x>=upper)&(g<0)),0.,g)


def curvature(evaluate,x,free,upper,step):
    columns=[]
    for i in free:
        lo=x.copy();hi=x.copy();lo[i]=max(0.,x[i]-step);hi[i]=min(upper,x[i]+step)
        columns.append((evaluate(hi)[1][free]-evaluate(lo)[1][free])/(hi[i]-lo[i]))
    h=np.column_stack(columns);h=(h+h.T)/2
    if not np.isfinite(h).all() or np.linalg.eigvalsh(h).min()<=0:
        raise ValueError('uncertified crossed curvature')
    return h


def polish(evaluate,result,upper):
    if result.success or int(result.status)!=2 or not str(result.message).startswith('ABNORMAL'):
        raise ValueError('only abnormal line-search continuation is admitted')
    x=np.asarray(result.x,float).copy();initial,_=evaluate(x)
    initial_objective=initial['objective'];steps=0
    for _ in range(min(20,MAXITER-int(result.nit))):
        value,g=evaluate(x);pg=projected_gradient(x,g,upper)
        free=np.flatnonzero((x>0)|(g<0))
        if not len(free):raise ValueError('no free crossed curvature for certification')
        h=curvature(evaluate,x,free,upper,1e-4)
        curvature(evaluate,x,free,upper,5e-5)
        if np.max(np.abs(pg))<=GTOL:
            if abs(value['objective']-initial_objective)>FTOL*max(1.,abs(initial_objective),abs(value['objective'])):
                raise ValueError('continuation exceeds original function tolerance')
            return x,dict(newton_steps=steps,projected_gradient_max=float(np.max(np.abs(pg))),
                          positive_curvature_verified=True,function_tolerance=FTOL,gradient_tolerance=GTOL)
        direction=np.linalg.solve(h,g[free]);accepted=False
        for j in range(50):
            candidate=x.copy();candidate[free]=np.clip(x[free]-direction*(.5**j),0.,upper)
            proposed,gg=evaluate(candidate)
            # Function changes within the ORIGINAL tolerance allow a floating-point
            # plateau only while the projected gradient strictly improves.
            if (abs(proposed['objective']-initial_objective)<=FTOL*max(1.,abs(initial_objective),abs(proposed['objective']))
                    and np.max(np.abs(projected_gradient(candidate,gg,upper)))<np.max(np.abs(pg))):
                x=candidate;steps+=1;accepted=True;break
        if not accepted:raise ValueError('crossed continuation cannot improve certified gradient')
    raise ValueError('crossed continuation iteration limit')


def fit(x,y,writers,markers):
    try:return old.fit(x,y,writers,markers)
    except ValueError as exc:
        if not str(exc).endswith('ABNORMAL: '):raise
    p=old.prepare(x,y,writers,markers);upper=math.log1p(old.original.MAX_RATIO)
    def evaluate(theta):return old.evaluate(p,theta)
    def objective(theta):
        value,g=evaluate(theta);return value['objective'],g
    result=minimize(objective,np.log1p([.1,.1]),jac=True,method='L-BFGS-B',
        bounds=[(0.,upper)]*2,options=dict(maxiter=MAXITER,maxls=50,ftol=FTOL,gtol=GTOL))
    theta,certificate=polish(evaluate,result,upper)
    if np.any(np.expm1(theta)>=old.original.MAX_RATIO*.999):raise ValueError('crossed variance ceiling')
    answer,_=evaluate(theta)
    answer.update(converged=True,iterations=int(result.nit)+certificate['newton_steps'],
        objective_evaluations=int(result.nfev),observations=p['n'],writers=p['writer_levels'],
        markers=p['marker_levels'],kept_columns=p['kept_columns'],
        estimator='same crossed Gaussian REML; abnormal line-search continuation certified at original tolerances',
        numerical_certificate=certificate)
    return answer
