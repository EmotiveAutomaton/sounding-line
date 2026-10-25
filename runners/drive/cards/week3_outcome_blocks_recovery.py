"""WC2 exact canonical-append provenance recovery; private text, counts only.

Original attempt retained. Quill's raw insert may shift a terminal newline or
rewrite retained text. The exact canonical whole-document transform is the
identity contract, as in Stage9; raw delta boundaries are not accepted atoms.
Every original codepoint is allocated from the certified append once. No
population, comparator, threshold, selection or downstream estimand changes.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-25.
NULL/ALTERNATIVE: extraction has no effect gate. A qualifying original span
crosses 80% once, independent of the logged selection index. Unicode atoms,
complete 50-produced-word windows, whole source population and external-writer
prompt controls are retained. Missing windows are unsupported, never zeros.
Final-document mismatch, ambiguous choice or source mutation refuses completion.
"""
from collections import Counter, defaultdict
import bisect
import hashlib
import json
import math
from pathlib import Path

from runners.stage9.coauthor import units, text_of, delta_ops
from runners.stage9.common import digest
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .timing_pmap_source import INPUTS, completed, bound_record
from .timing_pmap_source_recovery import Sources

CONFIG = dict(card='WC2-inputs-recovery', schema=1, mode='full', expected_sessions=1399,
              session_limit=1399, window_words=50)
PILOT = dict(CONFIG, mode='pilot', session_limit=140)
CONSTRUCTED = dict(CONFIG, mode='constructed', expected_sessions=6, session_limit=6)


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
        origin = pending if not user and pending is not None else None
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
            c = choices.get(origin); valid = c is not None and c['decision'] in ('accept', 'edit')
            other = []
            if valid:
                selected = [o for o in c['options'] if o['index'] in c['matched_option_indices']]
                if (len(selected) != 1 or not c['verified_insertion']
                        or after != before[:-1]+normalized(selected[0]['original'])+'\n'):
                    raise ValueError('actual inserted span differs from unique canonical choice')
                other = [normalized(o['original']) for o in c['options'] if o['index'] not in c['matched_option_indices']]
                if not other: raise ValueError('accepted menu has no unchosen comparator')
            inserted=[]
            for char in text:
                inserted.append(((origin,atoms),char));atoms+=1
            accepted[origin] = dict(origin=origin, inserted_ordinal=ordinal, text=text,
                unchosen=other, canonical=valid, atoms={a for a, _ in inserted}, removed=set(), failure_ordinal=None)
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


def word_stream(words):
    result = sorted((w for w in words if w['is_word']), key=lambda w:(w['ordinal'],w['index']))
    if len({w['index'] for w in result}) != len(result): raise ValueError('duplicate production word')
    return result


def window(words, start, count=50):
    selected = words[start:start+count]
    if len(selected) != count: return None
    return dict(text=' '.join(w['token'] for w in selected),
                word_indices=[w['index'] for w in selected], first_ordinal=selected[0]['ordinal'],
                last_completed_ordinal=max(w['completed_ordinal'] for w in selected),
                position=start/max(1,len(words)), words=count)


def after(words, ordinal, sentence=True):
    start = bisect.bisect_right([w['ordinal'] for w in words], ordinal)
    while sentence and start < len(words) and not words[start]['sentence_start']: start += 1
    return window(words,start)


def prepare_session(meta, events, timeline, canonical, p6):
    words = word_stream(p6['words']); result = []; audit = Counter()
    for span in spans(events,timeline,canonical):
        failed = span['failure_ordinal'] is not None and bool(span['text'].strip())
        audit['legacy_failure_candidates'] += failed
        if not span['canonical']:
            audit['noncanonical_failure_candidates'] += failed
            continue
        audit['canonical_failure_candidates'] += failed
        if not span['text'].strip(): continue
        kind = 'deleted' if failed else 'kept' if 5*span['retained_codepoints'] >= 4*span['original_codepoints'] else 'partial'
        if kind == 'partial':
            audit['partially_retained_spans'] += 1; continue
        ordinal = span['failure_ordinal'] if failed else span['inserted_ordinal']
        own = after(words,ordinal)
        audit[kind+'_complete_windows'] += own is not None
        audit[kind+'_incomplete_windows'] += own is None
        result.append(dict(id=meta['session']+':'+str(span['origin']),session=meta['session'],
            writer=meta['writer'],prompt=meta['prompt'],timestamp=meta['timestamp'], kind=kind,
            ordinal=ordinal,position=bisect.bisect_right([w['ordinal'] for w in words],ordinal)/max(1,len(words)),
            span=span,window=own,sensitivity=after(words,ordinal,False) if failed else None))
    candidates = [dict(session=meta['session'],writer=meta['writer'],prompt=meta['prompt'],**item)
                  for i,w in enumerate(words) if w['sentence_start'] and (item:=window(words,i)) is not None]
    return dict(session=meta['session'],writer=meta['writer'],prompt=meta['prompt'],timestamp=meta['timestamp'],
                typed_words=len(words),events=result,context_windows=candidates,audit=dict(audit))


def match_context(row, candidates, sensitivity=False):
    own = row['sensitivity'] if sensitivity else row['window']
    if own is None: return []
    groups = defaultdict(list)
    for w in candidates:
        if w['writer'] != row['writer'] and w['prompt'] == row['prompt']:
            groups[w['writer']].append(w)
    return [min(group,key=lambda w:(abs(w['position']-own['position']),w['session'],w['first_ordinal']))
            for _,group in sorted(groups.items())]


