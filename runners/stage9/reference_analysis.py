"""Pair every fitted choice profile with its family's fixed reference packages.

DESIGN CHECK: C01/C05/C07/X01/X07/X11; LESSONS 3--5, CONTROLS 6.
NULL: identical forecasts give zero; a lucky seed cannot replace all three seeds.
ALTERNATIVE: complete paired differences preserve the direction within each family.
Missing/unfinished sources refuse or retain explicit failed branches. Invalid
calibration prevents scoring; nonfinite inputs remain assigned and unpromotable.
Reference weights are fixed, not additional optimizer replicates. Broad generation
is independent of this choice comparison. No selection, reserve or admission here.
"""
import argparse
import math
from pathlib import Path
import time

from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .factorial_analysis import complete_job, source_queues
from .queue import inside, verify_sources, writer
from .reader_packages import reference_package
from .recipe_selection import PILOT_FITS
from .revision_predictions import sources
from .scoring import classify, paired_extended, score_json
from .training_jobs import FITS, cell_identity

REFERENCES = tuple((family, kind) for family in ('qwen', 'smollm') for kind in ('base', 'archive'))
FIELDS = ('unit', 'source_unit', 'domain', 'law', 'purpose', 'target_type', 'rival_log_score')


def summarize(fits, references, scope, draws=4000):
    expected = FITS if scope == 'scientific' else PILOT_FITS if scope == 'pilot' else ()
    if not expected or len(fits) != len(expected) or {(r['family'], r['recipe'], r['seed']) for r in fits} != set(expected):
        raise ValueError('reference comparison requires every assigned fit')
    if len(references) != 4 or {(r['family'], r['package_kind']) for r in references} != set(REFERENCES):
        raise ValueError('all four fixed reference packages are required')
    if any('seed' in r for r in references):
        raise ValueError('a fixed reference is not an optimizer-seed replicate')
    if any(r['status'] not in ('COMPLETE', 'FAILED', 'NOT_RUN') for r in fits + references):
        raise ValueError('unfinished comparison source')
    lookup = {(r['family'], r['package_kind']): r for r in references}
    families = {}
    for family in ('qwen', 'smollm'):
        own = [r for r in fits if r['family'] == family]
        comparisons = {}
        for recipe in sorted({r['recipe'] for r in own}):
            selected = sorted((r for r in own if r['recipe'] == recipe), key=lambda r: r['seed'])
            for kind in ('base', 'archive'):
                ref = lookup[(family, kind)]; members = selected + [ref]
                unavailable = [r for r in members if r['status'] != 'COMPLETE']
                key = recipe + '-vs-' + kind
                if unavailable:
                    comparisons[key] = {'disposition': 'NOT RUN WITH REASON', 'unavailable': unavailable,
                                        'excluded_fits': 0, 'scientific_admission': False}
                    continue
                reference = {r['source_unit']: r for r in ref['choice_rows']}
                count = 192 if scope == 'scientific' else 2
                if len(reference) != len(ref['choice_rows']) or len(reference) != count:
                    raise ValueError('complete unique reference cohort required')
                paired = []
                for fit in selected:
                    rows = {r['source_unit']: r for r in fit['choice_rows']}
                    if len(rows) != len(fit['choice_rows']) or set(rows) != set(reference):
                        raise ValueError('paired fitted/reference source cohorts differ')
                    if fit['comparison_contract'] != ref['comparison_contract']:
                        raise ValueError('paired source, question or ordinary-rival provenance differs')
                    for unit in sorted(reference):
                        left, right = rows[unit], reference[unit]
                        if {k: left[k] for k in FIELDS} != {k: right[k] for k in FIELDS}:
                            raise ValueError('paired public questions or ordinary-rival scores differ')
                        valid = all(x is True for x in (left['valid'], right['valid'], fit['instrument_accepted'], ref['instrument_accepted']))
                        values = (left['reader_log_score'], right['reader_log_score'])
                        finite = all(type(x) in (float, int) and math.isfinite(x) for x in values)
                        paired.append({**{k: left[k] for k in FIELDS if k != 'rival_log_score'},
                                       'seed': fit['seed'], 'valid': valid, 'nonfinite_component': not finite,
                                       'difference': values[0] - values[1] if valid and finite else None})
                groups = {'overall': paired}
                for field in ('domain', 'law'):
                    for value in sorted({r[field] for r in paired}):
                        groups[field + '|' + value] = [r for r in paired if r[field] == value]

                def estimate(rows, crossed=False):
                    if any(r['nonfinite_component'] for r in rows):
                        return {'mean': None, 'ci': None, 'finite_estimate': False,
                                'n_targets': len(rows), 'n_units': len({r['unit'] for r in rows}),
                                'nonfinite_inputs': sum(r['nonfinite_component'] for r in rows),
                                'excluded_targets': 0, 'promotion_eligible': False,
                                'extended_mean': 'undefined comparison with nonfinite input', 'disposition': 'DESCRIPTIVE'}
                    return paired_extended(rows, draws=draws, seed=9021, **({'second_cluster': 'seed'} if crossed else {}))

                summaries = {}
                for name, rows in groups.items():
                    valid = all(r['valid'] for r in rows)
                    summary = estimate(rows, True) if valid else None
                    summaries[name] = {'estimate': summary, 'assigned': len(rows),
                                       'invalid': sum(not r['valid'] for r in rows),
                                       'per_seed': {str(f['seed']): estimate([r for r in rows if r['seed'] == f['seed']])
                                                    for f in selected} if valid else {},
                                       'disposition': classify(summary, threshold=.05, descriptive=scope == 'pilot') if valid else 'IMPLEMENTATION INVALID'}
                comparisons[key] = {'groups': summaries, 'paired_rows_sha256': digest(score_json(paired)),
                                    'seed_count': len(selected), 'reference_package_count': 1,
                                    'excluded_fits': 0, 'scientific_admission': False}
        families[family] = {'comparisons': comparisons}
    return {'families': families, 'fits': fits, 'references': references, 'scope': scope,
            'scientific_admission': False, 'practical_effect_nats': .05,
            'method': 'paired proper-log-score differences; equal optimizer seeds and public-question clusters, fixed reference package',
            'limitation': 'conditional on the pinned reference; three fitted seeds are not independent reference fits; generation and historical admission remain separate'}


