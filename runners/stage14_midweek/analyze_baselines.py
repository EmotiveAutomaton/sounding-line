"""Saved-output SM2/SM3 consumer; no model calls or target-driven selection.

DESIGN CHECK: LESSONS 3-5. NULL: paired identical scores give zero contrast;
known sharper wrong vectors lose proper score. ALTERNATIVE: writer-paired gain
survives population, personal, effort-feature and shuffled-weight comparisons.
All intervals descriptive pending the complete campaign; no p-values or selection.
"""
import math
import numpy as np
from .data import RAW,ACTIONS
from .baselines import proper
from runners.stage14.common import read,freeze,filehash

def interval(values,seed=20261013):
    values=np.asarray(values,dtype=float)
    if not len(values) or not np.isfinite(values).all():raise ValueError('invalid writer values')
    sampled=np.random.default_rng(seed).choice(values,size=(10000,len(values)),replace=True).mean(axis=1)
    return dict(mean=float(values.mean()),interval=np.quantile(sampled,[.025,.975]).tolist())

def crossed(rows,values,seed=20261013):
    writers=sorted({r['writer'] for r in rows});prompts=sorted({r['prompt'] for r in rows})
    sums=np.zeros((len(writers),len(prompts)));counts=np.zeros_like(sums)
    for r,v in zip(rows,values):
        w=writers.index(r['writer']);p=prompts.index(r['prompt']);sums[w,p]+=v;counts[w,p]+=1
    rng=np.random.default_rng(seed);boot=[]
    for _ in range(10000):
        wc=np.bincount(rng.integers(len(writers),size=len(writers)),minlength=len(writers))
        pc=np.bincount(rng.integers(len(prompts),size=len(prompts)),minlength=len(prompts))
        denom=counts@pc;present=denom>0;weights=wc*present
        if weights.sum():boot.append(float(np.sum(np.divide(sums@pc,denom,out=np.zeros(len(writers)),where=present)*weights)/weights.sum()))
    return np.quantile(boot,[.025,.975]).tolist()

def run():
    folder=RAW/'baselines-v1';data=RAW/'data-v2';out=RAW/'baseline-analysis-v1'
    terminal=read(folder/'COMPLETE.json');pins=read(folder/'INPUTS.json')
    for name,h in terminal['outputs'].items():
        if filehash(folder/name)!=h:raise ValueError('producer output changed')
    for name,h in pins.items():
        if filehash(data/name)!=h:raise ValueError('data changed')
    rows=read(folder/'PREDICTIONS.json');targets={r['key']:r for r in read(data/'EVALUATOR.json') if not r['pilot']}
    if len(rows)!=len(targets) or {r['key'] for r in rows}!=set(targets):raise ValueError('roster mismatch')
    training=read(data/'TRAINING.json');all_history={r['key']:r for c in training.values() for r in c['history']}
    for fit in read(folder/'FITS.json'):
        if set(fit['train_keys'])!={k for k,r in all_history.items() if r['resolved_at']<=fit['cutoff']}:raise ValueError('temporal fit mismatch')
    arms=sorted(rows[0]['probabilities']);writers=sorted({r['writer'] for r in rows})
    for r in rows:
        t=targets[r['key']]
        if (r['writer'],r['prompt'],r['pilot'])!=(t['writer'],t['prompt'],False):raise ValueError('target binding mismatch')
        if sorted(r['probabilities'])!=arms:raise ValueError('incomplete arm roster')
        for arm,p in r['probabilities'].items():
            p=np.asarray(p)
            if p.shape!=(4,) or not np.isfinite(p).all() or (p<0).any() or abs(p.sum()-1)>1e-12:raise ValueError('invalid baseline vector')
            for metric,value in proper(p,ACTIONS.index(t['handling'])).items():
                if abs(value-r['scores'][arm][metric])>1e-12:raise ValueError('saved proper score mismatch')
    pairs=[(a,b) for a in arms for b in ('B-pop','B-writer','B-mixlogit') if a!=b]
    pairs+= [('P04-E','P04-effort-features'),('P04-E','P04-E-shuffle'),('P04-effort-features','B-mixlogit')]
    report=[];per_writer=[]
    for arm,rival in sorted(set(pairs)):
        for metric in ('half_brier','log_loss'):
            # Positive is improvement of the arm over the rival, for both metrics.
            vals=[r['scores'][rival][metric]-r['scores'][arm][metric] for r in rows]
            wm=[float(np.mean([v for r,v in zip(rows,vals) if r['writer']==w])) for w in writers]
            report.append(dict(arm=arm,rival=rival,metric=metric,**interval(wm),crossed_interval=crossed(rows,vals)))
            per_writer.extend(dict(writer=w,arm=arm,rival=rival,metric=metric,gain=v) for w,v in zip(writers,wm))
    counts=[sum(r['writer']==w for r in rows) for w in writers]
    planning_se=math.sqrt(sum(.36**2/n+.04**2 for n in counts))/len(writers)
    summary=dict(status='COMPLETE',writers=len(writers),targets=len(rows),arms=arms,contrasts=report,
        planning_mde=2.8016*planning_se,planning_basis='fixed external planning SDs, actual targets per writer, unadjusted 80% normal approximation; not empirical pilot estimate',
        uncertainty='10000 writer resamples; crossed writer/prompt sensitivity; shared history/donor pool remains',
        interpretation='descriptive secondary cell; no p-values, no theory verdict, no outcome-driven model or roster changes',
        producer_sha256=filehash(folder/'COMPLETE.json'),source_sha256=filehash(__file__),inference_calls=0)
    freeze(out/'PER_WRITER.json',per_writer);freeze(out/'SUMMARY.json',summary)
    freeze(out/'COMPLETE.json',dict(status='COMPLETE',outputs={n:filehash(out/n) for n in ('PER_WRITER.json','SUMMARY.json')},producer_sha256=summary['producer_sha256'],source_sha256=summary['source_sha256']))
    return dict(status='COMPLETE',writers=len(writers),targets=len(rows),inference_calls=0)

if __name__=='__main__':print(run())
