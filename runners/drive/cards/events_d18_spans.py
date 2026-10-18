"""D18 original insertion spans, with exact Unicode survival provenance.

DESIGN CHECK: LESSONS 3-5. A fully deleted original must have no surviving atoms;
an intact survivor must retain every atom contiguously. Partial deletion and
internal insertion are exclusions, not intact survival. Equal-length matches
cannot cross session or source. Invalid replay/boundaries refuse the session.
No tokens, keypresses, mental goals or final-text-only denominator are inferred.
"""
import math
from collections import Counter
from runners.stage9.coauthor import units, text_of, delta_ops


def extract(events, timeline):
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('initialization required')
    times = [float(e['eventTimestamp']) for e in events]
    if not all(map(math.isfinite, times)) or times != sorted(times):
        raise ValueError('invalid chronology')
    prompt = events[0]['currentDoc']
    if prompt != timeline['initial_document']:
        raise ValueError('P2 initial prompt differs')
    atoms, spans, deletion_source = [], [], {}
    unknown_inserted_codepoints = 0

    def mint(text):
        result = []
        for char in text:
            atom = len(atoms); atoms.append(char)
            result.extend([atom] * len(units(char)))
        return result

    doc, owners = units(prompt), mint(prompt)
    current_menu = pending = run = None
    accepted_origins = set()
    for ordinal, event in enumerate(events):
        name = event['eventName']
        if name == 'suggestion-open':
            current_menu = ordinal
        if name == 'suggestion-select':
            if current_menu is None:
                raise ValueError('selection without observed menu')
            pending = current_menu
        ops = delta_ops(event.get('textDelta'))
        is_user = event.get('eventSource') == 'user'
        inserts = [op for op in ops if op.get('insert', '')]
        deletes = [op for op in ops if op.get('delete', 0)]
        pure = is_user and len(inserts) == 1 and not deletes
        if not pure:
            run = None
        if not ops:
            continue
        before, prior = text_of(doc), owners
        out, changed, insertion_chunks, deleted, position = [], [], [], [], 0
        for op in ops:
            if 'insert' in op:
                labels = mint(op['insert'])
                insertion_chunks.append(dict(start=len(out), labels=labels, text=op['insert']))
                out.extend(units(op['insert'])); changed.extend(labels)
            else:
                count = op.get('retain', op.get('delete'))
                if type(count) is not int or count < 0 or position + count > len(doc):
                    raise ValueError('invalid UTF-16 boundary')
                if 'retain' in op:
                    out.extend(doc[position:position + count]); changed.extend(owners[position:position + count])
                elif count:
                    deleted.extend(owners[position:position + count])
                position += count
        out.extend(doc[position:]); changed.extend(owners[position:])
        doc, owners = out, changed
        after = text_of(doc)  # strict UTF-16 decoding rejects half-surrogate edits
        if not is_user and pending is not None:
            inserted = [a for chunk in insertion_chunks for a in chunk['labels']]
            if (not before.endswith('\n') or not after.startswith(before[:-1]) or not after.endswith('\n')
                    or len(doc) - len(prior) != len(inserted) or deleted):
                raise ValueError('accepted insertion is not canonical append')
            if pending in accepted_origins:
                raise ValueError('duplicate accepted span origin')
            accepted_origins.add(pending)
            # Canonical append can shift Quill's terminal newline. Atom text is
            # the actual resulting span, not the delta string's nominal order.
            actual = after[len(before) - 1:-1]
            inserted = mint(actual)
            owners = prior[:-1] + inserted + prior[-1:]
            ids = list(dict.fromkeys(inserted))
            if inserted:
                spans.append(dict(origin='accepted', ordinal=ordinal, source_ordinal=pending,
                    end_ordinal=ordinal, insertions=1, ids=ids, text=actual))
            pending = None
        elif is_user:
            for chunk in insertion_chunks:
                if not chunk['labels']:
                    continue
                ids = list(dict.fromkeys(chunk['labels']))
                if pure and run is not None and chunk['start'] == run['end_utf16'] and ordinal == run['end_ordinal'] + 1:
                    run['ids'].extend(ids); run['text'] += chunk['text']; run['insertions'] += 1
                    run['end_ordinal'] = ordinal; run['end_utf16'] += len(chunk['labels'])
                else:
                    row = dict(origin='typed', ordinal=ordinal, source_ordinal=ordinal,
                        end_ordinal=ordinal, insertions=1, ids=ids, text=chunk['text'])
                    spans.append(row)
                    run = row if pure else None
                    if run is not None:
                        run['end_utf16'] = chunk['start'] + len(chunk['labels'])
        else:
            unknown_inserted_codepoints += sum(len(c['text']) for c in insertion_chunks)
        for atom in set(deleted):
            if atom in deletion_source:
                raise ValueError('original atom deleted twice')
            deletion_source[atom] = 'user' if is_user else 'system'
        if len(doc) != len(owners):
            raise ValueError('provenance length differs')
    if text_of(doc) != timeline['final_document']:
        raise ValueError('P2 final replay differs')
    final_ids = list(dict.fromkeys(owners))
    if len(final_ids) != len(text_of(doc)):
        raise ValueError('final codepoint provenance differs')
    if ''.join(atoms[a] for a in final_ids) != text_of(doc):
        raise ValueError('final atom text differs')
    positions = {a: i for i, a in enumerate(final_ids)}
    result = []
    support = Counter({prefix + '_' + metric: 0 for prefix in ('all', 'accepted', 'typed')
        for metric in ('spans', 'deleted_spans', 'retained_spans', 'partial_spans', 'original_codepoints',
                       'surviving_codepoints', 'partial_surviving_codepoints', 'partial_original_codepoints',
                       'system_affected_spans', 'nonlexical_spans')})
    support.update(prompt_codepoints=len(prompt), unknown_system_inserted_codepoints=unknown_inserted_codepoints)
    for i, span in enumerate(spans):
        ids = span.pop('ids'); span.pop('end_utf16', None)
        remaining = [a for a in ids if a in positions]
        present = [positions[a] for a in remaining]
        contiguous = bool(present) and present == list(range(present[0], present[0] + len(present)))
        status = 'deleted' if not remaining else 'retained' if len(remaining) == len(ids) and contiguous else 'partial'
        system_removed = sum(deletion_source.get(a) == 'system' for a in ids)
        row = dict(span, key=str(i), codepoints=len(ids), surviving_codepoints=len(remaining),
            deleted_codepoints=len(ids) - len(remaining), system_deleted_codepoints=system_removed,
            status=status, original_contiguous_at_end=contiguous, lexical=bool(span['text'].strip()))
        if len(row['text']) != len(ids):
            raise ValueError('original span codepoints differ')
        result.append(row)
        for prefix in ('all', span['origin']):
            support[prefix + '_spans'] += 1
            support[prefix + '_' + status + '_spans'] += 1
            support[prefix + '_original_codepoints'] += len(ids)
            support[prefix + '_surviving_codepoints'] += len(remaining)
            support[prefix + '_partial_surviving_codepoints'] += len(remaining) if status == 'partial' else 0
            support[prefix + '_partial_original_codepoints'] += len(ids) if status == 'partial' else 0
            support[prefix + '_system_affected_spans'] += bool(system_removed)
            support[prefix + '_nonlexical_spans'] += not row['lexical']
    return dict(prompt=prompt, spans=result, support=dict(support))


