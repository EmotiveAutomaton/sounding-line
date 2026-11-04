"""S4(b) explicit visible navigation and strictly earlier own-text features.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-3 read November 3. Known event
ordinals and vectors must agree under null and alternative. Opening snapshots,
hidden events, future histories and canonical-choice substitutions must fail
or remain excluded. This source computes no scientific contrast or reliability.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import math
import time
from bisect import bisect_left
import numpy as np
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from runners.stage14.common import atomic
from .timing_pmap_source import completed
from . import week4_t4_history as history


def configuration(mode):
    if mode not in ('constructed', 'timing', 'full'):
        raise ValueError('Unknown S4 menu source mode')
    return dict(card='S4-menu-source', mode=mode, seed=20261102, pilot_sessions=140)


def navigation(events, start, end, independent=False):
    if not 0 <= start < end <= len(events) or events[start]['eventName'] != 'suggestion-open':
        raise ValueError('Invalid opened-menu boundary')
    times = [float(e['eventTimestamp']) for e in events[start:end]]
    if not all(map(math.isfinite, times)) or times != sorted(times):
        raise ValueError('Invalid menu clocks')
    visible = True
    intervals = []
    episode = start
    selected = None
    hover, keys, hidden = [], [], []
    for i in range(start + 1, end):
        name = events[i]['eventName']
        if name == 'suggestion-open':
            raise ValueError('Unbounded next menu')
        if name == 'suggestion-reopen':
            if visible:
                raise ValueError('Reopen while visible')
            visible, episode = True, i
        if name in ('suggestion-hover', 'suggestion-up', 'suggestion-down'):
            if visible:
                (hover if name == 'suggestion-hover' else keys).append(i)
            else:
                hidden.append(i)
        if name == 'suggestion-select':
            if not visible:
                raise ValueError('Selection while hidden')
            selected = i
        if name in ('suggestion-select', 'suggestion-close') and visible:
            intervals.append((episode, i))
            visible = False
        if selected is not None:
            break
    if visible:
        intervals.append((episode, end))
    if independent:
        # Independent predecessor queries use raw boundary names, not the
        # production visibility state, intervals or collected event lists.
        stop = selected if selected is not None else end
        boundary_names = {'suggestion-open', 'suggestion-reopen', 'suggestion-close', 'suggestion-select'}
        boundaries = [i for i in range(start, stop) if events[i]['eventName'] in boundary_names]
        visible_ids = {i for i in range(start + 1, stop)
                       if events[boundaries[bisect_left(boundaries, i) - 1]]['eventName']
                       in ('suggestion-open', 'suggestion-reopen')}
        hover = [i for i in range(start + 1, stop) if i in visible_ids and events[i]['eventName'] == 'suggestion-hover']
        keys = [i for i in range(start + 1, stop) if i in visible_ids and events[i]['eventName'] in ('suggestion-up', 'suggestion-down')]
        hidden = [i for i in range(start + 1, stop) if i not in visible_ids and events[i]['eventName'] in ('suggestion-hover', 'suggestion-up', 'suggestion-down')]
    arm = 'both' if hover and keys else 'pointer' if hover else 'keyboard' if keys else 'neither'
    return dict(arm=arm, hover_ordinals=hover, keyboard_ordinals=keys, hidden_navigation_ordinals=hidden,
                selection_ordinal=selected, visible_episodes=[list(x) for x in intervals])


def halves(sessions, seed):
    by = defaultdict(list)
    for s in sessions:
        by[s['writer']].append(s['session'])
    result = {}
    for writer, ids in by.items():
        if len(set(ids)) != len(ids):
            raise ValueError('Duplicate session')
        order = sorted(ids, key=lambda sid: (hashlib.sha256(f'{seed}:{sid}'.encode()).hexdigest(), sid))
        result.update({sid: i % 2 for i, sid in enumerate(order)})
    return result


def own_options(state, writer, refs, vector):
    sums, counts, sessions = state
    own = history.unit(sums[writer]) if writer in sums else None
    witness = dict(sequences=int(counts.get(writer, 0)), sessions=history.digest(sorted(sessions.get(writer, []))))
    values = None if own is None else [float(np.dot(vector(ref), own)) for ref in refs]
    if values is not None and (not np.isfinite(values).all() or any(abs(x) > 1 + 1e-5 for x in values)):
        raise ValueError('Invalid own-history similarity')
    return values, witness


def fixture():
    names = ['system-initialize', 'suggestion-open', 'suggestion-close', 'suggestion-hover',
             'suggestion-reopen', 'suggestion-hover', 'suggestion-down', 'suggestion-select', 'suggestion-hover']
    return [dict(eventName=name, eventTimestamp=i * 1000, currentHoverIndex=0) for i, name in enumerate(names)]


def known_answers():
    a = navigation(fixture(), 1, 9)
    assert a == navigation(fixture(), 1, 9, True)
    assert a['hover_ordinals'] == [5] and a['keyboard_ordinals'] == [6] and a['hidden_navigation_ordinals'] == [3]
    assert navigation(fixture(), 1, 3)['arm'] == 'neither'
    hs = [dict(session='a', writer='w', end_at=1., count=1, total=np.array([1., 0.])),
          dict(session='b', writer='w', end_at=2., count=1, total=np.array([0., 1.]))]
    for selector in (history.Sweep(hs), history.Prefix(hs)):
        assert own_options(selector.at(1.), 'w', [0], lambda r: np.array([1., 0.]))[0] is None
        assert own_options(selector.at(2.), 'w', [0, 1], lambda r: np.eye(2)[r])[0] == [1., 0.]
    return dict(explicit_events_only=True, hidden_and_post_selection_excluded=True,
                reopen_preserved=True, strictly_earlier_only=True, no_effect=True)


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']):
        raise ValueError('Frozen configuration required')
    output = Path(output)
    started = time.process_time()
    checks = known_answers()
    if config['mode'] == 'constructed':
        if inputs:
            raise ValueError('Constructed mode has no human inputs')
        rows = [dict(navigation=navigation(fixture(), 1, 9, verification))]
        summary = dict(mode='constructed', checks=checks, scientific_effect_computed=False)
    else:
        if set(inputs) != {'encoding_completion', 'source_inputs'}:
            raise ValueError('Exact source registry and encoding required')
        sessions, histories, refs, vector = history.load(dict(encoding_completion=inputs['encoding_completion']))
        ec = Path(inputs['encoding_completion'])
        mc = Path(read(ec.parent/'PLAN.json')['inputs']['menus_completion'])
        completed(mc, mc.parent/'PLAN.json')
        registered = read(mc.parent/'PLAN.json')['inputs']['source_inputs']
        if filehash(registered) != filehash(inputs['source_inputs']):
            raise ValueError('Source registry differs from canonical menu source')
        registry = read(inputs['source_inputs'])
        source_root = Path(registry['repo_root']).resolve()
        prepared = {s['session']: s for s in read(registry['prepared_sessions'])}
        roster = {s['session']: s for s in read(registry['raw_roster'])}
        if len(sessions) != 1399 or len({s['session'] for s in sessions}) != 1399:
            raise ValueError('Complete primary population required')
        split = halves(sessions, config['seed'])
        selected = sorted(sessions, key=lambda s: (hashlib.sha256(f"{config['seed']}:{s['session']}".encode()).hexdigest(), s['session']))
        if config['mode'] == 'timing':
            selected = selected[:config['pilot_sessions']]
        selection = history.Prefix(histories)
        rows, bindings = [], []
        for index, s in enumerate(selected):
            sid = s['session']; meta = roster[sid]; prep = prepared[sid]
            if s['writer'] != prep['writer'] or s['writer'] != meta['writer']:
                raise ValueError('Source writer join differs')
            path = (source_root/meta['path']).resolve()
            path.relative_to(source_root)
            if filehash(path) != meta['source_sha256']:
                raise ValueError('Raw event source changed')
            events = [json.loads(line) for line in path.read_text(encoding='utf8').splitlines()]
            menus = {r['key']: r for r in prep['rows']}
            if len(menus) != len(prep['rows']) or set(menus) != {m['key'] for m in s['menus']}:
                raise ValueError('Menu coverage differs')
            for m in s['menus']:
                p = menus[m['key']]
                if m['ordinal'] != p['ordinal'] or m['options'] != p['menu'] or m['open_at'] != float(events[p['ordinal']]['eventTimestamp']):
                    raise ValueError('Menu source boundary differs')
                nav = navigation(events, p['ordinal'], p['end_ordinal'], verification)
                own, witness = own_options(selection.at(m['open_at']), s['writer'], refs[m['key']]['options'], vector)
                choice = m['choice']
                if choice is not None and (type(choice) is not int or not 0 <= choice <= len(m['options'])):
                    raise ValueError('Invalid canonical choice')
                rows.append(dict(key=m['key'], session=sid, writer=s['writer'], genre=s['genre'], half=split[sid],
                                 handling=m['handling'], canonical_choice=choice, dismissal_index=len(m['options']),
                                 open_at=m['open_at'], navigation=nav, option_own_cosines=own, history_witness=witness))
            bindings.append(dict(session=sid, source_sha256=meta['source_sha256']))
            if index % 25 == 0:
                atomic(output/'PROGRESS.json', dict(phase='verify-menu-source' if verification else 'menu-source', done=index + 1, total=len(selected)))
        rows.sort(key=lambda r: r['key'])
        if len({r['key'] for r in rows}) != len(rows):
            raise ValueError('Duplicate output menu')
        summary = dict(mode=config['mode'], sessions=len(selected), writers=len({s['writer'] for s in selected}), menus=len(rows),
                       browsing_counts=dict(sorted(Counter(r['navigation']['arm'] for r in rows).items())),
                       handling_counts=dict(sorted(Counter(r['handling'] for r in rows).items())),
                       missing_own_history=sum(r['option_own_cosines'] is None for r in rows), checks=checks,
                       complete_population=config['mode']=='full', scientific_effect_computed=False,
                       scope='Observed visible-menu navigation and all offered options against strictly earlier own typed text; no device-to-intention or gaze claim.')
        binding = dict(inputs={k: filehash(v) for k, v in inputs.items()}, config=config, sources=bindings)
        if verification:
            if read(output/'BINDING.json') != binding:
                raise ValueError('Binding replay differs')
        else:
            write_equal(output/'BINDING.json', binding)
    if verification:
        if read(output/'SUMMARY.json') != summary or gzread(output/'PRIVATE_ROWS.json.gz') != rows:
            raise ValueError('Complete menu source replay differs')
        return dict(verified=True, full_source_replay=True, no_effect=True)
    write_equal(output/'SUMMARY.json', summary)
    gzip_equal(output/'PRIVATE_ROWS.json.gz', rows)
    cpu = time.process_time() - started
    write_equal(output/'TIMING.json', dict(cpu_seconds=cpu, full_source_and_verification_forecast=3 * cpu * 1399 / summary.get('sessions', 1399),
                                          scientific_effect_computed=False))
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
