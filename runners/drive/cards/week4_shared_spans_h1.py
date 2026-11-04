"""R1 shared_spans.h1: physical insertion identity; prior failed modules retained.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 6-7 reread 2026-11-02.
Case: the three old failures must reproduce before this successor runs.
NULL and ALTERNATIVE share exact source and canonical-choice population checks.
Missing comparators remain unsupported; reused menu identities are not insertion
identities. Original codepoint survival is never replacement text. No effect fit.
"""
import math
from runners.stage9.coauthor import units, text_of, delta_ops

def normalized(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')

def spans(events, timeline, canonical):
    """Replay original accepted atoms; keep original and canonical event censuses."""
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('initialization required')
    clock = [float(e['eventTimestamp']) for e in events]
    if not all(map(math.isfinite, clock)) or clock != sorted(clock):
        raise ValueError('nonfinite/unordered source clock')
    choices = {e['ordinal']: e for e in canonical['events'] if e['usable']}
    if len(choices) != sum(bool(e['usable']) for e in canonical['events']):
        raise ValueError('duplicate canonical menu')
    doc = units(events[0]['currentDoc']); owners = [None] * len(doc)
    current = pending = None; accepted = {}; atoms = 0
    for ordinal, event in enumerate(events):
        name = event['eventName']
        if name == 'suggestion-open': current = ordinal
        if name == 'suggestion-select': pending = current
        ops = delta_ops(event.get('textDelta'))
        if not ops: continue
        user = event.get('eventSource') == 'user'
        menu_origin = pending if not user and pending is not None else None
        origin = ordinal if menu_origin is not None else None
        before, prior = text_of(doc), owners
        out = []; labels = []; inserted = []; deleted = []; position = 0
        for op in ops:
            if 'insert' in op:
                for char in op['insert']:
                    tag = (origin, atoms) if origin is not None else None
                    atoms += 1
                    out.extend(units(char)); labels.extend([tag] * len(units(char)))
                    if tag is not None: inserted.append((tag, char))
            else:
                n = op.get('retain', op.get('delete'))
                if type(n) is not int or n < 0 or position+n > len(doc):
                    raise ValueError('invalid UTF16 delta boundary')
                if 'retain' in op:
                    out.extend(doc[position:position+n]); labels.extend(prior[position:position+n])
                else: deleted.extend(prior[position:position+n])
                position += n
        out.extend(doc[position:]); labels.extend(prior[position:]); doc, owners = out, labels
        after = text_of(doc)
        if origin is not None:
            if (not before.endswith('\n') or not after.startswith(before[:-1])
                    or not after.endswith('\n') or len(doc)<len(prior)):
                raise ValueError('accepted insertion is not canonical append')
            if origin in accepted: raise ValueError('accepted origin reused')
            # Derive the semantic append from the FULL verified transform.
            # A raw insert can move the old terminal newline across its boundary,
            # or rewrite unchanged prefix text; neither changes accepted atoms.
            text = after[len(before)-1:-1]
            c = choices.get(menu_origin); valid = c is not None and c['decision'] in ('accept', 'edit')
            other = []
            if valid:
                selected = [o for o in c['options'] if o['index'] in c['matched_option_indices']]
                if (len(selected) != 1 or not c['verified_insertion']
                        or after != before[:-1]+normalized(selected[0]['original'])+'\n'):
                    raise ValueError('actual inserted span differs from unique canonical choice')
                other = [normalized(o['original']) for o in c['options'] if o['index'] not in c['matched_option_indices']]
            inserted=[]
            for char in text:
                inserted.append(((origin,atoms),char));atoms+=1
            accepted[origin] = dict(origin=origin, menu_origin=menu_origin, inserted_ordinal=ordinal, text=text,
                unchosen=other, canonical=valid, option_count=len(c['options']) if valid else None,
                comparator_supported=bool(valid and other),
                comparator_support='available' if valid and other else 'single_option_menu' if valid else 'noncanonical_choice',
                atoms={a for a, _ in inserted}, removed=set(), failure_ordinal=None)
            newlabels = [a for a, char in inserted for _ in units(char)]
            owners = prior[:-1] + newlabels + prior[-1:]; pending = None
            if len(owners)!=len(doc):raise ValueError('canonical atom provenance length differs')
        if user:
            for tag in set(deleted)-{None}:
                if tag[0] not in accepted: raise ValueError('deleted accepted atom has no origin')
                accepted[tag[0]]['removed'].add(tag)
            for item in accepted.values():
                if (item['atoms'] and item['failure_ordinal'] is None
                        and 5*len(item['removed']) >= 4*len(item['atoms'])):
                    item['failure_ordinal'] = ordinal
    if text_of(doc) != timeline['final_document'] or canonical['final_document'] != timeline['final_document']:
        raise ValueError('final document differs from authenticated P2/canonical replay')
    surviving = set(owners)-{None}; result = []
    for _, item in sorted(accepted.items()):
        result.append({k:v for k,v in item.items() if k not in ('atoms', 'removed')} | dict(
            original_codepoints=len(item['atoms']), deleted_codepoints=len(item['removed']),
            retained_codepoints=len(item['atoms'] & surviving)))
    return result
