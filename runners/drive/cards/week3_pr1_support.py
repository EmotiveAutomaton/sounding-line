"""PR1 saved-source support census, before freezing the comparison.

DESIGN CHECK: LESSONS 2-5 reread 2026-10-27, including missing support,
authentication, immutable reentry and whole-handler replay. Under NULL and
ALTERNATIVE the same complete source roster and eligibility rules apply.
Duplicate/missing joins, changed bytes, invalid duration and incomplete windows
refuse. Ties and overlapping examination/fast flags remain explicit. Support
is neither an effect nor scientific admission; no cosine or label is computed.
"""
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path
import time

from runners.stage14.common import read, filehash, freeze, atomic

CONFIG = dict(version=1, minimum_writers=25, minimum_each=10)


def indexed(rows):
    out = {r['key']: r for r in rows}
    if len(out) != len(rows):
        raise ValueError('duplicate menu key')
    return out


def join_session(dwell, windows):
    a, b = indexed(dwell), indexed(windows)
    if a.keys() != b.keys():
        raise ValueError('complete menu coverage differs')
    out = []
    for key in sorted(a):
        d, w = a[key], b[key]
        if any(d[k] != w[k] for k in ('writer', 'session', 'handling')):
            raise ValueError('menu identity differs')
        if d['menu_size'] != len(w['options']) or len(d['hovered']) != d['menu_size']:
            raise ValueError('option coverage differs')
        if any(type(v) is not bool for v in d['hovered']) or type(d['hover_target_complete']) is not bool:
            raise ValueError('hover flags differ')
        seconds = d['dwell_seconds']
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError('finite nonnegative duration required')
        episodes = d['visible_episodes']
        if not episodes or any(type(e['observed_end']) is not bool or
                type(e['seconds']) not in (int, float) or not math.isfinite(e['seconds']) or
                e['seconds'] < 0 for e in episodes):
            raise ValueError('observed episode schema differs')
        if type(d['dwell_observed']) is not bool or d['dwell_observed'] != all(e['observed_end'] for e in episodes):
            raise ValueError('duration censoring differs')
        if not math.isclose(seconds, sum(e['seconds'] for e in episodes), rel_tol=0, abs_tol=1e-9):
            raise ValueError('duration total differs')
        window = w['window'] is not None
        if window:
            ids, orders = w['window_indices'], w['window_ordinals']
            if not isinstance(w['window'], str) or not w['window'].strip() or len(ids) != 50 or len(set(ids)) != 50 or len(orders) != 50:
                raise ValueError('complete fifty-word window required')
            if any(len(o) != 2 or any(type(v) is not int for v in o) or
                    o[0] <= w['resolution_ordinal'] or o[1] <= w['resolution_ordinal'] for o in orders):
                raise ValueError('window does not follow resolution')
        elif w['window_indices'] is not None or w['window_ordinals'] is not None:
            raise ValueError('missing window has inconsistent indices')
        if w['handling'] not in ('accept', 'edit', 'dismiss', 'ignore'):
            raise ValueError('canonical handling required')
        # A missing hover target still records a hover event, not absence of one.
        out.append(dict(key=key, writer=w['writer'], session=w['session'], prompt=w['prompt'],
            handling=w['handling'], dwell_seconds=seconds, dwell_observed=d['dwell_observed'],
            logged_hover=any(d['hovered']) or not d['hover_target_complete'],
            hover_target_complete=d['hover_target_complete'], complete_window=window))
    return out


def quantile(values, fraction):
    values = sorted(values)
    index = (len(values)-1)*fraction
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo] + (values[hi]-values[lo])*(index-lo)


