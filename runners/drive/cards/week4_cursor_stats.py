"""S4(a) distance-standardized writer contrast, separate from S4(b).

DESIGN CHECK: Week4 S4, LESSONS2-5 and inherited controls reviewed 2026-11-02.
NULL: equal edit rates give exact zero and a null decision. ALTERNATIVE:
positive/reversed rates retain their signs. Within-session AND distance-bin
label reassignment preserves support; degenerate or biased references remain
visible. Bootstrap writers, never individual correlated landings. No mouse
identity, higher-order intention or causal effect is manufactured by this fit.
"""
from pathlib import Path
from collections import defaultdict,Counter
import time
import numpy as np
from .timing_p6 import write_equal,gzread
from .timing_census import read,filehash
from .batch_runtime import check_files
from .states_v2 import contrast_state

CONFIG=dict(card='S4a-distance-comparison',seed=20261102,draws=2000,permutations=200)
BINS=('1','2','3-5','>5')

def arrays(sessions):
    rows=[]
    for s in sessions:
        for r in s['landings']:
            rows.append((s['writer'],s['session'],r['bin'],int(r['kind']=='jump'),int(r['edit_near'])))
    writers=sorted({r[0] for r in rows});wmap={w:i for i,w in enumerate(writers)}
    cells=sorted({(r[0],r[2]) for r in rows});cmap={c:i for i,c in enumerate(cells)}
    strata=defaultdict(list)
    for i,r in enumerate(rows):strata[(r[1],r[2])].append(i)
    return dict(writers=writers,cell_writer=np.array([wmap[w] for w,b in cells],int),
        cell=np.array([cmap[(w,b)] for w,s,b,g,y in rows],int),
        group=np.array([g for w,s,b,g,y in rows],int),outcome=np.array([y for w,s,b,g,y in rows],int),
        strata=[np.array(v,int) for k,v in sorted(strata.items())],rows=len(rows))

def writer_effects(a,labels=None):
    labels=a['group'] if labels is None else labels
    ncell=len(a['cell_writer']);cell=a['cell'];y=a['outcome']
    nj=np.bincount(cell,weights=labels,minlength=ncell);ns=np.bincount(cell,weights=1-labels,minlength=ncell)
    sj=np.bincount(cell,weights=labels*y,minlength=ncell);ss=np.bincount(cell,weights=(1-labels)*y,minlength=ncell)
    both=(nj>0)&(ns>0);weight=np.minimum(nj,ns)*both
    # Cross multiplication makes identical observed proportions exactly zero.
    difference=np.divide(sj*ns-ss*nj,nj*ns,out=np.zeros(ncell),where=both)
    w=a['cell_writer'];nw=len(a['writers'])
    numerator=np.bincount(w,weights=weight*difference,minlength=nw)
    denominator=np.bincount(w,weights=weight,minlength=nw)
    effect=np.divide(numerator,denominator,out=np.zeros(nw),where=denominator>0)
    jumps=np.bincount(w,weights=nj*both,minlength=nw);steps=np.bincount(w,weights=ns*both,minlength=nw)
    supported=(jumps>=10)&(steps>=10)
    return effect,supported,dict(jumps=jumps.astype(int).tolist(),steps=steps.astype(int).tolist(),weights=denominator.tolist())

def analyze(sessions,separable=True,config=CONFIG):
    if config!=CONFIG:raise ValueError('Frozen S4 inference required')
    a=arrays(sessions);effects,supported,support=writer_effects(a)
    coverage=dict(writers=len(a['writers']),supported_writers=int(supported.sum()),required_writers=20,landings=a['rows'],separable_groups=bool(separable))
    if not separable or supported.sum()<20:
        return dict(state='design cannot test',coverage=coverage,scientific_effect_computed=False),dict(writers=a['writers'],support=support)
    values=effects[supported];observed=float(np.mean(values));rng=np.random.default_rng(config['seed'])
    boot=np.mean(values[rng.integers(0,len(values),size=(config['draws'],len(values)))],axis=1)
    interval=np.quantile(boot,[.025,.975]);controls=[];rng=np.random.default_rng(config['seed']+1)
    for draw in range(config['permutations']):
        labels=a['group'].copy()
        for idx in a['strata']:labels[idx]=rng.permutation(labels[idx])
        perm,eligible,_=writer_effects(a,labels)
        if not np.array_equal(eligible,supported):raise ValueError('Conditional shuffle changed fixed support')
        controls.append(float(np.mean(perm[supported])))
    controls=np.array(controls);reference=np.quantile(controls,[.025,.975]);biased=bool(reference[0]>0 or reference[1]<0)
    p_positive=float((1+np.sum(controls>=observed))/(1+len(controls)))
    p_two_sided=float((1+np.sum(np.abs(controls)>=abs(observed)))/(1+len(controls)))
    state=contrast_state(observed,*interval)
    summary=dict(state=state,estimate=observed,interval=interval.tolist(),coverage=coverage,
        reference=dict(positive_probability=p_positive,two_sided_probability=p_two_sided,interval=reference.tolist(),biased=biased,permutations=len(controls)),
        control_status='biased reference' if biased else 'passes',draws=len(boot),scientific_effect_computed=True,
        scope='Observed landing contrast standardized within writer and distance; observational, not device or causal identification.')
    private=dict(writers=a['writers'],effects=effects.tolist(),supported=supported.tolist(),support=support,bootstrap=boot.tolist(),controls=controls.tolist())
    return summary,private

def load(inputs):
    if set(inputs)!={'source_completion'}:raise ValueError('Exact source completion required')
    root=Path(inputs['source_completion']).parent;c=read(inputs['source_completion']);p=read(root/'PLAN.json')
    if not c['fresh_process_verified'] or not read(root/'VERIFIED.json')['complete_source_replay']:raise ValueError('Source incomplete')
    check_files(p['pins'])
    for name,h in c['outputs'].items():
        if filehash(root/name)!=h:raise ValueError('Source output changed: '+name)
    summary=read(root/'output/SUMMARY.json')
    if not summary['complete_population']:raise ValueError('Unadmitted partial source')
    sessions=[gzread(p) for p in sorted((root/'output/sessions').glob('*.json.gz'))]
    if len(sessions)!=summary['sessions']:raise ValueError('Source roster incomplete')
    return sessions,summary

def run(output,inputs,config,verification=False):
    start=time.process_time();sessions,census=load(inputs);summary,private=analyze(sessions,census['separable_groups'],config)
    genres={g:analyze([s for s in sessions if s['genre']==g],census['separable_groups'],config)[0] for g in sorted({s['genre'] for s in sessions})}
    values={'PRIMARY.json':summary,'GENRES.json':genres,'PRIVATE_INFERENCE.json':private,'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})}
    output=Path(output)
    if verification:
        for name,value in values.items():
            if read(output/name)!=value:raise ValueError('S4 statistical replay differs: '+name)
        return dict(verified=True,full_statistical_replay=True)
    for name,value in values.items():write_equal(output/name,value)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start))
    return dict(status='complete',scientific_admission=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
