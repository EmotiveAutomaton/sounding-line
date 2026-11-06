"""Private event-midpoint text and later visible menus for commissioned PLAN.

DESIGN CHECK: LESSONS 2-5 reread 2026-11-04; PLAN_SOURCE.md is prospective.
NULL/ALTERNATIVE: exact histories pass independent source replay regardless of
effect; malformed edits, future leakage and changed/unseen menus refuse.
All support counts retained. No provider call, model fit or scientific verdict.
"""
from collections import Counter
import json
from pathlib import Path
import time

from runners.stage9.coauthor import replay, suggestions
from runners.stage9.common import digest
from .timing_census import read, filehash
from .timing_p6 import write_equal, gzip_equal, gzread
from runners.stage14.common import atomic
from .week4_t4_menus_v2 import load as load_menus, normalize_pins


def configuration(mode):
    if mode not in ('constructed', 'timing', 'full'):
        raise ValueError('Unknown PLAN source scope')
    return dict(card='PLAN-source', mode=mode, seed=20261102,
                pilot_sessions=140, full_sessions=1399, midpoint='floor_event_count')


def byte_delta(document, value):
    """Independent byte slicing, deliberately not canonical apply_delta."""
    if value in ('', None):
        return document
    value = json.loads(value) if isinstance(value, str) else value
    if not isinstance(value, dict) or set(value) != {'ops'} or not isinstance(value['ops'], list):
        raise ValueError('Malformed delta')
    at, chunks = 0, []
    for op in value['ops']:
        if not isinstance(op, dict) or set(op)-{'retain', 'delete', 'insert', 'attributes'}:
            raise ValueError('Malformed operation')
        actions = set(op) & {'retain', 'delete', 'insert'}
        if len(actions) != 1:
            raise ValueError('Ambiguous operation')
        action = next(iter(actions))
        if action == 'insert':
            if not isinstance(op[action], str):
                raise ValueError('Nontext insertion')
            chunks.append(op[action].encode('utf-16-le'))
        else:
            n = op[action]
            if type(n) is not int or n < 0 or at+2*n > len(document):
                raise ValueError('Invalid UTF-16 boundary')
            if action == 'retain':
                chunks.append(document[at:at+2*n])
            at += 2*n
    result = b''.join(chunks)+document[at:]
    result.decode('utf-16-le')
    return result


def source_session(events, canonical, menus):
    if len(events) < 2:
        raise ValueError('Too few source events')
    cut = len(events)//2
    document = None
    midpoint = None
    opened = {}
    previous = None
    for ordinal, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError('Nonobject event')
        number = event.get('eventNum')
        if number is not None:
            if type(number) is not int or previous is not None and number <= previous:
                raise ValueError('Nonincreasing event order')
            previous = number
        name = event.get('eventName')
        if name == 'system-initialize':
            if document is not None or not isinstance(event.get('currentDoc'), str):
                raise ValueError('Invalid initialization')
            document = event['currentDoc'].encode('utf-16-le')
        else:
            if document is None:
                raise ValueError('Event before initialization')
            if name == 'suggestion-open':
                opened[ordinal] = dict(document=document.decode('utf-16-le'),
                                       options=suggestions(event.get('currentSuggestions')))
            document = byte_delta(document, event.get('textDelta'))
        if ordinal+1 == cut:
            midpoint = document.decode('utf-16-le')
    prefix = replay(events[:cut])
    whole = replay(events)
    if prefix['errors'] or prefix['final_document'] != midpoint:
        raise ValueError('Independent midpoint replay differs')
    if not whole['reconstructed'] or whole['errors'] or whole['final_document'] != document.decode('utf-16-le'):
        raise ValueError('Independent full document replay differs')
    for key in ('events', 'events_count', 'event_counts', 'deltas', 'errors', 'semantic_errors',
                'reconstructed', 'final_document', 'final_utf16_length', 'decision_counts'):
        if whole[key] != canonical[key]:
            raise ValueError('Frozen canonical replay differs: '+key)
    choices = {r['ordinal']: r for r in whole['events']}
    if set(opened) != set(choices):
        raise ValueError('Opened-menu census differs')
    for ordinal, row in choices.items():
        if opened[ordinal] != {k: row[k] for k in ('document', 'options')}:
            raise ValueError('Independent menu document/options differ')
    if len({m['ordinal'] for m in menus}) != len(menus):
        raise ValueError('Duplicate canonical menu')
    if {m['ordinal'] for m in menus} != {o for o, c in choices.items() if c['usable']}:
        raise ValueError('Canonical menu coverage differs')
    later, private = [], []
    for m in sorted(menus, key=lambda r: r['ordinal']):
        c = choices[m['ordinal']]
        if [o['original'] for o in c['options']] != m['options']:
            raise ValueError('Unseen or changed menu')
        indices = [o['index'] for o in c['options']]
        matched = [i for i, o in enumerate(c['options']) if o['index'] in c['matched_option_indices']]
        if c['decision'] in ('accept', 'edit'):
            if len(matched) != 1 or not c['verified_insertion']:
                raise ValueError('Ambiguous canonical insertion')
            expected_choice = matched[0]
        else:
            if matched or c['decision'] not in ('dismiss', 'ignore'):
                raise ValueError('Invalid canonical handling')
            expected_choice = len(indices) if c['decision']=='dismiss' else None
        if (m['choice'], m['handling'], m['original_option_ids']) != (expected_choice, c['decision'], indices):
            raise ValueError('Canonical choice binding differs')
        if m['ordinal'] < cut:
            continue
        later.append([o['trimmed'] for o in c['options']])
        private.append(dict(ordinal=m['ordinal'], key=m['key'], choice=m['choice'],
                            handling=m['handling'], original_option_ids=m['original_option_ids'],
                            original_texts=m['options']))
    counts = dict(raw_later_openings=sum(o >= cut for o in opened),
                  usable_later_openings=len(later),
                  later_choices=sum(m['choice'] is not None for m in private),
                  midpoint_nonempty=bool(midpoint.strip()))
    return dict(event_count=len(events), cut=cut, counts=counts,
                provider_text_only=dict(midpoint_text=midpoint, later_options=later),
                private_choices=private)


