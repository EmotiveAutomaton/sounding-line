"""WB1.h1 physical API insertion identities; original choice eligibility retained.

DESIGN CHECK: LESSONS 2 and 3-5 read; explicit October 29 healing commission.
NULL no eligible acceptance => empty eligible table, complete source retained.
ALTERNATIVE exact known surviving original UTF-16 units, not replacement units.
All excluded inserts remain explicit; source/final/population disagreement fails.
Old shared attempts are unchanged. No scientific scores or embeddings here.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta, replay
from .timing_census import read, filehash
from .timing_events import source_sessions, accepted_lifetimes as old_lifetimes
from .timing_p6 import write_equal, progress

CONFIG = dict(card='WB1.h1-insertion-provenance', mode='constructed', expected_sessions=7)


def reconstruct(events, timeline):
    canonical = replay(events)
    if canonical['errors'] or not canonical['reconstructed']:
        raise ValueError('canonical document reconstruction failed')
    choices = {r['ordinal']: r for r in canonical['events']}
    eligible = {r['ordinal'] for r in timeline['decisions'] if r['handling'] in ('accept', 'edit')}
    expected = {k for k, r in choices.items() if r['usable'] and r['decision'] in ('accept', 'edit')}
    if eligible != expected:
        raise ValueError('canonical/P2 eligible population differs')
    doc = units(events[0]['currentDoc']); owners = [None]*len(doc)
    current = pending = None
    physical = {}; menu_instances = defaultdict(list)
    for ordinal, event in enumerate(events):
        if event['eventName'] == 'suggestion-open': current = ordinal
        if event['eventName'] == 'suggestion-select': pending = current
        if not delta_ops(event.get('textDelta')): continue
        prior = owners; before = text_of(doc)
        doc, owners, _ = apply_delta(doc, owners, event['textDelta'], insertion_owner=None)
        if event.get('eventSource') != 'user' and pending is not None:
            after = text_of(doc); count = len(doc)-len(prior)
            if not before.endswith('\n') or not after.startswith(before[:-1]) or not after.endswith('\n') or count < 0:
                raise ValueError('API insertion disagrees with canonical P2 append')
            choice = choices.get(pending)
            if choice is None: raise ValueError('physical insertion has no canonical menu')
            valid = pending in eligible
            if valid:
                offered = {r['original'].replace('\r\n','\n').replace('\r','\n')
                           for r in choice['options'] if r['index'] in choice['matched_option_indices']}
                if not choice['verified_insertion'] or count <= 0 or after[len(before)-1:-1] not in offered:
                    raise ValueError('eligible insertion not verified against offered text')
            physical[ordinal] = dict(menu_ordinal=pending, insertion_ordinal=ordinal,
                original_utf16=count, eligible=valid, exclusion=choice['exclusion'])
            menu_instances[pending].append(ordinal)
            owners = prior[:-1]+[(ordinal,i) for i in range(count)]+prior[-1:]
            pending = None
        if len(owners) != len(doc): raise ValueError('physical provenance length differs')
    if text_of(doc) != timeline['final_document'] or canonical['final_document'] != timeline['final_document']:
        raise ValueError('final document differs')
    counts = Counter(x[0] for x in owners if x is not None)
    for k, r in physical.items(): r['surviving_utf16'] = counts[k]
    # P2's accepted labels include excluded selections but never replacement text.
    p2 = Counter()
    for span in timeline['final_spans']:
        if span['origin'] in ('accepted','accepted_edited'):
            p2[span['insertion_ordinal']] += span['end_utf16']-span['start_utf16']
    observed = Counter()
    for r in physical.values(): observed[r['menu_ordinal']] += r['surviving_utf16']
    if +p2 != +observed: raise ValueError('P2 accepted-origin survival differs')
    lifetimes = {}
    for menu in sorted(eligible):
        found = menu_instances[menu]
        if len(found) != 1: raise ValueError('eligible menu has nonunique physical insertion')
        r = physical[found[0]]
        lifetimes[menu] = {k:r[k] for k in ('original_utf16','surviving_utf16')}
    return dict(eligible=lifetimes, physical=[physical[k] for k in sorted(physical)],
                all_events=len(events), final_utf16=len(doc), canonical_eligible=len(eligible))


def fixture(kind):
    """Complete raw logs with actual canonical options, no supplied eligibility oracle."""
    events=[dict(eventName='system-initialize',eventSource='api',eventTimestamp=0,currentDoc='p\n')]
    def add(name='text-insert',source='user',**fields):
        events.append(dict(eventName=name,eventSource=source,eventTimestamp=len(events)*1000,**fields))
    text='a\U0001f600b'
    add('suggestion-open', currentSuggestions=[dict(index=0,original=text,trimmed=text)])
    add('suggestion-select',currentSuggestionIndex=0)
    insert = 'unmatched' if kind=='unmatched' else text
    ops=[dict(retain=1),dict(insert=insert)]
    if kind=='newline': ops=[dict(retain=1),dict(insert=insert+'\n'),dict(delete=1)]
    if kind=='rewrite': ops=[dict(delete=2),dict(insert='p'+insert+'\n')]
    add(source='api',textDelta=dict(ops=ops))
    if kind=='repeated':
        add('suggestion-select',currentSuggestionIndex=0)
        add(source='api',textDelta=dict(ops=[dict(retain=5),dict(insert='again')]))
    if kind=='edited':
        add(textDelta=dict(ops=[dict(retain=2),dict(insert='X')]))
        add('text-delete',textDelta=dict(ops=[dict(retain=3),dict(delete=2)]))
    if kind=='deleted': add('text-delete',textDelta=dict(ops=[dict(retain=1),dict(delete=4)]))
    c=replay(events)
    rows=[dict(key=str(r['ordinal']),ordinal=r['ordinal'],end_ordinal=len(events),handling=r['decision'],menu=r['options'])
          for r in c['events'] if r['usable']]
    from runners.drive.timeline import rebuild
    return events,rebuild(events,rows)


def run(output,inputs,config,verification=False):
    mode=config.get('mode'); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    if mode=='constructed':
        if config!=CONFIG or inputs: raise ValueError('frozen constructed configuration required')
        cases=[(k,*fixture(k)) for k in ('plain','newline','rewrite','repeated','unmatched','edited','deleted')]
    elif mode in ('timing','corpus'):
        expected=dict(card=CONFIG['card'],mode=mode,expected_sessions=1399)
        if config!=expected or set(inputs)!={'source_inputs'}: raise ValueError('frozen source configuration required')
        source=read(inputs['source_inputs'])
        def stream():
            for row,timeline,meta in source_sessions(source,'raw_roster'):
                raw=Path(source['repo_root'])/meta['path']
                events=[json.loads(s) for s in raw.read_text(encoding='utf8').splitlines()]
                yield row['session'],events,timeline
        cases=stream()
    else: raise ValueError('unknown mode')
    started=time.process_time(); rows=[]
    for sid,events,timeline in cases:
        result=reconstruct(events,timeline)
        try:
            old=old_lifetimes(events,timeline['final_document'])
            for key,value in result['eligible'].items():
                if {k:old[key][k] for k in value}!=value: raise ValueError('old/new eligible lifetime differs')
            old_status='exact_eligible_parity'
        except ValueError as exc:
            if str(exc) not in ('empty/repeated accepted span',): raise
            old_status=str(exc)
        payload=dict(session=sid,source_sha256=timeline.get('source_sha256'),reconstruction=result,old_status=old_status)
        import hashlib
        target=output/'sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json')
        if verification:
            # JSON keys become strings on disk; compare canonical JSON representations.
            if json.dumps(read(target),sort_keys=True)!=json.dumps(json.loads(json.dumps(payload)),sort_keys=True):
                raise ValueError('independent source replay differs')
        else: write_equal(target,payload)
        rows.append(dict(session=sid,path=target.relative_to(output).as_posix(),sha256=filehash(target),
            eligible=len(result['eligible']),physical=len(result['physical']),old_status=old_status))
        progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=len(rows),total=140 if mode=='timing' else config['expected_sessions']))
        if mode=='timing' and len(rows)==140: break
    expected=140 if mode=='timing' else config['expected_sessions']
    if len(rows)!=expected: raise ValueError('complete source population differs')
    result=dict(sessions=len(rows),rows=rows,scientific_admission=False,full_population=mode=='corpus',
        bindings={k:filehash(v) for k,v in inputs.items()})
    if verification:
        if read(output/'RESULTS.json')!=result: raise ValueError('source index replay differs')
        return dict(verified=True,complete_source_replay=True,scientific_admission=False)
    write_equal(output/'RESULTS.json',result)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,sessions=len(rows)))
    return dict(status='complete',scientific_admission=False,sessions=len(rows))


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