def profile(plan, queue, status, assignment, scope, expected):
    choice, cr = complete_job(plan, queue, status, assignment['choice_job'], 'runners.stage9.choice_analysis')
    calibration, pr = complete_job(plan, queue, status, assignment['calibration_job'], 'runners.stage9.calibration_check')
    receipts = {'choice': cr, 'calibration': pr}
    if choice is None or calibration is None:
        return {'status': 'NOT_RUN', 'reason': 'choice or calibration source unavailable', 'profile_receipts': receipts}
    ci = read(choice / 'IDENTITY.json'); cp = read(choice / 'PROFILE.json')
    neural = inside(ci['inputs']['neural']['path']); ni = read(neural / 'IDENTITY.json')
    nd = read(neural / 'COMPLETE.json'); pi = read(calibration / 'IDENTITY.json')
    if (file_hash(neural / 'COMPLETE.json') != ci['inputs']['neural']['complete_sha256'] or
            nd['identity_sha256'] != digest(ni) or nd.get('execution_complete') is not True or
            closure([REPO / p for p in nd['outputs']['files']]) != nd['outputs']):
        raise ValueError('comparison neural producer changed')
    if (ci['operation'] != 'choice-profile-v1' or ci['scope'] != scope or
            pi['operation'] != 'actual-package-calibration-consumer-v1' or pi['scope'] != scope or
            ni['family'] != expected['family'] or ni['package_kind'] != expected['package_kind'] or
            ni['adapter_sha256'] != expected['adapter_sha256'] or ni['operation'] != 'genuine_choice' or
            ni['scope'] != scope or cp['role'] != ('discovery' if scope == 'scientific' else 'pilot') or
            cp['selection_only'] is not False or cp['assigned_units'] != (192 if scope == 'scientific' else 2) or
            ci['package'] != pi['package'] or ci['package'] != read(neural / 'PACKAGE.json')):
        raise ValueError('comparison requires the actual complete choice package and its calibration')
    if ni['training_complete_sha256'] != expected['training_complete_sha256']:
        raise ValueError('comparison fitting or reference identity changed')
    contract = {'cases_complete_sha256': ni['cases_complete_sha256'], 'operation': ni['operation'],
                'inputs': {k: ci['inputs'][k] for k in ('baseline', 'development', 'selection')}}
    return {'status': 'COMPLETE', 'choice_rows': read(choice / 'PAIRED_ROWS.json'),
            'comparison_contract': contract, 'instrument_accepted': read(calibration / 'DECISION.json')['instrument_accepted'],
            'profile_receipts': receipts, 'adapter_sha256': ni['adapter_sha256']}


