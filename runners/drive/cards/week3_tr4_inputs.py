"""TR4 complete handling/chronology inputs; no forecast or scientific score.

DESIGN CHECK: LESSONS sections 2-5 read 2026-10-27. Under NULL and ALTERNATIVE
every primary session remains, with four canonical classes and unknowns apart.
Original menus count once; reopened displays are never new decisions. Missing
coverage, changed bindings, invalid classes and replay disagreement refuse.
Overlapping/touching sessions retain explicit ambiguity, never invented order.
Known-answer checks cover all classes, empty/orphan displays and chronology.
"""
from collections import Counter, defaultdict
import hashlib
import math
from pathlib import Path
import time

from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import gzread, write_equal, progress

CLASSES = ('accept', 'edit', 'dismiss', 'ignore')
SEED = 20261026


def session_counts(unit, roster):
    if any(unit[k] != roster[k] for k in ('session', 'writer', 'prompt', 'start', 'end')):
        raise ValueError('session identity or clock differs')
    start, end = unit['start'], unit['end']
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in (start, end)) or end < start:
        raise ValueError('finite ordered session clocks required')
    menus = {}; counts = Counter(); unknown = Counter(); repeats = orphans = 0
    previous = -1; last_stamp = start
    for d in unit['displays']:
        ordinal, stamp = d['ordinal'], d['timestamp']
        if type(ordinal) is not int or ordinal <= previous:
            raise ValueError('display ordinal order differs')
        if type(stamp) not in (int, float) or not math.isfinite(stamp) or not last_stamp <= stamp <= end:
            raise ValueError('display clock order differs')
        previous, last_stamp = ordinal, stamp
        if type(d['reopened']) is not bool or type(d['handling_usable']) is not bool:
            raise ValueError('boolean handling/reopen flag required')
        label = d['handling']; usable = d['handling_usable']
        if (usable and label not in CLASSES) or (not usable and label is not None):
            raise ValueError('canonical handling class differs')
        options = d['options']
        if not isinstance(options, list) or any(not isinstance(x, dict) or
                not {'index', 'original', 'trimmed'} <= x.keys() or
                type(x['index']) is not int or not isinstance(x['original'], str) or
                not isinstance(x['trimmed'], str) for x in options):
            raise ValueError('canonical option-record schema required')
        origin = d['origin']
        if d['reopened']:
            repeats += 1
            if origin is None:
                if options or usable or not d.get('unanchored_display_event'):
                    raise ValueError('invalid unanchored reopen')
                orphans += 1
                continue
            if origin not in menus:
                raise ValueError('reopen lacks original menu')
            old = menus[origin]
            if (label, usable, d.get('handling_exclusion')) != (
                    old['handling'], old['handling_usable'], old.get('handling_exclusion')):
                raise ValueError('reopen handling differs')
            if options != old['options'] and not (options == [] and d.get('empty_display_event')):
                raise ValueError('reopen alternatives differ')
            continue
        if type(origin) is not int or origin != ordinal or origin in menus:
            raise ValueError('original menu identity differs')
        if not options and usable:
            raise ValueError('empty original menu cannot supply handling')
        menus[origin] = d
        if usable:
            counts[label] += 1
        else:
            reason = d.get('handling_exclusion')
            if not isinstance(reason, str) or not reason:
                raise ValueError('unknown handling needs source reason')
            unknown[reason] += 1
    if roster['displays'] != len(unit['displays']):
        raise ValueError('display coverage differs')
    return dict(session=unit['session'], writer=unit['writer'], prompt=unit['prompt'],
        start=start, end=end, half=roster['half'], counts={k: counts[k] for k in CLASSES},
        known_menus=sum(counts.values()), unknown_menus=sum(unknown.values()),
        unknown_reasons=dict(sorted(unknown.items())), original_menus=len(menus),
        reopened_displays=repeats, unanchored_reopens=orphans,
        displays=len(unit['displays']), observed_choices=bool(counts))


