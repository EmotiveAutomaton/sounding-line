"""D5 complete, provenance-separated text and process source preparation.

DESIGN CHECK: LESSONS 3-5 read 2026-10-29. NULL and ALTERNATIVE retain the
complete prepared source; no effect or identification gate is computed.
Whole raw timeline and process-row replay must equal their completed sources.
Unknown origin and absent text share stay explicit; changed joins/bytes refuse.
"""
from collections import Counter
from pathlib import Path
import hashlib, json, math, time
from runners.stage14.common import read, filehash, freeze, atomic
from runners.stage9.coauthor import units
from runners.drive.timeline import rebuild
from .timing_pmap_source import INPUTS, completed, bound_record
from .timing_pmap_source_recovery import Sources
from .timing_p6 import training_sequences, gzip_equal, gzread

CONFIG = dict(card='D5-inputs', schema=1)
ORIGINS = ('prompt', 'typed', 'accepted', 'accepted_edited', 'api_unknown')


def text_views(timeline, p6, process, meta):
    identity = tuple(timeline[k] for k in ('session', 'writer', 'prompt'))
    for row in (p6, process, meta):
        if tuple(row[k] for k in ('session', 'writer', 'prompt')) != identity:
            raise ValueError('Source identity differs')
    start, end = meta['timestamp'], meta['end_at']
    if not all(type(v) in (int, float) and math.isfinite(v) for v in (start, end)) or end < start:
        raise ValueError('Invalid source chronology')
    if (p6['timestamp'], p6['end_at']) != (start, end) or process['timestamp'] != start:
        raise ValueError('Source chronology differs')
    cursor = 0; texts = []; typed = []; codepoints = Counter(); utf16 = Counter()
    for span in timeline['final_spans']:
        origin, text = span['origin'], span['text']
        if origin not in ORIGINS or not isinstance(text, str) or not text:
            raise ValueError('Invalid span origin or text')
        a, b = span['start_utf16'], span['end_utf16']
        if type(a) is not int or type(b) is not int or a != cursor or b-a != len(units(text)):
            raise ValueError('Noncontiguous UTF16 coverage')
        cursor = b; texts.append(text); codepoints[origin] += len(text); utf16[origin] += b-a
        if origin == 'typed':
            if typed and typed[-1]['end_utf16'] == a:
                typed[-1]['text'] += text; typed[-1]['end_utf16'] = b
            else:
                typed.append(dict(start_utf16=a, end_utf16=b, text=text))
    if ''.join(texts) != timeline['final_document'] or cursor != len(units(timeline['final_document'])):
        raise ValueError('Final document coverage differs')
    sequences = training_sequences(timeline)
    if sequences != p6['training_sequences']:
        raise ValueError('Final typed token source differs')
    produced = dict(sorted(Counter(w['token'] for w in p6['words'] if w['is_word']).items()))
    if produced != process['word_counts'] or sum(produced.values()) != process['typed_words']:
        raise ValueError('Production token source differs')
    nonprompt = sum(codepoints.values())-codepoints['prompt']
    model = codepoints['accepted']+codepoints['accepted_edited']
    reason = 'empty_nonprompt_text' if not nonprompt else 'unknown_api_origin' if codepoints['api_unknown'] else None
    return dict(session=identity[0], writer=identity[1], prompt=identity[2],
        timestamp=start, end_at=end, final_document=timeline['final_document'],
        final_spans=timeline['final_spans'], final_typed_groups=typed,
        final_typed_token_sequences=sequences, production_tokens=p6['words'],
        process=process, source_hashes=process['source_hashes'],
        codepoints_by_origin={k:codepoints[k] for k in ORIGINS},
        utf16_by_origin={k:utf16[k] for k in ORIGINS},
        nonprompt_codepoints=nonprompt, model_share=None if reason else model/nonprompt,
        model_share_missing_reason=reason,
        known_accepted_fraction=model/nonprompt if nonprompt else None,
        final_typed_codepoints=codepoints['typed'],
        source_only=True, scientific_admission=False)


def replay_timeline(events, meta, timeline):
    fresh = rebuild(events, meta['rows'])
    fresh.update({k:timeline[k] for k in ('session', 'writer', 'prompt', 'source_sha256')})
    if fresh != timeline:
        raise ValueError('Whole raw timeline replay differs')


