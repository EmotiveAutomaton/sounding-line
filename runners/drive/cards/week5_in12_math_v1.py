"""IN12 fixed-scale writer-cluster regression and declared paired-report secondary.

No participant data or item identities are included in results. Production uses
cluster sufficient statistics; replay uses a separate weighted row-level solve.
"""
import numpy as np
import pandas as pd

NEGATIVE = ('anger', 'disgust', 'fear', 'guilt', 'sadness', 'shame')
POSITIVE = ('joy', 'pride')
STYLE = ('suddenness', 'familiarity', 'predict_event', 'goal_relevance',
         'chance_responsblt', 'self_responsblt', 'chance_control', 'attention', 'effort')


def item_score(anxious, calm):
    a, c = np.asarray(anxious, float), np.asarray(calm, float)
    if not (np.isfinite(a).all() and np.isfinite(c).all() and
            ((a >= 1) & (a <= 7) & (c >= 1) & (c <= 7)).all()):
        raise ValueError('Only documented 1-to-7 emotional-stability items')
    return (a+8-c)/2


def fixed_table(frame, independent=False):
    frame = frame.loc[frame.N.notna()].copy().sort_values('text_id').reset_index(drop=True)
    frame['response_style'] = frame[list(STYLE)].mean(axis=1)
    frame['intensity_z'] = np.nan; scales = {}
    for prompt, indexes in frame.groupby('emotion', sort=True).groups.items():
        y = frame.loc[indexes, 'intensity'].to_numpy(float)
        if independent:
            mean = sum(float(v) for v in y)/len(y)
            sd = (sum((float(v)-mean)**2 for v in y)/(len(y)-1))**.5 if len(y) > 1 else 0.
        else:
            mean = float(y.mean()); sd = float(y.std(ddof=1)) if len(y) > 1 else 0.
        scales[prompt] = {'rows': len(y), 'mean': mean, 'SD': sd, 'usable': sd > 1e-12}
        if sd > 1e-12:
            frame.loc[indexes, 'intensity_z'] = (y-mean)/sd
    return frame, scales


def design(frame, prompts):
    part = frame.loc[frame.emotion.isin(prompts)].copy()
    if part.empty or not np.isfinite(part.intensity_z).all():
        return None
    present = sorted(part.emotion.unique())
    x = np.column_stack([np.ones(len(part)), part.N, part.confidence, part.response_style,
                         *[part.emotion.eq(k).astype(float) for k in present[1:]]])
    y = part.intensity_z.to_numpy(float); people = part.prolific_id.to_numpy(str)
    keys, code = np.unique(people, return_inverse=True)
    xx = np.zeros((len(keys), x.shape[1], x.shape[1])); xy = np.zeros((len(keys), x.shape[1]))
    np.add.at(xx, code, x[:, :, None]*x[:, None, :]); np.add.at(xy, code, x*y[:, None])
    return {'x': x, 'y': y, 'people': people, 'keys': keys, 'xx': xx, 'xy': xy,
            'rows': len(y), 'prompts': present}


def slope(panel, counts, independent=False):
    if panel is None:
        return None, 'missing or constant outcome'
    if independent:
        w = np.array([counts.get(k, 0) for k in panel['people']], float)
        use = w > 0
        x = panel['x'][use]*np.sqrt(w[use, None]); y = panel['y'][use]*np.sqrt(w[use])
        if len(y) < x.shape[1]:
            return None, 'rank deficient'
        beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=1e-11)
        if rank != x.shape[1]:
            return None, 'rank deficient'
    else:
        w = np.array([counts.get(k, 0) for k in panel['keys']], float)
        gram = np.einsum('n,nij->ij', w, panel['xx']); rhs = np.einsum('n,ni->i', w, panel['xy'])
        if np.linalg.matrix_rank(gram, tol=1e-9) != gram.shape[0]:
            return None, 'rank deficient'
        beta = np.linalg.solve(gram, rhs)
    if not np.isfinite(beta).all():
        return None, 'nonfinite estimate'
    return float(beta[1]), None


