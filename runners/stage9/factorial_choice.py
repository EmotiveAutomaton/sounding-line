"""All-seed choice effects without an unrelated generation prerequisite.

DESIGN CHECK: C05/C07/X01/X11/X12; LESSONS 3--5, CONTROLS 6; brief 7.2.
NULL: a lucky seed, failed fit, invalid calibration or changed comparison cannot
be hidden by selection. ALTERNATIVE: complete paired choice effects retain the
original equal-seed factorial estimand and each family separately. Generation is
measured in its own selected-recipe profile; it neither admits nor blocks choice.
Bands remain the existing factorial dispositions, including every failed member.
"""
import argparse
from pathlib import Path
import time

from runners.stage9.common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from runners.stage9.factorial_analysis import source_queues, summarize as factorial_summary
from runners.stage9.reference_analysis import profile
from runners.stage9.revision_predictions import sources
from runners.stage9.queue import inside, verify_sources, writer
from runners.stage9.scoring import score_json
from runners.stage9.training_jobs import cell_identity


def collect(manifest, queue, assignment, scope, fit_manifest=None, fit_queue=None):
    manifest, queue, assignment = map(inside, (manifest, queue, assignment))
    fits, plan, status, provenance = source_queues(manifest, queue, scope, fit_manifest, fit_queue)
    assigned = read(assignment)
    if set(assigned) != {'fits'}:
        raise ValueError('explicit choice-factorial fit assignment required')
    fields = {'family', 'recipe', 'seed', 'choice_job', 'calibration_job'}
    if any(set(row) != fields or type(row['seed']) is not int for row in assigned['fits']):
        raise ValueError('choice factorial assigns only choice and own calibration, at each actual seed')
    mapping = {(r['family'], r['recipe'], r['seed']): r for r in assigned['fits']}
    if len(mapping) != len(assigned['fits']) or set(mapping) != {(r['family'], r['recipe'], r['seed']) for r in fits}:
        raise ValueError('choice factorial must retain every assigned fit')
    rows = []
    for fit in fits:
        if fit['status'] != 'COMPLETE':
            rows.append(fit); continue
        expected = {'family': fit['family'], 'package_kind': 'fitted', 'adapter_sha256': fit['adapter_sha256'],
                    'training_complete_sha256': fit['complete_sha256']}
        key = fit['family'], fit['recipe'], fit['seed']
        rows.append(fit | profile(plan, queue, status, mapping[key], scope, expected))
    # Distinct source/comparator contracts cannot be paired just because row IDs agree.
    for family in ('qwen', 'smollm'):
        contracts = [r['comparison_contract'] for r in rows if r['status'] == 'COMPLETE' and r['family'] == family]
        if contracts and any(contract != contracts[0] for contract in contracts):
            raise ValueError('choice factorial source or development-selected comparator differs')
    return rows, provenance


def summarize(rows, scope, draws=4000):
    if any('generation' in row for row in rows):
        raise ValueError('choice factorial cannot silently consume a generation profile')
    result = factorial_summary(rows, scope, draws)
    for family in result['families'].values():
        family['generation_scope'] = 'generation is a separate selected-recipe diagnostic, not a choice prerequisite'
    return result


def run(directory, manifest, queue, assignment, scope, fit_manifest=None, fit_queue=None):
    start, cpu = time.monotonic(), time.process_time(); directory = inside(directory)
    prefix = 'factorial-choice-pilots' if scope == 'pilot' else 'scientific-factorial-choice'
    if scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / prefix):
        raise ValueError('choice factorial output scope differs')
    rows, provenance = collect(manifest, queue, assignment, scope, fit_manifest, fit_queue)
    source = sources(); cell = cell_identity()
    identity = {'cell_identity': cell, 'operation': 'complete-seed-choice-factorial-v1', 'scope': scope,
                'source': source, 'source_queues': provenance, 'assignment_sha256': file_hash(inside(assignment)),
                'rows_sha256': digest(rows), 'generation_dependency': False}
    with writer(directory):
        Units(directory, identity)
        if (directory / 'COMPLETE.json').exists():
            done = read(directory / 'COMPLETE.json')
            if done['identity_sha256'] != digest(identity) or closure([REPO / p for p in done['outputs']['files']]) != done['outputs']:
                raise ValueError('completed choice factorial changed')
            return done
        freeze(directory / 'FACTORIAL.json', score_json(summarize(rows, scope)))
        freeze(directory / 'FIT_ROWS.json', rows); verify_sources(source)
        done = {'cell_identity': cell, 'identity_sha256': digest(identity), 'execution_complete': True,
                'generation_dependency': False, 'scientific_admission': False,
                'wall_seconds': time.monotonic() - start, 'parent_cpu_seconds': time.process_time() - cpu,
                'outputs': closure([directory / name for name in ('IDENTITY.json', 'FACTORIAL.json', 'FIT_ROWS.json')])}
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
