"""TR3 exact edit stream and insertion provenance, without feature selection.

DESIGN CHECK: LESSONS 2-5 reread in the 2026-10-26 TR3 build. NULL and
ALTERNATIVE retain every session and edit. False adjacency, survivor selection,
API-as-user, wrong Unicode boundaries or changed source must fail. Exhaustive
states: exact source preparation or explicit refusal; no scientific result.
"""
from collections import Counter
import hashlib
from pathlib import Path
import time

from runners.stage9.coauthor import apply_delta, delta_ops, text_of, units
from . import week3_frames_io as source
from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import gzip_equal, gzread, write_equal, progress
from .week3_tr3_inputs import clock


def prepare(meta, events, timeline, canonical, exposure):
    identity = {k: meta[k] for k in ('session', 'writer', 'prompt')}
    if any(any(row[k] != v for k, v in identity.items()) for row in (timeline, exposure)):
        raise ValueError('source identity mismatch')
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('initialization required')
    initial = events[0]['currentDoc']
    doc = units(initial); owners = [None] * len(doc)
    start, end = clock(meta['timestamp']), clock(meta['end_at'])
    if (exposure['start'], exposure['end']) != (start, end):
        raise ValueError('source clocks differ')
    edits = []; sources = {}; inserted = Counter(); previous = start
    for ordinal, event in enumerate(events):
        stamp = clock(event['eventTimestamp'])
        if not start <= stamp <= end or stamp < previous:
            raise ValueError('unordered or out-of-range event clock')
        previous = stamp
        if ordinal and event['eventName'] == 'system-initialize':
            raise ValueError('repeated initialization')
        ops = delta_ops(event.get('textDelta'))
        if not ops:
            continue
        label = event.get('eventSource')
        if label is not None and not isinstance(label, str):
            raise ValueError('invalid source label')
        sources[ordinal] = label
        for op in ops:
            if 'insert' in op:
                # units validates text before the character count is trusted.
                units(op['insert']); inserted[label] += len(op['insert'])
        doc, owners, _ = apply_delta(doc, owners, {'ops': ops}, insertion_owner=ordinal)
        edits.append(dict(ordinal=ordinal, timestamp=stamp, source=label, operations=ops))
    final = text_of(doc)
    if final != canonical['final_document'] or final != timeline['final_document']:
        raise ValueError('final document differs from authenticated source')
    if inserted['user'] != exposure['typed_inserted_characters']:
        raise ValueError('user insertion total differs from exposure census')
    final_runs = []; begin = 0
    while begin < len(doc):
        stop = begin + 1
        while stop < len(doc) and owners[stop] == owners[begin]:
            stop += 1
        content = text_of(doc[begin:stop])  # Refuses a mixed-ownership surrogate.
        owner = owners[begin]
        final_runs.append(dict(start_utf16=begin, end_utf16=stop,
            insertion_ordinal=owner, source=sources.get(owner), characters=len(content),
            initial=owner is None))
        begin = stop
    return dict(**identity, initial_document=initial, edits=edits,
        final_document=final, final_ownership_runs=final_runs,
        user_inserted_characters=inserted['user'],
        final_user_characters=sum(r['characters'] for r in final_runs if r['source']=='user'),
        all_inserted_characters=sum(inserted.values()),
        scientific_admission=False, outcome_features_prepared=False)


def run(output, inputs, config, verification=False):
    mode = config.get('mode')
    if config != dict(mode=mode, seed=20261026) or mode not in ('constructed', 'full'):
        raise ValueError('frozen typing configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if mode == 'constructed':
        if set(inputs) != {'fixture'}: raise ValueError('fixture required')
        selected = read(inputs['fixture'])['sessions']; sources = None; parent = None
    else:
        if set(inputs) != {'pmap_completion', 'exposure_completion'}:
            raise ValueError('complete parent inputs required')
        parent = Path(inputs['exposure_completion']).parent
        completed(inputs['exposure_completion'], parent/'output/CENSUS.json')
        selected, sources = source.load({'pmap_completion':inputs['pmap_completion']},
            dict(card='TR3-typing',mode='full',expected_sessions=1399,session_limit=1399,seed=20261026))
        if set(selected) != {r['session'] for r in read(parent/'output/CENSUS.json')['roster']}:
            raise ValueError('parent population differs')
    stats = Counter(); bindings = []; started = time.process_time()
    for i, item in enumerate(selected):
        if sources is None:
            args = item; pins = {}
        else:
            args, pins = source.source_args(item, sources); args.pop('p6')
            unit = parent/'output/sessions'/(hashlib.sha256(item.encode()).hexdigest()+'.json.gz')
            completed(inputs['exposure_completion'], unit)
            args['exposure'] = gzread(unit)
        row = prepare(**args); sid = row['session']
        dest = output/'sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(dest) != row: raise ValueError('typing session replay differs')
        else: gzip_equal(dest, row)
        stats.update(sessions=1, edits=len(row['edits']),
            user_inserted_characters=row['user_inserted_characters'],
            final_user_characters=row['final_user_characters'])
        bindings.append(dict(session=sid, source_hashes=pins))
        if sources is not None and sources.unit_binding(sid) != pins:
            raise ValueError('source changed during typing preparation')
        progress(output/'PROGRESS.json',dict(phase='verify-typing' if verification else 'typing',done=i+1,total=len(selected)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('typing yields at complete session boundary')
    summary = dict(stats, full_population=mode=='full', constructed=mode=='constructed',
        outcome_features_prepared=False, scientific_admission=False,
        scope='Exact edit stream and final insertion provenance; no feature or effect')
    payloads = {'SUMMARY.json':summary, 'BINDING.json':dict(config=config,
        inputs={k:filehash(v) for k,v in inputs.items()}, units=bindings)}
    for name, value in payloads.items():
        if verification:
            if read(output/name) != value: raise ValueError('typing aggregate replay differs')
        else: write_equal(output/name,value)
    if verification: return dict(verified=True,complete_typing_replay=True,scientific_admission=False)
    if not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,sessions=len(selected)))
    return dict(status='complete',counts_only=True,summary=summary,scientific_admission=False)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