def load(inputs):
    if set(inputs) != {'pmap_complete'}:
        raise ValueError('Exact source contract required')
    path = Path(inputs['pmap_complete']).resolve(); terminal = read(path)
    if terminal['status'] != 'COMPLETE' or not terminal['fresh_process_verified']:
        raise ValueError('Incomplete process source')
    plan_path = path.parent/'PLAN.json'
    if terminal['outputs'].get('PLAN.json') != filehash(plan_path):
        raise ValueError('Process plan changed')
    old_plan = read(plan_path)
    source = Sources({k:old_plan['inputs'][k] for k in INPUTS})
    saved = {}
    for name in sorted(terminal['outputs']):
        if name.startswith('output/sessions/') and name.endswith('.json.gz'):
            p = (path.parent/name).resolve(); p.relative_to(path.parent)
            completed(path, p); row = gzread(p)
            if row['session'] in saved: raise ValueError('Duplicate process session')
            saved[row['session']] = (p, row)
    if set(saved) != set(source.p2) or len(saved) != 1399 or len({v[1]['writer'] for v in saved.values()}) != 61:
        raise ValueError('Complete source census differs')
    return source, saved


def compute(output, inputs, config, verification=False):
    if config != CONFIG: raise ValueError('Frozen D5 source configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    binding = dict(inputs={k:filehash(v) for k,v in inputs.items()}, config=config)
    if (output/'BINDING.json').exists() and read(output/'BINDING.json') != binding:
        raise ValueError('Input binding changed')
    if not verification: freeze(output/'BINDING.json', binding)
    source, saved = load(inputs); index = []; counts = Counter(); absent = Counter()
    started = time.process_time()
    for i, sid in enumerate(sorted(saved)):
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():
            raise InterruptedError('D5 source yields at session boundary')
        old_path, old = saved[sid]
        fresh = source.session(sid)
        if fresh != old: raise ValueError('Complete process replay differs')
        timeline = bound_record(source.inputs['session_index'], source.p2[sid])
        p6 = bound_record(source.inputs['p6_index'], source.p6[sid])
        meta = source.meta[sid]; raw = (source.root/source.roster[sid]['path']).resolve()
        raw.relative_to(source.root)
        if filehash(raw) != fresh['source_hashes']['raw']:
            raise ValueError('Raw source changed')
        events = [json.loads(line) for line in raw.read_text(encoding='utf8').splitlines()]
        replay_timeline(events, meta, timeline)
        value = text_views(timeline, p6, fresh, meta)
        name = 'sessions/'+hashlib.sha256(sid.encode()).hexdigest()+'.json.gz'
        if verification:
            if gzread(output/name) != value: raise ValueError('Fresh D5 source replay differs')
        else: gzip_equal(output/name, value)
        counts.update(value['codepoints_by_origin'])
        absent[value['model_share_missing_reason'] or 'available'] += 1
        index.append(dict(session=sid, writer=value['writer'], file=name,
            sha256=filehash(output/name), pmap_sha256=filehash(old_path), source_hashes=fresh['source_hashes']))
        if i % 25 == 0: atomic(output/'PROGRESS.json', dict(phase='verify' if verification else 'source', done=i+1, total=len(saved)))
        if not verification and i+1 == math.ceil(.1*len(saved)) and not (output/'FIRST_TENTH.json').exists():
            freeze(output/'FIRST_TENTH.json', dict(sessions=i+1,
                projected_cpu_seconds=max(.001,4*(time.process_time()-started)*len(saved)/(i+1)),
                scope='Two full source passes times two safety factor; not scientific cost admission'))
    summary = dict(sessions=len(index), writers=len({r['writer'] for r in index}),
        codepoints_by_origin={k:counts[k] for k in ORIGINS}, model_share_support=dict(sorted(absent.items())),
        source_only=True, all_sessions_retained=True, whole_timeline_replay=True,
        process_replay_equal=True, final_typed_sequences_equal=True, effect_computed=False,
        scientific_admission=False, scope='Recorded text provenance and process features; not cognitive contribution')
    for name, value in {'BINDING.json':binding, 'SOURCE_UNITS.json':index, 'SUMMARY.json':summary}.items():
        if verification:
            if read(output/name) != value: raise ValueError('Complete D5 source replay differs')
        else: freeze(output/name, value)
    return dict(verified=True, full_fresh_source_replay=True, source_only=True) if verification else dict(status='complete', source_only=True)


def execute(output, inputs, config): return compute(output, inputs, config)
def verify(output, inputs, config): return compute(output, inputs, config, True)
