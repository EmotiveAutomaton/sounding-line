"""Separate-block CRV1 timing on the Rosslund et al. derived tables.

DESIGN CHECK (2026-11-26)
Lessons read: LESSONS §2 on source units and roster coverage, §3 on falsifiable
controls, and §5 on tested entry points. Under the null, present timing values
in both registers with equal paired means give a zero difference. Under the
alternative, longer infant-directed vowels give a positive duration difference
and slower infant-directed articulation gives a negative rate difference.
Unpaired sessions cannot contribute in either case. Changes to the units or
weights can create a false sign and are checked on invented unequal sessions.
Verdict bands per arm, exhaustive: above zero, below zero or including zero
(including endpoints); below the support floor, file the descriptive difference
where calculable. An empty paired sample has no estimate.
"""
from collections import Counter, defaultdict
import csv
import math
import numpy as np


def summarize(path, measure):
    duration = measure == 'vowel_ms'
    if not duration and measure != 'syllables_per_phonation_second':
        raise ValueError('Unexpected timing measure')
    required = {'id_parent','session','register'} | (
        {'vowel_dur'} if duration else {'phonation_time_ms','n_syllables'})
    by_session = defaultdict(list)
    seen = set()
    excluded = Counter()
    rows = 0
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader = csv.DictReader(f)
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError('Missing provider field')
        for row in reader:
            rows += 1
            parent, session, register = (row[k].strip() for k in ('id_parent','session','register'))
            if any(x.casefold() in {'','na','nan'} for x in (parent,session,register)):
                excluded['missing_key'] += 1
                continue
            register = register.upper()
            if register not in ('IDS','ADS'):
                raise ValueError('Unexpected register')
            seen.add((parent,session))
            try:
                length=float(row['vowel_dur' if duration else 'phonation_time_ms'])
                syllables=0.0 if duration else float(row['n_syllables'])
            except (TypeError,ValueError):
                excluded['missing_measure'] += 1
                continue
            if not math.isfinite(length) or length<=0 or not math.isfinite(syllables) or syllables<0 or not syllables.is_integer():
                excluded['invalid_measure'] += 1
                continue
            value=length if duration else 1000*syllables/length
            by_session[parent,session,register].append(value)
    differences=defaultdict(list)
    for parent,session in sorted(seen):
        infant=by_session.get((parent,session,'IDS'))
        adult=by_session.get((parent,session,'ADS'))
        if infant and adult:
            differences[parent].append(float(np.mean(infant)-np.mean(adult)))
    values=np.array([np.mean(differences[p]) for p in sorted(differences)])
    pairs=sum(map(len,differences.values()))
    retained=sum(map(len,by_session.values()))
    if rows!=retained+sum(excluded.values()):
        raise ValueError('Row accounting differs')
    result=dict(rows=rows,valid_rows=retained,excluded=dict(excluded),sessions=len(seen),
                paired_sessions=pairs,unpaired_sessions=len(seen)-pairs,people=len(values),
                mean=float(values.mean()) if len(values) else None,interval=None)
    if len(values)>=20:
        rng=np.random.default_rng(20261125)
        draws=values[rng.integers(len(values),size=(2000,len(values)))].mean(axis=1)
        result['interval']=np.percentile(draws,[2.5,97.5]).tolist()
    return result
