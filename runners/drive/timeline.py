"""UTF-16 event replay with persistent origins; never individual inferred keypresses.

DESIGN CHECK: LESSONS 2-5 read 2026-10-16. NULL: malformed delta or chronology
refuses a session, pointer absence never proves nonexposure. ALTERNATIVE: exact
fixtures retain text/origins through Unicode, replacement, deletion and shifts.
Timing bands: direct select/close, first-edit proxy, or censored end; never pooled
without a disclosed convention. Original canonical handling labels are retained.
"""
import math
from collections import Counter
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta


def rebuild(events, rows):
    if not events or events[0]['eventName'] != 'system-initialize': raise ValueError('initialization required')
    times = [float(e['eventTimestamp']) for e in events]
    if not all(math.isfinite(t) for t in times) or times != sorted(times): raise ValueError('invalid chronology')
    doc = units(events[0]['currentDoc']); owners = [('prompt', 0)]*len(doc)
    deltas, edits, final_touches, owned_insertions = [], [], set(), {}
    pending = None; current_menu = None
    for i, event in enumerate(events):
        name, source = event['eventName'], event.get('eventSource')
        if name == 'suggestion-open': current_menu = i
        if name == 'suggestion-select': pending = current_menu
        delta = event.get('textDelta')
        if delta in ('', None): continue
        before = text_of(doc); ops = delta_ops(delta); position = 0; touched = set()
        for op in ops:
            if 'delete' in op:
                touched.update(o[1] for o in owners[position:position+op['delete']] if o[0]=='accepted')
                position += op['delete']
            elif 'retain' in op: position += op['retain']
            elif 0 < position < len(doc) and owners[position-1] == owners[position] and owners[position][0]=='accepted':
                touched.add(owners[position][1])
        kind = 'typed' if source == 'user' else 'accepted' if pending is not None else 'api_unknown'
        owner = (kind, pending if kind == 'accepted' else i)
        previous = owners
        doc, owners, _ = apply_delta(doc, owners, delta, insertion_owner=owner)
        after = text_of(doc)
        if kind == 'accepted':
            # The original replay's verified full append controls Quill's terminal newline shift.
            if not before.endswith('\n') or not after.startswith(before[:-1]) or not after.endswith('\n'):
                raise ValueError('accepted insertion is not canonical append')
            extra = len(doc)-len(previous)
            if extra < 0: raise ValueError('negative accepted span')
            owners = previous[:-1]+[owner]*extra+previous[-1:]
            owned_insertions[pending] = after[len(before)-1:-1]; pending = None
        if source == 'user': final_touches.update(touched)
        inserted = ''.join(o['insert'] for o in ops if 'insert' in o)
        deleted_units = sum(o.get('delete',0) for o in ops)
        record = dict(ordinal=i, seconds=(times[i]-times[0])/1000, source=source,
            inserted_codepoints=len(inserted), inserted_utf16=len(units(inserted)),
            deleted_utf16=deleted_units, accepted_owners_touched=sorted(touched))
        deltas.append(record)
        if source == 'user' and (deleted_units or touched):
            left = 0
            while left < min(len(before),len(after)) and before[left] == after[left]: left += 1
            right = 0
            while right < min(len(before),len(after))-left and before[-right-1] == after[-right-1]: right += 1
            old_end, new_end = len(before)-right, len(after)-right
            edits.append(dict(**record, before=before[max(0,left-256):min(len(before),old_end+256)],
                after=after[max(0,left-256):min(len(after),new_end+256)], changed_start_codepoint=left,
                before_changed_end=old_end,after_changed_end=new_end,context_each_side_codepoints=256,
                full_documents_retained_in_source_replay=True))
    if len(doc) != len(owners): raise ValueError('origin length differs')
    spans = []; start = 0
    while start < len(doc):
        origin = owners[start]; end = start+1
        while end < len(doc) and owners[end] == origin: end += 1
        category = 'accepted_edited' if origin[0]=='accepted' and origin[1] in final_touches else origin[0]
        spans.append(dict(start_utf16=start,end_utf16=end,origin=category,insertion_ordinal=origin[1],text=text_of(doc[start:end])))
        start = end
    decisions = []; previous_boundary = 0
    for r in rows:
        start, end = r['ordinal'], min(r['end_ordinal'],len(events))
        direct = [i for i in range(start+1,end) if events[i]['eventName'] in ('suggestion-select','suggestion-close')]
        typed = [d for d in deltas if start < d['ordinal'] < end and d['source']=='user' and d['inserted_codepoints']]
        if r['handling'] != 'ignore' and direct:
            at, kind = direct[-1], 'observed_selection_or_close'
        elif typed: at, kind = typed[0]['ordinal'], 'first_user_insert_proxy'
        else: at, kind = min(end,len(events)-1), 'right_censored_at_next_menu_or_end'
        if at < start: raise ValueError('resolution before menu')
        between = [d for d in deltas if previous_boundary < d['ordinal'] <= at and d['source']=='user']
        interactions = [dict(ordinal=i,event=events[i]['eventName'],hover=events[i].get('currentHoverIndex'),
            selected=events[i].get('currentSuggestionIndex'),seconds=(times[i]-times[start])/1000)
            for i in range(start,end) if events[i]['eventName'].startswith('suggestion-')]
        decisions.append(dict(key=r['key'],ordinal=start,handling=r['handling'],menu_size=len(r['menu']),
            latency_seconds=(times[at]-times[start])/1000,latency_kind=kind,resolution_ordinal=at,
            typed_since_previous_decision=sum(d['inserted_codepoints'] for d in between),
            utf16_since_previous_decision=sum(d['inserted_utf16'] for d in between),interactions=interactions))
        previous_boundary = at
    return dict(final_document=text_of(doc),final_spans=spans,deltas=deltas,edits=edits,decisions=decisions,
        duration_seconds=(times[-1]-times[0])/1000,event_counts=dict(Counter(e['eventName'] for e in events)),
        initial_document=events[0]['currentDoc'],independent_final_document=False,
        timing_unit='logged delta event, not individual keypress',exposure='highlight/hover observed; actual reading unknown')