def assemble(sessions):
    if len({s['session'] for s in sessions}) != len(sessions): raise ValueError('duplicate source session')
    candidates = [w for s in sessions for w in s['context_windows']]
    events = [e for s in sessions for e in s['events']]; audit = Counter()
    for s in sessions: audit.update(s['audit'])
    by_prompt = defaultdict(list)
    for w in candidates: by_prompt[w['prompt']].append(w)
    for e in events:
        e['context'] = match_context(e,by_prompt[e['prompt']])
        e['sensitivity_context'] = match_context(e,by_prompt[e['prompt']],True) if e['kind']=='deleted' else []
    kept = defaultdict(list)
    for e in events:
        if e['kind']=='kept' and e['window'] and e['context']: kept[e['writer']].append(e)
    for e in events:
        e['kept_reference'] = None
        if e['kind'] != 'deleted' or not e['window'] or not e['context']: continue
        kept_candidates = kept[e['writer']]
        if kept_candidates:
            # Frozen equal-scale coordinates: relative position and log word length.
            length = max(1,len(e['span']['text'].split()))
            def distance(k):
                d=(e['position']-k['position'])**2+math.log(max(1,len(k['span']['text'].split()))/length)**2
                return d,k['session'],k['ordinal']
            k=min(kept_candidates,key=distance)
            e['kept_reference']=dict(id=k['id'],distance=distance(k)[0])
    complete=[e for e in events if e['kind']=='deleted' and e['window'] and e['context']]
    support=len(complete)>=150 and len({e['writer'] for e in complete})>=25
    summary=dict(card='WC2-inputs',sessions=len(sessions),writers=len({s['writer'] for s in sessions}),
        audit=dict(audit),complete_deleted_windows=sum(e['kind']=='deleted' and e['window'] is not None for e in events),
        complete_deleted_with_context=len(complete),writers_with_context=len({e['writer'] for e in complete}),
        complete_deleted_with_kept_reference=sum(e['kept_reference'] is not None for e in complete),
        support=support,support_policy='at least150 complete deleted windows with external-writer prompt references from at least25writers',
        context_window_count=len(candidates),unique_embedding_texts=len({t for e in events if e['window'] for t in
            [e['span']['text'],*e['span']['unchosen'],e['window']['text'],*[x['text'] for x in e['context']],
             *([e['sensitivity']['text']] if e['sensitivity'] else []),*[x['text'] for x in e['sensitivity_context']]]}),
        scientific_admission=False,counts_only=True)
    return dict(sessions=[{k:s[k] for k in ('session','writer','prompt','timestamp','typed_words')} for s in sessions],
                events=events,summary=summary)


def load(inputs,config):
    if config not in (CONFIG,PILOT,CONSTRUCTED): raise ValueError('fixed WC2 input design required')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}: raise ValueError('constructed fixture required')
        value=read(inputs['fixture'])
        if len(value)!=6: raise ValueError('six-session constructed fixture required')
        return value,None
    if set(inputs)!={'pmap_completion'}: raise ValueError('sealed PMAP source required')
    parent=Path(inputs['pmap_completion']).parent
    completed(inputs['pmap_completion'],parent/'PLAN.json')
    plan=read(parent/'PLAN.json')
    sources=Sources({k:plan['inputs'][k] for k in INPUTS})
    if len(sources.p2)!=config['expected_sessions']: raise ValueError('full source population differs')
    return sorted(sources.p2)[:config['session_limit']],sources


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    selected,sources=load(inputs,config); sessions=[]; pins=[]
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    for number,item in enumerate(selected):
        if sources is None:
            args=item; pin={}; sid=args['meta']['session']
        else:
            sid=item; pin=sources.metadata(sid)['source_hashes']; p=sources.inputs
            raw=(sources.root/sources.roster[sid]['path']).resolve()
            canonical=sources.root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
            args=dict(meta=sources.meta[sid],events=[json.loads(t) for t in raw.read_text(encoding='utf8').splitlines() if t.strip()],
                timeline=bound_record(p['session_index'],sources.p2[sid]),canonical=read(canonical),
                p6=bound_record(p['p6_index'],sources.p6[sid]))
        value=prepare_session(**args); sessions.append(value); pins.append(dict(session=sid,source_hashes=pin))
        dest=output/'sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(dest)!=value: raise ValueError('complete source replay differs')
        else: gzip_equal(dest,value)
        if sources is not None and sources.unit_binding(sid)!=pin: raise ValueError('source changed during extraction')
        progress(output/'PROGRESS.json',dict(phase='source-replay' if verification else 'source',done=number+1,total=len(selected)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists(): raise InterruptedError('owner requested yield')
    value=assemble(sessions); binding['source_units']=pins
    if verification:
        if read(output/'BINDING.json')!=binding or gzread(output/'EVENTS.json.gz')!=value: raise ValueError('WC2 preparation changed')
        if read(output/'SUMMARY.json')!=value['summary']: raise ValueError('WC2 support receipt changed')
        return dict(verified=True,full_source_replay=True)
    write_equal(output/'BINDING.json',binding);gzip_equal(output/'EVENTS.json.gz',value)
    write_equal(output/'SUMMARY.json',value['summary'])
    return dict(status='complete',counts_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
