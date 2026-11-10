"""Exact original TR5 learners with sealed 128-choice checkpoints.

Every run length is retained. Selection, arithmetic order and score-before-
update clocks are the frozen original implementation. Fresh verification
recomputes every state transition rather than trusting saved model states.
"""
from collections import defaultdict
from pathlib import Path
import copy,math
import numpy as np
from runners.stage9.common import digest
from . import week3_trust_learners as old
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal


class YieldCheckpoint(Exception):pass


def state(model):
    if isinstance(model,old.Adaptive):
        return dict(kind='adaptive',base=model.base,gain=model.gain,p=model.p,variance=model.variance)
    return dict(kind='changepoint',hazard=model.hazard,weights=model.weights.tolist(),a=model.a.tolist(),b=model.b.tolist())


def restore(model,saved):
    if isinstance(model,old.Adaptive):
        if (saved['kind'],saved['base'],saved['gain'])!=('adaptive',model.base,model.gain):raise ValueError('Adaptive state identity changed')
        model.p=saved['p'];model.variance=saved['variance']
    else:
        if (saved['kind'],saved['hazard'])!=('changepoint',model.hazard):raise ValueError('Change-point state identity changed')
        model.weights=np.array(saved['weights']);model.a=np.array(saved['a']);model.b=np.array(saved['b'])


def score(root,model,values,binding,verifying,should_yield):
    root=Path(root);total=0.;previous=digest(state(model))
    for offset in range(0,len(values),128):
        if should_yield():raise YieldCheckpoint()
        path=root/f'block-{offset//128:05d}.json.gz';seal=path.with_suffix('.seal.json')
        unit=dict(binding=binding,offset=offset,previous_sha256=previous,labels_sha256=digest(values[offset:offset+128]))
        if path.exists():
            if not seal.exists() or read(seal)!=dict(unit=unit,sha256=filehash(path)):raise ValueError('TR5 learner checkpoint seal differs')
            saved=gzread(path)
        else:
            if seal.exists() or verifying:raise ValueError('TR5 complete learner checkpoint missing')
            saved=None
        if verifying or saved is None:
            for y in values[offset:offset+128]:
                p=model.predict()
                if not 0<p<1 or y not in (0,1):raise ValueError('Invalid prequential value')
                total+=math.log(p if y else 1-p);model.update(y)
            value=dict(unit=unit,choices=min(offset+128,len(values)),log_likelihood=total,state=state(model))
            if verifying:
                if saved!=value:raise ValueError('TR5 full transition replay differs')
            else:
                gzip_equal(path,value);write_equal(seal,dict(unit=unit,sha256=filehash(path)))
        else:
            if saved['unit']!=unit or saved['choices']!=min(offset+128,len(values)):raise ValueError('TR5 checkpoint cursor differs')
            total=saved['log_likelihood'];restore(model,saved['state'])
        previous=filehash(path)
    return total


def fit(root,train,test,verifying=False,should_yield=lambda:False):
    if not train or not test:raise ValueError('Independent train/test choices required')
    root=Path(root);binding=digest(dict(train=train,test=test,revision='TR5-original-exact-128'))
    adaptive=[];changes=[]
    for j,(base,gain) in enumerate((b,g) for b in (.01,.05,.1) for g in (.2,.5,1.)):
        model=old.Adaptive(base,gain)
        ll=score(root/f'train-adaptive-{j}',model,train,binding,verifying,should_yield);adaptive.append((ll,base,gain,model))
    for j,hazard in enumerate((.01,.025,.05,.1,.2)):
        model=old.ChangePoint(hazard)
        ll=score(root/f'train-change-{j}',model,train,binding,verifying,should_yield);changes.append((ll,hazard,model))
    a=max(adaptive,key=lambda x:(x[0],-x[1],-x[2]));c=max(changes,key=lambda x:(x[0],-x[1]))
    p=(sum(train)+1)/(len(train)+2)
    return dict(training_choices=len(train),heldout_choices=len(test),fixed_log_likelihood=sum(math.log(p if y else 1-p) for y in test),
                adaptive_log_likelihood=score(root/'test-adaptive',copy.deepcopy(a[3]),test,binding,verifying,should_yield),
                changepoint_log_likelihood=score(root/'test-change',copy.deepcopy(c[2]),test,binding,verifying,should_yield),
                frozen_training_selection=dict(adaptive_base=a[1],adaptive_gain=a[2],hazard=c[1]))


def by_writer(root,sessions,verifying=False,should_yield=lambda:False):
    groups=defaultdict(list)
    for session in sessions:groups[session['writer']].append(session)
    rows=[];unsupported=[]
    for ordinal,(writer,values) in enumerate(sorted(groups.items())):
        if should_yield():raise YieldCheckpoint()
        values=sorted(values,key=lambda s:(s['timestamp'],s['session']))
        if len(values)<4:unsupported.append(writer);continue
        cut=max(1,min(len(values)-1,math.floor(.75*len(values))))
        sets=[[int(m['handling'] in ('accept','edit')) for s in block for m in s['menu'] if not m['censored']] for block in (values[:cut],values[cut:])]
        if not all(sets):unsupported.append(writer);continue
        value=fit(Path(root)/f'writer-{ordinal:04d}',*sets,verifying,should_yield)
        rows.append(dict(writer=writer,training_sessions=[s['session'] for s in values[:cut]],heldout_sessions=[s['session'] for s in values[cut:]],**value))
    return dict(rows=rows,unsupported_writers=unsupported,
                split='first75%wholechronological sessions train; final25%test; at least4sessions; no test tuning',
                inference='observed handling prediction; not a readout of internal trust')
