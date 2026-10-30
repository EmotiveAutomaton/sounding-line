"""Frozen TR4.h1 worlds, full calibration and fresh native replay.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 5-7 reread 2026-10-29. NULL families
include prompt-block nuisance while maintaining conditional exchangeability.
ALTERNATIVE contains within-cell drift. Complete-rule size/sensitivity gates
are frozen before execution; a gate failure is retained, never a retry trigger.
"""
from itertools import permutations
from pathlib import Path
import time
import numpy as np
from . import week3_tr4_conditional as control
from . import week3_tr4_comparison as parent
from . import week3_tr4_analysis as original
from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import write_equal, progress

FAMILIES = ('stationary', 'prompt_block', 'drift_15', 'drift_30')
WORLDS = [[family, start + i] for family, start, n in zip(
    FAMILIES, (2026102900, 2026103000, 2026103100, 2026103200), (32, 32, 8, 8)) for i in range(n)]
CONFIGS = {
    'constructed': dict(mode='constructed'),
    'cost': dict(mode='cost', worlds=[['drift_30', 2026103999]], repetitions=200, bootstraps=2000),
    'main': dict(mode='main', worlds=WORLDS, repetitions=200, bootstraps=2000),
}


def construct(family, seed):
    if family not in FAMILIES or type(seed) is not int:
        raise ValueError('frozen family and integer seed required')
    rng = np.random.default_rng(seed)
    rows, truth, writers = [], [], {}
    dose = {'stationary': 0., 'prompt_block': .30, 'drift_15': .15, 'drift_30': .30}[family]
    for w in range(18):
        writer = f'w{w:02d}'
        writers[writer] = 'discovery' if w < 4 else 'test'
        initial = float(rng.uniform(.45, .55))
        for j in range(24):
            prompt = str(int(j >= 12)) if family == 'prompt_block' else str(j % 2)
            accept = initial + ((1 if w % 2 else -1) * dose if j >= 12 else 0.)
            p = np.array([accept] + [(1 - accept) / 3] * 3)
            count = 50 if (j // 2) % 2 == 0 else 200
            x = rng.multinomial(count, p)
            session = f'{writer}-{j:02d}'
            rows.append(dict(writer=writer, session=session, prompt=prompt, half=writers[writer],
                             start=j*3, end=j*3+1, counts=dict(zip(parent.CLASSES, x.tolist()))))
            truth.append(dict(session=session, probabilities=p.tolist(), choices=count))
    return dict(census=dict(rows=rows, split=dict(seed=parent.SEED, writers=writers,
                    session_counts={w:24 for w in writers})), truth=truth, family=family, seed=seed)


def known_answers():
    uniform = original.constructed('uniform')
    value = control.analyze(uniform, 5, 31)
    if value['primary']['estimate'] != 0 or value['primary']['probability'] != 1:
        raise ValueError('equal-share arithmetic failed')
    if value['primary']['status'] != 'unsupported':
        raise ValueError('nonmoving support must remain unsupported')
    # Enumerate an entire conditional orbit, using the actual forecast statistic.
    group = parent.prepare(uniform)[0][0]
    group['data'] = group['data'].copy()
    group['data'][8:12] = np.array([[850,50,50,50],[50,850,50,50],[50,50,850,50],[50,50,50,850]])
    values = []
    for order in permutations(range(4)):
        data = group['data'].copy()
        data[8:12] = group['data'][8:12][list(order)]
        values.append(parent.primary(group, data)['gain'])
    # Exact group includes identity once; +1 randomly sampled formula is separate.
    ranks = [float(np.mean(np.asarray(values) >= v - 1e-12)) for v in values]
    if sum(p < .05 for p in ranks) > 1:
        raise ValueError('exact 24-order rank size failed')
    p1 = control.probability(.5, [-.2, .1, .7, .5])
    p2 = control.probability(8.5, [7.8, 8.1, 8.7, 8.5])
    if p1 != p2 or p1 != .6:
        raise ValueError('rank offset or tie accounting failed')
    world = construct('prompt_block', 2026103998)
    groups, _ = parent.prepare(world['census'])
    rng = np.random.default_rng(1)
    for g in groups:
        changed = control.shuffle(g, rng)
        if not np.array_equal(changed.sum(axis=1), g['data'].sum(axis=1)):
            raise ValueError('sample count changed')
        for indices in control.cells(g):
            if sorted(map(tuple, changed[indices])) != sorted(map(tuple, g['data'][indices])):
                raise ValueError('conditional cell changed')
    return dict(uniform=value, exact_orbit_statistics=values, exact_orbit_probabilities=ranks,
                rank_offset_probability=p1, conditional_multisets_preserved=True,
                scientific_admission=False)


def summarize(cells):
    rows = []
    for family in FAMILIES:
        selected = [c['result']['primary'] for c in cells if c['family'] == family]
        rows.append(dict(family=family, worlds=len(selected),
                         positives=sum(p['status'] == 'positive_conditional_order' for p in selected),
                         unsupported=sum(p['status'] == 'unsupported' for p in selected)))
    complete = [r['worlds'] for r in rows] == [32,32,8,8]
    gates = dict(complete_matrix=complete,
                 stationary_size=complete and rows[0]['positives'] <= 3,
                 prompt_nuisance_size=complete and rows[1]['positives'] <= 3,
                 high_dose_sensitivity=complete and rows[3]['positives'] >= 7,
                 complete_support=complete and all(r['unsupported'] == 0 for r in rows))
    return dict(families=rows, gates=gates, calibration_pass=all(gates.values()),
                constructed=True, scientific_admission=False,
                scope='Finite conditional instrument check, not universal size/power or human evidence')


def run(output, inputs, config, verification=False):
    mode = config.get('mode')
    if mode not in CONFIGS or config != CONFIGS[mode]:
        raise ValueError('frozen complete configuration required')
    expected = {'parent_landing'} | ({'cost_completion','cost_landing'} if mode == 'main' else set())
    if set(inputs) != expected:
        raise ValueError('exact parent/cost bindings required')
    landing = read(inputs['parent_landing'])
    if not landing['full_write_through'] or landing['id'] != 'S15-TR4-20261027':
        raise ValueError('original fully landed parent required')
    if mode == 'main':
        cost = Path(inputs['cost_completion'])
        completed(cost, cost.parent/'output/SUMMARY.json')
        gate = read(inputs['cost_landing'])
        if not gate['full_write_through'] or not gate['admitted'] or gate['cost_completion_sha256'] != filehash(cost):
            raise ValueError('admitted cost landing required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/'cells').mkdir(exist_ok=True)
    started = time.process_time()
    if mode == 'constructed':
        payload = known_answers()
    else:
        cells = []
        for index, (family, seed) in enumerate(config['worlds']):
            world = construct(family, seed)
            def update(phase, done, total):
                if done % 20 == 0 or done == total:
                    progress(output/'PROGRESS.json', dict(phase=('verify-' if verification else '') + phase,
                        world=index+1, worlds=len(config['worlds']), done=done, total=total))
                if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
                    raise InterruptedError('TR4.h1 yield at complete reference boundary')
            result = control.analyze(world['census'], config['repetitions'], config['bootstraps'], update)
            cell = dict(family=family, seed=seed, world=world, result=result)
            path = output/'cells'/f'{index:02d}.json'
            if verification:
                if read(path) != cell:
                    raise ValueError('complete world replay differs')
            else:
                write_equal(path, cell)
            cells.append(cell)
        payload = summarize(cells)
    for name, value in {'SUMMARY.json':payload, 'BINDING.json':dict(config=config,
                       inputs={k:filehash(v) for k,v in inputs.items()})}.items():
        if verification:
            if read(output/name) != value:
                raise ValueError('complete conditional control replay differs')
        else:
            write_equal(output/name, value)
    if not verification and not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json', dict(cpu_seconds=time.process_time()-started))
    if verification:
        return dict(verified=True, complete_input_replay=True, scientific_admission=False)
    return dict(status='complete', mode=mode, scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