def assemble(rows, census, split, full):
    roster = census['roster']; by_id = {r['session']: r for r in roster}
    counts = Counter(r['writer'] for r in rows)
    if len(by_id) != len(roster) or len({r['session'] for r in rows}) != len(rows) or set(by_id) != {r['session'] for r in rows}:
        raise ValueError('complete unique session coverage required')
    if split['seed'] != SEED or split['session_counts'] != dict(counts) or set(split['writers']) != set(counts):
        raise ValueError('exact WB1 split population required')
    if set(split['writers'].values()) != {'discovery', 'test'}:
        raise ValueError('both WB1 writer halves required')
    if full and (len(rows) != 1399 or len(counts) != 61):
        raise ValueError('full primary population required')
    groups = defaultdict(list)
    for row in rows:
        if row['half'] != split['writers'][row['writer']]:
            raise ValueError('writer half differs')
        groups[row['writer']].append(row)
    out = []; overlaps = set()
    for writer, group in sorted(groups.items()):
        for row in sorted(group, key=lambda r: (r['start'], r['session'])):
            prior = sorted(r['session'] for r in group if r['end'] < row['start'])
            later = sorted(r['session'] for r in group if r['start'] > row['end'])
            ambiguous = sorted(r['session'] for r in group if r['session'] != row['session']
                and max(r['start'], row['start']) <= min(r['end'], row['end']))
            original = by_id[row['session']]
            if prior != original['strict_prior_sessions'] or ambiguous != original['overlapping_or_touching_sessions'] or len(prior) != original['chronological_index']:
                raise ValueError('source chronology differs')
            overlaps.update(tuple(sorted((row['session'], sid))) for sid in ambiguous)
            out.append(dict(row, strict_prior_sessions=prior, strict_later_sessions=later,
                overlapping_or_touching_sessions=ambiguous, writer_sessions=len(group),
                writer_meets_12_sessions=len(group) >= 12))
    summary = dict(sessions=len(rows), writers=len(counts),
        eligible_writers=sum(n >= 12 for n in counts.values()),
        sessions_of_eligible_writers=sum(n for n in counts.values() if n >= 12),
        sessions_without_observed_choices=sum(not r['observed_choices'] for r in rows),
        overlapping_or_touching_pairs=len(overlaps),
        **{k: sum(r[k] for r in rows) for k in ('known_menus', 'unknown_menus', 'original_menus', 'displays', 'reopened_displays', 'unanchored_reopens')},
        classes=list(CLASSES), full_population=full, constructed=not full,
        scientific_admission=False, forecasts_computed=False,
        scope='Complete input census only; unknown choices and chronology ambiguity retained; no forecasting or current-person inference')
    for ours, theirs in [('original_menus', 'unique_menus'), ('displays', 'display_events')]:
        if summary[ours] != census['summary'][theirs]:
            raise ValueError('aggregate source coverage differs')
    if summary['known_menus'] + summary['unknown_menus'] != summary['original_menus']:
        raise ValueError('handling partition differs')
    return dict(rows=out, summary=summary, split=split)


def run(output, inputs, config, verification=False):
    mode = config.get('mode')
    if config != dict(mode=mode, seed=SEED) or mode not in ('constructed', 'full'):
        raise ValueError('frozen input configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    started = time.process_time()
    if mode == 'constructed':
        if set(inputs) != {'fixture'}:
            raise ValueError('fixture required')
        f = read(inputs['fixture']); census, split = f['census'], f['split']; parent = None
    else:
        if set(inputs) != {'exposure_completion'}:
            raise ValueError('complete canonical handling source required')
        parent = Path(inputs['exposure_completion']).parent
        for name in ('CENSUS.json', 'WB1_WRITER_SPLIT.json'):
            completed(inputs['exposure_completion'], parent/'output'/name)
        census = read(parent/'output/CENSUS.json'); split = read(parent/'output/WB1_WRITER_SPLIT.json')
    rows = []; bindings = []
    for i, r in enumerate(census['roster']):
        sid = r['session']
        if parent is None:
            unit = f['units'][sid]; h = None
        else:
            path = parent/'output/sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
            completed(inputs['exposure_completion'], path); h = filehash(path); unit = gzread(path)
        rows.append(session_counts(unit, r)); bindings.append(dict(session=sid, source_sha256=h))
        progress(output/'PROGRESS.json', dict(phase='verify-inputs' if verification else 'inputs', done=i+1, total=len(census['roster'])))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('input census yields at session boundary')
    value = assemble(rows, census, split, full=mode == 'full')
    payloads = {'CENSUS.json': value, 'SUMMARY.json': value['summary'],
        'BINDING.json': dict(config=config, inputs={k: filehash(v) for k, v in inputs.items()}, units=bindings)}
    for name, data in payloads.items():
        if verification:
            if read(output/name) != data:
                raise ValueError('input replay differs')
        else:
            write_equal(output/name, data)
    if verification:
        return dict(verified=True, complete_input_replay=True, scientific_admission=False)
    if not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json', dict(cpu_seconds=time.process_time()-started,
            scope='Input census only; all six forecasts and controls unmeasured'))
    return dict(status='complete', scientific_admission=False, summary=value['summary'])


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
