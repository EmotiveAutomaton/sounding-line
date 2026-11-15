"""IN14 pair construction and writer-intercept carry-over fit.

DESIGN CHECK: LESSONS 2/3, CONTROLS 6/7. Pair before exclusion; never bridge a
missing survey. A decaying 0.5 plant has mean 0.372883 at gaps 2..10; zero stays
zero. Writer demeaning is checked against an explicit dummy-variable solve.
"""
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

NEGATIVE = ('anger', 'boredom', 'disgust', 'fear', 'guilt', 'sadness', 'shame')
POSITIVE = ('joy', 'pride', 'relief', 'trust')
FEELINGS = (*NEGATIVE, *POSITIVE)
PRIOR = (*FEELINGS, 'surprise')
TERMS = ('baseline', 'prompt', 'same_valence', 'second_prompt')


def timestamp(value):
    """Honor the source's explicit numeric-equivalent CET/EET labels."""
    clock, zone = str(value).rsplit(' ', 1)
    if zone not in ('CET', 'EET'):
        raise ValueError('Undocumented timestamp zone')
    return datetime.strptime(clock, '%Y/%m/%d %I:%M:%S %p').replace(
        tzinfo=timezone(timedelta(hours={'CET': 1, 'EET': 2}[zone]))).astimezone(timezone.utc)


def pairs(frame, eligible_rounds):
    required = {'text_id', 'prolific_id', 'emotion', 'timestamp', 'round_number', *PRIOR}
    if not required.issubset(frame) or frame.text_id.duplicated().any():
        raise ValueError('Complete uniquely keyed survey frame required')
    data = frame.copy(); data['_time'] = data.timestamp.map(timestamp)
    if not data.round_number.str.fullmatch(r'round-[2-9]').all():
        raise ValueError('Unreviewed questionnaire round')
    data['_round'] = data.round_number.str.extract(r'(\d+)$')[0].astype(int)
    counts = dict.fromkeys(('first_record', 'ineligible_round', 'unqualified', 'same_prompt',
                            'first_prompt_set_aside', 'nonpositive_gap', 'retained'), 0)
    records = []
    for person, group in data.groupby('prolific_id', sort=True):
        group = group.sort_values(['_time', '_round', 'text_id'])
        if (group._round.diff().dropna() < 0).any():
            raise ValueError('Timestamp order contradicts round order')
        counts['first_record'] += 1
        raw = group.to_dict('records')
        for pair_ordinal, (a, b) in enumerate(zip(raw, raw[1:])):
            gap = (b['_time']-a['_time']).total_seconds()/60
            reason = ('nonpositive_gap' if gap <= 0 else
                      'ineligible_round' if a['round_number'] not in eligible_rounds or b['round_number'] not in eligible_rounds else
                      'unqualified' if not a.get('source_qualified', True) or not b.get('source_qualified', True) else
                      'same_prompt' if a['emotion'] == b['emotion'] else
                      'first_prompt_set_aside' if a['emotion'] not in FEELINGS else 'retained')
            counts[reason] += 1
            if reason != 'retained':
                continue
            valence = NEGATIVE if a['emotion'] in NEGATIVE else POSITIVE
            for feeling in FEELINGS:
                x, y = float(a[feeling]), float(b[feeling])
                if not np.isfinite([x, y]).all() or not (1 <= x <= 5 and 1 <= y <= 5):
                    raise ValueError('Current-state rating outside documented 1..5')
                records.append({'prolific_id': person, 'pair_id': a['text_id']+':'+b['text_id'],
                    'first_text_id': a['text_id'], 'second_text_id': b['text_id'], 'raw_pair_ordinal': pair_ordinal,
                    'first_prompt': a['emotion'], 'second_prompt_label': b['emotion'],
                    'second_round': b['round_number'], 'feeling': feeling, 'gap_minutes': gap,
                    'baseline': x, 'outcome': y, 'prompt': float(feeling == a['emotion']),
                    'same_valence': float(feeling in valence and feeling != a['emotion']),
                    'second_prompt': float(feeling == b['emotion']),
                    'first_intensity': a.get('intensity'), 'second_intensity': b.get('intensity'),
                    'first_duration': a.get('emotion_duration_rank'), 'N': a.get('N')})
    return pd.DataFrame(records), counts


def design(frame, terms=TERMS):
    if frame.empty:
        return None
    x = frame[list(terms)].to_numpy(float); y = frame.outcome.to_numpy(float)
    keys, codes = np.unique(frame.prolific_id.to_numpy(str), return_inverse=True)
    blocks = []; raw_blocks = []
    for i, key in enumerate(keys):
        use = codes == i; a = x[use]; b = y[use]
        raw_blocks.append((key, a.copy(), b.copy()))
        a = a-a.mean(axis=0); b = b-b.mean()
        blocks.append((key, a, b))
    return {'blocks': blocks, 'raw_blocks': raw_blocks, 'terms': list(terms), 'keys': keys.tolist(), 'rows': len(frame)}


