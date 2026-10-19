"""Exact final-survivor input adapter for the authorized EV comparisons.

DESIGN CHECK: LESSONS 2-5 read October18. Constructed Unicode edits, duplicate
spellings and deletion/reinsertion have known occurrence identities. An intact
word must match its entire ordered original character tuple; a same-spelling
replacement must not match the deleted occurrence. Changed source text, P6
fields, P5 source partition, surrogate boundaries or ambiguous identities refuse
the input, under either a null or an alternative scientific world. Lost/changed
words remain explicit support exclusions, never a zero departure. No statistical
fit, model call, corpus dispatch or scientific admission occurs in this module.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import math

from runners.stage9.coauthor import delta_ops, units, text_of
from runners.drive.cards.timing_text import TOKEN, replay_words
from runners.drive.cards.timing_revision_events import replay_revision_events

SCORE_FIELDS = frozenset(('population_probability', 'population_surprisal',
                          'population_log_frequency'))


def source_atoms(events):
    """Replay original atoms, with P5's explicit terminal-newline relocation.

    Typed ids count typed codepoints only, exactly as the frozen P6 ledger.
    API atoms use their actual canonical inserted slice; they never acquire a
    typed identity. A retained final atom must still spell its original character.
    """
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('initialization required')
    atoms, typed_count = [], 0

    def mint(text, source, ordinal):
        nonlocal typed_count
        labels = []
        for char in text:
            typed_id = typed_count if source == 'typed' else None
            if typed_id is not None:
                typed_count += 1
            identity = len(atoms)
            atoms.append(dict(char=char, source=source, ordinal=ordinal, typed_id=typed_id))
            labels.extend([identity] * len(units(char)))
        return labels

    doc = units(events[0]['currentDoc'])
    owners = mint(events[0]['currentDoc'], 'prompt', 0)
    current = pending = None
    previous_time = -math.inf
    for ordinal, event in enumerate(events):
        stamp = float(event['eventTimestamp'])
        if not math.isfinite(stamp) or stamp < previous_time:
            raise ValueError('invalid chronology')
        previous_time = stamp
        if event['eventName'] == 'suggestion-open':
            current = ordinal
        if event['eventName'] == 'suggestion-select':
            if current is None:
                raise ValueError('selection without menu')
            pending = current
        ops = delta_ops(event.get('textDelta'))
        if not ops:
            continue
        user = event.get('eventSource') == 'user'
        source = 'typed' if user else 'accepted' if pending is not None else 'api_unknown'
        before, prior = text_of(doc), owners
        out, labels, position, inserted, deleted = [], [], 0, 0, 0
        for op in ops:
            if 'insert' in op:
                values = units(op['insert'])
                out.extend(values)
                labels.extend(mint(op['insert'], source, ordinal))
                inserted += len(values)
            else:
                count = op.get('retain', op.get('delete'))
                if type(count) is not int or count < 0 or position + count > len(doc):
                    raise ValueError('invalid UTF16 boundary')
                if 'retain' in op:
                    out.extend(doc[position:position + count])
                    labels.extend(prior[position:position + count])
                else:
                    deleted += count
                position += count
        out.extend(doc[position:]); labels.extend(prior[position:])
        doc, owners = out, labels
        after = text_of(doc)
        if source == 'accepted':
            if (not before.endswith('\n') or not after.startswith(before[:-1])
                    or not after.endswith('\n') or deleted
                    or len(doc) - len(prior) != inserted):
                raise ValueError('accepted insertion is not canonical append')
            owners = prior[:-1] + mint(after[len(before)-1:-1], source, ordinal) + prior[-1:]
            pending = None
        if len(owners) != len(doc):
            raise ValueError('atom length differs')
    final = text_of(doc)
    codepoint_atoms, cursor = [], 0
    for char in final:
        width = len(units(char))
        ids = owners[cursor:cursor + width]
        if len(set(ids)) != 1 or atoms[ids[0]]['char'] != char:
            raise ValueError('final atom spelling or Unicode identity differs')
        codepoint_atoms.append(atoms[ids[0]])
        cursor += width
    return final, codepoint_atoms, atoms


def final_document(events, keys, *, expected_final=None, expected_p6=None, p5_sentences=None):
    """Build private exporter input and an exhaustive original occurrence ledger.

    External consumers must authenticate source bytes and completed P2/P5/P6/D33
    records before calling. Supplied expected records are strict equality checks,
    not a substitute for their hashes. No casefold search or positional guess joins
    an occurrence. P6's original casefold token is checked only after id matching.
    """
    audited = replay_revision_events(events)
    original = replay_words(events)
    if audited['replay'] != original:
        raise ValueError('revision companion changed original P6 semantics')
    if expected_p6 is not None:
        words = [{k: v for k, v in w.items() if k not in SCORE_FIELDS} for w in expected_p6]
        if words != original['words']:
            raise ValueError('frozen P6 occurrence fields differ')
    final, labels, atoms = source_atoms(events)
    if final != original['final_document'] or expected_final is not None and final != expected_final:
        raise ValueError('final document differs from source')
    if p5_sentences is not None:
        covered, previous_end = set(), 0
        for row in p5_sentences:
            a, b = row['start_codepoint'], row['end_codepoint']
            if not previous_end <= a < b <= len(final) or final[a:b] != row['text']:
                raise ValueError('P5 sentence span differs')
            previous_end = b
            covered.update(i for i in range(a, b) if not final[i].isspace())
            counts = Counter()
            for char, label in zip(final[a:b], labels[a:b]):
                if not char.isspace():
                    counts[label['source']] += len(units(char))
            if dict(counts) != row['origin_counts'] or (bool(counts) and set(counts) == {'typed'}) != row['writer_typed']:
                raise ValueError('P5 source partition differs')
        if covered != {i for i, char in enumerate(final) if not char.isspace()}:
            raise ValueError('P5 sentence coverage differs')
    typed = {a['typed_id']: a for a in atoms if a['typed_id'] is not None}
    surviving = {}
    for match in TOKEN.finditer(final):
        part = labels[match.start():match.end()]
        if part and all(a['source'] == 'typed' for a in part):
            ids = tuple(a['typed_id'] for a in part)
            if ids in surviving:
                raise ValueError('duplicate final occurrence identity')
            surviving[ids] = (match.start(), match.end())
    ledger, spans, used = [], {}, set()
    for word, audit in zip(original['words'], audited['revision_events']):
        if word['index'] != audit['index']:
            raise ValueError('occurrence index differs')
        ids = tuple(audit['character_ids'])
        if ids in used or len(set(ids)) != len(ids):
            raise ValueError('duplicate production identity')
        used.add(ids)
        exact = ''.join(typed[i]['char'] for i in ids)
        if exact.casefold() != word['token'] or len(exact) != word['length']:
            raise ValueError('original occurrence spelling differs')
        span = surviving.get(ids)
        disposition = 'intact-final-token' if span else 'not-an-intact-final-token'
        row = dict(index=word['index'], character_ids=list(ids), is_word=word['is_word'],
                   disposition=disposition, final_codepoints=list(span) if span else None)
        if span:
            a, b = span
            if final[a:b] != exact:
                raise ValueError('surviving occurrence spelling differs')
            spans[a] = (b, 'p6:' + str(word['index']))
        ledger.append(row)
    provenance, cursor = [], 0
    while cursor < len(final):
        label = labels[cursor]
        if cursor in spans:
            end, occurrence = spans[cursor]
        else:
            end = cursor + 1
            while (end < len(final) and end not in spans
                   and (labels[end]['source'], labels[end]['ordinal']) == (label['source'], label['ordinal'])):
                end += 1
            occurrence = 'source:' + str(cursor)
        provenance.append(dict(start=cursor, end=end, occurrenceId=occurrence,
                               source=label['source'],
                               productionOrdinals=sorted({a['ordinal'] for a in labels[cursor:end]})))
        cursor = end
    if len(audited['revision_events']) != len(original['words']):
        raise ValueError('incomplete occurrence audit')
    return dict(document=dict(keys=keys, text=final,
            textSha256=hashlib.sha256(final.encode('utf8')).hexdigest(),
            variant='final-document', provenance=provenance), occurrences=ledger,
            support=dict(original_occurrences=len(ledger),
                intact_final_occurrences=sum(r['final_codepoints'] is not None for r in ledger),
                original_words=sum(r['is_word'] for r in ledger),
                intact_final_words=sum(r['is_word'] and r['final_codepoints'] is not None for r in ledger)),
            production_mapping='constructed adapter only; corpus source authentication and D33/export joins still required')
