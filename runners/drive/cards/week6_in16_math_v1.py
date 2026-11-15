"""IN16 conditional random-intercept share and matched-IN12 clearing units.

DESIGN CHECK: LESSONS 2/3, CONTROLS 6/7. REML conditional share must recover a
0.20 plant within 0.03; clearing recovers 0.2 and zero. Independent replay
inverts each writer covariance block; production uses sufficient statistics.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from . import week5_in as original
from . import week5_in12_math_v1 as in12


def fixed_table(frame):
    table = frame.copy().sort_values('text_id').reset_index(drop=True)
    table['response_style'] = table[list(in12.STYLE)].mean(axis=1)
    mask = table.N.notna() & table.emotion_duration_rank.notna() & table.event_duration_rank.notna()
    table['clearing_eligible'] = mask
    scales = {}
    for field in ('emotion_duration_rank', 'intensity'):
        table[field+'_z'] = np.nan
        for prompt, idx in table.loc[mask].groupby('emotion', sort=True).groups.items():
            x = table.loc[idx, field].to_numpy(float); sd = float(x.std(ddof=1)) if len(x)>1 else 0.
            scales[field+':'+prompt] = {'mean': float(x.mean()), 'SD': sd, 'rows': len(x)}
            if sd > 1e-12:
                table.loc[idx, field+'_z'] = (x-x.mean())/sd
    n = table.loc[mask, ['prolific_id', 'N']].drop_duplicates()
    if n.prolific_id.duplicated().any():
        raise ValueError('Conflicting writer trait scores')
    n_sd = float(n.N.std(ddof=1)) if len(n)>1 else 0.
    return table, scales, n_sd


def matrix(frame, columns, outcome):
    if frame.empty:
        return None
    labels = sorted(frame.emotion.unique())
    x = np.column_stack([np.ones(len(frame)), frame[columns].to_numpy(float),
                         *[frame.emotion.eq(k).to_numpy(float) for k in labels[1:]]])
    y = frame[outcome].to_numpy(float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        return None
    blocks = []
    people = frame.prolific_id.to_numpy(str)
    for key in sorted(set(people)):
        a = x[people == key]; b = y[people == key]
        blocks.append({'key': key, 'x': a, 'y': b, 'n': len(b), 'xx': a.T@a,
                       'xy': a.T@b, 'yy': float(b@b), 'sx': a.sum(0), 'sy': float(b.sum())})
    return {'blocks': blocks, 'p': x.shape[1], 'rows': len(y), 'prompts': labels,
            'keys': [b['key'] for b in blocks]}


def prepare(frame):
    table, scales, n_sd = fixed_table(frame)
    clearing = table.loc[table.clearing_eligible]
    counts = table.groupby('prolific_id').size()
    share = table.loc[table.prolific_id.isin(counts[counts >= 3].index)]
    return {'clearing': matrix(clearing, ['N', 'intensity_z', 'event_duration_rank', 'response_style'], 'emotion_duration_rank_z'),
            'share': matrix(share, list(original.APPRAISALS), 'intensity'), 'scales': scales,
            'N_writer_SD': n_sd, 'keys': sorted(table.prolific_id.unique()),
            'support': {'no_emotion_duration': int(table.no_emotion_reported.sum()),
                        'missing_or_conflicting_personality': int(table.N.isna().sum()),
                        'clearing_rows': len(clearing), 'share_rows': len(share),
                        'share_writers': share.prolific_id.nunique()}}


def clearing(panel, counts, independent=False):
    if panel is None:
        return None, 'missing or constant clearing input'
    blocks = [(b, int(counts.get(b['key'], 0))) for b in panel['blocks'] if counts.get(b['key'], 0)>0]
    if not blocks:
        return None, 'no sampled writers'
    if independent:
        x = np.concatenate([b['x']*np.sqrt(w) for b, w in blocks]); y = np.concatenate([b['y']*np.sqrt(w) for b,w in blocks])
        beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=1e-11)
        if rank != panel['p']:
            return None, 'rank deficient'
    else:
        a = sum(w*b['xx'] for b,w in blocks); b = sum(w*b['xy'] for b,w in blocks)
        if np.linalg.matrix_rank(a, tol=1e-9) != panel['p']:
            return None, 'rank deficient'
        beta = np.linalg.solve(a,b)
    return float(beta[1]), None


def writer_share(panel, counts, independent=False):
    """REML random writer intercept, share=tau2/(tau2+sigma2), boundary allowed."""
    if panel is None:
        return None, 'no writer-share support'
    blocks = [(b, int(counts.get(b['key'], 0))) for b in panel['blocks'] if counts.get(b['key'],0)>0]
    n = sum(w*b['n'] for b,w in blocks); p=panel['p']
    if len(blocks)<2 or n <= p:
        return None, 'fewer than two independent writers or residual degrees of freedom'
    def objective(log_ratio):
        ratio = np.expm1(log_ratio)
        a=np.zeros((p,p)); rhs=np.zeros(p); yy=0.; logdet=0.
        for block,w in blocks:
            size=block['n']
            if independent:
                covariance=np.eye(size)+ratio*np.ones((size,size))
                ivx=np.linalg.solve(covariance,block['x']); ivy=np.linalg.solve(covariance,block['y'])
                a += w*(block['x'].T@ivx); rhs += w*(block['x'].T@ivy)
                yy += w*float(block['y']@ivy); logdet += w*np.linalg.slogdet(covariance)[1]
            else:
                shrink=ratio/(1+size*ratio)
                a += w*(block['xx']-shrink*np.outer(block['sx'],block['sx']))
                rhs += w*(block['xy']-shrink*block['sx']*block['sy'])
                yy += w*(block['yy']-shrink*block['sy']**2); logdet += w*np.log1p(size*ratio)
        if np.linalg.matrix_rank(a,tol=1e-9) != p:
            return np.inf
        sign, determinant=np.linalg.slogdet(a)
        residual=yy-float(rhs@np.linalg.solve(a,rhs))
        if sign<=0 or residual<=1e-12:
            return np.inf
        return float(logdet+determinant+(n-p)*np.log(residual/(n-p)))
    fit=minimize_scalar(objective,bounds=(0.,12.),method='bounded',options={'xatol':1e-9,'maxiter':200})
    if not fit.success or not np.isfinite(fit.fun):
        return None,'REML failed or rank deficient'
    zero=objective(0.)
    optimum=0. if zero <= fit.fun+1e-9 else float(fit.x)
    if optimum>=12.-1e-5:
        return None,'REML optimum reached fixed upper bracket'
    return float(-np.expm1(-optimum)),None


def evaluate(prepared, counts, independent=False):
    values={}; failures={}
    for name, function in [('clearing',clearing),('writer_share',writer_share)]:
        panel=prepared['clearing' if name=='clearing' else 'share']
        try:
            panel_counts=counts.get(name,counts)
            value,reason=function(panel,panel_counts,independent)
        except np.linalg.LinAlgError:
            value,reason=None,'numerical linear algebra failure'
        values[name]=value
        if reason: failures[name]=reason
    values['clearing_per_N_SD']=None if values['clearing'] is None else values['clearing']*prepared['N_writer_SD']
    return {'value':values,'failures':failures}
