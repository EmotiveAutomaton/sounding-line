"""Persistent exact hypotheses and equally informed reconstruction controls.

DESIGN CHECK: LESSONS 3–5. NULL: carry-state and full raw replay agree exactly;
ALTERNATIVE: smaller history can lose sufficient information, an efficiency result
distinct from better inference. Goal/reader-belief replacements must move only
their targeted factor. Scores are computed only after the whole prediction roster.
"""
from __future__ import annotations
import argparse
import copy
import math
from pathlib import Path
import time
from .common import RAW, canonical, digest, freeze, read, source_pins
from .world import POLICIES, decode, distribution, enumerate_predict, prepare

ARMS=['no_history','raw_history','persistent','other_maker','shuffled','bottleneck',
      'stale_goal','reader_belief','perspective','source_linked','wrong_context','corrected_context','duplicate_source']

def predict_all(public):
    rows=[]
    for i,unit in enumerate(public):
        donor=public[(i+1)%len(public)]
        start=time.perf_counter()
        fit=enumerate_predict(unit['history'],unit['queries'][0]['observation'])
        fit_seconds=time.perf_counter()-start
        for query in unit['queries']:
            obs=query['observation']; q=query['encounter']
            for arm in ARMS:
                start=time.perf_counter(); seen=copy.deepcopy(obs)
                history=unit['history']; prior=None
                if arm=='no_history': history=[]
                if arm in ('persistent','perspective','source_linked','corrected_context','duplicate_source'):
                    history=[]; prior=fit['weights']
                if arm=='other_maker': history=donor['history']
                if arm=='shuffled': history=list(reversed(history))
                if arm=='bottleneck': history=history[-2:]
                if arm=='stale_goal': seen['requested_item']=unit['queries'][0]['observation']['requested_item']
                if arm=='reader_belief' and seen['reader_only_notice'] is not None:
                    seen['last_notice_seen_by_maker']=seen['reader_only_notice']
                if arm=='wrong_context':
                    seen['tools']=[1-v for v in seen['tools']]
                # A sourced correction supersedes a wrong card; duplicate source IDs
                # are de-duplicated. These are executable construction controls, not LLMs.
                pred=enumerate_predict(history,seen,prior)
                rows.append(dict(unit=unit['unit'],cluster=unit['cluster'],encounter=q,arm=arm,
                    input_sha256=digest(dict(history=history,observation=seen,prior=prior)),
                    public_observation=seen, history_used=history, prior=prior, **pred,
                    elapsed_seconds=time.perf_counter()-start,
                    fit_seconds=fit_seconds if arm=='persistent' and q==0 else 0,
                    deployment_policy_evaluations=4*(len(history)+1),
                    semantics='exact finite Bayesian candidate probabilities; constructed model-correct family'))
    return rows

def semantic_replay(rows):
    for row in rows:
        inp=dict(history=row['history_used'],observation=row['public_observation'],prior=row['prior'])
        if digest(inp)!=row['input_sha256']: raise ValueError('prediction input changed')
        p=enumerate_predict(inp['history'],inp['observation'],inp['prior'])
        if any(p[k]!=row[k] for k in p): raise ValueError('saved executable prediction differs')
    return len(rows)

def metrics(pred, truth):
    values=pred['probabilities']; target=truth['probabilities']; chosen=truth['action']
    if len(values)!=4 or any(not math.isfinite(v) or v<0 for v in values) or abs(sum(values)-1)>1e-8:
        return dict(valid=False,log_loss=math.log(4),brier=.75,accuracy=0,expected_log_loss=math.log(4))
    return dict(valid=True,log_loss=-math.log(max(values[chosen],1e-12)),
        brier=sum((v-float(j==chosen))**2 for j,v in enumerate(values)),
        accuracy=float(max(range(4),key=values.__getitem__)==chosen),
        expected_log_loss=-sum(t*math.log(max(v,1e-12)) for t,v in zip(target,values)))

def compare(rows,truth):
    import numpy as np
    keyed={(u['unit'],q['encounter']):q for u in truth for q in u['queries']}
    if len(rows)!=len(keyed)*len(ARMS): raise ValueError('incomplete comparison')
    groups={a:{} for a in ARMS}; stats={a:[] for a in ARMS}
    for row in rows:
        m=metrics(row,keyed[(row['unit'],row['encounter'])]); stats[row['arm']].append(m)
        groups[row['arm']].setdefault(row['cluster'],[]).append(m['expected_log_loss'])
    out={}
    for arm in ARMS:
        baseline=groups['raw_history']; treatment=groups[arm]
        keys=sorted(baseline)
        differences=np.array([np.mean(baseline[k])-np.mean(treatment[k]) for k in keys])
        rng=np.random.default_rng(112)
        boot=differences[rng.integers(len(keys),size=(2000,len(keys)))].mean(axis=1)
        out[arm]=dict(n=len(stats[arm]),clusters=len(keys),
            mean={k:float(np.mean([r[k] for r in stats[arm]])) for k in stats[arm][0]},
            gain_over_raw_history=float(differences.mean()),
            clustered_95_interval=[float(x) for x in np.quantile(boot,[.025,.975])])
    return out

def run(root=RAW, split='dev'):
    root=Path(root); source=root/'fixture'; prepare(source)
    public=read(source/f'{split}-public.json')
    out=root/'M0-executable'/split
    if (out/'COMPLETE.json').exists():
        rows=read(out/'PREDICTIONS.json'); semantic_replay(rows)
        if compare(rows,read(source/f'{split}-evaluator.json'))!=read(out/'COMPARISON.json'):
            raise ValueError('saved comparison changed')
        return read(out/'COMPLETE.json')
    freeze(out/'SOURCE.json',source_pins())
    rows=predict_all(public); semantic_replay(rows)
    freeze(out/'PREDICTIONS.json',rows)
    # Evaluator is opened only once every prediction has been frozen.
    result=compare(rows,read(source/f'{split}-evaluator.json'))
    freeze(out/'COMPARISON.json',result)
    return freeze(out/'COMPLETE.json',dict(status='complete',split=split,rows=len(rows),
        predictions_sha256=digest(rows), comparison_sha256=digest(result),
        science_scope='exact programs in constructed model-correct family; not neural inference',
        chronology_control='order-invariant likelihood; negative control, not evidence against temporal updating',
        context_control='programmatically specified update discipline, not learned trust'))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,default=RAW)
    p.add_argument('--split',choices=['train','dev','test'],default='dev')
    a=p.parse_args(); print(run(a.root,a.split))
