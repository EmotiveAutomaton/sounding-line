"""Internal PSD2 binary checklist descriptions. No shame verdict or row-level output."""
import numpy as np
import pandas as pd

from .week7_status_v1 import joint_terms

PAIRS = ('Embarassment', 'Guilt')  # Source spelling.
COLUMNS = ('id', 'Pride', *PAIRS)


def describe(frame):
    if not frame.columns.is_unique or not set(COLUMNS).issubset(frame.columns):
        raise ValueError('Required checklist columns missing or duplicated')
    frame = frame.loc[:, list(COLUMNS)].copy()
    if frame['id'].isna().any():
        raise ValueError('Person key missing')
    for field in COLUMNS[1:]:
        frame[field] = pd.to_numeric(frame[field], errors='raise')
        if not frame[field].dropna().isin([0, 1]).all():
            raise ValueError('Checklist item outside binary range')
    panels = {}
    for item in PAIRS:
        terms = []
        complete_prompts = 0
        for _, group in frame.groupby('id', sort=True):
            pride = group['Pride'].to_numpy(dtype=float)
            other = group[item].to_numpy(dtype=float)
            complete_prompts += int((np.isfinite(pride) & np.isfinite(other)).sum())
            numerator, weight = joint_terms(pride, other, cut=1)
            if weight:
                terms.append((numerator, weight))
        people = len(terms)
        panel = dict(eligible_people=people, excluded_people=int(frame.id.nunique())-people,
                     pairwise_missing_prompts=len(frame)-complete_prompts,
                     eligible_prompts=int(sum(weight for _,weight in terms)))
        if people >= 20:
            values = np.asarray(terms)
            total = values.sum(axis=0)
            rng = np.random.default_rng(20261125)
            draws = []
            for _ in range(2000):
                indices = rng.integers(people, size=people)
                num, den = values[indices].sum(axis=0)
                draws.append(num/den)
            panel.update(ratio=float(total[0]/total[1]),
                         interval=np.percentile(draws, [2.5, 97.5]).tolist(),
                         bootstrap_se=float(np.std(draws,ddof=1)),draws=len(draws))
        panels[item] = panel
    return dict(people=int(frame.id.nunique()), prompts=len(frame), pairs=panels)

