"""Whole-player sufficient statistics for the remaining two-day table cards.

DESIGN CHECK: targets are tested conditional on the registered controls. Zero
variance remains zero after the Gram decomposition. No rank failure redraws.
"""
import numpy as np
from .week5_ch_models import keep_columns
from . import week5_ch8_math_v2 as checked


def sufficient(groups,columns,required=1,reference=False):
    xx=[];xy=[];counts=[]
    for rows in groups:
        y=np.asarray([r[0] for r in rows],float)
        x=np.asarray([r[1] for r in rows],float).reshape(-1,len(columns))
        a,b=checked.block(y,x,reference);xx.append(a);xy.append(b);counts.append(len(y))
    if not sum(counts):raise ValueError('No eligible outcome rows')
    xx=np.asarray(xx);xy=np.asarray(xy);total=xx.sum(axis=0)
    norms=np.sqrt(np.maximum(np.diag(total),0));denom=np.outer(norms,norms)
    corr=np.divide(total,denom,out=np.zeros_like(total),where=denom>1e-20)
    eigen,vectors=np.linalg.eigh(corr)
    root=np.sqrt(np.where(eigen>1e-12,eigen,0))[:,None]*vectors.T;root[:,norms==0]=0
    nuisance=[required+j for j in keep_columns(root[:,required:],0)]
    order=nuisance+list(range(required));accepted=keep_columns(root[:,order],0)
    if any(len(nuisance)+j not in accepted for j in range(required)):
        raise ValueError('Target not identifiable conditional on registered controls')
    kept=list(range(required))+nuisance
    return dict(xx=xx[:,kept][:,:,kept],xy=xy[:,kept],kept=kept,
                columns=[columns[j] for j in kept],rows=sum(counts),players_with_rows=sum(n>0 for n in counts))


def prepare(groups,columns,required=1,reference=False):
    seen=0
    def streamed():
        nonlocal seen
        for group in groups:
            seen+=len(group)
            yield group
    try:
        stat=sufficient(streamed(),columns,required,reference)
        values=checked.coefficients(stat,reference=reference).tolist()
        return stat,dict(coefficients=values,columns=stat['columns'],rows=stat['rows'],players=stat['players_with_rows'])
    except ValueError as exc:return None,dict(unsupported=str(exc),rows=seen)


def sample(stat,weights,reference=False):
    if stat is None:return None
    try:return checked.coefficients(stat,weights,reference).tolist()
    except ValueError:return None


def summarize(point,draws,bar=None):
    if 'unsupported' in point:return dict(point,intervals=None,invalid_draws=len(draws))
    intervals=[checked.interval([None if d is None else d[j] for d in draws]) for j in range(len(point['coefficients']))]
    se=None if intervals[0] is None else float(np.std([d[0] for d in draws],ddof=1))
    return dict(point,intervals=intervals,invalid_draws=sum(d is None for d in draws),bar=bar,
                sees=None if se is None else 2.8*se,supports_at=None if se is None or bar is None else bar+2.8*se)


def ratio(numerator,denominator):return None if not denominator else float(numerator/denominator)
