"""Descriptive matched-writer history curves; no fitting or inference.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-3 read 2026-10-15.
NULL: constant writer gains yield zero matched changes despite composition shift.
ALTERNATIVE: planted within-writer changes survive matching. Missing support is
unestimable, not zero; malformed probabilities and duplicate decisions refuse.
"""
import argparse
import math
from collections import defaultdict
from statistics import mean
from runners.stage14.common import REPO, read, freeze, pins, check_pins, filehash, now

ROOT = REPO/'results/phase_2_4_stage_15/raw/history-texture-v1'
SOURCE = REPO/'results/phase_2_4_stage_15/raw/phase0-v1/T0c'
BINS = ((0,0),(1,9),(10,29),(30,99),(100,299),(300,10**9))
ARMS = ('B-pop','B-writer')


def curves(rows):
    """Rows contain a writer, history count and independently supplied gain."""
    groups = []
    for lo, hi in BINS:
        g = defaultdict(list)
        for r in rows:
            if lo <= r['history_decisions'] <= hi:
                g[r['writer']].append(r['gain'])
        groups.append(g)
    def describe(g, names):
        names = sorted(names)
        return dict(writers=len(names), decisions=sum(len(g[n]) for n in names),
                    mean_gain=mean(mean(g[n]) for n in names) if names else None)
    bins = [dict(bounds=list(b), **describe(g,g)) for b,g in zip(BINS,groups)]
    matched = []
    for i,(a,b) in enumerate(zip(groups,groups[1:])):
        common = sorted(set(a)&set(b))
        differences = [mean(b[w])-mean(a[w]) for w in common]
        loo = [(sum(differences)-d)/(len(differences)-1) for d in differences] if len(common)>1 else []
        matched.append(dict(early_bin=i,late_bin=i+1,early=describe(a,common),late=describe(b,common),
            difference=mean(differences) if differences else None,
            positive=sum(d>0 for d in differences),zero=sum(d==0 for d in differences),negative=sum(d<0 for d in differences),
            leave_one_writer_out_range=[min(loo),max(loo)] if loo else None))
    common = set.intersection(*(set(g) for g in groups))
    return dict(bins=bins,adjacent_matched=matched,balanced=[describe(g,common) for g in groups])


def loss(p,y):
    if len(p)!=4 or any(not math.isfinite(v) or v<0 for v in p) or abs(sum(p)-1)>1e-9:
        raise ValueError('invalid probabilities')
    p=[max(v,1e-8) for v in p];total=sum(p);p=[v/total for v in p]
    return .5*sum((v-int(i==y))**2 for i,v in enumerate(p))


def analyze(pred):
    if len({r['key'] for r in pred})!=len(pred):raise ValueError('duplicate decisions')
    out={}
    for subset in ('all','own_prompt_novel','global_prompt_novel'):
        selected=[r for r in pred if subset=='all' or r[subset]]
        out[subset]={}
        for arm in ARMS:
            scored=[]
            for r in selected:
                y=('accept','edit','dismiss','ignore').index(r['truth'])
                gain=loss(r['probabilities'][arm],y)-loss(r['probabilities']['B-mixlogit'],y)
                scored.append(dict(writer=r['writer'],history_decisions=r['history_decisions'],gain=gain))
            out[subset][arm]=curves(scored)
    return out


def prepare():
    sources=[SOURCE/n for n in ('COMPLETE.json','PREDICTIONS.json','FITS.json')]
    sources += [REPO/n for n in ('runners/next_round/history_texture.py','tests/test_next_round_addendum.py',
        'docs/design/stage-15/VALIDITY_EXPLORATION_ADDENDUM.md')]
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(sources),inference_calls=0,scientific_admission=False))


def run():
    plan=read(ROOT/'PLAN.json');check_pins(plan['pins'])
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    for n,h in read(SOURCE/'COMPLETE.json')['outputs'].items():
        if filehash(SOURCE/n)!=h:raise ValueError('prior output changed')
    summary=analyze(read(SOURCE/'PREDICTIONS.json'))
    freeze(ROOT/'SUMMARY.json',summary);check_pins(plan['pins'])
    freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={'SUMMARY.json':filehash(ROOT/'SUMMARY.json')},
        plan_sha256=filehash(ROOT/'PLAN.json'),scientific_admission=False,inference_calls=0))
    print('Complete saved-output history texture; independent verification required.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args()
    prepare() if a.action=='prepare' else run()
