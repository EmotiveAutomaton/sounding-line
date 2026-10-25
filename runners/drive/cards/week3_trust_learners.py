"""TR5 frozen online handling learners; train-only tuning, whole-session holdout.

DESIGN CHECK: LESSONS3-5, 2026-10-25. No held-out labels tune a learning rate
or hazard. Scoring is prequential: each target is scored before its update.
The Bernoulli change-point mixture keeps every run length, without pruning.
Missing independent held-out sessions are unsupported, never training scores.
"""
from collections import defaultdict
import copy
import math

import numpy as np


class Adaptive:
    def __init__(self,base,gain):self.base=base;self.gain=gain;self.p=.5;self.variance=.25
    def predict(self):return self.p
    def update(self,y):
        error=y-self.p
        self.variance=.95*self.variance+.05*error*error
        rate=min(.8,max(.01,self.base+self.gain*math.sqrt(self.variance)))
        self.p=min(1-1e-9,max(1e-9,self.p+rate*error))


class ChangePoint:
    def __init__(self,hazard):self.hazard=hazard;self.weights=np.ones(1);self.a=np.ones(1);self.b=np.ones(1)
    def predict(self):return float(self.hazard*.5+(1-self.hazard)*(self.weights*self.a/(self.a+self.b)).sum())
    def update(self,y):
        p=self.a/(self.a+self.b);likelihood=p if y else 1-p
        weights=np.r_[self.hazard*.5,(1-self.hazard)*self.weights*likelihood]
        self.weights=weights/weights.sum();self.a=np.r_[1+y,self.a+y];self.b=np.r_[2-y,self.b+1-y]


def score(model,values):
    total=0.
    for y in values:
        p=model.predict()
        if not 0<p<1 or y not in (0,1):raise ValueError('invalid prequential probability or outcome')
        total+=math.log(p if y else 1-p);model.update(y)
    return total


def fit(train,test):
    if not len(train) or not len(test):raise ValueError('independent training and test choices required')
    candidates=[]
    for base in (.01,.05,.1):
        for gain in (.2,.5,1.):
            model=Adaptive(base,gain);ll=score(model,train);candidates.append((ll,base,gain,model))
    adaptive=max(candidates,key=lambda x:(x[0],-x[1],-x[2]))
    choices=[]
    for hazard in (.01,.025,.05,.1,.2):
        model=ChangePoint(hazard);ll=score(model,train);choices.append((ll,hazard,model))
    change=max(choices,key=lambda x:(x[0],-x[1]))
    p=(sum(train)+1)/(len(train)+2)
    fixed=sum(math.log(p if y else 1-p) for y in test)
    return dict(training_choices=len(train),heldout_choices=len(test),
                fixed_log_likelihood=fixed,adaptive_log_likelihood=score(copy.deepcopy(adaptive[3]),test),
                changepoint_log_likelihood=score(copy.deepcopy(change[2]),test),
                frozen_training_selection=dict(adaptive_base=adaptive[1],adaptive_gain=adaptive[2],hazard=change[1]))


def by_writer(sessions):
    groups=defaultdict(list)
    for session in sessions:groups[session['writer']].append(session)
    rows=[];unsupported=[]
    for writer,values in sorted(groups.items()):
        values=sorted(values,key=lambda s:(s['timestamp'],s['session']))
        if len(values)<4:unsupported.append(writer);continue
        cut=max(1,min(len(values)-1,math.floor(.75*len(values))))
        sets=[[int(m['handling'] in ('accept','edit')) for s in block for m in s['menu'] if not m['censored']] for block in (values[:cut],values[cut:])]
        if not all(sets):unsupported.append(writer);continue
        result=fit(*sets)
        rows.append(dict(writer=writer,training_sessions=[s['session'] for s in values[:cut]],
                         heldout_sessions=[s['session'] for s in values[cut:]],**result))
    return dict(rows=rows,unsupported_writers=unsupported,
                split='first75%wholechronological sessions train; final25%test; at least4sessions; no test tuning',
                inference='observed handling prediction; not a readout of internal trust')
