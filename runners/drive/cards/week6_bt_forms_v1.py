"""Three commissioned diary forms with a shared bootstrap for their variance ratios."""
import numpy as np
import pandas as pd
from . import week6_person_ladder_v1 as ladder
from . import week6_person_slopes_v1 as op
from . import week6_br_v1 as br

def project(frame, events, feelings):
    """Events are graded distances from the scale floor. Missing stays missing."""
    people, ids = np.unique(frame.id.astype(str), return_inverse=True)
    days = frame.day.to_numpy(float)
    by_person = frame.day.groupby(ids)
    start, end = (by_person.transform(k).to_numpy() for k in ('min', 'max'))
    early, late = br.forms.gap_masks(days, start, end)
    scaled = {k: ladder.scale(frame[k], ids) for k in feelings}
    slopes = {}
    grades = {}
    for event, grade in events.items():
        indicator = np.where(np.isfinite(grade), grade > 0, np.nan)
        for feeling, values in scaled.items():
            name = event+'/'+feeling
            slopes[name] = (indicator, values)
            grades[name] = grade
    data = dict(n=len(people), ids=ids, feelings=scaled, slopes=slopes)
    return data, grades, (days > (start+end)/2).astype(int), np.where(early, 0, np.where(late, 1, -1))

def prepare(data, grades, half, gap, replay):
    usual = ladder.half_panel(data, half, replay)[0]
    separated = ladder.half_panel(data, gap, replay)[0]
    panels = {}
    for name, (_, y) in data['slopes'].items():
        panels[name] = dict(PST1=usual[name], PST4=br.graded_halves(data, grades[name], y, half, replay), PST5=separated[name])
    return panels

def fit(parts, weight, seed, guard):
    valid = np.isfinite(parts[0]['b']) & np.isfinite(parts[1]['b'])
    a, b = ladder.supported(parts, valid)
    n = int(valid.sum())
    if n < 2:
        return dict(people=n, reading='insufficient support')
    w = np.minimum(a[weight], b[weight])
    level = (a['L'], b['L'])
    spread = (a['S'], b['S'])
    use = bool(op.wpearson(w, *spread) >= .30)
    rng = np.random.default_rng(seed)
    chunks = []
    for start in range(0, 2001, 50):
        guard()
        batch = min(50, 2001-start)
        W = op.boot_counts(rng, n, batch-int(start==0))*w
        if start==0:
            W = np.vstack([w, W])
        raw, adj, _ = op.adjust(W, (a['b'],b['b']), [level, spread] if use else [level])
        mean = op.wmean(W, (a['b']+b['b'])/2)
        chunks.append(np.column_stack([raw, adj, mean]))
    raw, adj, mean = np.concatenate(chunks).T
    stat = lambda x:ladder.stat(x[0], x[1:])
    m, v = stat(mean), stat(adj)
    ratio = None
    if m['interval'] and m['interval'][0]*m['interval'][1]>0 and mean[0]!=0:
        with np.errstate(divide='ignore', invalid='ignore'):
            draws = np.divide(adj, np.square(mean), out=np.full_like(adj,np.nan), where=mean!=0)
        ratio = stat(draws)
    return dict(people=n, mean=m, raw=stat(raw), adjusted=v, variance_over_squared_mean=ratio,
                spread_selected=use, reading='stable' if v['interval'] and v['interval'][0]>0 else 'could not say')

def score(panels, member, guard):
    rows = {}
    for j, (name, forms) in enumerate(panels.items()):
        row = {key: fit(parts, 'sxx' if key=='PST4' else 'n1', [20261121,int(member),i,j],guard)
               for i,(key,parts) in enumerate(forms.items())}
        row['held'] = all(form['reading']=='stable' for form in row.values())
        rows[name] = row
    return rows