def fit(panel, counts=None, independent=False):
    if panel is None:
        return None, 'no eligible rows'
    counts = dict.fromkeys(panel['keys'], 1) if counts is None else counts
    input_blocks = panel['raw_blocks'] if independent else panel['blocks']
    blocks = [(k, a, b, int(counts.get(k, 0))) for k, a, b in input_blocks if counts.get(k, 0) > 0]
    p = len(panel['terms'])
    if not blocks:
        return None, 'no sampled writers'
    if independent:
        # Explicit intercept columns on original rows independently check demeaning.
        n = sum(len(b) for _, _, b, _ in blocks)
        x = np.zeros((n, p+len(blocks))); y = np.empty(n); offset = 0
        for j, (_, a, b, w) in enumerate(blocks):
            sl = slice(offset, offset+len(b)); x[sl, :p] = a*np.sqrt(w)
            x[sl, p+j] = np.sqrt(w); y[sl] = b*np.sqrt(w); offset += len(b)
        beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=1e-11)
        if rank != x.shape[1]:
            return None, 'rank deficient'
        beta = beta[:p]
    else:
        xx = sum(w*(a.T@a) for _, a, b, w in blocks)
        xy = sum(w*(a.T@b) for _, a, b, w in blocks)
        if np.linalg.matrix_rank(xx, tol=1e-9) != p:
            return None, 'rank deficient'
        beta = np.linalg.solve(xx, xy)
    if not np.isfinite(beta).all():
        return None, 'nonfinite estimate'
    answer = dict(zip(panel['terms'], map(float, beta)))
    if 'prompt' in answer and 'same_valence' in answer:
        answer['shape_minus_mood'] = answer['prompt']-answer['same_valence']
    return answer, None


def prepare(frame):
    panels = {'under10': design(frame.loc[frame.gap_minutes < 10]) if not frame.empty else None,
              '10to60': design(frame.loc[frame.gap_minutes.ge(10) & frame.gap_minutes.lt(60)]) if not frame.empty else None,
              '60plus': design(frame.loc[frame.gap_minutes.ge(60)]) if not frame.empty else None}
    if not frame.empty:
        for value, part in frame.groupby('first_intensity', sort=True):
            panels[f'intensity_{value:g}'] = design(part.loc[part.gap_minutes < 10])
        for value, part in frame.groupby('first_duration', sort=True):
            panels[f'duration_rank_{value:g}'] = design(part.loc[part.gap_minutes < 10])
        # One row per pair, measuring the second prompt's own prior rating.
        same = ((frame.first_prompt.isin(NEGATIVE) & frame.second_prompt_label.isin(NEGATIVE)) |
                (frame.first_prompt.isin(POSITIVE) & frame.second_prompt_label.isin(POSITIVE)))
        reach = frame.loc[same & frame.second_prompt.eq(1)].copy()
        reach['increase'] = reach.outcome-reach.baseline
        reach['outcome'] = reach.second_intensity
        terms = ['increase', 'baseline']
        for index, prompt in enumerate(sorted(reach.second_prompt_label.unique())[1:]):
            column = f'second_prompt_intercept_{index}'
            reach[column] = reach.second_prompt_label.eq(prompt).astype(float); terms.append(column)
        panels['same_valence_reach'] = design(reach, terms)
    return panels


def person_preparation(frame, independent=False):
    """Private per-writer fits only; no unvalidated corrected reliability output."""
    rows=[]
    if frame.empty: return rows
    for writer,part in frame.loc[frame.gap_minutes < 10].groupby('prolific_id',sort=True):
        pair_ids=list(dict.fromkeys(part.pair_id))
        if len(pair_ids)<4: continue
        whole,reason=fit(design(part),independent=independent);half=[]
        for ids in (pair_ids[:len(pair_ids)//2],pair_ids[len(pair_ids)//2:]):
            value,error=fit(design(part.loc[part.pair_id.isin(ids)]),independent=independent)
            half.append({'prompt':value['prompt'] if value else None,'failure':error})
        left=part.loc[part.pair_id.isin(pair_ids[:len(pair_ids)//2])]
        right=part.loc[part.pair_id.isin(pair_ids[len(pair_ids)//2:])]
        boundary=set(left.first_text_id)|set(left.second_text_id)
        overlap=boundary & (set(right.first_text_id)|set(right.second_text_id))
        rows.append({'prolific_id':writer,'pairs':len(pair_ids),'prompt':whole['prompt'] if whole else None,
                     'failure':reason,'halves':half,'halves_share_survey':bool(overlap),
                     'N':None if part.N.isna().all() else float(part.N.dropna().iloc[0])})
    return rows


def evaluate(panels, counts, independent=False):
    result, failures = {}, {}
    for name, panel in panels.items():
        try:
            value, reason = fit(panel, counts, independent)
        except np.linalg.LinAlgError:
            value, reason = None, 'numerical linear algebra failure'
        result[name] = value
        if reason:
            failures[name] = reason
    return {'value': result, 'failures': failures}
