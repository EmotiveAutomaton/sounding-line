"""Exact D33-to-final-document input join, before any engine score is read.

DESIGN CHECK: LESSONS 3-5 reread October18. Under either scientific null or
alternative, original D33 rows must be preserved, including non-survivors and
sessions outside an input pilot. An altered occurrence, duplicate key, false
typed provenance or nonfinite original covariate refuses the join. Deleted or
retyped lookalikes cannot become matches. Constructed known identities and a
fresh serialized process precede corpus use. This component neither scores
words nor admits a scientific comparison; callers authenticate source chains.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import math


ROW_FIELDS = frozenset(('writer', 'session', 'index', 'personal_surprise',
    'donor_surprise', 'population_surprisal', 'log_pause', 'length',
    'log_frequency', 'sentence_start', 'after_punctuation'))
DISPOSITIONS = ('outside-input-cohort', 'not-intact-final-word',
                'awaiting-engine-score')


def document_index(record):
    """Validate the serialized occurrence/provenance relationship, not its source."""
    document = record['document']
    keys, text = document['keys'], document['text']
    if (document['variant'] != 'final-document' or not isinstance(text, str)
            or not all(isinstance(keys.get(k), str) and keys[k]
                       for k in ('writer', 'session', 'prompt'))
            or hashlib.sha256(text.encode('utf8')).hexdigest() != document['textSha256']):
        raise ValueError('final document identity or bytes differ')
    spans, cursor = {}, 0
    for span in document['provenance']:
        a, b, identity = span['start'], span['end'], span['occurrenceId']
        if (type(a) is not int or type(b) is not int or a != cursor
                or not a < b <= len(text) or not isinstance(identity, str)
                or identity in spans
                or span['source'] not in ('typed', 'accepted', 'prompt', 'api_unknown')):
            raise ValueError('invalid final provenance partition')
        spans[identity] = span
        cursor = b
    if cursor != len(text):
        raise ValueError('incomplete final provenance partition')
    occurrences, identities, matched = {}, set(), set()
    for position, occurrence in enumerate(record['occurrences']):
        index, ids = occurrence['index'], occurrence['character_ids']
        if (type(index) is not int or index != position or type(occurrence['is_word']) is not bool
                or not isinstance(ids, list) or not ids
                or any(type(i) is not int or i < 0 for i in ids)
                or len(ids) != len(set(ids)) or tuple(ids) in identities):
            raise ValueError('invalid original occurrence identity')
        identities.add(tuple(ids))
        span = occurrence['final_codepoints']
        key = 'p6:' + str(index)
        if span is None:
            if occurrence['disposition'] != 'not-an-intact-final-token' or key in spans:
                raise ValueError('non-survivor has final provenance')
        else:
            if (not isinstance(span, list) or len(span) != 2
                    or any(type(v) is not int for v in span)
                    or not 0 <= span[0] < span[1] <= len(text)
                    or span[1] - span[0] != len(ids)
                    or occurrence['disposition'] != 'intact-final-token'):
                raise ValueError('invalid final occurrence span')
            provenance = spans.get(key)
            if (provenance is None or provenance['source'] != 'typed'
                    or [provenance['start'], provenance['end']] != span):
                raise ValueError('final occurrence lacks exact typed provenance')
            matched.add(key)
        occurrences[index] = occurrence
    if {k for k in spans if k.startswith('p6:')} != matched:
        raise ValueError('unmatched final production provenance')
    expected = dict(original_occurrences=len(occurrences),
        intact_final_occurrences=sum(o['final_codepoints'] is not None for o in occurrences.values()),
        original_words=sum(o['is_word'] for o in occurrences.values()),
        intact_final_words=sum(o['is_word'] and o['final_codepoints'] is not None for o in occurrences.values()))
    if record['support'] != expected:
        raise ValueError('occurrence support differs')
    return occurrences


def join_rows(rows, records):
    """Keep every original row and covariate, attaching only exact input identity.

    Both inputs must already be authenticated and source-replayed by the caller.
    Not-in-cohort is a pilot disposition, never a scientific exclusion. Surviving
    words still require an exact engine span/content-word join before analysis.
    """
    sessions = {}
    for record in records:
        occurrences = document_index(record)
        sid = record['document']['keys']['session']
        if sid in sessions:
            raise ValueError('duplicate input session')
        sessions[sid] = (record, occurrences)
    joined, seen = [], set()
    for row in rows:
        if (set(row) != ROW_FIELDS or type(row['index']) is not int or row['index'] < 0
                or not all(isinstance(row[k], str) and row[k] for k in ('writer', 'session'))
                or type(row['length']) is not int or row['length'] <= 0
                or any(type(row[k]) is not int or row[k] not in (0, 1)
                       for k in ('sentence_start', 'after_punctuation'))):
            raise ValueError('original D33 row schema differs')
        for k in ROW_FIELDS - {'writer', 'session', 'index'}:
            if type(row[k]) not in (int, float) or not math.isfinite(row[k]):
                raise ValueError('nonfinite original D33 field')
        identity = (row['session'], row['index'])
        if identity in seen:
            raise ValueError('duplicate original D33 occurrence')
        seen.add(identity)
        value = dict(original=deepcopy(row), disposition='outside-input-cohort',
                     final_codepoints=None, character_ids=None, text_sha256=None)
        if row['session'] in sessions:
            record, occurrences = sessions[row['session']]
            if record['document']['keys']['writer'] != row['writer']:
                raise ValueError('original writer differs from document')
            occurrence = occurrences.get(row['index'])
            if occurrence is None or not occurrence['is_word']:
                raise ValueError('original word missing from occurrence ledger')
            if len(occurrence['character_ids']) != row['length']:
                raise ValueError('original word length differs from occurrence')
            value.update(character_ids=list(occurrence['character_ids']),
                         text_sha256=record['document']['textSha256'])
            if occurrence['final_codepoints'] is None:
                value['disposition'] = 'not-intact-final-word'
            else:
                value.update(disposition='awaiting-engine-score',
                             final_codepoints=list(occurrence['final_codepoints']))
        joined.append(value)
    counts = Counter(r['disposition'] for r in joined)
    return dict(rows=joined, support=dict(original_rows=len(rows),
        original_writers=len({r['writer'] for r in rows}), input_sessions=len(sessions),
        dispositions={k: counts[k] for k in DISPOSITIONS}),
        engine_scored=False, scientific_admission=False)
