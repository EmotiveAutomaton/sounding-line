"""GEN1 atom ledger: the PMAP pair replay with parallel typed identities.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-7 read 2026-10-23.
NULL/ALTERNATIVE: original PMAP counts and intervals must be exactly identical.
Wrong Unicode provenance, manufactured deletion adjacencies or source mismatch
refuse extraction. No score, resampling or source policy is changed here.
Copied from timing_pmap_source.raw_features; the frozen original is untouched.
"""
from collections import Counter, defaultdict
import math
from runners.stage9.coauthor import units, text_of, delta_ops

def raw_pairs(events, timeline, canonical):
    """Original-character deletion share and adjacent typed-atom bigram timing.

    Noncanonical API insertions remain non-typed provenance. Only canonical
    usable accept/edit origins contribute to the accepted denominator. All raw
    transforms, including terminal-newline relocation, must reconstruct P2.
    """
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('initialization required')
    clock = [float(e['eventTimestamp']) / 1000 for e in events]
    if not all(map(math.isfinite, clock)) or clock != sorted(clock):
        raise ValueError('invalid raw chronology')
    accepted = {r['ordinal']: r for r in canonical['events']
                if r['usable'] and r['decision'] in ('accept', 'edit')}
    doc = units(events[0]['currentDoc']); atoms = []; owners = []
    original, deleted, seen_pairs = set(), set(), set()
    typed_ids, pair_rows = {}, []
    bigram_counts, intervals = Counter(), defaultdict(list)
    current = pending = None
    inside_additions = excluded_api_characters = 0

    def mint(text, source, ordinal, single):
        result = []
        for char in text:
            idx = len(atoms)
            atoms.append((char, source, ordinal, single))
            if source == 'typed': typed_ids[idx] = len(typed_ids)
            result.extend([idx] * len(units(char)))
            if source == 'accepted': original.add(idx)
        return result

    owners = mint(events[0]['currentDoc'], 'prompt', 0, False)
    for ordinal, e in enumerate(events):
        if e['eventName'] == 'suggestion-open': current = ordinal
        if e['eventName'] == 'suggestion-select': pending = current
        ops = delta_ops(e.get('textDelta'))
        if not ops: continue
        user = e.get('eventSource') == 'user'
        text = ''.join(o['insert'] for o in ops if 'insert' in o)
        source = 'typed' if user else 'accepted' if pending in accepted else 'api_excluded'
        single = user and len(text) == 1
        before, prior = text_of(doc), owners
        out, labels, newids, chunks, position = [], [], [], [], 0
        for op in ops:
            if 'insert' in op:
                ids = mint(op['insert'], source, ordinal, single)
                if user and 0 < position < len(prior) and prior[position-1] in original and prior[position] in original:
                    inside_additions += len(op['insert'])
                chunks.append((len(labels),len(labels)+len(ids)))
                out.extend(units(op['insert'])); labels.extend(ids); newids.extend(ids)
            else:
                count = op.get('retain', op.get('delete'))
                if type(count) is not int or count < 0 or position + count > len(doc):
                    raise ValueError('invalid UTF16 delta')
                if 'retain' in op:
                    out.extend(doc[position:position+count]); labels.extend(prior[position:position+count])
                elif user:
                    deleted.update(a for a in prior[position:position+count] if a in original)
                position += count
        out.extend(doc[position:]); labels.extend(prior[position:]); doc, owners = out, labels
        after = text_of(doc)
        if not user and pending is not None:
            if not before.endswith('\n') or not after.startswith(before[:-1]) or not after.endswith('\n') or len(doc)-len(prior) != len(newids):
                raise ValueError('API insertion is not exact canonical append')
            actual = after[len(before)-1:-1]
            if pending in accepted:
                c = accepted[pending]
                choices = [o for o in c['options'] if o['index'] in c['matched_option_indices']]
                if not c['verified_insertion'] or not choices or any(o['original'].replace('\r\n','\n').replace('\r','\n') != actual for o in choices):
                    raise ValueError('accepted raw insertion differs from verified canonical identity')
            else: excluded_api_characters += len(actual)
            owners = prior[:-1] + newids + prior[-1:]; pending = None
        if user and newids:
            # Only new adjacency at this insertion, never a pair manufactured by deletion.
            fresh = set(newids)
            adjacent = set()
            for start,stop in chunks:
                ids = list(dict.fromkeys(owners[max(0,start-2):min(len(owners),stop+2)]))
                adjacent.update(zip(ids,ids[1:]))
            for a, b in sorted(adjacent):
                if (a in fresh or b in fresh) and atoms[a][1] == atoms[b][1] == 'typed' and (a,b) not in seen_pairs:
                    seen_pairs.add((a,b)); ca, _, oa, sa = atoms[a]; cb, _, ob, sb = atoms[b]
                    pair = ca.casefold() + cb.casefold()
                    if len(ca.casefold()) != 1 or len(cb.casefold()) != 1: continue
                    bigram_counts[pair] += 1
                    pair_rows.append(dict(a=typed_ids[a], b=typed_ids[b], pair=pair, ordinal=ordinal,
                        a_char=ca, b_char=cb, seconds=None))
                    if sa and sb and oa < ob:
                        dt = clock[ob] - clock[oa]
                        if dt >= 0:
                            intervals[pair].append(dt)
                            pair_rows[-1]['seconds'] = dt
    if text_of(doc) != timeline['final_document']:
        raise ValueError('raw reconstruction differs from P2')
    return dict(pairs=pair_rows, typed_atoms={typed_ids[i]: atoms[i][0] for i in typed_ids}, bigram_counts=dict(sorted(bigram_counts.items())),
        bigram_intervals={k:v for k,v in sorted(intervals.items())}, accepted_characters=len(original),
        edited_accepted_characters=len(deleted), internal_added_characters=inside_additions,
        excluded_api_characters=excluded_api_characters)
