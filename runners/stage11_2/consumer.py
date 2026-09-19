"""Semantic consumer, strict and bounded losses, clustered paired comparisons.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6. NULL: uniforms have the analytic Brier
floor; invalid forecasts are failures, not uniform successes. ALTERNATIVE: a
correct distribution minimizes expected Brier loss. Maker-observation changes
the counterfactual truth; reader-only information does not. No test selection.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
import numpy as np
from .common import RAW, digest, freeze, read
from .world import decode, reference, enumerate_predict


def measures(p,target,observed=None):
    n=len(target)
    valid=(p is not None and len(p)==n and all(type(x) in (float,int) and math.isfinite(x) and 0<=x<=1 for x in p) and abs(sum(p)-1)<1e-6)
    if not valid:
        return dict(valid=False,expected_brier=2.,capped_expected_log_loss=-math.log(1e-12),
            strict_expected_log_loss=None,zero_support=True,modal_accuracy=0.,
            sampled_brier=2. if observed is not None else None,sampled_accuracy=0. if observed is not None else None)
    zero=any(t>0 and x==0 for x,t in zip(p,target))
    log=-sum(t*math.log(max(x,1e-12)) for x,t in zip(p,target))
    return dict(valid=True,expected_brier=1+sum(x*x for x in p)-2*sum(x*t for x,t in zip(p,target)),
        capped_expected_log_loss=log,strict_expected_log_loss=None if zero else log,zero_support=zero,
        modal_accuracy=float(max(range(n),key=p.__getitem__)==max(range(n),key=target.__getitem__)),
        sampled_brier=None if observed is None else sum((x-(i==observed))**2 for i,x in enumerate(p)),
        sampled_accuracy=None if observed is None else float(max(range(n),key=p.__getitem__)==observed))


def target_for(row,truth):
    g,b=decode(row['observation'])
    # The maker_observation arm changes the maker's actual received notice. Its
    # counterfactual is evaluated under that notice, never the original outcome.
    if row['question']=='belief':return [float(i==b) for i in range(2)], b
    if row['question']=='goal':return [float(i==g) for i in range(2)],g
    if row['question'] in ('skill','preference'):
        v=truth[row['question']];return [float(i==v) for i in range(2)],v
    obs=row['observation']
    target=reference(truth['preference'],truth['skill'],g,b,obs['world_family'],obs['tools'])
    return target, None if row['arm']=='maker_observation' else truth['action']


def summarize(rows,baseline):
    groups={}
    for r in rows:groups.setdefault((r['arm'],r['question']),[]).append(r)
    output={}
    for (arm,question),rs in sorted(groups.items()):
        means={}
        for key in rs[0]['score']:
            values=[r['score'][key] for r in rs]
            means[key]=None if any(x is None for x in values) else float(np.mean(values))
        ref={(r['unit'],r['encounter']):r for r in groups[(baseline,question)]}
        clustered={}
        for r in rs:
            difference=ref[(r['unit'],r['encounter'])]['score']['expected_brier']-r['score']['expected_brier']
            clustered.setdefault(r['cluster'],[]).append(difference)
        diffs=np.array([np.mean(v) for k,v in sorted(clustered.items())])
        rng=np.random.default_rng(112)
        boot=diffs[rng.integers(len(diffs),size=(2000,len(diffs)))].mean(axis=1)
        output[arm+':'+question]=dict(n=len(rs),clusters=len(diffs),mean=means,
            expected_brier_gain_over_reference=float(diffs.mean()),clustered_95_interval=np.quantile(boot,[.025,.975]).tolist(),
            reference=baseline,invalid=sum(not r['score']['valid'] for r in rs),zero_support=sum(r['score']['zero_support'] for r in rs),
            seconds=sum(r.get('seconds',0) for r in rs),prompt_tokens=sum((r.get('cost') or {}).get('prompt_eval_count',0) or 0 for r in rs))
    return output


def run(branch,split,root=RAW):
    from .views import install
    install()
    from .repair import verify
    from .model_study import ARMSETS,encounters
    sub=Path(root)/'repair-v1';out=sub/f'{branch}-ollama-{split}'
    population=read(sub/'fixture'/f'{split}-public.json')
    for i,u in enumerate(population):
        for q in encounters(branch,i):
            for arm in ARMSETS[branch]:
                for question in (['action','belief'] if branch=='M3' else ['action']):
                    if not (out/'calls'/f'{i:03d}-{q}-{arm}-{question}'/'COMPLETE.json').exists():
                        raise ValueError('audit refuses incomplete call; it cannot perform inference')
    verify(sub,branch,split)
    predictions=read(out/'PREDICTIONS.json');truth=read(sub/'fixture'/f'{split}-evaluator.json')
    public={u['unit']:u for u in read(sub/'fixture'/f'{split}-public.json')}
    keyed={(u['unit'],t['encounter']):t for u in truth for t in u['queries']}
    scored=[];cheap=[];seen=set()
    for r in predictions:
        t=keyed[(r['unit'],r['encounter'])];target,observed=target_for(r,t)
        scored.append(dict(r,score=measures(r['probabilities'],target,observed),target=target))
        key=(r['unit'],r['encounter'],r['question'])
        if key not in seen and r['arm'] in ('raw_history','raw_facts'):
            seen.add(key);u=public[r['unit']];obs=r['observation']
            if r['question']=='action':p=enumerate_predict(u['history'],obs)['probabilities']
            else:
                g,b=decode(obs);p=[float(k==b) for k in range(2)]
            cheap.append(dict(r,arm='exact_public_history',score=measures(p,target,observed),seconds=0,cost={}))
    baseline='raw_facts' if branch=='M4' else 'raw_history'
    result=summarize(scored+cheap,baseline)
    freeze(out/'SCORED.json',scored);freeze(out/'COMPARISON.json',result)
    return freeze(out/'AUDIT.json',dict(status='complete',rows=len(scored),predictions_sha256=digest(predictions),comparison_sha256=digest(result),
        invalid_policy='failure: Brier 2, modal accuracy 0, capped log loss -log(1e-12); retained in every denominator',
        log_policy='strict zero-support loss is infinite, serialized null with zero_support; capped losses explicitly secondary',
        counterfactual='maker-observation truth recomputed; no fabricated sampled counterfactual action',
        scope='one constructed family; clusters are maker/world histories; no human transfer or calibrated confidence'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--branch',required=True);p.add_argument('--split',required=True)
    a=p.parse_args();print(run(a.branch,a.split,a.root)['status'])
