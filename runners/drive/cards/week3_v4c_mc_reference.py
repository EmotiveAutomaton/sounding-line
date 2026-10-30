"""V4.c separately fitted no-taste generator and whole R-both split statistic.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-30.
NULL retains fitted writer intercepts, causal habit and complete fixed menus;
ALTERNATIVE adds taste only in the original outer constructed worlds. Every
synthetic history is rebuilt after generation, and every split direction,
scale, K, decay and variance is refitted. Missing support/nonconvergence fail
closed. Plug-in nuisance estimation is not an exact finite-sample null test:
the original complete outer calibration remains mandatory. No old label changes.
"""
import copy
import heapq
from collections import defaultdict
import numpy as np
from scipy.special import expit, logit
from . import menus_v4_saved_diagnostics as source
from . import menus_v4_split_stats as split
from .menus_v4_stats import variance_reader, predict
from runners.drive.statistics import half_brier

DECAYS=(.5,.8,.95)


def validate(rows,base):
    if not rows or len({r['key'] for r in rows})!=len(rows):
        raise ValueError('Nonempty unique decision keys required')
    for r in rows:
        p=np.asarray(base[r['key']],float)
        if p.shape!=(4,) or not np.isfinite(p).all() or not np.all(p>0) or not np.isclose(p.sum(),1,rtol=0,atol=1e-12):
            raise ValueError('Strict four-action baseline required')
        if not np.isfinite([r['open_at'],r['resolved_at']]).all() or r['resolved_at']<r['open_at']:
            raise ValueError('Invalid decision chronology')


def fit_null(rows,saved,base,maxiter=100):
    """Select no-taste decay on original train/cal, then fit all observed rows.

    Fixed writer conditional modes for an intercept and causal acceptance-habit
    coefficient are retained in simulation. The final nuisance fit uses all
    rows, including writers absent from original training. It is explicitly a
    plug-in conditional parametric bootstrap, not independent confirmation.
    """
    validate(rows,base)
    keys=np.asarray([r['key'] for r in rows]);writers=np.asarray([r['writer'] for r in rows])
    y=np.asarray([source.ACTIONS.index(r['handling']) for r in rows]);accept=(y==0).astype(float)
    population=np.asarray([base[k] for k in keys])
    train=np.isin(keys,saved['train_keys']);cal=np.isin(keys,saved['calibration_keys'])
    if not train.any() or not cal.any() or np.any(train&cal):raise ValueError('Null train/calibration support invalid')
    candidates={};designs={}
    for decay in DECAYS:
        x=np.c_[np.ones(len(rows)),source.kernel(rows,base,decay)]
        fit=variance_reader(x[train],accept[train],population[train,0],writers[train],maxiter)
        loss=float(half_brier(predict(fit,x[cal],population[cal],writers[cal]),y[cal]).mean())
        candidates[str(decay)]=dict(fit=fit,calibration_loss=loss);designs[decay]=x
    decay=min(DECAYS,key=lambda d:(candidates[str(d)]['calibration_loss'],d))
    fit=variance_reader(designs[decay],accept,population[:,0],writers,maxiter)
    if set(fit['coefficients'])!=set(writers):raise ValueError('Missing fitted writer offset')
    return dict(decay=decay,fit=fit,selection=candidates,writer_count=len(set(writers)),
                scope='Fitted conditional no-taste law; all observed nuisance rows, fixed writer modes; no taste coordinates')


def generate(rows,base,model,seed):
    validate(rows,base)
    decay=model['decay']
    if decay not in DECAYS:raise ValueError('Undeclared habit decay')
    coefficients=model['fit']['coefficients'];groups=defaultdict(list)
    for r in rows:groups[r['writer']].append(base[r['key']])
    if set(coefficients)!=set(groups):raise ValueError('Missing or foreign writer coefficient')
    if any(np.asarray(v).shape!=(2,) or not np.isfinite(v).all() for v in coefficients.values()):
        raise ValueError('Finite intercept and habit coefficient required')
    centers={w:np.asarray(v).mean(0) for w,v in groups.items()}
    current={w:v.copy() for w,v in centers.items()};last={};pending=[]
    generated=copy.deepcopy(rows);rng=np.random.default_rng(seed);audit={}
    for r in sorted(generated,key=lambda r:(r['open_at'],r['key'])):
        while pending and pending[0][0]<=r['open_at']:
            resolved,key,w,opened,outcome=heapq.heappop(pending)
            current[w]=decay*current[w]+(1-decay)*np.eye(4)[outcome]
            if w not in last or (opened,key)>last[w][:2]:last[w]=(opened,key,outcome)
        w=r['writer'];intercept,habit=coefficients[w];q=np.asarray(base[r['key']],float).copy()
        h=float(current[w][0]-centers[w][0]);accept=float(expit(logit(q[0])+intercept+habit*h))
        q[1:]*=(1-accept)/(1-q[0]);q[0]=accept
        if not np.isfinite(q).all() or np.any(q<0) or not np.isclose(q.sum(),1,atol=1e-12,rtol=0):
            raise ValueError('Invalid generated probability law')
        outcome=int(rng.choice(4,p=q));r['handling']=source.ACTIONS[outcome]
        r['previous_handling']=source.ACTIONS[last[w][2]] if w in last else None
        audit[r['key']]=dict(probabilities=q.tolist(),habit=h,outcome=outcome)
        heapq.heappush(pending,(r['resolved_at'],r['key'],w,r['open_at'],outcome))
    return generated,audit


def statistic(rows,sessions,saved,geometry,base,maxiter=100):
    halves=[]
    for half in (0,1):
        designs,audit,support=split.select_half(rows,sessions,saved,geometry,base,half,maxiter)
        use=support['test'];fit=variance_reader(designs['R-both'][use],support['accept'][use],
            support['population'][use,0],support['writers'][use],maxiter)
        halves.append(dict(audit=audit,fit=fit))
    value=float(np.mean([h['fit']['likelihood_ratio'] for h in halves]))
    return dict(likelihood_ratio=value,halves=halves,reader='R-both')


def reference_probability(observed,values):
    values=np.asarray(values,float)
    if values.shape!=(199,) or not np.isfinite(values).all() or not np.isfinite(observed):
        raise ValueError('Exactly 199 complete finite references required')
    return float((1+np.sum(values>=observed))/200)
