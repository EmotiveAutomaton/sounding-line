"""Same grouped normal likelihood in natural parameters, including its exponential limit."""
import numpy as np
from scipy.special import log_ndtr, logsumexp
from . import week7_grouped_price as first


def log_bins(slope, precision, secondary):
    # For t = log10(price) - top cut, log density has form a*t - b*t*t/2 + constant.
    # At b=0 the conditional *priced* distribution may exist without any finite normal.
    a,b=np.broadcast_arrays(np.atleast_1d(slope),np.atleast_1d(precision))
    exp_limit=b==0
    spread=np.sqrt(np.where(b>0,b,1.))
    z=(first.CUTS-first.CUTS[-1])*spread[:,None]-a[:,None]/spread[:,None]
    left,right=z[:,:-1],z[:,1:]
    upper=np.where(left>=0,log_ndtr(-left),log_ndtr(right))
    lower=np.where(left>=0,log_ndtr(-right),log_ndtr(left))
    with np.errstate(invalid='ignore',divide='ignore'):
        finite=upper+np.log(-np.expm1(np.minimum(lower-upper,0)))
        if not secondary:finite=np.column_stack((log_ndtr(z[:,0]),finite))
        norm=logsumexp(finite,axis=1)
        ratio=log_ndtr(-z[:,-1])-norm
        logp=finite-norm[:,None]
    if exp_limit.any():
        aa=a[exp_limit,None]
        if secondary:
            logits=aa*np.arange(6)
            logp[exp_limit]=logits-logsumexp(logits,axis=1,keepdims=True)
        else:
            with np.errstate(invalid='ignore',divide='ignore'):
                logp[exp_limit]=np.column_stack((-6*aa,aa*np.arange(-5,1)+np.log(-np.expm1(-aa))))
        ratio[exp_limit]=np.nan
    logp[(b<0)|(~np.isfinite(logp).all(1))]=-1e50
    return logp,ratio


def fit_tail(counts,secondary,*,force_check=False):
    odds=np.full(len(counts),np.nan) if force_check else first.tail_odds(counts,secondary)
    pos=~np.isfinite(odds)
    if not pos.any():return odds
    observed=counts[pos,1:] if secondary else counts[pos]
    freq=observed/np.maximum(observed.sum(1,keepdims=True),1)
    # Search across mode locations and both rising and falling price profiles.
    grid=[(a,b) for b in (0.,.03,.12,.4,1.2,4.) for a in
          np.unique(np.r_[np.arange(-7.,2.)*b,[-2.,-.5,0.,.1,.3,.6,1.,2.,4.]])]
    ga,gb=np.asarray(grid).T
    ll=freq@log_bins(ga,gb,secondary)[0].T
    best=np.argmax(ll,axis=1);a,b=ga[best].copy(),gb[best].copy()
    score=ll[np.arange(len(best)),best]
    def ll_at(aa,bb):
        return (freq*log_bins(aa,bb,secondary)[0]).sum(1)
    # A changing mesh operates on each histogram independently. Always compare explicitly
    # to the boundary, which cannot supply a normalized, untruncated upper-tail estimate.
    def maximize(a,b,score,boundary):
        da=np.full(len(a),.4);db=np.full(len(b),.13)
        directions=((-1,0),(1,0)) if boundary else ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))
        for _ in range(190):
            bestscore=score.copy();aa=a.copy();bb=b.copy()
            for x,y in directions:
                new_a=a+x*da;new_b=np.maximum(0,b+y*db)
                trial=ll_at(new_a,new_b)
                better=trial>bestscore+1e-14
                aa[better]=new_a[better];bb[better]=new_b[better];bestscore[better]=trial[better]
            moved=bestscore>score
            da[~moved]*=.5;db[~moved]*=.5
            a,b,score=aa,bb,bestscore
            if da.max()<2e-6:break
        return a,b,score
    limited=ll[:,gb==0]
    edge_a=ga[gb==0][np.argmax(limited,axis=1)]
    _,_,edge=maximize(edge_a,np.zeros(len(a)),limited.max(1),True)
    a,b,score=maximize(a,b,score,False)
    # Refine correlated slopes and precisions together and verify an interior maximum.
    for _ in range(10):
        h=np.maximum(1e-6,np.abs(a)*1e-5)
        k=np.maximum(1e-7,np.minimum(b*.1,1e-5))
        left,right=ll_at(a-h,b),ll_at(a+h,b)
        down,up=ll_at(a,b-k),ll_at(a,b+k)
        g=(right-left)/(2*h);j=(up-down)/(2*k)
        aa=(right+left-2*score)/h**2
        bb=(up+down-2*score)/k**2
        ab=(ll_at(a+h,b+k)-ll_at(a+h,b-k)-ll_at(a-h,b+k)+ll_at(a-h,b-k))/(4*h*k)
        det=aa*bb-ab*ab
        clean=(b>1e-6)&(det>1e-10)&(aa<0)&(bb<0)
        safe=np.where(clean,det,1.)
        da=np.where(clean,(ab*j-bb*g)/safe,0.);db=np.where(clean,(ab*g-aa*j)/safe,0.)
        scale=np.ones(len(a))
        for _ in range(8):
            trial=ll_at(a+scale*da,b+scale*db)
            bad=(trial<score-5e-14)|(b+scale*db<=0)
            if not bad.any():break
            scale[bad]*=.5
        accept=(trial>=score-5e-14)&(b+scale*db>0)&clean
        a[accept]+=scale[accept]*da[accept];b[accept]+=scale[accept]*db[accept]
        score=ll_at(a,b)
        if not (clean&((abs(g)>1e-6)|(abs(j)>1e-6))).any():break
    with np.errstate(over='ignore',invalid='ignore'):
        recovered=np.exp(log_bins(a,b,secondary)[1])
    ok=((observed>0).sum(1)>=2)&clean&(abs(g)<1e-4)&(abs(j)<1e-4)&(score>edge+1e-8)&np.isfinite(recovered)
    odds[pos]=np.where(ok,recovered,np.nan)
    return odds
