"""Meeting-level model components for the BG target-role and speech cards.

DESIGN CHECK: LESSONS 3–5. An additive role model should leave zero excess
under a planted additive null. Lack of exposure, both joining conditions or
model rank leaves the contrast undefined. Resampling always retains a meeting.
"""
from math import isfinite

import numpy as np


def speaking_share(target, floors, start, end, denominator):
    seconds={speaker:floor.seconds(start,end) for speaker,floor in floors.items()}
    if denominator=="voiced":
        total=sum(seconds.values())
    elif denominator=="elapsed":
        total=end-start
    else:
        raise ValueError("Choose the frozen speaking-share definition")
    return seconds[target]/total if total>0 else None


def talk_crossproducts(rows):
    """Use the unjoined-minus-joined direction. All times are observed on the same clock."""
    x=[];y=[]
    for row in rows:
        if row["before"] is None or row["after"] is None:
            continue
        x.append([1.,float(not row["joined"]),float(row["phase"]),float(row["before"])])
        y.append(float(row["after"]))
    if not x:
        return np.zeros((4,4)),np.zeros(4),0
    x=np.asarray(x);y=np.asarray(y)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Nonfinite meeting observation")
    return x.T@x,x.T@y,len(y)


def talk_fit(blocks, weights):
    """Return the adjusted change in percentage points using whole-meeting counts."""
    counts=np.asarray(weights)
    if len(blocks)!=len(counts) or np.any(counts<0) or np.any(counts!=np.floor(counts)):
        raise ValueError("Invalid meeting multiplicities")
    gram=np.zeros((4,4));rhs=np.zeros(4)
    for (cross,product,_),weight in zip(blocks,counts):
        gram+=weight*cross;rhs+=weight*product
    if np.linalg.matrix_rank(gram)!=4:
        return None
    return 100.*float(np.linalg.solve(gram,rhs)[1])


def role_model(exposure, observed, design):
    """Fit the additive Poisson exposure model and return expected event counts.

    The caller supplies additive target and laugher roles and the turn-position
    and concurrent-laughter controls. The response may contain fractional credit.
    """
    from scipy.optimize import minimize
    t=np.asarray(exposure,dtype=float); y=np.asarray(observed,dtype=float); x=np.asarray(design,dtype=float)
    if t.ndim!=1 or y.shape!=t.shape or x.ndim!=2 or x.shape[0]!=len(t):
        raise ValueError("Role-model arrays do not align")
    if (not np.isfinite(x).all() or not np.isfinite(t).all() or not np.isfinite(y).all()
            or np.any(t<=0) or np.any(y<0)):
        raise ValueError("Invalid counts or exposure")
    if y.sum()==0 or np.linalg.matrix_rank(x)!=x.shape[1]:
        return None
    def objective(beta):
        linear=x@beta
        with np.errstate(over="ignore"):
            mu=t*np.exp(linear)
        return float(np.sum(mu-y*linear)),x.T@(mu-y)
    fit=minimize(objective,np.zeros(x.shape[1]),jac=True,method="BFGS",options={"gtol":1e-8,"maxiter":250})
    if not np.isfinite(fit.x).all() or np.max(np.abs(objective(fit.x)[1]))>1e-6*max(1.,float(y.sum())):
        return None
    mu=t*np.exp(x@fit.x)
    return mu if np.isfinite(mu).all() else None


def role_direction(primary, latest, fractional):
    """The BG sign check only compares defined excess rates, with exact zero neutral."""
    if any(value is None or not isfinite(value) for value in (primary,latest,fractional)):
        return "undefined"
    if primary*latest<0 or primary*fractional<0:
        return "sign reversal; no verdict"
    return "descriptive"