def fixture():
    events = [dict(eventName='system-initialize', currentDoc='A\U0001f600B\n')]
    # Four edits/padding precede midpoint; four shown menus follow it.
    events += [dict(eventName='text-insert', textDelta={'ops':[{'retain':3}, {'delete':1}, {'insert':'C'}]})]
    events += [dict(eventName='cursor', currentDoc='untrusted future document') for _ in range(6)]
    for i in range(4):
        events += [dict(eventName='suggestion-open', currentSuggestions=[
            dict(index=7, original='\nleft', trimmed='left'),
            dict(index=3, original='\nright', trimmed='right')]),
            dict(eventName='suggestion-close')]
    canonical = replay(events)
    menus = [dict(ordinal=r['ordinal'], key=str(r['ordinal']), choice=2,
                  handling='dismiss', original_option_ids=[7,3], options=['\nleft','\nright'])
             for r in canonical['events']]
    return events, canonical, menus


def stream(inputs, mode):
    if mode == 'constructed':
        if inputs:
            raise ValueError('Human inputs in constructed validation')
        e, c, m = fixture()
        yield dict(session='constructed', writer='constructed', genre='constructed'), e, c, m, {}
        return
    sessions, _ = load_menus(inputs, mode)
    source = read(inputs['source_inputs'])
    root = Path(source['repo_root'])
    raw = {s['session']: s for s in read(source['raw_roster'])}
    pins = normalize_pins(read(source['source_pins']))
    for s in sessions:
        meta = raw[s['session']]
        path = (root/meta['path']).resolve()
        path.relative_to(root)
        if filehash(path) != meta['source_sha256']:
            raise ValueError('Changed raw log')
        cp = root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':path.stem})+'.json')
        if filehash(cp) != pins[cp.relative_to(root).as_posix()]:
            raise ValueError('Changed canonical log')
        events = [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]
        yield s, events, read(cp), s['menus'], dict(raw_sha256=filehash(path), canonical_sha256=filehash(cp))


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']):
        raise ValueError('Changed frozen configuration')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    start = time.process_time()
    records, sources = [], []
    counts = Counter()
    for s, events, canonical, menus, binding in stream(inputs, config['mode']):
        row = source_session(events, canonical, menus)
        row.update(session=s['session'], writer=s['writer'], genre=s['genre'])
        records.append(row)
        sources.append(dict(session=s['session'], **binding))
        counts['sessions'] += 1
        for key, value in row['counts'].items():
            counts[key] += value
        for key in ('raw_later_openings', 'usable_later_openings', 'later_choices'):
            counts['sessions_ge4_'+key] += row['counts'][key] >= 4
            counts['nonempty_sessions_ge4_'+key] += row['counts'][key] >= 4 and row['counts']['midpoint_nonempty']
        atomic(output/'PROGRESS.json', dict(phase='verify' if verification else 'execute', sessions=len(records)))
    expected = 1 if config['mode']=='constructed' else 140 if config['mode']=='timing' else 1399
    if len(records) != expected:
        raise ValueError('Selected roster incomplete')
    summary = dict(mode=config['mode'], counts=dict(counts), required_t5_sessions=300,
                   source_replay=True, scientific_admission=False, paid_requests=0,
                   scope='Midpoint/source support only; PLAN calibration and T5 consumer admission remain.')
    values = {'SUMMARY.json':summary, 'BINDING.json':dict(config=config,
              inputs={k:filehash(v) for k,v in inputs.items()}, sources=sources)}
    if verification:
        if gzread(output/'PRIVATE_SESSIONS.json.gz') != records:
            raise ValueError('Complete private source replay differs')
        for name, value in values.items():
            if read(output/name) != value:
                raise ValueError('Aggregate source replay differs')
        return dict(verified=True, complete_source_replay=True, scientific_admission=False)
    for name, value in values.items():
        write_equal(output/name, value)
    gzip_equal(output/'PRIVATE_SESSIONS.json.gz', records)
    used = time.process_time()-start
    size = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
    write_equal(output/'TIMING.json', dict(cpu_seconds=used,
        projected_full_cpu_seconds_with_fresh_verification=3*used*1399/expected,
        projected_full_output_bytes=3*size*1399/expected))
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
