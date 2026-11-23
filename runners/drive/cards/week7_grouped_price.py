"""Grouped Portuguese price responses, with both predeclared fits and whole-person draws."""
import numpy as np
from scipy.special import ndtr

CUTS=np.arange(.5,7.,1.)


def tail_odds(counts, exclude_zero):
    """Fit priced bins conditional on their included interval, independently by histogram."""
    counts=np.asarray(counts,float)
    included=counts[:,1:] if exclude_zero else counts
    total=included.sum(1)
    weights=included/np.maximum(total[:,None],1)
    centres=np.arange(1 if exclude_zero else 0,7)
    mean=weights@centres
    log_sd=.5*np.log(np.maximum(.1,weights@(centres**2)-mean**2)+1/12)
    def probabilities(mu,ls):
        cdf=ndtr((CUTS[None,:]-mu[:,None])/np.exp(ls[:,None]))
        bins=np.diff(cdf,axis=1) if exclude_zero else np.diff(cdf,axis=1,prepend=0.)
        return bins,cdf[:,-1]
    def objective(mu,ls):
        bins,_=probabilities(mu,ls)
        return (weights*np.log(np.maximum(bins,1e-300))).sum(1)-np.log(np.maximum(bins.sum(1),1e-300))
    h=.0001
    for _ in range(90):
        f=objective(mean,log_sd)
        mp,mm=objective(mean+h,log_sd),objective(mean-h,log_sd)
        sp,sm=objective(mean,log_sd+h),objective(mean,log_sd-h)
        gm,gs=(mp-mm)/(2*h),(sp-sm)/(2*h)
        hmm,hss=(mp+mm-2*f)/h**2,(sp+sm-2*f)/h**2
        hms=(objective(mean+h,log_sd+h)-objective(mean+h,log_sd-h)
             -objective(mean-h,log_sd+h)+objective(mean-h,log_sd-h))/(4*h*h)
        det=hmm*hss-hms*hms
        good=(hmm<0)&(det>1e-12)
        denom=np.where(good,det,1.)
        dm=np.clip(np.where(good,(hms*gs-hss*gm)/denom,gm),-2,2)
        ds=np.clip(np.where(good,(hms*gm-hmm*gs)/denom,gs),-.5,.5)
        step=np.ones_like(mean)
        for _ in range(15):
            ok=objective(mean+step*dm,log_sd+step*ds)>=f-1e-14
            if np.all(ok):break
            step[~ok]*=.5
        mean+=step*dm
        log_sd+=step*ds
        if np.max(np.maximum(abs(step*dm),abs(step*ds)))<1e-7:break
    # Open-ended or numerically unidentified maxima have no finite predicted upper tail.
    bins,upper=probabilities(mean,log_sd)
    gm=(objective(mean+h,log_sd)-objective(mean-h,log_sd))/(2*h)
    gs=(objective(mean,log_sd+h)-objective(mean,log_sd-h))/(2*h)
    valid=(total>0)&((included>0).sum(1)>=2)&good&(abs(gm)<1e-5)&(abs(gs)<1e-5)&(bins.sum(1)>1e-12)
    with np.errstate(divide='ignore',invalid='ignore'):
        odds=ndtr((mean-CUTS[-1])/np.exp(log_sd))/bins.sum(1)
    return np.where(valid,odds,np.nan)


def samples(counts,fit_tail=tail_odds):
    """Last axis has seven prices followed by refusal. Missing entries are already excluded."""
    total=counts.sum(-1)
    with np.errstate(invalid='ignore',divide='ignore'):
        share=counts/total[:,:,None]
    results=[share[:,:,7],share[:,:,6]-np.minimum(share[:,:,7],share[:,:,5])]
    shape=total.shape
    for secondary in (False,True):
        odds=fit_tail(counts[:,:,:7].reshape(-1,7),secondary).reshape(shape)
        results.append(share[:,:,7]-share[:,:,int(secondary):7].sum(-1)*odds)
    return np.stack(results,axis=-1),share[:,:,0]


def interval(a):
    a=np.asarray(a)
    limits=np.quantile(a[1:],[.025,.975]).tolist() if np.isfinite(a[1:]).all() else [None,None]
    return dict(point=float(a[0]) if np.isfinite(a[0]) else None,interval=limits,
                finite_draws=int(np.isfinite(a[1:]).sum()))


def run(answers, draws=2000, progress=None, fit_tail=tail_odds):
    a=np.asarray(answers,float)
    if a.ndim!=2 or a.shape[1]!=20 or not np.isin(a[np.isfinite(a)],np.arange(1,9)).all():
        raise ValueError('Unexpected price item codes')
    a=a[np.isfinite(a).any(axis=1)]
    if not len(a):raise ValueError('No answered price items')
    people=len(a)
    indicator=(a[:,:,None]==np.arange(1,9)).reshape(people,-1).astype(float)
    rng=np.random.default_rng(2026112207)
    outputs=[];zeros=[]
    for start in range(0,draws+1,24):
        count=min(24,draws+1-start)
        weights=rng.multinomial(people,np.full(people,1/people),size=count)
        if start==0:weights[0]=1
        curves,zero=samples((weights@indicator).reshape(count,20,8),fit_tail)
        outputs.extend(curves);zeros.extend(zero)
        if progress:progress(start+count-1)
    quantities=('refusal','dip','excess_primary','excess_secondary')
    output=np.array(outputs)
    pooled={key:interval(output[:,:,j].mean(1)) for j,key in enumerate(quantities)}
    item_results=[dict(item=i+1,zero=interval(np.array(zeros)[:,i]),answered=int(np.isfinite(a[:,i]).sum()),
                      **{key:interval(output[:,i,j]) for j,key in enumerate(quantities)}) for i in range(20)]
    odd=a[:,::2];even=a[:,1::2]
    n_odd=np.isfinite(odd).sum(1); n_even=(even<8).sum(1)
    keep=(n_odd>0)&(n_even>0)
    x=(odd[keep]==8).sum(1)/n_odd[keep]
    y=np.where(even[keep]<8,even[keep]-1,0).sum(1)/n_even[keep]
    corr=float(np.corrcoef(x,y)[0,1]) if len(x)>1 and np.std(x)>0 and np.std(y)>0 else None
    complete=a[np.isfinite(a).all(1)]==8
    variance=None
    if len(complete):
        prob=complete.mean(0);denom=(prob*(1-prob)).sum()
        if denom:variance=float(complete.sum(1).var()/denom)
    def side(reading):
        lo,hi=pooled[reading]['interval']
        return 0 if lo is None else (1 if lo>0 else -1 if hi<0 else 0)
    sign=side('excess_primary')
    return dict(draws=draws,people=people,items=item_results,pooled=pooled,
         excess_reading={1:'positive',-1:'negative',0:'undecided'}[sign if sign==side('excess_secondary') else 0],
         complete_people=len(complete),refusal_variance_ratio=variance,odd_even_people=len(x),odd_even_corr=corr)
