"""LA5 timing formulas over already qualified numeric meeting tracks.

DESIGN CHECK: independent literal interval/count implementation; exact boundary
and distinct-speaker cases. A timing pattern is not proof of mockery or a target.
"""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import math
import re
import numpy as np
from . import week5_la_back_half as qualified

MARK = re.compile(r'(laugh|laughter|breath[- ]laugh|while[- ]laughing)', re.I)


def word_count(act):
    return sum(w.get('kind') == 'word' and not w.get('laugh', False)
               and not MARK.search(w.get('annotation', '')) for w in act['words'])


def word_windows(speech):
    all_starts, by_speaker = [], defaultdict(list)
    for row in speech:
        if not math.isfinite(row['start']) or not math.isfinite(row['end']) or row['end'] < row['start']:
            raise ValueError('Qualified word timing is invalid')
        all_starts.append(row['start']); by_speaker[row['speaker']].append(row['start'])
    return sorted(all_starts), {k: sorted(v) for k, v in by_speaker.items()}


def window_count(starts, low, high):
    return bisect_left(starts, high)-bisect_left(starts, low)


def events(acts, laughs, speech, metadata, independent=False):
    """One meeting at a time; raw text and raw identities never emitted."""
    counts = Counter(source_acts=len(acts), source_timed_words=len(speech))
    vocal = [e for e in laughs if e.get('label') == 'vocal']
    counts['nonvocal_marks_excluded'] = len(laughs)-len(vocal)
    vocal.sort(key=lambda e: (e['start'], e['end'], e['speaker']))
    if any(not math.isfinite(e['start']) or not math.isfinite(e['end']) or e['end'] < e['start'] for e in vocal):
        raise ValueError('Qualified laugh timing is invalid')
    laugh_starts = [e['start'] for e in vocal]
    starts, speakers = word_windows(speech); rows = []
    duration = float(metadata['duration'])
    for act in sorted(acts, key=lambda a: (a['start'], a['end'], a['speaker'], a['id'])):
        nwords = word_count(act)
        if nwords < 3:
            counts['acts_below_three_words'] += 1
            continue
        if not math.isfinite(act['start']) or not math.isfinite(act['end']) or act['end'] < act['start']:
            raise ValueError('Qualified act timing is invalid')
        if independent:
            hits = [e for e in vocal if act['end'] <= e['start'] <= act['end']+2 and e['speaker'] != act['speaker']]
        else:
            hits = [e for e in vocal[bisect_left(laugh_starts, act['end']):bisect_right(laugh_starts, act['end']+2)]
                    if e['speaker'] != act['speaker']]
        other_people = sorted({e['speaker'] for e in hits})
        if len(other_people) < 2:
            counts['acts_without_two_distinct_other_laughers'] += 1
            continue
        first, last = min(e['start'] for e in hits), max(e['start'] for e in hits)
        joined = any(e['speaker'] == act['speaker'] and first-1 <= e['start'] <= first+3 for e in vocal)
        before = (act['start']-60, act['start']); after = (last, last+60)
        if independent:
            bt = sum(before[0] <= w['start'] < before[1] for w in speech)
            bx = sum(before[0] <= w['start'] < before[1] and w['speaker'] == act['speaker'] for w in speech)
            at = sum(after[0] <= w['start'] < after[1] for w in speech)
            ax = sum(after[0] <= w['start'] < after[1] and w['speaker'] == act['speaker'] for w in speech)
        else:
            own = speakers.get(act['speaker'], [])
            bt, bx = window_count(starts, *before), window_count(own, *before)
            at, ax = window_count(starts, *after), window_count(own, *after)
        person = metadata['speakers'][act['speaker']].get('person')
        role = metadata['speakers'][act['speaker']].get('role') if metadata['corpus'] == 'AMI' else None
        edge = before[0] < 0 or after[1] > duration
        outcome = ax/at-bx/bt if at and bt else None
        eligible = bool(person is not None and outcome is not None and not edge)
        counts['candidate_events'] += 1; counts['joined_events' if joined else 'not_joined_events'] += 1
        counts['missing_global_person_events'] += person is None
        counts['zero_word_denominator_events'] += outcome is None
        counts['window_outside_observed_meeting_span_events'] += edge
        counts['model_eligible_events'] += eligible
        rows.append({'act': act['id'], 'meeting': act['meeting'], 'speaker': act['speaker'],
            'person': person, 'corpus': metadata['corpus'], 'role': role,
            'act_start': float(act['start']), 'act_end': float(act['end']), 'act_words': nwords,
            'other_laughers': len(other_people), 'first_other_laugh': float(first), 'last_other_laugh': float(last),
            'joined': bool(joined), 'before_total_words': bt, 'before_target_words': bx,
            'after_total_words': at, 'after_target_words': ax, 'outcome': outcome,
            'window_outside_observed_span': bool(edge), 'model_eligible': eligible})
    counts['exclusion_categories_may_overlap'] = True
    return rows, dict(counts)


def arrays(rows):
    selected = [r for r in rows if r['model_eligible']]
    if not selected:
        return None
    people = np.array([r['person'] for r in selected], str)
    meetings = np.array([r['meeting'] for r in selected], str)
    base = np.array([[not r['joined'], r['act_start']/60, r['act_words'], r['other_laughers']] for r in selected], float)
    x = np.column_stack((base, qualified.columns(meetings)))
    return x, np.array([r['outcome'] for r in selected], float), people, meetings


def estimate(prepared, multiplicities=None, universe=None):
    if prepared is None:
        return None
    x, y, people, meetings = prepared
    return qualified.scalar_speaker_fit(x, y, people, meetings, counts=multiplicities, universe=universe)


def dense_reference(prepared, multiplicities=None, universe=None):
    if prepared is None:
        return None
    x, y, people, meetings = prepared
    universe = sorted(set(meetings)) if universe is None else universe
    counts = np.ones(len(universe)) if multiplicities is None else np.asarray(multiplicities)
    lookup = dict(zip(universe, counts)); w = np.array([lookup[m] for m in meetings], float)
    keep = w > 0
    nuisance = np.column_stack((np.ones(len(x)), qualified.columns(people), x[:, 1:]))
    scale = np.sqrt(w[keep]); n = nuisance[keep]*scale[:, None]
    target, outcome = x[keep, 0]*scale, y[keep]*scale
    residual_x = target-n@np.linalg.lstsq(n, target, rcond=1e-12)[0]
    residual_y = outcome-n@np.linalg.lstsq(n, outcome, rcond=1e-12)[0]
    denominator = residual_x@residual_x
    if denominator <= 1e-10*max(1., target@target):
        return None
    return float((residual_x@residual_y)/denominator)


def uncertainty(values, independent=False):
    if not independent:
        return np.quantile(values, [.025, .975]).tolist(), float(np.std(values, ddof=1))
    ordered = sorted(map(float, values)); n = len(ordered); result = []
    for q in (.025, .975):
        location = q*(n-1); lo = int(location); fraction = location-lo
        result.append(ordered[lo]*(1-fraction)+ordered[min(lo+1, n-1)]*fraction)
    mean = sum(ordered)/n
    return result, math.sqrt(sum((v-mean)**2 for v in ordered)/(n-1))
