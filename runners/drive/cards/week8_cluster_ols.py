"""Within-person least squares with whole-cluster bootstrap weights."""
import numpy as np
import pandas as pd

def fit(design, outcome, people, groups, roster, weights, contrasts):
    """Fit each contrast on identical cases. A repeated group retains all its people."""
    x=np.asarray(design,dtype=float)
    y=np.asarray(outcome,dtype=float)
    people=np.asarray(people)
    groups=np.asarray(groups)
    by=pd.Index(roster)
    if not by.is_unique or weights.shape[1]!=len(by):
        raise ValueError('Resampling roster mismatch')
    good=np.isfinite(y)&np.all(np.isfinite(x),axis=1)&pd.notna(people)&pd.notna(groups)
    f=pd.DataFrame(x[good])
    f['outcome']=y[good]
    k=x.shape[1]
    data=f-f.groupby(people[good],sort=False).transform('mean')
    gram=np.zeros((len(by),k,k))
    rhs=np.zeros((len(by),k))
    codes=by.get_indexer(groups[good])
    if (codes<0).any():
        raise ValueError('Observations outside frozen group roster')
    for group,idx in pd.Series(codes).groupby(codes).indices.items():
        xx=data.iloc[idx,:k].to_numpy()
        yy=data.iloc[idx,k].to_numpy()
        gram[group]=xx.T@xx
        rhs[group]=xx.T@yy
    # With aliased controls an individual registered contrast can still be identified.
    form=np.asarray(contrasts,dtype=float)
    all_weights=np.vstack((np.ones((1,len(by))),weights))
    xx=(all_weights@gram.reshape(len(by),k*k)).reshape(-1,k,k)
    xy=all_weights@rhs
    inv=np.linalg.pinv(xx,rcond=1e-11,hermitian=True)
    projection=inv@xx
    estimates=((inv@xy[:,:,None])[:,:,0])@form.T
    identified=np.max(np.abs(form[None,:,:]@projection-form[None,:,:]),axis=2)<1e-7
    estimates[~identified]=np.nan
    contributing=np.any(gram!=0,axis=(1,2))
    support=dict(rows=int(good.sum()),people=int(pd.Series(people[good]).nunique()),
                 clusters_with_rows=int(len(set(codes))),clusters_with_variation=int(contributing.sum()))
    return estimates,support

def summary(values):
    if not np.isfinite(values[0]):
        return dict(estimate=None,interval=None,finite_draws=int(np.isfinite(values[1:]).sum()))
    valid=values[1:][np.isfinite(values[1:])]
    # A confidence interval is unavailable if any registered draw lacks the contrast.
    ci=np.quantile(valid,[.025,.975]).tolist() if len(valid)==len(values)-1 else None
    return dict(estimate=float(values[0]),interval=ci,finite_draws=len(valid))

def draws(n,seed,number=2000):
    if n<1:
        raise ValueError('Empty cluster roster')
    return np.random.default_rng(seed).multinomial(n,np.full(n,1/n),size=number)