def match(spans, ratio=1.25):
    """One session only: original length, same origin, fixed greedy source order."""
    if ratio != 1.25:
        raise ValueError('unfrozen length caliper')
    eligible, exclusions = [], []
    for row in spans:
        reason = ('partial survival or internal insertion' if row['status'] == 'partial' else
                  'system deletion involved' if row['system_deleted_codepoints'] else
                  'whitespace-only original span' if not row['lexical'] else None)
        if reason:
            exclusions.append(dict(key=row['key'], reason=reason))
        else:
            eligible.append(row)
    pairs, used = [], set()
    for origin in ('accepted', 'typed'):
        deleted = sorted((s for s in eligible if s['origin'] == origin and s['status'] == 'deleted'),
                         key=lambda s: (s['ordinal'], int(s['key'])))
        retained = [s for s in eligible if s['origin'] == origin and s['status'] == 'retained']
        for row in deleted:
            options = [s for s in retained if s['key'] not in used and max(s['codepoints'], row['codepoints']) <= ratio * min(s['codepoints'], row['codepoints'])]
            if not options:
                exclusions.append(dict(key=row['key'], reason='no unused same-origin length match'))
                continue
            other = min(options, key=lambda s: (abs(math.log(s['codepoints'] / row['codepoints'])), s['ordinal'], int(s['key'])))
            used.update((row['key'], other['key']))
            pairs.append(dict(origin=origin, deleted=row['key'], retained=other['key'],
                deleted_codepoints=row['codepoints'], retained_codepoints=other['codepoints']))
        exclusions.extend(dict(key=s['key'], reason='unmatched retained span') for s in retained if s['key'] not in used)
    return pairs, exclusions
