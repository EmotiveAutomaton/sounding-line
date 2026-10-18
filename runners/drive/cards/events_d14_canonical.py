"""One canonical-choice successor of the frozen D14 primary.

DESIGN CHECK: LESSONS3-5. Null, positive and reversed probability slopes retain
their directions. Correct selected offer support and its seven offer covariates;
menu-level predictors, projection, weights and original bootstrap seed stay fixed.
Authenticate every reused extraction. Failures remain invalid, never redrawn.
Complete fresh verification rebuilds source rows and every fit. No causal claim.
"""
from collections import defaultdict
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

from . import events_d14 as old
from . import events_d14_stats as stats
from . import menus_canonical_selection as canonical
from .events_d4 import save, read_sealed, assert_close
from .events_d4_sources import bind_completed
from .menus_io import read, write, sha256, input_hashes

CONFIG = dict(bootstrap=2000, seed=20261017, permutations=200,
              permutation_seed=20261018, threads=1)
INPUTS = {'sessions', 'selection_reader', 'selection_complete', 'original_complete'}


def suffix(row):
    position = row['position']
    return np.r_[np.eye(5)[position] if position < 5 else np.zeros(5),
                 position >= 5, np.log1p(row['disturbance']['candidate_characters'])]


def correct(rows, nuisance, offered, sessions, audit):
    menus = {r['key']: r for s in sessions for r in s['rows']}
    proofs = {key: audit.join(row) for key, row in menus.items()}
    choices = {(r['key'], r['position']): r for r in offered}
    if len(choices) != len(offered):
        raise ValueError('Duplicate frozen offered disturbance')
    groups = defaultdict(list)
    matrix = np.asarray(nuisance, float)
    if matrix.ndim != 2 or len(matrix) != len(rows) or matrix.shape[1] < 7:
        raise ValueError('Original nuisance shape differs')
    for i, row in enumerate(rows):
        menu = menus[row['key']]
        if (row['writer'], row['session'], row['handling']) != (menu['writer'], menu['session'], menu['handling']):
            raise ValueError('Original menu identity differs')
        if row['protected'] != int(menu['handling'] in ('edit', 'dismiss')):
            raise ValueError('Original protection outcome differs')
        if row != dict(choices[(row['key'], row['position'])], protected=row['protected'], handling=row['handling']):
            raise ValueError('Original row differs from saved offered features')
        if not np.array_equal(matrix[i, -7:], suffix(row)):
            raise ValueError('Original offer covariates differ')
        groups[row['key']].append(i)
    corrected, controls, changed = [], [], 0
    for key, ids in sorted(groups.items()):
        menu, proof = menus[key], proofs[key]
        positions = sorted(rows[i]['position'] for i in ids)
        expected = list(range(len(menu['menu']))) if menu['handling'] == 'dismiss' else proof['prepared_positions']
        if positions != expected or menu['handling'] not in ('accept', 'edit', 'dismiss'):
            raise ValueError('Original eligible offer support differs')
        selected = proof['canonical_positions']
        if menu['handling'] in ('accept', 'edit'):
            if len(selected) != 1 or not proof['verified_insertion'] or not proof['canonical_usable']:
                raise ValueError('Canonical selected offer unsupported')
            changed += selected != positions
        elif selected:
            raise ValueError('Dismissed menu has selected offer')
        eligible = positions if menu['handling'] == 'dismiss' else selected
        base = matrix[ids[0], :-7]
        if any(not np.array_equal(matrix[i, :-7], base) for i in ids):
            raise ValueError('Menu-level nuisance differs across offered rows')
        for position in eligible:
            candidate = choices[(key, position)]
            if (candidate['writer'], candidate['session']) != (menu['writer'], menu['session']):
                raise ValueError('Corrected offered identity differs')
            if candidate['topic_drift'] is None or candidate['disturbance']['candidate_characters'] != len(menu['menu'][position]):
                raise ValueError('Corrected offer text/support differs')
            row = dict(candidate, protected=int(menu['handling'] in ('dismiss', 'edit')), handling=menu['handling'])
            corrected.append(row); controls.append(np.r_[base, suffix(row)].tolist())
    order = sorted(range(len(corrected)), key=lambda i: tuple(corrected[i][k] for k in ('writer', 'session', 'key', 'position')))
    return [corrected[i] for i in order], [controls[i] for i in order], dict(
        original_rows=len(rows), corrected_rows=len(corrected), eligible_menus=len(groups),
        corpus_menus=len(menus), corrected_selected_menus=changed,
        original_excluded_menus_retained=len(menus)-len(groups),
        reuse='Frozen all-offer disturbances and menu-level nuisance; selected offer and its seven covariates corrected')


