"""Whole-writer, generated-choice costing of the retained T4.h1 estimator.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-04. Under either generating law,
actual choices cannot affect selection, generated choices or fits. Preserve
every selected writer's menus, training-only scaling and original fit checks.
Wrong source, floor, selection or replay must refuse; timing never admits a
human comparison. The full-population cost hold remains.
"""
from collections import Counter, defaultdict
from pathlib import Path
import copy
import time
import numpy as np
from runners.stage14.common import atomic, digest
from . import week4_t4_inputs as source
from . import week4_t4_matched_cost as original
from . import week4_t4_matched_cost_h1 as parent
from . import week4_t4_kernel_h1 as kernel
from .timing_pmap_source import completed
from .timing_p6 import read, gzread, write_equal


def configuration(mode):
    return dict(parent.configuration(mode), card='T4.h1-whole-writer-cost',
                sample_seed=20261102, sample_writers=25,
                strata='majority genre of distinct source sessions; lexical ties')


def selection(rows, supported, size):
    """Hamilton quotas, fixed seeded ranks, no choices or features consulted."""
    supported = sorted(supported)
    if len(set(supported)) != len(supported) or type(size) is not int or not 1 <= size <= len(supported):
        raise ValueError('Invalid sample size or supported roster')
    sessions = defaultdict(dict)
    allowed = set(supported)
    for row in rows:
        if row['writer'] not in allowed:
            continue
        previous = sessions[row['writer']].setdefault(row['session'], row['genre'])
        if previous != row['genre']:
            raise ValueError('Session genre changed')
    if set(sessions) != allowed:
        raise ValueError('Supported writer absent from source')
    strata = defaultdict(list)
    for writer in supported:
        counts = Counter(sessions[writer].values())
        genre = min(counts, key=lambda g: (-counts[g], g))
        strata[genre].append(writer)
    total = len(supported)
    quotas = {g: size * len(v) // total for g, v in sorted(strata.items())}
    order = sorted(strata, key=lambda g: (-(size * len(strata[g]) % total), g))
    for genre in order[:size - sum(quotas.values())]:
        quotas[genre] += 1
    rng = np.random.default_rng(20261102)
    chosen = sorted(w for g in sorted(strata) for w in rng.permutation(strata[g]).tolist()[:quotas[g]])
    return dict(seed=20261102, population_writers=total, sample_writers=size,
                selected_writers=chosen, stratum_population={g: len(v) for g, v in sorted(strata.items())},
                stratum_selected=quotas,
                selected_sessions=sorted(s for w in chosen for s in sessions[w]))


def pack_sample(rows, supported, size, menus_per_half=20):
    manifest = selection(rows, supported, size)
    chosen = set(manifest['selected_writers'])
    retained = [r for r in rows if r['writer'] in chosen]
    packed = source.assemble(retained, menus_per_half, size)
    if not packed['summary']['support_pass'] or packed['writers'] != manifest['selected_writers']:
        raise ValueError('Selected whole writers do not meet the unchanged support floor')
    source.independently_check(retained, packed)
    manifest['retained_source_menus'] = len(retained)
    manifest['retained_source_keys_sha256'] = digest(sorted(r['key'] for r in retained))
    return packed, manifest


def fixture():
    rows = []
    for w in range(6):
        for row in source.fixture()[:8]:
            row = copy.deepcopy(row)
            row.update(writer=str(w), key=f'{w}-{row["half"]}-{row["key"]}',
                       session=f'{w}-{row["half"]}', genre='a' if w < 3 else 'b')
            rows.append(row)
    return rows


def known_answers():
    rows = fixture()
    packed, manifest = pack_sample(rows, [str(w) for w in range(6)], 3, 2)
    if manifest['stratum_selected'] != {'a': 2, 'b': 1}:
        raise ValueError('Known sample quota differs')
    reverse, other = pack_sample(list(reversed(rows)), [str(w) for w in reversed(range(6))], 3, 2)
    if reverse != packed or other != manifest:
        raise ValueError('Source ordering changes sample')
    changed = copy.deepcopy(rows)
    for row in changed:
        row['choice'] = row['dismissal_index']
    altered, other = pack_sample(changed, [str(w) for w in range(6)], 3, 2)
    if other != manifest:
        raise ValueError('Choices change sample')
    for regime in (False, True):
        a = original.generated(packed, 20261102, regime)
        b = original.generated(altered, 20261102, regime)
        if not all(np.array_equal(a[k], b[k]) for k in a):
            raise ValueError('Human choices reach generated fits')
    return dict(original.known_answers(), whole_writer_retention=True,
                stratified_selection_replay=True, sample_training_only_scaling=True,
                original_scalar_reconstruction=True)


def load(inputs):
    # Authenticate the original full input and both complete constructed banks.
    full = parent.load(inputs)
    ic = Path(inputs['inputs_completion'])
    completed(ic, ic.parent / 'PLAN.json')
    plan = read(ic.parent / 'PLAN.json')
    if plan['module'] != 'runners.drive.cards.week4_t4_inputs' or plan['config'] != source.configuration('full'):
        raise ValueError('Original full source packing required')
    hc = Path(plan['inputs']['history_completion'])
    for name in ('FEATURES.json.gz', 'SUMMARY.json', 'PRIVATE_SUPPORT.json'):
        completed(hc, hc.parent / 'output' / name)
    if read(hc.parent / 'output/SUMMARY.json')['mode'] != 'full':
        raise ValueError('Full history source required')
    if full['writers'] != read(hc.parent / 'output/PRIVATE_SUPPORT.json')['supported_writers']:
        raise ValueError('Full support roster changed')
    rows = gzread(hc.parent / 'output/FEATURES.json.gz')
    return pack_sample(rows, full['writers'], 25)


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']):
        raise ValueError('Frozen sample cost configuration required')
    output = Path(output)
    start = time.process_time()
    checks = known_answers()
    if config['mode'] == 'constructed':
        if inputs:
            raise ValueError('Constructed inputs must be empty')
        packed, manifest = pack_sample(fixture(), [str(w) for w in range(6)], 3, 2)
        seeds = config['seeds'][:1]
    else:
        packed, manifest = load(inputs)
        seeds = config['seeds']
    load_seconds = time.process_time() - start
    receipts, durations = [], []
    for seed in seeds:
        for individual in (False, True):
            begin = time.process_time()
            data = original.generated(packed, seed, individual)
            shared = kernel.fit(data, False)
            personal = kernel.fit(data, True)
            receipts.append(dict(seed=seed, regime='individual' if individual else 'shared',
                                 shared=shared, individual=personal))
            durations.append(time.process_time() - begin)
            atomic(output / 'PROGRESS.json', dict(phase='verify-cost' if verification else 'cost',
                                                  done=len(receipts), total=2 * len(seeds)))
    summary = dict(mode=config['mode'], generated_worlds=len(receipts), writers=len(packed['writers']),
                   population_supported_writers=manifest['population_writers'],
                   training_menus=len(packed['train']['w']), test_menus=len(packed['test']['w']),
                   selected_source_menus=manifest['retained_source_menus'],
                   stratum_population=manifest['stratum_population'], stratum_selected=manifest['stratum_selected'],
                   human_choices_fitted=False, human_choices_scored=False, checks=checks,
                   bounded_fits=sum(r['individual']['boundary_coordinates'] > 0 for r in receipts),
                   scientific_admission=False)
    if verification:
        for name, expected in (('SUMMARY.json', summary), ('PRIVATE_FITS.json', receipts),
                               ('PRIVATE_SELECTION.json', manifest)):
            if read(output / name) != expected:
                raise ValueError('Complete sample generated-fit replay differs: ' + name)
        return dict(verified=True, complete_generated_fit_replay=True, complete_selection_replay=True)
    write_equal(output / 'PRIVATE_SELECTION.json', manifest)
    write_equal(output / 'PRIVATE_FITS.json', receipts)
    write_equal(output / 'SUMMARY.json', summary)
    write_equal(output / 'TIMING.json', dict(load_cpu_seconds=load_seconds, pair_cpu_seconds=durations,
        core_refit_forecast_cpu_seconds=config['replay_factor'] * config['safety_factor'] *
        (load_seconds + max(durations) * config['refit_pairs']) + 20,
        scope='Sample core fitting only; scientific calibration, parameter uncertainty and joins excluded; no main admission'))
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