def assemble(rows, full):
    indexed(rows)
    by_writer = defaultdict(list)
    for r in rows:
        by_writer[r['writer']].append(r)
    groups, classified = [], []
    for writer, source in sorted(by_writer.items()):
        durations = [r['dwell_seconds'] for r in source if r['handling'] == 'dismiss' and r['dwell_observed']]
        q1, q2 = (quantile(durations, 1/3), quantile(durations, 2/3)) if durations else (None, None)
        counts = Counter()
        for r in sorted(source, key=lambda r: r['key']):
            dismissal = r['handling'] == 'dismiss'
            timed = dismissal and r['dwell_observed']
            lower = timed and r['dwell_seconds'] <= q1
            upper = timed and r['dwell_seconds'] >= q2
            examined = dismissal and (upper or r['logged_hover'])
            usable = dismissal and r['complete_window']
            flags = dict(dismissed=dismissal, duration_observed=timed,
                complete_dismissed_window=usable, lower_tercile=lower, upper_tercile=upper,
                examined=examined, examined_with_window=examined and usable,
                fast_with_window=lower and usable,
                overlap_with_window=examined and lower and usable,
                fast_only_with_window=lower and not examined and usable,
                tercile_tie_overlap=lower and upper)
            counts.update(k for k, v in flags.items() if v)
            classified.append(dict(r, **flags))
        n = CONFIG['minimum_each']
        groups.append(dict(writer=writer, counts=dict(sorted(counts.items())), lower_cutoff=q1,
            upper_cutoff=q2, literal_support=counts['examined_with_window'] >= n and counts['fast_with_window'] >= n,
            disjoint_support=counts['examined_with_window'] >= n and counts['fast_only_with_window'] >= n))
    sessions = {r['session'] for r in rows}
    if full and (len(sessions) != 1399 or len(groups) != 61):
        raise ValueError('complete primary population required')
    total = Counter()
    for g in groups:
        total.update(g['counts'])
    literal = sum(g['literal_support'] for g in groups)
    disjoint = sum(g['disjoint_support'] for g in groups)
    return dict(rows=classified, writers=groups, summary=dict(sessions=len(sessions), writers=len(groups),
        menus=len(rows), counts=dict(sorted(total.items())), literal_supported_writers=literal,
        disjoint_supported_writers=disjoint, literal_minimum_met=literal >= 25,
        disjoint_minimum_met=disjoint >= 25, constructed=not full, full_population=full,
        scientific_admission=False, effect_computed=False, comparison_frozen=False,
        scope='Saved-source support census; observed examination proxies are not attention; overlap and ties retained'))


def authenticated(terminal, relative):
    base, c = terminal
    path = (base / relative).resolve()
    path.relative_to(base.resolve())
    if c['outputs'].get(relative) != filehash(path):
        raise ValueError('completed source bytes differ')
    return path


def terminal(path):
    c = read(path)
    if c.get('status') != 'COMPLETE' or not c.get('fresh_process_verified'):
        raise ValueError('verified complete source required')
    return Path(path).parent, c


def run(output, inputs, config, verification=False):
    mode = config.get('mode')
    if config != dict(CONFIG, mode=mode) or mode not in ('constructed', 'full'):
        raise ValueError('frozen census configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    binding = dict(config=config, inputs={k: filehash(v) for k, v in inputs.items()})
    if (output/'BINDING.json').exists() and read(output/'BINDING.json') != binding:
        raise ValueError('source binding changed')
    if mode == 'constructed':
        if set(inputs) != {'fixture'}: raise ValueError('constructed input differs')
        f = read(inputs['fixture']); sources = f['sessions']; dwells = f['dwell']; terminals = None
    else:
        if set(inputs) != {'dwell_completion', 'window_completion'}: raise ValueError('explicit saved sources required')
        dc, wc = terminal(inputs['dwell_completion']), terminal(inputs['window_completion'])
        dwells = read(authenticated(dc, 'output/ROWS.json'))
        dplan = read(dc[0]/'PLAN.json'); wplan = read(wc[0]/'PLAN.json')
        for plan in (dplan, wplan):
            for path, h in plan['pins'].items():
                if filehash(path) != h: raise ValueError('historical source pin changed')
        if dplan['module'] != 'runners.drive.cards.events_d6' or wplan['module'] != 'runners.drive.cards.menus_d20_recovery':
            raise ValueError('unexpected historical source')
        sources = {r['session']: None for r in dwells}; terminals = wc
    dwell_sessions = defaultdict(list)
    for r in dwells: dwell_sessions[r['session']].append(r)
    if set(sources) != set(dwell_sessions): raise ValueError('session coverage differs')
    rows, seals = [], []
    for i, sid in enumerate(sorted(sources)):
        if terminals is None:
            unit = sources[sid]; source_hash = None
        else:
            path = authenticated(terminals, 'output/sessions/'+sid+'.json.gz')
            unit = json.loads(gzip.decompress(path.read_bytes())); source_hash = filehash(path)
        if any(r['session'] != sid for r in unit['rows']): raise ValueError('session path identity differs')
        rows.extend(join_session(dwell_sessions[sid], unit['rows']))
        seals.append(dict(session=sid, window_source_sha256=source_hash))
        atomic(output/'PROGRESS.json', dict(phase='verify-support' if verification else 'support', done=i+1, total=len(sources)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('support yields at session boundary')
    value = assemble(rows, full=mode == 'full')
    payloads = {'CENSUS.json': value, 'SUMMARY.json': value['summary'], 'BINDING.json': binding, 'SOURCE_UNITS.json': seals}
    for name, data in payloads.items():
        if verification:
            if read(output/name) != data: raise ValueError('complete saved-source replay differs')
        else: freeze(output/name, data)
    if verification: return dict(verified=True, complete_input_replay=True, scientific_admission=False)
    return dict(status='complete', scientific_admission=False, summary=value['summary'])


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
