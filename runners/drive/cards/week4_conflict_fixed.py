"""S6.p writer fixed effects with the complete original paired inference.

DESIGN CHECK: LESSONS3-5 and CONTROLS1-7 read2026-11-04.
Known NULL/conflict-only own coefficients are zero; signed alternatives recover
unchanged. Exact writer offsets leave fixed slopes invariant. Collinear focal
terms and incomplete reference banks invalidate, never redraw. Native dense
dummy equivalence precedes full calibration and human cost admission.
"""
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read
from . import week4_conflict_stats as parent
from . import week4_conflict_inference as inference
from .timing_stats import sufficient


def fixed_fit(groups):
    centered=[]
    for g in groups:
        n=g['n']
        if n<2:raise ValueError('Writer has no within-unit support')
        centered.append(dict(n=n,xx=g['xx']-np.outer(g['sx'],g['sx'])/n,
            xy=g['xy']-g['sx']*g['sy']/n,yy=g['yy']-g['sy']**2/n,
            sx=np.zeros_like(g['sx']),sy=0.))
    keep,omitted=parent.basis(centered)
    xx=sum(g['xx'] for g in centered);xy=sum(g['xy'] for g in centered)
    a=xx[np.ix_(keep,keep)];b=xy[keep];scale=np.sqrt(np.maximum(np.diag(a),1e-30))
    normalized=a/np.outer(scale,scale)
    if np.linalg.matrix_rank(normalized,tol=1e-9)!=len(keep):
        raise ValueError('Within-writer design not identifiable')
    beta=np.linalg.solve(normalized,b/scale)/scale
    if not np.isfinite(beta).all() or not np.allclose(a@beta,b,atol=1e-7,rtol=1e-10):
        raise ValueError('Fixed-effects normal equations failed')
    coefficients={parent.NAMES[j]:float(beta[k]) for k,j in enumerate(keep)}
    return dict(own=coefficients['own_surprise'],coefficients=coefficients,
        omitted_columns=omitted,estimator='within-writer fixed effects')


def paired_fit(groups, unused_base_groups):
    a,b=fixed_fit(groups),parent.adjusted_fit(groups)
    return dict(adjusted_own=a['own'],original_own=b['own'],
        paired_difference=a['own']-b['own'],entropy=a['coefficients']['entropy'],
        negative_margin=a['coefficients']['negative_margin'],adjusted=a,original=b)


# Preserve the exact original streams and complete-bank invalidity handling.
# Its ten-column auxiliary groups are unused: the comparator is the full
# twelve-column random-intercept parent in paired_fit above.
run=parent.copied(parent.run,paired_fit=paired_fit,adjusted_fit=fixed_fit)


def dense_coefficients(rows):
    x,y,w=parent.design(rows);writers=sorted(set(w))
    columns=[j for j,n in enumerate(parent.NAMES) if n!='intercept']
    dummies=np.column_stack([w==name for name in writers]).astype(float)
    z=np.column_stack([x[:,columns],dummies])
    beta=np.linalg.lstsq(z,y,rcond=None)[0]
    return {parent.NAMES[j]:float(beta[k]) for k,j in enumerate(columns)}


def known_answers():
    result={}
    for name in parent.WORLDS:
        rows,truth=parent.world(name);x,y,w=parent.design(rows)
        value=fixed_fit(sufficient(x,y,w));dense=dense_coefficients(rows)
        for key,v in value['coefficients'].items():
            if abs(v-dense[key])>2e-8:raise ValueError('Dense dummy parity failed')
        for key in ('own_surprise','donor_surprise','entropy','negative_margin'):
            if abs(value['coefficients'][key]-truth[key])>2e-8:
                raise ValueError('Known fixed-effects coefficient failed')
        result[name]=dict(verified=True,dense_dummy_verified=True)
    return result


def configuration(mode):
    value=inference.configuration(mode)
    return dict(value,card='W4-S6.p-fixed-effects')


def human_rows(inputs,full=False):
    keys={'source_completion','parent_completion'}|({'calibration_completion','cost_completion'} if full else set())
    if set(inputs)!=keys:raise ValueError('Exact S6.p dependency bundle required')
    root=Path(inputs['parent_completion']).resolve().parent
    s=inference.authenticated(root);p=read(root/'PLAN.json')
    if p['module']!=inference.__name__ or p['config']!=inference.configuration('human-full') or s['state']!='complete':
        raise ValueError('Complete original parent required')
    if p['inputs']['source_completion']!=inputs['source_completion']:
        raise ValueError('Different parent source')
    rows=inference.human_rows({'source_completion':inputs['source_completion']})
    if full:
        for key,mode in [('calibration_completion','calibration-full'),('cost_completion','human-cost')]:
            root=Path(inputs[key]).resolve().parent;s=inference.authenticated(root);p=read(root/'PLAN.json')
            if p['module']!=__name__ or p['config']!=configuration(mode):raise ValueError('Wrong follow-up validation')
            if key=='calibration_completion' and not s['calibration_pass']:raise ValueError('Follow-up calibration did not pass')
            if key=='cost_completion' and p['inputs']!={k:inputs[k] for k in ('source_completion','parent_completion')}:
                raise ValueError('Follow-up cost used different source')
    return rows


_stats=SimpleNamespace(run=run,known_answers=known_answers,world=parent.world,WORLDS=parent.WORLDS)
one_pass=parent.copied(inference.one_pass,configuration=configuration,stats=_stats,human_rows=human_rows)


def execute(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config,True)