def load(inputs, config):
    if set(inputs) != INPUTS or config != CONFIG:
        raise ValueError('Frozen D14 canonical contract differs')
    root = Path(inputs['original_complete']).parent / 'output'
    for name in ('INPUTS.json', 'ROWS.json', 'NUISANCE.json', 'PROJECTION.json', 'WRITER_INDEX.json'):
        bind_completed(inputs['original_complete'], root/name)
    binding = read(root/'INPUTS.json')
    if Path(binding['paths']['sessions']).resolve() != Path(inputs['sessions']).resolve():
        raise ValueError('Original prepared source differs')
    for path, h in binding['pins'].items():
        if sha256(path) != h:
            raise ValueError('Original frozen source changed')
    offered = []
    for writer in old.load(root/'WRITER_INDEX.json'):
        path = root/writer['file']; bind_completed(inputs['original_complete'], path)
        if sha256(path) != writer['sha256']:
            raise ValueError('Original writer extraction changed')
        offered.extend(old.load(path)['offered_disturbances'])
    rows, nuisance, audit = correct(old.load(root/'ROWS.json'), old.load(root/'NUISANCE.json'),
        offered, read(inputs['sessions']), canonical.load(inputs))
    return rows, nuisance, audit, old.load(root/'PROJECTION.json')


def draw(moments, multiplicity=None):
    try:
        value, certificate = stats.fit_draw(moments, multiplicity)
        return dict(effect=value, certificate=certificate, error=None)
    except ValueError as exc:
        return dict(effect=None, certificate=None, error=str(exc))


def compute(output, inputs, config, verify=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.monotonic()
    rows, nuisance, audit, projection = load(inputs, config)
    def record(name, value):
        if verify: assert_close(read_sealed(output/name), value)
        else: save(output/name, value)
    for name, value in [('BINDING.json', dict(inputs=input_hashes(inputs), config=config)),
                        ('ROWS.json', rows), ('NUISANCE.json', nuisance),
                        ('SOURCE_AUDIT.json', audit), ('PROJECTION.json', projection)]:
        record(name, value)
    results = {}
    for arm, shuffle in [('primary', None), ('original_drift_shuffle', config['seed']+1)]:
        moments = stats.sufficient(rows, nuisance, shuffle_seed=shuffle)
        record('MOMENTS_'+arm+'.json', moments); point = draw(moments)
        rng = np.random.default_rng(config['seed'])
        selections = rng.integers(len(moments), size=(2000, len(moments)))
        draws = []
        for index, selection in enumerate(selections):
            if not verify and (output/'YIELD_REQUEST.json').exists():
                return dict(status='yielded', arm=arm, draw=index)
            value = draw(moments, np.bincount(selection, minlength=len(moments)))
            record(f'{arm}/{index:04d}.json', value); draws.append(value)
            if not verify and arm == 'primary' and index == 199:
                write(output/'FIRST_TENTH.json', dict(projected_seconds=2*(time.monotonic()-started)*21,
                    scope='Conservative combined execution/replay; setup charged repeatedly'))
        good = [v['effect'] for v in draws if v['error'] is None]
        results[arm] = stats.summarize(point['effect'], good, len(draws)-len(good))
        results[arm]['point_certificate'] = point['certificate']
    menus = defaultdict(list)
    for i, row in enumerate(rows): menus[(row['writer'], row['key'])].append(i)
    groups = defaultdict(list)
    for (writer, key), ids in sorted(menus.items()):
        if len({rows[i]['protected'] for i in ids}) != 1:
            raise ValueError('Protection outcome differs within a handled menu')
        groups[(writer, len(ids))].append(ids)
    controls = []
    for index in range(config['permutations']):
        if not verify and (output/'YIELD_REQUEST.json').exists():
            return dict(status='yielded', arm='outcome_permutations', draw=index)
        rng = np.random.default_rng(config['permutation_seed']+index)
        y = np.array([r['protected'] for r in rows])
        for group in sorted(groups):
            blocks = groups[group]
            values = rng.permutation([y[ids[0]] for ids in blocks])
            for ids, value in zip(blocks, values): y[ids] = value
        shuffled = [dict(row, protected=int(y[i])) for i, row in enumerate(rows)]
        value = draw(stats.sufficient(shuffled, nuisance)); record(f'controls/{index:04d}.json', value); controls.append(value)
    values = [r['effect'] for r in controls if r['error'] is None]
    reference = dict(total=200, finite=len(values), invalid=200-len(values), bias_flag=None)
    if len(values) == 200:
        mean, sd = float(np.mean(values)), float(np.std(values, ddof=1))
        reference.update(mean=mean, sd=sd, bias_flag=abs(mean)>.25*sd)
    result = dict(card='D14-canonical', primary=results['primary'], original_drift_shuffle=results['original_drift_shuffle'],
        repeated_outcome_control=reference, source_audit=audit, original_preserved=True,
        fake_writer_control='Not applicable to population adjusted slope; no identification claim',
        inference='Descriptive probability slope; no causal set point or restoration result', scientific_admission=False)
    record('SUMMARY.json', result); return result


def execute(output, inputs, config):
    if (Path(output)/'SUMMARY.json').exists(): raise ValueError('Completed output is immutable')
    with threadpool_limits(limits=1): return compute(output, inputs, config)


def verify(output, inputs, config):
    with threadpool_limits(limits=1): compute(output, inputs, config, verify=True)
    return dict(verified=True, fresh_source_and_all_fit_replay=True)
