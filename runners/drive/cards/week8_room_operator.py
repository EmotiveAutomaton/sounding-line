"""Laugh-excluded room measurements and a conditional count model (Week 8 RML1).

DESIGN CHECK (LESSONS §§2–5). A laugh planted inside an annotated window changes
no clean speech measure. A planted negative change-size coefficient is recovered.
Missing bins never become adjacent. Unidentified models have no table.
"""
from bisect import bisect_right
import math

import numpy as np


def merged(spans):
    result = []
    for a, b in sorted(spans):
        if not (0 <= a < b < math.inf):
            raise ValueError('Invalid time span')
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def unmasked(a, b, masks, ends):
    for index in range(bisect_right(ends, a), len(masks)):
        left, right = masks[index]
        if left >= b:
            break
        if a < left:
            yield a, left
        a = max(a, right)
        if a >= b:
            return
    if a < b:
        yield a, b


def pieces(a, b, bins):
    b = min(b, 30. * bins)
    while a < b:
        index = int(a // 30.)
        stop = min(b, 30. * (index + 1))
        yield index, a, stop
        a = stop


def measure_channel(pcm, rate, words, masks):
    bins = int(len(pcm) // (30 * rate))
    ends = [b for _, b in masks]
    counts, seconds, frame_n, db_sum, db_sq = np.zeros((5, bins))
    for a, b, quantity in words:
        if not (0 <= a < b and quantity > 0):
            raise ValueError('Invalid word span')
        for left, right in unmasked(a, b, masks, ends):
            for t, first, last in pieces(left, right, bins):
                counts[t] += quantity * (last-first) / (b-a)
    frame = round(.020 * rate)
    for a, b in merged((a,b) for a,b,_ in words):
        for left, right in unmasked(a, b, masks, ends):
            for t, first, last in pieces(left, right, bins):
                seconds[t] += last-first
                start = math.ceil(first*rate/frame - 1e-10) * frame
                stop = math.floor(last*rate/frame + 1e-10) * frame
                if stop <= start:
                    continue
                values = pcm[start:stop].reshape(-1, frame).astype(float) / 32768.
                energy = np.einsum('ij,ij->i', values, values) / frame
                active = energy > 0
                db = 10. * np.log10(energy[active])
                frame_n[t] += len(db)
                db_sum[t] += db.sum()
                db_sq[t] += db @ db
    return np.array([counts, seconds, frame_n, db_sum, db_sq])


def combine(channels):
    if not channels:
        return np.empty((3, 0))
    bins = min(x.shape[1] for x in channels)
    accumulated, support = np.zeros((2, bins)), np.zeros((2, bins))
    for x in channels:
        counts, seconds, n, sums, squares = x[:, :bins]
        if n.sum():
            mean = sums.sum()/n.sum()
            var = squares.sum()/n.sum() - mean**2
            measured = n > 0
            if var > 1e-10:
                accumulated[0, measured] += (sums[measured]/n[measured] - mean)/np.sqrt(var)
                support[0, measured] += 1
        measured = seconds > 0
        if measured.any():
            pace = counts[measured]/seconds[measured]
            if pace.std() > 1e-10:
                accumulated[1, measured] += (pace-pace.mean())/pace.std()
                support[1, measured] += 1
    component = np.divide(accumulated, support, out=np.full_like(accumulated, np.nan), where=support > 0)
    return np.vstack((component.mean(axis=0), component))


def design(level, laughs):
    end = np.arange(6, len(level))
    if len(end) == 0:
        return np.empty((0, 6)), np.empty(0)
    history = np.asarray([level[end-i] for i in range(6,0,-1)]).T
    complete = np.isfinite(history).all(axis=1)
    history, end = history[complete], end[complete]
    delta = history[:,5] - history[:,3]
    mean = history[:,3:].mean(axis=1)
    peak_then_fall = (history[:,:3].max(axis=1) > .8) & (delta < -.5)
    prior = laughs[end-3]+laughs[end-2]+laughs[end-1]
    return np.column_stack((abs(delta),delta,mean,mean**2,peak_then_fall,prior)), laughs[end]


def score(groups, beta):
    scores, info = [], []
    for x,y in groups:
        log_mu = x @ beta
        p = np.exp(log_mu-log_mu.max())
        p /= p.sum()
        centered = x - p @ x
        scores.append(y @ centered)
        info.append(y.sum() * ((centered.T*p) @ centered))
    return np.asarray(scores),np.asarray(info)


def fit(groups, draws=2000):
    groups = [(x,y) for x,y in groups if len(y)>1 and y.sum()>0]
    if len(groups)<2:
        return None
    beta = np.zeros(6)
    try:
        for _ in range(100):
            s,h = score(groups,beta)
            step = np.linalg.solve(h.sum(axis=0),s.sum(axis=0))
            if not np.isfinite(step).all():
                return None
            beta += step
            if max(abs(step)) < 1e-9:
                break
        else:
            return None
        s,h = score(groups,beta)
        rng = np.random.default_rng(2026112709)
        weights = rng.multinomial(len(groups),np.full(len(groups),1/len(groups)),size=draws)
        info = np.einsum('bm,mij->bij',weights,h)
        sampled = beta+np.linalg.solve(info,(weights @ s)[...,None])[...,0]
        if not np.isfinite(sampled).all():
            return None
        lo,hi = np.quantile(sampled,[.025,.975],axis=0)
        return dict(meetings=len(groups),weights=np.column_stack((beta,lo,hi)).tolist(),draws=draws)
    except np.linalg.LinAlgError:
        return None


def fixture():
    rate=1000
    rng=np.random.default_rng(3908)
    wave=rng.integers(-1000,1001,120*rate,dtype=np.int16)
    masks=merged([(28,30),(29.9,31.1)])
    words=[(5,10,4),(20,40,6),(45,48,5),(65,72,2),(97,104,7)]
    base=measure_channel(wave,rate,words,masks)
    changed=wave.copy()
    changed[28000:31100]=32767
    assert np.array_equal(base,measure_channel(changed,rate,words,masks))
    assert np.allclose(base[0,:2],[4+8*.3,5+8.9*.3])
    assert np.allclose(base[1,:2],[13,11.9])
    assert np.allclose(combine([base,base]),combine([base]))
    assert not np.isfinite(combine([measure_channel(np.zeros_like(wave),rate,[],[])])).any()
    levels=rng.normal(size=20)
    levels[7]=np.nan
    x,_=design(levels,np.ones(20))
    assert len(x)==8 and np.all(x[:,-1]==3)
    groups=[]
    for _ in range(55):
        levels=rng.normal(size=100)
        y=rng.poisson(1.,size=len(levels))
        delta=abs(levels[2:-1]-levels[:-3])
        y[3:]=rng.poisson(np.exp(.6-.65*delta))
        groups.append(design(levels,y))
    result=fit(groups,200)
    assert result and -.85 < result['weights'][0][0] < -.45 and result['weights'][0][2]<0
    assert fit([(np.zeros((15,6)),np.ones(15))]*20,10) is None
    return dict(constructed=True,checks=['masked room-wide contamination','clean word mass and seconds across boundary','concurrent channel averaging','empty and silent bins','consecutive six-bin clock','planted conditional coefficient','singular model withheld'])
