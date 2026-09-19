"""Executable mismatch route: distinguish adding a candidate from reweighting.

DESIGN CHECK: LESSONS 3-5. NULL: stochastic lapses can trigger false additions;
ALTERNATIVE: a missing trained policy can be added after public counterevidence.
Pre-observation forecasts stay immutable; full four-policy Bayes remains rival.
"""
import argparse
from pathlib import Path
from .common import RAW,digest,freeze,read,source_pins
from .world import decode,distribution,enumerate_predict,POLICIES
from .consumer import measures,summarize


def reconstruct(history,mode):
    weights=[.25]*4 if mode=='full' else [.5,0.,.5,0.]
    versions=[]
    for event in history:
        obs=event['observation'];before=enumerate_predict([],obs,weights)['probabilities']
        probability=before[event['action']];added=[];prior=list(weights)
        if mode=='revision' and probability<.04 and any(w==0 for w in weights):
            absent=[i for i,w in enumerate(weights) if w==0]
            weights=[.2/len(absent) if i in absent else .8*w for i,w in enumerate(weights)];added=absent
        after=enumerate_predict([event],obs,weights)['weights']
        versions.append(dict(sequence=event['sequence'],before_prediction=before,before_weights=prior,
            observation=event,observed_probability=probability,mismatch=probability<.04,added_candidates=added,
            after_weights=after,state_status='inferred hypotheses, not observed traits'))
        weights=after
    return weights,versions


def predict(public):
    rows=[]
    for u in public:
        for mode in ['full','restricted','revision']:
            weights,versions=reconstruct(u['history'],mode)
            for q in u['queries']:
                pred=enumerate_predict([],q['observation'],weights)
                rows.append(dict(unit=u['unit'],cluster=u['cluster'],encounter=q['encounter'],arm=mode,question='action',
                    probabilities=pred['probabilities'],latent=pred['latent'],versions=versions))
    return rows


def run(split,root=RAW):
    root=Path(root);out=root/'M0-revision'/split;public=read(root/'fixture'/f'{split}-public.json')
    if not (out/'SOURCE.json').exists():freeze(out/'SOURCE.json',source_pins())
    rows=predict(public);freeze(out/'PREDICTIONS.json',rows)
    truth=read(root/'fixture'/f'{split}-evaluator.json');keyed={(u['unit'],q['encounter']):q for u in truth for q in u['queries']}
    scored=[]
    for r in rows:
        t=keyed[(r['unit'],r['encounter'])]
        scored.append(dict(r,score=measures(r['probabilities'],t['probabilities'],t['action'])))
    result=summarize(scored,'full');freeze(out/'COMPARISON.json',result)
    return freeze(out/'COMPLETE.json',dict(status='complete',split=split,rows=len(rows),
        predictions_sha256=digest(rows),comparison_sha256=digest(result),
        additions=sum(bool(v['added_candidates']) for r in rows if r['arm']=='revision' and r['encounter']==0 for v in r['versions']),
        scope='predeclared programmatic mismatch response; missing candidate added from fixed four-policy library, not open-ended discovery'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--split',choices=['dev','test'],required=True)
    a=p.parse_args();print(run(a.split,a.root)['status'])
