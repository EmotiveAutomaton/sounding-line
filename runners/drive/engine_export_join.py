"""Exact engine span joins and retained typed fragments; no inference admission.

DESIGN CHECK: LESSONS 2-5 reread October 18. Under null and alternative,
identity and all coordinate systems must agree. Wrong source, substituted
occurrence, nonfinite score or false provenance fails closed. Missing lexical
support is explicit, never a zero score. Constructed actual-exporter outputs,
including repeated words and Unicode boundary differences, precede corpus use.
Callers must authenticate producer completion, engine/reader pins and replay.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import math

from .engine_d33_join import document_index, join_rows


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf8')).hexdigest()


def exact_span(text, value):
    a, b = value['codepoints']
    if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text)
            or any(not isinstance(value[k], list) or len(value[k]) != 2
                   or any(type(v) is not int for v in value[k]) for k in ('utf8', 'utf16'))
            or value['exact'] != text[a:b]
            or value['utf8'] != [len(text[:a].encode('utf8')), len(text[:b].encode('utf8'))]
            or value['utf16'] != [len(text[:a].encode('utf-16-le'))//2, len(text[:b].encode('utf-16-le'))//2]):
        raise ValueError('exported coordinate or exact slice differs')
    return a, b


def finite(value):
    return type(value) in (float, int) and math.isfinite(value)


def word_index(document, exported):
    """Check actual exporter fields; presence alone is not source authentication."""
    if (exported['status'] not in ('complete', 'unsupported')
            or hashlib.sha256(document['text'].encode('utf8')).hexdigest() != document['textSha256']
            or exported['keys'] != document['keys']
            or exported['variant'] != document['variant']
            or exported['textSha256'] != document['textSha256']
            or exported['inputRecordSha256'] != digest(document)
            or exported['provenance'] != document['provenance']
            or exported['provenanceSha256'] != digest(document['provenance'])
            or exported['productionMappingValidated'] is not False
            or exported['fragmentConstruction'] != document.get('fragmentConstruction')):
        raise ValueError('exported input identity or provenance differs')
    text, regions, end = document['text'], {}, 0
    for region in exported['regions']:
        a, b, ident = region['start'], region['end'], region['id']
        if (type(a) is not int or type(b) is not int or not end <= a < b <= len(text)
                or not isinstance(ident, str) or not ident or ident in regions
                or text[end:a].strip()):
            raise ValueError('exported region partition differs')
        regions[ident] = (a, b)
        end = b
    if not regions or text[end:].strip():
        raise ValueError('exported region partition incomplete')
    if exported['status'] == 'unsupported':
        if (exported['reason'] != 'No scorable content words after names/numbers/code holdouts'
                or exported['words'] or 'normalization' in exported):
            raise ValueError('unsupported export has scores or wrong reason')
        return {}
    norm = exported['normalization']
    if not finite(norm['median']) or not finite(norm['iqr']) or norm['iqr'] < 0:
        raise ValueError('invalid engine normalization')
    found, previous = {}, -1
    for position, word in enumerate(exported['words']):
        a, b = exact_span(text, word['span'])
        x, y = exact_span(text, word['allocatedSpan'])
        lo, hi = regions[word['region']]
        if not lo <= a < b <= y <= hi or x != a or a < previous or (a, b) in found:
            raise ValueError('duplicate, unordered or invalid engine word span')
        previous = b
        if (type(word['content']) is not bool or type(word['heldOut']) is not bool
                or not finite(word['allocatedTokenLossNats']) or word['allocatedTokenLossNats'] < 0):
            raise ValueError('invalid engine word flags or loss')
        expected = [{'index': i, 'codepoints': [max(a, p['start']), min(b, p['end'])]}
            for i, p in enumerate(document['provenance']) if a < p['end'] and b > p['start']]
        if word['provenanceIntersections'] != expected:
            raise ValueError('engine provenance intersections differ')
        if word['content'] and not word['heldOut']:
            departure = ((word['allocatedTokenLossNats']-norm['median'])/norm['iqr']
                         if norm['iqr'] > 1e-12 else 0.)
            if not finite(word['departure']) or not math.isclose(word['departure'], departure, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError('engine departure differs from pinned normalization')
        elif word['departure'] is not None:
            raise ValueError('excluded engine word carries departure')
        found[a, b] = (position, word)
    eligible = sum(w['content'] and not w['heldOut'] for w in exported['words'])
    if (not eligible or eligible != norm['words']
            or sum(w['heldOut'] for w in exported['words']) != norm['heldOut']):
        raise ValueError('engine eligible-word denominator differs')
    return found


def join_exports(rows, records, exports):
    """Retain all original rows. Only identical lexical spans receive a score."""
    if len(records) != len(exports):
        raise ValueError('export cohort length differs')
    joined = join_rows(rows, records)
    lookup = {}
    for record, exported in zip(records, exports):
        document = record['document']
        lookup[document['keys']['session']] = (exported, word_index(document, exported))
    for row in joined['rows']:
        row['engine'] = None
        if row['disposition'] != 'awaiting-engine-score':
            continue
        exported, words = lookup[row['original']['session']]
        if exported['status'] == 'unsupported':
            row['disposition'] = 'engine-unsupported-document'
            continue
        matched = words.get(tuple(row['final_codepoints']))
        if matched is None:
            row['disposition'] = 'engine-no-exact-word-match'
            continue
        index, word = matched
        if word['heldOut']:
            row['disposition'] = 'engine-held-out'
        elif not word['content']:
            row['disposition'] = 'engine-not-content'
        else:
            row['disposition'] = 'engine-scored'
            row['engine'] = dict(word_index=index, departure=word['departure'],
                allocated_token_loss_nats=word['allocatedTokenLossNats'])
    joined['support']['dispositions'] = dict(sorted(Counter(r['disposition'] for r in joined['rows']).items()))
    joined['engine_export_consumed'] = True
    joined['engine_scored'] = any(r['disposition'] == 'engine-scored' for r in joined['rows'])
    joined['scientific_admission'] = False
    return joined


def typed_fragments(record):
    """Retain every surviving typed codepoint; separate gaps with two newlines.

    Adjacent typed provenance intervals stay adjacent. Non-typed gaps become
    explicit synthetic boundaries, never lexical glue. This is fragmented text,
    not original prose. Source and fragment offsets are retained for every piece.
    """
    document_index(record)
    source = record['document']; text = source['text']
    pieces, provenance, mappings, runs = [], [], [], []
    cursor, previous_end = 0, None
    for original in source['provenance']:
        if original['source'] != 'typed':
            continue
        a, b = original['start'], original['end']
        if previous_end is not None and previous_end != a:
            pieces.append('\n\n')
            provenance.append(dict(start=cursor, end=cursor+2,
                occurrenceId='separator:'+str(len(runs)), source='synthetic-boundary'))
            cursor += 2
        if previous_end != a:
            runs.append(dict(source_start=a, source_end=b, start=cursor, end=cursor+b-a))
        else:
            runs[-1].update(source_end=b, end=cursor+b-a)
        piece = deepcopy(original)
        piece.update(start=cursor, end=cursor+b-a)
        provenance.append(piece)
        mappings.append(dict(occurrenceId=original['occurrenceId'], source_codepoints=[a,b],
                             fragment_codepoints=[cursor,cursor+b-a]))
        pieces.append(text[a:b]); cursor += b-a; previous_end = b
    fragment = ''.join(pieces)
    construction = dict(method='all-surviving-typed-runs-separated-by-two-newlines-v1',
        source_text_sha256=source['textSha256'], source_record_sha256=digest(source),
        mappings=mappings, runs=runs, original_prose=False,
        synthetic_separator_codepoints=2*max(0,len(runs)-1))
    support = dict(typed_codepoints=sum(m['source_codepoints'][1]-m['source_codepoints'][0] for m in mappings),
                   contiguous_runs=len(runs), nonwhitespace_typed_codepoints=sum(not c.isspace() for p in pieces if p != '\n\n' for c in p))
    if not fragment.strip():
        return dict(status='unsupported-no-typed-words', document=None, construction=construction, support=support)
    return dict(status='complete', document=dict(keys=deepcopy(source['keys']), text=fragment,
        textSha256=hashlib.sha256(fragment.encode('utf8')).hexdigest(), variant='writer-typed-fragments',
        provenance=provenance, fragmentConstruction=construction), support=support)
