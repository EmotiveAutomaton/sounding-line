"""Separate calibration and selective reporting, with all-attempt denominators.

DESIGN CHECK: LESSONS 3-5. NULL: failed/invalid attempts remain costly; confident
errors worsen proper losses. ALTERNATIVE: calibration reduces reserve loss at a
frozen temperature. Calibration never selects a winner using reserved labels.
"""
import math
import numpy as np
from .scoring import probabilities,proper_loss,interval


def temper(p,t):
    if not isinstance(p,(list,tuple)) or probabilities(p,len(p)) is None:return None
    v=np.power(np.maximum(p,1e-12),1/t);return (v/v.sum()).tolist()


def fit(rows):
    if not rows:raise ValueError('no calibration records')
    choices=[.5,.75,1.,1.5,2.,3.,4.]
    losses={str(t):np.mean([proper_loss(temper(r['probabilities'],t),r['truth'],r.get('n',len(r['probabilities']) if isinstance(r.get('probabilities'),list) else 4))['log_loss'] for r in rows]) for t in choices}
    t=min(choices,key=lambda t:(losses[str(t)],abs(t-1),t))
    return dict(temperature=t,fit_units=len({r['unit'] for r in rows}),losses=losses,
                method='grid temperature from independent calibration components; no general precision claim from small human component counts')


def evaluate(rows,model):
    scores=[]
    for r in rows:
        p=temper(r['probabilities'],model['temperature']);scores.append(dict(unit=r['unit'],**proper_loss(p,r['truth'],r.get('n',len(r['probabilities']) if isinstance(r.get('probabilities'),list) else 4))))
    total={k:interval([s[k] for s in scores],[s['unit'] for s in scores]) for k in ('brier','log_loss','correct')}
    total['attempts']=len(scores);total['invalid']=sum(not s['valid'] for s in scores)
    total['selective']={}
    for confidence in (.5,.7,.9):
        chosen=[s for s in scores if s['valid'] and s['confidence']>=confidence]
        total['selective'][str(confidence)]=dict(coverage=len(chosen)/len(scores),attempts=len(chosen),
            accuracy=interval([s['correct'] for s in chosen],[s['unit'] for s in chosen]) if chosen else None)
    return total
