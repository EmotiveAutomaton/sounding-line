"""Additive KP source mapping; private rows; no automatic source opening.

DESIGN CHECK: LESSONS 2,3,5. Full original D33 keys survive the join; each rider
has an explicit eligibility disposition. NULL/ALTERNATIVE use identical mapping.
Malformed chronology, surrogate splits and duplicate identities fail closed.
No within-delta keystrokes, future history, final-text survival filter, person
identity or missed sixth word is invented. Boundary ambiguity is counted.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from runners.stage9.coauthor import delta_ops, units, text_of
from .timing_revision_events import replay_revision_events
from .timing_d33 import cache_probability
from .timing_d33_supported_source import histories
from . import timing_d33_calibrated as d33
from .timing_p6 import gzread


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def personal_total_surprise(population_probability, personal_probability):
    if not (0 < population_probability <= 1 and 0 < personal_probability <= 1):
        raise ValueError('Unsupported personal or population probability')
    return -math.log(population_probability) + math.log(population_probability / personal_probability)


def delta_provenance(events):
    """User deletion operations in Unicode codepoints, with insertion ordinals.

    Individual contiguous delete operations, not sums of disjoint operations,
    meet the three-character threshold. Prompt/API text remains a separate
    provenance class. Equal timestamps retain observed event ordinal only.
    """
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('Initialization required')
    doc = units(events[0]['currentDoc']); owners = [None] * len(doc)
    deletions, exposure = [], []
    previous = -math.inf
    for ordinal, event in enumerate(events):
        stamp = float(event['eventTimestamp']) / 1000.
        if not math.isfinite(stamp) or stamp < previous:
            raise ValueError('Event chronology invalid')
        previous = stamp
        operations = delta_ops(event.get('textDelta'))
        is_user = event.get('eventSource') == 'user'
        if (event['eventName'] in ('suggestion-open', 'suggestion-reopen')
                or event['eventName'] == 'suggestion-select'
                and any('insert' in operation and operation['insert'] for operation in operations)):
            exposure.append(ordinal)
        out, provenance, position = [], [], 0
        for operation_index, operation in enumerate(operations):
            if 'insert' in operation:
                for char in operation['insert']:
                    u = units(char)
                    out.extend(u); provenance.extend([ordinal if is_user else None] * len(u))
                continue
            action = 'retain' if 'retain' in operation else 'delete'
            count = operation[action]
            if type(count) is not int or count < 0 or position + count > len(doc):
                raise ValueError('Invalid UTF16 extent')
            segment = doc[position:position + count]
            prior = owners[position:position + count]
            if action == 'retain':
                out.extend(segment); provenance.extend(prior)
            else:
                chars = text_of(segment)  # Refuses half-surrogate deletion.
                if is_user and len(chars) >= 3:
                    starts, offset = [], 0
                    for char in chars:
                        width = len(units(char))
                        if len(set(prior[offset:offset + width])) != 1:
                            raise ValueError('Character provenance disagrees')
                        starts.append(prior[offset]); offset += width
                    deletions.append({'ordinal': ordinal, 'operation_index': operation_index,
                                      'seconds': stamp, 'codepoints': len(chars),
                                      'typed_at_ordinals': starts})
            position += count
        out.extend(doc[position:]); provenance.extend(owners[position:])
        text_of(out)
        doc, owners = out, provenance
    return {'deletions': deletions, 'suggestion_ordinals': sorted(set(exposure)),
            'final_document': text_of(doc)}


def word_windows(words, events, *, personal_surprise):
    """All typed word occurrences, not merely the D33 scoring subset.

    A tied onset has no individual keypress ordering in the log. Such a focal
    or sixth-word boundary remains unsupported rather than being sorted into
    an invented within-delta order. A right-censored window is not a zero.
    """
    source = delta_provenance(events)
    typed = sorted((w for w in words if w['is_word']), key=lambda w: (w['ordinal'], w['index']))
    if len({w['index'] for w in typed}) != len(typed):
        raise ValueError('Duplicate typed occurrence')
    ties = Counter(w['ordinal'] for w in typed)
    out = {}
    for i, word in enumerate(typed):
        start = word['ordinal']; reasons = []
        close = typed[i + 6]['ordinal'] if i + 6 < len(typed) else None
        recent_suggestion = any(exposure <= start and
            sum(exposure <= w['ordinal'] <= start for w in typed) <= 5
            for exposure in source['suggestion_ordinals'])
        if recent_suggestion:
            reasons.append('within_five_typed_words_after_suggestion')
        if ties[start] > 1:
            reasons.append('focal_onset_order_ambiguous_within_delta')
        if close is None:
            reasons.append('sixth_following_word_not_observed')
        elif close <= start or ties[close] > 1:
            reasons.append('sixth_onset_order_ambiguous_within_delta')
        deletions = [d for d in source['deletions'] if start < d['ordinal'] < close] if close is not None else []
        earlier = any(any(o is not None and o < start for o in d['typed_at_ordinals']) for d in deletions)
        following = any(any(o is not None and o >= start for o in d['typed_at_ordinals']) for d in deletions)
        other = any(any(o is None for o in d['typed_at_ordinals']) for d in deletions)
        next_words = typed[i + 1:i + 4]
        continuation_reasons = [r for r in reasons if r != 'sixth_following_word_not_observed' and r != 'sixth_onset_order_ambiguous_within_delta']
        if len(next_words) != 3:
            continuation_reasons.append('three_following_words_not_observed')
        elif any(ties[w['ordinal']] > 1 or w['ordinal'] <= start for w in next_words):
            continuation_reasons.append('continuation_order_ambiguous_within_delta')
        elif any(w['index'] not in personal_surprise for w in next_words):
            continuation_reasons.append('continuation_personal_probability_unsupported')
        out[word['index']] = {'kp1_exclusions': reasons,
            'deletion': int(bool(deletions)) if not reasons else None,
            'deletion_earlier_typed': int(earlier) if not reasons else None,
            'deletion_word_or_following': int(following) if not reasons else None,
            'deletion_prompt_or_api': int(other) if not reasons else None,
            'deletion_mixed_typed_provenance': int(earlier and following) if not reasons else None,
            'continuation_exclusions': continuation_reasons,
            'continuation_surprise': (sum(personal_surprise[w['index']] for w in next_words) / 3.
                                      if not continuation_reasons else None)}
    return out


def prior_usage(target, lookup):
    """Earlier completed sessions only; typed P6 occurrences including revisions."""
    result = {}
    for session in sorted(lookup.values(), key=lambda s: (s['timestamp'], s['session'])):
        if session['writer'] != target['writer'] or not session['end_at'] < target['timestamp']:
            continue
        for word in session['words']:
            if not word['is_word']:
                continue
            stamp = float(word['seconds'])
            if not session['timestamp'] <= stamp <= session['end_at']:
                raise ValueError('Word clock outside authenticated session')
            count, last = result.get(word['token'], (0, -math.inf))
            result[word['token']] = (count + 1, max(last, stamp))
    return result


def add_recency(word, usage):
    if word['token'] not in usage:
        return {'kp3_exclusions': ['word_not_typed_in_earlier_completed_session']}
    count, last = usage[word['token']]
    hours = (float(word['seconds']) - last) / 3600.
    if count < 1 or not math.isfinite(hours) or hours < 0:
        raise ValueError('Invalid earlier use chronology')
    return {'log_earlier_count': math.log(count), 'log1p_hours_since_last_use': math.log1p(hours),
            'kp3_exclusions': []}


def load_authenticated(inputs, *, decisions):
    """Owner-only later source stage. This builder has NOT invoked this function.

    Explicit decision strings bind material packet interpretations. They are
    presently proposals, never interpreted as authority by this module.
    """
    expected = {'frozen_fit': 'exact_joint_D33_including_donor',
                'continuation': 'total_personal_surprisal',
                'window': 'logged_delta_strict_order_ambiguous_excluded',
                'deletion': 'user_contiguous_codepoint_delete_any_provenance'}
    if decisions != expected:
        raise ValueError('Owner-reviewed source decisions required')
    root = Path(inputs['d33_completion']).resolve().parent
    done, plan = read(root / 'COMPLETE.json'), read(root / 'PLAN.json')
    if (done.get('status') != 'COMPLETE' or done.get('fresh_process_verified') is not True
            or plan['module'] != 'runners.drive.cards.timing_d33_calibrated'):
        raise ValueError('Frozen complete D33 source required')
    for name in ('PLAN.json', 'output/DESIGN.json.gz', 'output/SUPPORTED_ROSTER.json',
                 'output/CALIBRATION.json', 'output/PRIMARY.json'):
        if done['outputs'][name] != digest(root / name):
            raise ValueError('Frozen D33 artifact changed: ' + name)
    source, old, _ = d33.load_source(plan['inputs'], plan['config'])
    roster = d33.select_population(old, source.saved)
    if roster != read(root / 'output/SUPPORTED_ROSTER.json'):
        raise ValueError('Frozen supported cohort differs')
    rows = gzread(root / 'output/DESIGN.json.gz')
    if {(r['session'], r['index']) for r in rows} != {tuple(k) for k in roster['retained_keys']}:
        raise ValueError('D33 row identities differ')
    tuning = read(root / 'output/CALIBRATION.json')
    frozen_fit = read(root / 'output/PRIMARY.json')['statistics']['point_fits']['primary']
    joined, dispositions = [], Counter()
    by_session = {}
    for row in rows:
        by_session.setdefault(row['session'], []).append(row)
    for sid in sorted(by_session):
        receipt = source.raw.session(sid)
        path = source.raw.root / source.raw.raw[sid]['path']
        if digest(path) != receipt['source_hashes']['raw']:
            raise ValueError('Source changed after authentication')
        with path.open(encoding='utf8') as stream:
            events = [json.loads(line) for line in stream]
        target = source.lookup[sid]; words = target['words']
        replay = replay_revision_events(events)
        projected = delta_provenance(events)
        if projected['final_document'] != replay['replay']['final_document']:
            raise ValueError('Independent provenance replay differs')
        counts, _ = histories(source.units['pair'][sid]['proof'], source.lookup)
        alpha = tuning[target['writer']]['alpha']['own']
        surprise = {}
        for word in words:
            p = word['population_probability']
            if word['is_word'] and p is not None and p > 0:
                mixture = (1 - alpha) * p + alpha * cache_probability(word, counts, p)
                surprise[word['index']] = personal_total_surprise(p, mixture)
        windows = word_windows(words, events, personal_surprise=surprise)
        usage = prior_usage(target, source.lookup)
        lookup = {w['index']: w for w in words}
        for row in by_session[sid]:
            word = lookup[row['index']]
            item = dict(row, **windows[row['index']], **add_recency(word, usage))
            joined.append(item)
            for key in ('kp1_exclusions', 'continuation_exclusions', 'kp3_exclusions'):
                dispositions.update(key + ':' + reason for reason in item[key])
    joined.sort(key=lambda r: (r['writer'], r['session'], r['index']))
    if len(joined) != len(rows):
        raise ValueError('Rider join lost original cohort rows')
    return {'rows': joined, 'frozen_fit': frozen_fit, 'coverage': roster['coverage'],
            'dispositions': dict(sorted(dispositions.items())), 'source_completion_sha256': digest(root / 'COMPLETE.json')}
