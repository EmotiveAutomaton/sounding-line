"""Pre-join acoustics and within-laugher comparisons. All event arrays stay in memory."""
from bisect import bisect_left

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from .week7_lgh1_sound_v1 import _pitch_and_fraction


def bounds(marks):
    times = sorted((float(m['start']), i, m['speaker']) for i,m in enumerate(marks))
    starts = [v[0] for v in times]
    result = [None]*len(marks)
    for onset, index, speaker in times:
        others = (v[0] for v in times[bisect_left(starts,onset):bisect_left(starts,np.nextafter(onset+1.,np.inf))]
                  if v[2] != speaker)
        first = next(others, None)
        prior = sum(v[2] != speaker for v in times[bisect_left(starts,onset-60.):bisect_left(starts,onset-3.)])
        end = min(marks[index]['end'], onset+1., first if first is not None else np.inf)
        result[index] = (onset,end,int(first is not None),prior)
    return result


def active_samples(samples,rate):
    """Count elapsed coverage once where active 40 ms frames overlap."""
    size, step = round(.04*rate), round(.01*rate)
    if len(samples) < size:
        return np.zeros(len(samples),dtype=bool)
    frames=np.lib.stride_tricks.sliding_window_view(samples,size)[::step]
    rms=np.sqrt(np.mean(frames*frames,axis=1))
    active=np.flatnonzero(rms >= max(1.e-12, .01*rms.max()))
    covered=np.zeros(len(samples)+1,dtype=int)
    np.add.at(covered,active*step,1)
    np.add.at(covered,active*step+size,-1)
    return np.cumsum(covered[:-1])>0


def prefix(samples, rate, baseline):
    """Measure only active elapsed time up to the first join."""
    valid=active_samples(samples,rate)
    if valid.sum()<round(.2*rate):
        return None
    _,fraction=_pitch_and_fraction(samples,rate)
    if fraction is None or baseline<=0:
        return None
    return fraction,float(20*np.log10(np.sqrt(np.mean(samples[valid]**2))/baseline))


def regress(history, draws=2000, shuffles=1000):
    """Bootstrap whole meetings, refitting speaker intercepts in every replicate."""
    data=np.asarray(history,float)
    if data.ndim!=2 or data.shape[1]!=6 or not np.isfinite(data).all():
        raise ValueError('Six finite columns required')
    _,party=np.unique(data[:,0],return_inverse=True)
    _,meet=np.unique(data[:,1],return_inverse=True)
    # Columns of z are voicing, level, earlier laughter and joined.
    z=data[:,2:]
    people,meetings=party.max()+1,meet.max()+1
    if meetings<2 or people<2:
        return []
    counts=np.zeros((meetings,people))
    np.add.at(counts,(meet,party),1.)
    moments=np.zeros((meetings,people,4))
    np.add.at(moments,(meet,party),z)
    totals=moments.sum(axis=1)
    sizes=counts.sum(axis=1)
    gram=np.stack([z[meet==m].T@z[meet==m] for m in range(meetings)])
    # Sparse person-by-meeting incidence makes the two-way fit inexpensive.
    incidence=sparse.csr_matrix(counts)
    ridge=1e-6

    def slopes(w):
        byperson=w@counts
        current=np.flatnonzero(byperson>0)
        S=np.einsum('m,mij->ij',w,gram)
        T=np.einsum('m,mpj->pj',w,moments)[current]
        total=S-T.T@(T/byperson[current,None])
        result=[]
        def coefficient(block,k):
            block=(block+block.T)/2
            g=block[:k,:k]
            if np.linalg.matrix_rank(g,tol=1e-10)!=k:return np.nan
            return np.linalg.solve(g,block[:k,3])[0]
        result.extend([coefficient(total,1),coefficient(total,3)])
        fraction=w/sizes
        group=incidence[:,current]
        D=sparse.diags(byperson[current]+ridge)-group.T@group.multiply(fraction[:,None])
        T2=T-np.asarray(group.T@(fraction[:,None]*totals))
        S2=S-totals.T@(fraction[:,None]*totals)
        full=S2-T2.T@spsolve(D.tocsc(),T2)
        result.append(coefficient(full,3))
        return result

    rng=np.random.default_rng(2026112706)
    ones=np.ones(meetings)
    point=np.asarray(slopes(ones))
    estimates=np.asarray([slopes(rng.multinomial(meetings,np.full(meetings,1/meetings))) for _ in range(draws)])
    order=np.lexsort((np.arange(len(z)),meet,party))
    keys=party[order].astype(np.int64)*meetings+meet[order]
    x,y=z[:,0],z[:,3]
    count=np.bincount(party)
    xr=x-(np.bincount(party,x)/count)[party]
    yr=y-(np.bincount(party,y)/count)[party]
    denom=xr@xr
    null=[]
    if denom>1e-10:
        for _ in range(shuffles):
            perm=np.lexsort((rng.random(len(order)),keys))
            null.append(float((yr[order]@xr[order][perm])/denom))
    rows=[]
    for i,p in enumerate(point):
        if not np.isfinite(p) or not np.isfinite(estimates[:,i]).all():
            continue
        lower,upper=np.quantile(estimates[:,i],[.025,.975])
        row=dict(model=i+1,estimate=float(p),lower=float(lower),upper=float(upper))
        if i==0 and null:
            row.update(shuffle95=float(np.quantile(null,.95)),shuffle_upper=float((1+np.sum(np.asarray(null)>=p-1e-15))/(shuffles+1)))
        rows.append(row)
    return rows


def fixture():
    rate=8000
    t=np.arange(rate)/rate
    tone=.3*np.sin(2*np.pi*180*t)
    rng=np.random.default_rng(68)
    marks=[dict(start=a,end=b,speaker=p) for a,b,p in
           [(5,6,'B'),(12,13,'A'),(63,64,'A'),(63.5,64,'B'),(70,71,'A'),(70,71,'B')]]
    windows=bounds(marks)
    assert windows[2]==(63.,63.5,1,1) and windows[-1][1]==70.
    assert prefix(tone[:1599],rate,.1) is None and prefix(tone[:1600],rate,.1)[0]>.9
    noise=rng.normal(0,.14,len(tone))
    hybrid=np.r_[noise[:rate//2],tone[rate//2:]]
    assert prefix(hybrid[:rate//2],rate,.1)==prefix(noise[:rate//2],rate,.1)
    assert prefix(hybrid,rate,.1)[0]>prefix(noise,rate,.1)[0]+.2
    records=[]
    for m in range(20):
        for p in range(12):
            for _ in range(4):
                v,level,earlier=rng.normal(size=3)
                outcome=float(.8*v+.2*level+rng.normal()>.1)
                records.append([p,m,v,level,earlier,outcome])
    result=regress(records,draws=35,shuffles=49)
    a=np.asarray(records)
    speakers=np.eye(12)[a[:,0].astype(int)]
    meeting=np.eye(20)[a[:,1].astype(int)]
    for k,(controls,terms) in enumerate([(speakers,1),(speakers,3),(np.c_[speakers,meeting[:,1:]],3)]):
        direct=np.linalg.lstsq(np.c_[a[:,2:2+terms],controls],a[:,-1],rcond=None)[0][0]
        assert abs(result[k]['estimate']-direct)<1e-7 and result[k]['lower']>0
    return dict(passed=True,checks=['tie and earlier other speaker','200 ms union','post-join placebo','three direct dummy-variable fits','meeting draws','within-speaker-meeting shuffle'])