def collect(manifest, queue, assignment, scope, fit_manifest=None, fit_queue=None):
    manifest, queue, assignment = map(inside, (manifest, queue, assignment))
    fits, plan, status, provenance = source_queues(manifest, queue, scope, fit_manifest, fit_queue)
    assigned = read(assignment)
    if set(assigned) != {'fits', 'references'}:
        raise ValueError('explicit fitted and reference assignments required')
    fm = {(r['family'], r['recipe'], r['seed']): r for r in assigned['fits']}
    rm = {(r['family'], r['package_kind']): r for r in assigned['references']}
    if (len(fm) != len(assigned['fits']) or set(fm) != {(r['family'], r['recipe'], r['seed']) for r in fits} or
            len(rm) != len(assigned['references']) or set(rm) != set(REFERENCES)):
        raise ValueError('missing or repeated package assignments')
    output = []
    for fit in fits:
        if fit['status'] != 'COMPLETE':
            output.append(fit); continue
        key = (fit['family'], fit['recipe'], fit['seed'])
        expected = {'family': fit['family'], 'package_kind': 'fitted', 'adapter_sha256': fit['adapter_sha256'],
                    'training_complete_sha256': fit['complete_sha256']}
        output.append(fit | profile(plan, queue, status, fm[key], scope, expected))
    references = []
    for family, kind in REFERENCES:
        _, adapter, identity = reference_package(family, kind)
        expected = {'family': family, 'package_kind': kind, 'adapter_sha256': adapter, 'training_complete_sha256': identity}
        references.append({'family': family, 'package_kind': kind} | profile(plan, queue, status, rm[(family, kind)], scope, expected))
    return output, references, provenance


def run(directory, manifest, queue, assignment, scope, fit_manifest=None, fit_queue=None):
    started, cpu = time.monotonic(), time.process_time()
    directory = inside(directory)
    prefix = 'reference-analysis-pilots' if scope == 'pilot' else 'scientific-reference-analysis'
    if scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / prefix):
        raise ValueError('reference analysis output scope differs')
    fits, refs, provenance = collect(manifest, queue, assignment, scope, fit_manifest, fit_queue)
    source = sources(); identity = {'cell_identity': cell_identity(), 'operation': 'fitted-reference-choice-analysis-v1',
                                    'scope': scope, 'source': source, 'source_queues': provenance,
                                    'assignment_sha256': file_hash(inside(assignment)), 'inputs_sha256': digest([fits, refs])}
    with writer(directory):
        Units(directory, identity)
        if (directory / 'COMPLETE.json').exists():
            done = read(directory / 'COMPLETE.json')
            if done['identity_sha256'] != digest(identity) or closure([REPO / p for p in done['outputs']['files']]) != done['outputs']:
                raise ValueError('completed reference analysis changed')
            return done
        freeze(directory / 'COMPARISONS.json', score_json(summarize(fits, refs, scope)))
        verify_sources(source)
        done = {'cell_identity': identity['cell_identity'], 'identity_sha256': digest(identity), 'execution_complete': True,
                'wall_seconds': time.monotonic() - started, 'parent_cpu_seconds': time.process_time() - cpu,
                'outputs': closure([directory / p for p in ('IDENTITY.json', 'COMPARISONS.json')]), 'scientific_admission': False}
        freeze(directory / 'COMPLETE.json', done); return done


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('output', 'manifest', 'queue', 'assignment'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('fitting-manifest', 'fitting-queue'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args()
    run(args.output, args.manifest, args.queue, args.assignment, args.scope, args.fitting_manifest, args.fitting_queue)
