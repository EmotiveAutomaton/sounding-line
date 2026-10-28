"""P3c complete saved edit-pair census and blinded calibration preparation.

DESIGN CHECK: LESSONS sections 2-5 reread for this design 2026-10-27.
NULL and ALTERNATIVE retain identical event populations and sampling rules.
Incomplete provenance is disclosed, never filtered by old intent labels. Missing
or duplicate events, changed source bytes and mismatched saved replay refuse.
This source instrument computes no intent predictions, agreement or effects.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random

from runners.stage14.common import read, filehash, freeze, atomic

CONFIG = dict(version=1, seed=20261026, calibration_pairs=200, timing_pairs=1000)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf8')).hexdigest()


def terminal(path):
    c = read(path)
    if c.get('status') != 'COMPLETE' or not c.get('fresh_process_verified'):
        raise ValueError('verified complete source required')
    return Path(path).parent.resolve(), c


def authenticated(source, relative):
    base, c = source
    path = (base / relative).resolve()
    path.relative_to(base)
    if c['outputs'].get(relative) != filehash(path):
        raise ValueError('completed source bytes differ')
    return path


def pairs(unit):
    for name in ('session', 'writer', 'prompt'):
        if not isinstance(unit[name], str) or not unit[name]:
            raise ValueError('source identity required')
    rows, seen = [], set()
    for e in sorted(unit['edits'], key=lambda r: r['ordinal']):
        ordinal = e['ordinal']
        if type(ordinal) is not int or ordinal < 0 or ordinal in seen:
            raise ValueError('unique edit ordinal required')
        seen.add(ordinal)
        if any(not isinstance(e[k], str) for k in ('before', 'after', 'changed_before', 'changed_after')):
            raise ValueError('unmodified text strings required')
        counts = e['deleted_origin_counts']; owners = e['accepted_owners_touched']
        if not isinstance(counts, dict) or any(not isinstance(k, str) or type(v) is not int or v < 0 for k,v in counts.items()):
            raise ValueError('invalid source provenance counts')
        if not isinstance(owners, list) or any(type(v) is not int or v < 0 for v in owners) or len(set(owners)) != len(owners):
            raise ValueError('invalid source owner links')
        expected = 'model' if owners else 'own' if counts and set(counts) == {'typed'} else 'other'
        if e['origin'] != expected:
            raise ValueError('source provenance category differs')
        rows.append(dict(key=digest([unit['session'], ordinal]), session=unit['session'], writer=unit['writer'],
            prompt=unit['prompt'], ordinal=ordinal, before=e['before'], after=e['after'],
            changed_before=e['changed_before'], changed_after=e['changed_after'],
            origin=e['origin'], deleted_origin_counts=counts, accepted_owners_touched=sorted(owners),
            pair_content_sha256=digest([e['before'], e['after']])))
    return rows


def save_unit(path, value, verification):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf8')
    if verification or path.exists():
        if gzip.decompress(path.read_bytes()) != data:
            raise ValueError('saved unit replay differs')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(gzip.compress(data, mtime=0))


def selection(keys):
    if len(keys) != len(set(keys)) or len(keys) < CONFIG['calibration_pairs']:
        raise ValueError('unique complete calibration population required')
    # Input order is canonical (session, ordinal). Each event is a sampling unit;
    # repeated text remains repeated evidence and is disclosed separately.
    order = list(keys)
    random.Random(CONFIG['seed']).shuffle(order)
    return order, keys[:CONFIG['timing_pairs']]


def run(output, inputs, config, verification=False):
    mode = config.get('mode')
    if config != dict(CONFIG, mode=mode) or mode not in ('constructed', 'full'):
        raise ValueError('frozen source configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    binding = dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()})
    if (output/'BINDING.json').exists() and read(output/'BINDING.json') != binding:
        raise ValueError('source binding changed')
    if mode == 'constructed':
        if set(inputs) != {'fixture'}: raise ValueError('constructed source differs')
        units = read(inputs['fixture'])['sessions']; source = None
        index = [dict(session=u['session'], unit=u) for u in units]
        source_summary = None
    else:
        if set(inputs) != {'p5_completion', 'p5_plan'}: raise ValueError('explicit completed P5 source required')
        source = terminal(inputs['p5_completion']); plan = read(inputs['p5_plan'])
        if Path(inputs['p5_plan']).resolve() != source[0]/'PLAN.json' or plan['module'] != 'runners.drive.cards.events_p5':
            raise ValueError('unexpected source plan')
        for path, h in plan['pins'].items():
            if filehash(path) != h: raise ValueError('historical source pin changed')
        index = read(authenticated(source, 'output/SESSION_INDEX.json'))
        source_summary = read(authenticated(source, 'output/SUMMARY.json'))
    if len({r['session'] for r in index}) != len(index): raise ValueError('duplicate source session')
    keys, entries, seals, writers, content_counts = [], [], [], set(), Counter()
    counts = Counter(); origins = Counter(); sampled_rows = {}
    for number, entry in enumerate(sorted(index, key=lambda r: r['session'])):
        sid = entry['session']
        if source is None:
            unit = entry['unit']; source_hash = None
        else:
            path = authenticated(source, 'output/'+entry['file'])
            source_hash = filehash(path)
            if source_hash != entry['sha256']: raise ValueError('source index hash differs')
            unit = json.loads(gzip.decompress(path.read_bytes()))
        if unit['session'] != sid: raise ValueError('source path identity differs')
        rows = pairs(unit); writers.add(unit['writer']); keys.extend(r['key'] for r in rows)
        name = 'pairs/'+digest(sid)+'.json.gz'
        save_unit(output/name, dict(session=sid, writer=unit['writer'], rows=rows), verification)
        entries.append(dict(session=sid, file=name, sha256=filehash(output/name), pairs=len(rows)))
        seals.append(dict(session=sid, source_sha256=source_hash))
        for r in rows:
            origins[r['origin']] += 1; content_counts[r['pair_content_sha256']] += 1
            counts['pairs'] += 1
            counts['unchanged_pair'] += r['before'] == r['after']
            counts['empty_before'] += not r['before'].strip()
            counts['empty_after'] += not r['after'].strip()
            counts['multiple_accepted_owners'] += len(r['accepted_owners_touched']) > 1
            counts['mixed_deleted_origins'] += len(r['deleted_origin_counts']) > 1
        atomic(output/'PROGRESS.json', dict(phase='verify-pairs' if verification else 'pairs',done=number+1,total=len(index)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('source preparation yields at session boundary')
    if mode == 'full' and (len(index) != 1399 or len(writers) != 61 or counts['pairs'] != source_summary['edits'] or len(index) != source_summary['sessions']):
        raise ValueError('complete primary population required')
    order, timing = selection(keys)
    calibration = order[:CONFIG['calibration_pairs']]; chosen = set(calibration)
    for entry in entries:
        u = json.loads(gzip.decompress((output/entry['file']).read_bytes()))
        sampled_rows.update({r['key']:r for r in u['rows'] if r['key'] in chosen})
    blind, mapping = [], []
    for i, key in enumerate(calibration):
        r = sampled_rows[key]; alias = f'pair-{i+1:03d}'
        blind.append(dict(pair_id=alias, before=r['before'], after=r['after']))
        mapping.append(dict(pair_id=alias, key=key, pair_content_sha256=r['pair_content_sha256']))
    summary = dict(sessions=len(index), writers=len(writers), counts=dict(sorted(counts.items())),
        origins=dict(sorted(origins.items())), unique_pair_contents=len(content_counts),
        calibration_pairs=len(blind), calibration_unique_contents=len({r['pair_content_sha256'] for r in mapping}),
        timing_pairs=len(timing), constructed=mode=='constructed', scientific_admission=False,
        labels_computed=False, agreement_computed=False, event_population='Every completed P5 edit event; mixed and other provenance retained')
    payloads = {'BINDING.json':binding, 'SOURCE_UNITS.json':seals, 'SESSION_INDEX.json':entries,
        'SUMMARY.json':summary, 'SAMPLE_ORDER.json':order, 'TIMING_ORDER.json':timing,
        'BLIND_CALIBRATION.json':blind, 'CALIBRATION_MAP.json':mapping}
    for name, value in payloads.items():
        if verification:
            if read(output/name) != value: raise ValueError('complete saved-source replay differs')
        else: freeze(output/name, value)
    if verification: return dict(verified=True, complete_input_replay=True, scientific_admission=False)
    return dict(status='complete', summary=summary, scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
