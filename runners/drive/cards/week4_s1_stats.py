"""S1 within-writer recurrence contrast with inherited timing controls.

DESIGN CHECK: Week4 S1/0.5, CONTROLS and LESSONS2-5 reviewed November2.
NULL: equal outcomes and nuisance-only variation give zero after adjustment.
ALTERNATIVE: positive/reversed personal recurrence retains its direction.
Within-session label permutations refit the label contrast, preserve all source
and support, and never shuffle words. Writer bootstrap preserves paired rows.
Unidentifiable contrasts refuse; no silent dropped permutation or nuisance.
"""
from collections import defaultdict,Counter
import numpy as np
from .timing_text import WORD
from .states_v2 import contrast_state

CONFIG=dict(seed=20261102,permutations=200,draws=2000,min_writers=25,min_each=20)

def history_grams(sequences,dictionary,n=4):
    found=set()
    for seq in sequences:
        sentence=[]
        def flush():
            for i in range(len(sentence)-n+1):
                gram=tuple(sentence[i:i+n])
                if any(t!='<content>' for t in gram):found.add(gram)
            sentence.clear()
        for token in seq:
            if token in ('.','!','?'):flush()
            elif WORD.fullmatch(token):sentence.append(token if token in dictionary else '<content>')
        flush()
    return found

def recurrence(grams,own,donor):
    if not grams:raise ValueError('No informative grams')
    # Repeated target occurrences count repeatedly; histories are presence sets.
    return (sum(tuple(g) in own for g in grams)-sum(tuple(g) in donor for g in grams))/len(grams)

def writer_arrays(rows):
    y=np.array([r['outcome'] for r in rows],float);label=np.array([r['label'] for r in rows],float)
    x=np.asarray([r['nuisance'] for r in rows],float)
    if x.ndim!=2 or not np.isfinite(x).all() or not np.isfinite(y).all() or not set(label)<= {0.,1.}:raise ValueError('Invalid observed arrays')
    scale=x.std(axis=0);scale[scale==0]=1
    z=np.column_stack([np.ones(len(y)),(x-x.mean(axis=0))/scale])
    u,s,v=np.linalg.svd(z,full_matrices=False);rank=int(np.sum(s>np.finfo(float).eps*max(z.shape)*s[0]));q=u[:,:rank]
    residual_y=y-q@(q.T@y)
    strata=defaultdict(list)
    for i,r in enumerate(rows):strata[r['session']].append(i)
    return dict(y=y,label=label,q=q,residual_y=residual_y,strata=[np.array(v,int) for k,v in sorted(strata.items())],rank=rank)

def coefficient(a,label=None):
    label=a['label'] if label is None else label
    x=label-a['q']@(a['q'].T@label);den=float(x@x)
    if den<=1e-10:raise ValueError('Label contrast not identifiable beyond nuisance span')
    value=float(x@a['residual_y']/den)
    # Analytically zero outcomes stay zero under finite-precision projection.
    if abs(value)<1e-12:value=0.
    return value

def analyze(rows,config=CONFIG):
    if config!=CONFIG:raise ValueError('Frozen S1 contrast required')
    by=defaultdict(list)
    for r in rows:by[r['writer']].append(r)
    counts={w:Counter(r['label'] for r in values) for w,values in by.items()}
    writers=[w for w in sorted(by) if min(counts[w][0],counts[w][1])>=config['min_each']]
    coverage=dict(writers=len(by),supported_writers=len(writers),required_writers=config['min_writers'],windows=len(rows),minimum_each=config['min_each'])
    if len(writers)<config['min_writers']:return dict(state='design cannot test',coverage=coverage,scientific_effect_computed=False),dict(support=counts)
    arrays=[writer_arrays(by[w]) for w in writers]
    try:effects=np.array([coefficient(a) for a in arrays])
    except ValueError as error:return dict(state='design cannot test',reason=str(error),coverage=coverage,scientific_effect_computed=False),dict(support=counts)
    raw=np.array([a['y'][a['label']==1].mean()-a['y'][a['label']==0].mean() for a in arrays])
    observed=float(effects.mean());rng=np.random.default_rng(config['seed']);indices=rng.integers(0,len(writers),size=(config['draws'],len(writers)))
    boot=effects[indices].mean(axis=1);interval=np.quantile(boot,[.025,.975]);reference=[];rng=np.random.default_rng(config['seed']+1)
    for draw in range(config['permutations']):
        values=[]
        for a in arrays:
            label=a['label'].copy()
            for idx in a['strata']:label[idx]=rng.permutation(label[idx])
            values.append(coefficient(a,label))
        reference.append(float(np.mean(values)))
    reference=np.array(reference);ref_interval=np.quantile(reference,[.025,.975]);biased=bool(ref_interval[0]>0 or ref_interval[1]<0)
    probability=float((1+np.sum(reference>=observed))/(1+len(reference)))
    state=contrast_state(observed,*interval)
    result=dict(state=state,estimate=observed,interval=interval.tolist(),unadjusted_difference=float(raw.mean()),coverage=coverage,
        reference=dict(positive_probability=probability,interval=ref_interval.tolist(),biased=biased,permutations=len(reference)),
        control_status='biased reference' if biased else 'passes',positive_gate=bool(interval[0]>0 and probability<.05 and not biased),
        scientific_effect_computed=True,draws=len(boot),
        method='Equal-writer mean flow coefficient after full nuisance-span adjustment; paired whole-writer percentile bootstrap; within-session label permutations refit the contrast.',
        scope='Descriptive conditional recurrence in observed typed windows; no causal or psychological identification.')
    detail=dict(writers=writers,effects=effects.tolist(),unadjusted=raw.tolist(),support=counts,bootstrap=boot.tolist(),reference=reference.tolist())
    return result,detail

def fixture(kind):
    if kind not in ('positive','null','negative','nuisance','unidentifiable'):raise ValueError('Unknown construction')
    rows=[];rng=np.random.default_rng(9)
    for writer in range(25):
        z=np.tile([-1.,0.,1.,2.],20);label=np.tile([0,0,1,1,0,1,0,1],10)
        nuisance=np.column_stack([z,rng.normal(size=len(z))])
        if kind=='unidentifiable':nuisance=np.column_stack([nuisance,label])
        y=np.zeros(len(z)) if kind in ('null','unidentifiable') else .1*z if kind=='nuisance' else (.3 if kind=='positive' else -.3)*label+.1*z
        for i in range(len(z)):
            rows.append(dict(writer=str(writer),session=f'{writer}-{i//40}',label=int(label[i]),outcome=float(y[i]),nuisance=nuisance[i].tolist()))
    return rows

def known_checks():
    result={}
    for kind in ('positive','null','negative','nuisance','unidentifiable'):
        s,_=analyze(fixture(kind))
        if kind=='unidentifiable':assert s['state']=='design cannot test'
        elif kind in ('null','nuisance'):assert s['estimate']==0 and s['interval']==[0.,0.] and not s['positive_gate']
        elif kind=='positive':assert abs(s['estimate']-.3)<1e-12 and s['positive_gate']
        else:assert abs(s['estimate']+.3)<1e-12 and s['interval'][1]<0 and not s['positive_gate']
        result[kind]=True
    return result
