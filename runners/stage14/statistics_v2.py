"""Frozen half-Brier and writer-level uncertainty; no per-row verdicts.

DESIGN CHECK: LESSONS 3-5. NULL: constant prior remains explicit, zero target mass
keeps infinite log loss, invalids keep denominator. ALTERNATIVE: paired writer
loss improvement survives the predeclared margin. Wide intervals are unresolved.
"""
import math
import numpy as np
from collections import defaultdict
ACTIONS=('accept','edit','dismiss','ignore')

def score(p,y):
    if len(p)!=4 or any(not math.isfinite(float(x)) or x<0 for x in p) or abs(sum(p)-1)>1e-6:
        return dict(half_brier=1.,log_loss='Infinity',correct=0,valid=False)
    return dict(half_brier=float(sum((float(x)-(j==y))**2 for j,x in enumerate(p))*.5),
        log_loss=-math.log(p[y]) if p[y]>0 else 'Infinity',correct=int(int(np.argmax(p))==y),valid=True)

def paired(rows,left,right,draws=4000):
    grouped=defaultdict(list)
    for r in rows:grouped[r['writer']].append(r['scores'][left]['half_brier']-r['scores'][right]['half_brier'])
    x=np.array([np.mean(grouped[k]) for k in sorted(grouped)])
    if len(x)<2:
        return dict(writers=len(x),equal_writer_mean=float(x.mean()) if len(x) else None,interval=None,margin=.01,disposition='UNRESOLVED_INSUFFICIENT_WRITERS',confirmation=False,unit='writer',half_width=None,parity_claim=False,scope='execution pilot only; no population inference')
    rng=np.random.default_rng(141010)
    bs=np.mean(x[rng.integers(len(x),size=(draws,len(x)))],axis=1)
    lo,hi=np.quantile(bs,[.025,.975]); margin=.01
    disposition='PROMISING' if hi < -margin else 'EXHAUSTED_AT_MARGIN' if lo > -margin else 'UNRESOLVED'
    return dict(writers=len(x),equal_writer_mean=float(x.mean()),interval=[float(lo),float(hi)],margin=margin,
        disposition=disposition,confirmation=False,unit='writer',half_width=float((hi-lo)/2),
        parity_claim=False,scope='descriptive exposure; no fresh independent confirmation')