def pair_rows(frame):
    """Equal writer weights over distinct-prompt mean intensity pairs."""
    means = frame.groupby(['prolific_id', 'emotion'], sort=True).intensity_z.mean()
    nn, npairs = [], []; eligible = 0
    for person in sorted(frame.prolific_id.unique()):
        values = means.loc[person].to_dict()
        negative = [values[k] for k in NEGATIVE if k in values and np.isfinite(values[k])]
        positive = [values[k] for k in POSITIVE if k in values and np.isfinite(values[k])]
        if len(negative) < 2:
            continue
        eligible += 1
        pairs = [(a, b) for i, a in enumerate(negative) for j, b in enumerate(negative) if i != j]
        nn.extend((person, a, b, 1/len(pairs)) for a, b in pairs)
        cross = [(a, b) for a in negative for b in positive]
        npairs.extend((person, a, b, 1/len(cross)) for a, b in cross)
    return nn, npairs, eligible


def correlation(rows, counts, independent=False):
    if not rows:
        return None
    w = np.array([r[3]*counts.get(r[0], 0) for r in rows]); total = w.sum()
    if total <= 0:
        return None
    x = np.array([r[1] for r in rows]); y = np.array([r[2] for r in rows])
    if independent:
        mx = sum(float(a*b) for a, b in zip(w, x))/total
        my = sum(float(a*b) for a, b in zip(w, y))/total
        cov = sum(float(a*(b-mx)*(c-my)) for a, b, c in zip(w, x, y))
        vx = sum(float(a*(b-mx)**2) for a, b in zip(w, x))
        vy = sum(float(a*(b-my)**2) for a, b in zip(w, y))
    else:
        dx = x-np.dot(w, x)/total; dy = y-np.dot(w, y)/total
        cov = np.dot(w, dx*dy); vx = np.dot(w, dx*dx); vy = np.dot(w, dy*dy)
    return float(cov/np.sqrt(vx*vy)) if vx > 1e-12 and vy > 1e-12 else None


def prepare(frame, independent=False):
    table, scales = fixed_table(frame, independent)
    panels = {'pooled': design(table, NEGATIVE)}
    panels.update({k: design(table, (k,)) for k in (*NEGATIVE, *POSITIVE)})
    pairs = pair_rows(table)
    return {'panels': panels, 'pairs': pairs, 'keys': sorted(table.prolific_id.unique()), 'scales': scales}


def evaluate(prepared, counts, independent=False):
    values, failures = {}, {}
    for name, panel in prepared['panels'].items():
        try:
            value, reason = slope(panel, counts, independent)
        except np.linalg.LinAlgError:
            value, reason = None, 'numerical linear algebra failure'
        values[name] = value
        if reason:
            failures[name] = reason
    if all(values[k] is not None for k in ('pooled', *NEGATIVE)):
        values['spread'] = float(np.sqrt(sum((values[k]-values['pooled'])**2 for k in NEGATIVE)/6))
    else:
        values['spread'] = None; failures['spread'] = 'all six slopes and pooled slope required'
    nn, cross, eligible = prepared['pairs']
    if eligible >= 300:
        supports = [len({r[0] for r in rows if counts.get(r[0], 0) > 0}) for rows in (nn, cross)]
        a = correlation(nn, counts, independent) if min(supports) >= 2 else None
        b = correlation(cross, counts, independent) if min(supports) >= 2 else None
        values['within_writer_correlation_difference'] = a-b if a is not None and b is not None else None
        if values['within_writer_correlation_difference'] is None:
            failures['within_writer_correlation_difference'] = 'paired intensity variance/support absent'
    return {'value': values, 'failures': failures}


def resample(keys, draw):
    rng = np.random.default_rng(np.random.SeedSequence([20261113, 12, draw]))
    counts = np.bincount(rng.integers(0, len(keys), len(keys)), minlength=len(keys))
    return dict(zip(keys, counts, strict=True))


def interval_se(values, independent=False):
    if independent:
        ordered = sorted(float(v) for v in values)
        def quantile(p):
            location = (len(ordered)-1)*p; lo = int(location); hi = min(lo+1, len(ordered)-1)
            return ordered[lo]+(location-lo)*(ordered[hi]-ordered[lo])
        mean = sum(ordered)/len(ordered)
        return [quantile(.025), quantile(.975)], (sum((v-mean)**2 for v in ordered)/(len(ordered)-1))**.5
    return np.quantile(values, [.025, .975]).tolist(), float(np.std(values, ddof=1))
