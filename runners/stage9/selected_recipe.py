"""Resolve a completed development recipe without selecting its luckiest seed.

DESIGN CHECK: C05/C06/C07/I06/X01/X11/X12; LESSONS 3--5, CONTROLS 6.
NULL: a changed ranking, incomplete seed set, substituted checkpoint or calibration
cannot reach inference. ALTERNATIVE: reconstruct the complete assigned fitting
grid and the original development-only rule, then retain each declared seed of
the chosen recipe. These are provenance/construction guards, not competence
thresholds. No eligible recipe refuses; independent queue branches remain usable.
"""
from pathlib import Path

from runners.stage9.common import REPO, ROOT, closure, digest, file_hash, read
from runners.stage9.queue import inside
from runners.stage9.training_jobs import FITS, training_root


def resolve(selection, manifest, queue, family, seed, scope):
    from runners.stage9.recipe_selection import PILOT_FITS, choose, fitting_rows
    from runners.stage9.neural_operations import training_package

    expected = FITS if scope == 'scientific' else PILOT_FITS if scope == 'pilot' else ()
    if type(seed) is not int or not any(f == family and s == seed for f, _, s in expected):
        raise ValueError('selected recipe requires a declared family, scope and training seed')
    selection, manifest, queue = map(inside, (selection, manifest, queue))
    prefix = 'scientific-recipe-selection' if scope == 'scientific' else 'recipe-selection-pilots'
    if not selection.is_relative_to(ROOT / 'private' / prefix):
        raise ValueError('recipe selection output scope differs')
    identity = read(selection / 'IDENTITY.json')
    done = read(selection / 'COMPLETE.json')
    files = [selection / name for name in ('IDENTITY.json', 'FITTING_ROWS.json', 'SELECTION.json')]
    if (identity.get('operation') != 'development-recipe-selection-v1'
        or identity.get('scope') != scope or done.get('execution_complete') is not True
        or done.get('development_only') is not True or done.get('scientific_admission') is not False
        or done.get('cell_identity') != identity.get('cell_identity')
        or done.get('identity_sha256') != digest(identity) or done.get('outputs') != closure(files)):
        raise ValueError('completed development selection identity or output closure differs')
    rows, manifest_sha = fitting_rows(manifest, queue, scope)
    result = choose(rows, scope)
    summaries = {f: {key: group[key] for key in ('selected', 'selected_recipe', 'selected_seeds', 'reason')}
                 for f, group in result['families'].items()}
    if (identity.get('fitting_manifest_sha256') != manifest_sha
        or identity.get('fitting_rows_sha256') != digest(rows)
        or read(selection / 'FITTING_ROWS.json') != rows or read(selection / 'SELECTION.json') != result
        or done.get('families') != summaries):
        raise ValueError('development selection does not reconstruct from all assigned fits')
    group = result['families'][family]
    if not group['selected'] or seed not in group['selected_seeds']:
        raise ValueError('family has no complete selected recipe containing this seed')
    recipe = group['selected_recipe']
    row = next(r for r in rows if (r['family'], r['recipe'], r['seed']) == (family, recipe, seed))
    training = (training_root(family, recipe, seed) if scope == 'scientific' else
                ROOT / 'private/training-handler-pilots/v2' / family / 'fit')
    _, adapter_sha, fit_sha = training_package(training, family, scope)
    if row['status'] != 'COMPLETE' or row['adapter_sha256'] != adapter_sha or row['complete_sha256'] != fit_sha:
        raise ValueError('selected training package differs from its original fitting row')
    provenance = {'selection': str(selection), 'selection_complete_sha256': file_hash(selection / 'COMPLETE.json'),
                  'fitting_manifest': str(manifest), 'fitting_queue': str(queue),
                  'fitting_manifest_sha256': manifest_sha, 'family': family, 'recipe': recipe, 'seed': seed,
                  'selected_seeds': group['selected_seeds'], 'training': str(training),
                  'training_complete_sha256': fit_sha, 'adapter_sha256': adapter_sha, 'scope': scope}
    return training, provenance


def execution_selection(selection, manifest, queue, seed, *, training, package_kind, family, scope):
    bundle = (selection, manifest, queue, seed)
    if all(value is None for value in bundle):
        return training, None
    if any(value is None for value in bundle):
        raise ValueError('selected execution requires the complete selection argument bundle')
    if training is not None or package_kind != 'fitted':
        raise ValueError('selected execution requires a fitted package without a fixed training path')
    return resolve(selection, manifest, queue, family, seed, scope)


def calibration_path(mapping, target_identity, scope):
    """Select only the declared calibration for the target's actual chosen fit.

    The map enumerates every assigned fit before selection; other calibrations'
    outcomes are never consulted. The caller still replays checked_calibration
    against the target's complete actual model/tokenizer/scoring package.
    """
    from runners.stage9.recipe_selection import PILOT_FITS

    mapping = inside(mapping)
    plan = read(mapping)
    expected = FITS if scope == 'scientific' else PILOT_FITS if scope == 'pilot' else ()
    rows = plan.get('calibrations', [])
    if (not expected or plan.get('scope') != scope or len(rows) != len(expected)
        or {(r['family'], r['recipe'], r['seed']) for r in rows} != set(expected)
        or any(type(r['seed']) is not int for r in rows)):
        raise ValueError('selected calibration map must enumerate every assigned fit')
    paths = [inside(Path(row['calibration'])) for row in rows]
    if len(set(paths)) != len(paths):
        raise ValueError('selected calibration map repeats a package output')
    prior = target_identity.get('recipe_selection')
    if not isinstance(prior, dict) or target_identity.get('scope') != scope or target_identity.get('package_kind') != 'fitted':
        raise ValueError('selected calibration requires an actual selected fitted target')
    _, rebuilt = resolve(prior['selection'], prior['fitting_manifest'], prior['fitting_queue'],
                         target_identity['family'], prior['seed'], scope)
    if (prior != rebuilt or target_identity.get('training_complete_sha256') != rebuilt['training_complete_sha256']
        or target_identity.get('adapter_sha256') != rebuilt['adapter_sha256']):
        raise ValueError('selected target provenance or checkpoint differs')
    key = (rebuilt['family'], rebuilt['recipe'], rebuilt['seed'])
    index = next(i for i, row in enumerate(rows) if (row['family'], row['recipe'], row['seed']) == key)
    return paths[index], {'mapping': str(mapping), 'mapping_sha256': file_hash(mapping), 'recipe_selection': rebuilt}
