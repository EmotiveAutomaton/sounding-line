"""Descriptive B2 exposure/cohort texture; no inference upgrades.

DESIGN CHECK: LESSONS 3-5, CONTROLS 6-7. Equal histories give zero; signed
alternatives retain sign. Missing support is unsupported, not a null. Nested
selection and exposure are separated; five stable cards stop further work.
"""
from pathlib import Path
import numpy as np
from runners.stage14.common import read, freeze, filehash
from .moral_expectation import DIMS, WEIGHTS, expectation, intervals, load
from .moral_exposure import check_parents

GRID = tuple(range(4, 12))


def card(counts, k, draws):
    a = np.asarray(counts)
    if a.ndim != 3 or a.shape[1:] != (4, 2) or not len(a):
        raise ValueError('Invalid cohort shape')
    if type(k) is not int or k not in GRID or type(draws) is not int or draws < 32:
        raise ValueError('Invalid texture allocation')
    n, s = a[:, :, 0], a[:, :, 1]
    # Validate every original record, including those below this threshold.
    expectation(n, s, 3)
    selected = n.min(axis=1) >= k
    base = dict(k=k, original_fingerprints=len(a), eligible_fingerprints=int(selected.sum()),
                eligible_share=float(selected.mean()))
    if selected.sum() < 1000:
        return dict(base, status='unsupported', required=1000)
    n, s = n[selected], s[selected]
    probs = [expectation(n, s, e) for e in (k, 3, n.min(axis=1)[:, None])]
    v = np.column_stack([p @ WEIGHTS for p in probs])
    v = np.column_stack([v, v[:, 0] - v[:, 1]])
    stats, classes = intervals(v, draws, [(-1, 1)] * 3 + [(-2, 2)])
    return dict(base, status='complete', draws=draws, compression_classes=classes,
                contrasts=dict(zip(('fixed', 'three', 'minimum', 'fixed_minus_three'), stats)),
                rates={name:dict(zip(DIMS,p.mean(axis=0).tolist()))
                       for name,p in zip(('fixed','three','minimum'),probs)})


def family(counts, parent_point, parent_interval, draws, stop=True):
    halfwidth = (parent_interval[1] - parent_interval[0]) / 2
    if not np.isfinite([parent_point, *parent_interval]).all() or halfwidth <= 0:
        raise ValueError('Invalid frozen parent interval')
    rows, stable, reason = [], 0, None
    for k in GRID:
        if reason:
            rows.append(dict(k=k, status='not run', reason=reason))
            continue
        r = card(counts, k, draws)
        rows.append(r)
        if r['status'] == 'unsupported':
            reason = 'nested cohorts below support floor'
        else:
            distance=max(abs(r['contrasts'][key]['difference']-parent_point)
                         for key in ('fixed','three','minimum'))
            stable = stable + 1 if distance <= halfwidth else 0
            r.update(max_parent_distance=distance, consecutive_stable=stable)
            if stop and stable >= 5: reason='five consecutive stable texture cards'
    return dict(status='complete', cards=rows, parent_point=parent_point,
                parent_half_interval_width=halfwidth, stopping_enabled=stop,
                descriptive=True, claim_upgrade=False, descendants=[])


def fixtures():
    out={}
    for sign in (-1,0,1):
        a=np.tile([[12,6]]*4,(1200,1,1))
        if sign>0:a[:,:2,1]=0
        if sign<0:a[:,2:,1]=0
        out[str(sign)]=family(a,0.,[-.1,.1],64)
    assert all(r['contrasts']['fixed']['difference']>0 for r in out['1']['cards'])
    assert all(r['contrasts']['fixed']['difference']<0 for r in out['-1']['cards'])
    assert all(r['contrasts']['fixed']['difference']==0 for r in out['0']['cards'][:5])
    assert all(r['status']=='not run' for r in out['0']['cards'][5:])
    return out


def calculate(inputs, config):
    if config.get('constructed'):return fixtures()
    for item in inputs.values():
        if filehash(item['path'])!=item['sha256']:raise ValueError('Changed input')
    counts,subset=load(inputs['source']['path'])
    parent=read(inputs['parent']['path']);integrated=read(inputs['integrated']['path'])
    exposure=read(inputs['exposure']['path'])
    n,s=counts[:,:,0],counts[:,:,1]
    minimum=expectation(n,s,n.min(axis=1)[:,None]);three=expectation(n,s,3)
    reproduction=dict(status='complete',common_fingerprints=len(counts),
        original_subset_rates=dict(zip(DIMS,subset.mean(axis=0).tolist())),
        original_subset_difference=float((subset@WEIGHTS).mean()),
        minimum_rates=dict(zip(DIMS,minimum.mean(axis=0).tolist())),
        minimum=dict(difference=float((minimum@WEIGHTS).mean())))
    check_parents(reproduction,parent,integrated)
    assert dict(zip(DIMS,three.mean(axis=0).tolist()))==exposure['three_rates']
    assert abs(float((three@WEIGHTS).mean())-exposure['three']['difference'])<1e-14
    assert sum(exposure['minimum_count_histogram'].values())==len(counts)
    return family(counts,parent['primary']['difference'],parent['primary']['interval'],
                  config['draws'],stop=config.get('stopping',True))


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    freeze(output/'SCIENCE.json',calculate(inputs,config))
    return dict(status='complete',constructed=bool(config.get('constructed')))


def verify(output,inputs,config):
    assert calculate(inputs,config)==read(Path(output)/'SCIENCE.json')
    return dict(verified=True,complete_recalculation=True)
