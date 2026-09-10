"""B03 component: terminal execution ledger and fresh-process saved calculations.

DESIGN CHECK: B03/X11/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: missing jobs, false live gates, changed sources/outputs, substituted execution
or lost failed-attempt cost refuse closure. ALTERNATIVE: every prior job retains
its actual terminal disposition and all observed costs; a newly spawned interpreter
reproduces the declared saved calculations under recorded compiled source bytes.
Bands: verified execution ledger or explicit refusal. This is not the complete B03
semantic adapter/data/isolation audit and cannot grant scientific admission.
"""
from .live_status import read as read_status
import argparse
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .process_identity import native_identity
from .queue import (conditions, inside, validate_manifest, verify_committed,
                    verify_disposition, verify_execution, verify_sources, writer)
from .revision_predictions import finish, reentry, sources
from .training_jobs import cell_identity

MODULE = 'runners.stage9.closure_ledger'


def prior_jobs(plan, own_cell):
    matches = [i for i, j in enumerate(plan['jobs'])
               if digest({'manifest_sha256': digest(plan), 'job': j}) == own_cell]
    if len(matches) != 1:
        raise ValueError('audit lacks its actual queue cell identity')
    index = matches[0]; own = plan['jobs'][index]; prior = plan['jobs'][:index]
    if (not prior or own['module'] != MODULE or own['resource'] != 'cpu'
            or own['role'] != 'closure' or own.get('allow_failed_dependencies') is not True
            or set(own['after']) != {j['id'] for j in prior}):
        raise ValueError('audit must wait for every prior job and retain failed dependencies')
    for later in plan['jobs'][index + 1:]:
        if (later['module'] != 'runners.stage9.final_packet' or later['role'] != 'closure'
                or own['id'] not in later['after']):
            raise ValueError('scientific, repair and calculation work must precede final audit')
    return own, {j['id']: j for j in prior}


def attempt_ledger(plan, queue_path, state, prior):
    rows = []; numbers = {}; previous_end = None
    for attempt in state['attempts']:
        key = attempt['job']
        if key not in prior:
            continue  # The running audit and final reporter account for themselves.
        job = prior[key]; cell = digest({'manifest_sha256': digest(plan), 'job': job})
        numbers[key] = numbers.get(key, 0) + 1
        directory = inside(queue_path / attempt['directory'], queue_path)
        expected_directory = queue_path / 'attempts' / (key + '-' + str(numbers[key]))
        if directory != expected_directory or attempt['cell_identity'] != cell or attempt['resource'] != job['resource']:
            raise ValueError('attempt identity, order or resource differs from its original job')
        config = read(directory / 'CONFIG.json')
        if (config['cell_identity'] != cell or config['module'] != job['module']
                or config['arguments'] != job['arguments'] or config['sources'] != plan['sources']
                or Path(config['repo']).resolve() != REPO or Path(config['attempt']).resolve() != directory):
            raise ValueError('actual attempt configuration differs from the scheduled invocation')
        start, end, wall, gpu = (attempt.get(k) for k in
            ('started_at', 'ended_at', 'occupied_wall_seconds', 'gpu_reserved_wall_seconds'))
        if (any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in (start, end, wall, gpu))
                or end < start or not math.isclose(wall, end - start, rel_tol=1e-9, abs_tol=1e-6)
                or not math.isclose(gpu, wall if job['resource'] == 'gpu' else 0, abs_tol=1e-6)
                or previous_end is not None and start < previous_end):
            raise ValueError('all attempt costs must reconcile with the actual serial intervals')
        previous_end = end
        if type(attempt.get('returncode')) is not int:
            raise ValueError('terminal attempt has no actual return code')
        wrapper = attempt.get('wrapper_process')
        ready = read(directory / 'READY.json') if (directory / 'READY.json').exists() else None
        if wrapper and native_identity(wrapper['pid']) == wrapper or ready and native_identity(ready['process']['pid']) == ready['process']:
            raise ValueError('a terminal job still owns a live native process')
        paths = [directory / 'CONFIG.json']
        for name in ('READY.json', 'EXECUTION.json', 'GPU_OBSERVATIONS.json', 'INTERRUPTION_AUTHORIZATION.json'):
            if (directory / name).exists():
                paths.append(directory / name)
        if job['resource'] == 'gpu':
            observed = read(directory / 'GPU_OBSERVATIONS.json') if (directory / 'GPU_OBSERVATIONS.json').exists() else []
            if (attempt.get('gpu_observation_count') != len(observed)
                    or attempt.get('gpu_utilization_measured') is not any(r['available'] for r in observed)):
                raise ValueError('GPU point-sample accounting differs from retained observations')
        rows.append({'job': key, 'attempt': numbers[key], 'returncode': attempt['returncode'],
                     'wall_seconds': wall, 'gpu_reserved_seconds': gpu, 'resource': job['resource'],
                     'evidence': closure(paths)})
    for key, job in prior.items():
        status = state['jobs'][key]
        if status['status'] == 'NOT_RUN':
            if numbers.get(key, 0):
                raise ValueError('unrun job has an executed attempt')
        elif not numbers.get(key) or status.get('attempt') != numbers[key]:
            raise ValueError('terminal job lost an attempt or its current attempt number')
        if status['status'] == 'COMPLETE':
            committed = read(queue_path / 'commits' / (key + '.json'))
            expected = 'attempts/' + key + '-' + str(numbers[key]) + '/EXECUTION.json'
            if committed['execution_path'] != expected:
                raise ValueError('completion is not the actual final attempt')
    return {'attempts': rows, 'attempt_count': len(rows),
            'occupied_wall_seconds': math.fsum(r['wall_seconds'] for r in rows),
            'gpu_reserved_wall_seconds': math.fsum(r['gpu_reserved_seconds'] for r in rows),
            'cpu_job_wall_seconds': math.fsum(r['wall_seconds'] for r in rows if r['resource'] == 'cpu'),
            'scope': 'all prior attempts including failures; excludes active audit and later packet',
            'utilization_scope': 'device-wide point samples; unobserved intervals and other users are not attributed'}


def calculations(plan, queue_path, prior):
    """An explicit original-plan list; no new reader calls or scientific replication."""
    from .confirmation_access import frozen_review
    from .confirmation_summary import arguments, collect
    selected = plan.get('final_calculations')
    if not isinstance(selected, list) or not selected:
        raise ValueError('original manifest must select final calculations before closure')
    result = {}; state = read_status(queue_path / 'STATUS.json')
    for item in selected:
        if set(item) != {'kind', 'job'} or item['kind'] != 'confirmation_family' or item['job'] not in prior or item['job'] in result:
            raise ValueError('unsupported, missing or duplicated selected final calculation')
        job = prior[item['job']]
        if state['jobs'][job['id']]['status'] != 'COMPLETE':
            result[job['id']] = {'status': state['jobs'][job['id']]['status'],
                'reason': state['jobs'][job['id']]['reason'],
                'disposition_sha256': state['jobs'][job['id']]['disposition_sha256']}
            continue
        if job['module'] != 'runners.stage9.confirmation_summary':
            raise ValueError('selected family calculation names another producer')
        context = frozen_review(Path(arguments(job, '--freeze')), Path(arguments(job, '--manifest')),
                                queue_path, arguments(job, '--scope'))
        expected_cell = digest({'manifest_sha256': digest(plan), 'job': job})
        recomputed = collect(context, queue_path, expected_cell)
        saved = (REPO / job['produces']).parent / 'FAMILY.json'
        if read(saved) != recomputed:
            raise ValueError('selected final calculation differs from complete saved inputs')
        result[job['id']] = {'status': 'REPRODUCED', 'file_sha256': file_hash(saved),
                            'calculation_sha256': digest(recomputed)}
    return result


def verify_identity(job, done):
    if 'identity_sha256' not in done:
        return
    directory = (REPO / job['produces']).parent
    if job['module'] == 'runners.stage9.training_jobs' and job.get('arguments', [])[:1] == ['collect']:
        from .closure_collections import collection_root
        directory = collection_root(job)
    if done['identity_sha256'] != digest(read(directory / 'IDENTITY.json')):
        raise ValueError('completed producer identity changed')


def snapshot(manifest_path, queue_path, own_cell):
    from .closure_capsules import queue_audits
    from .closure_baselines import queue_audits as baseline_audits
    from .closure_neural import queue_audits as neural_audits
    from .closure_human import queue_audits as human_audits
    from .closure_cases import queue_audits as case_audits
    from .closure_coverage import inspect as coverage_audit
    from .closure_services import queue_audits as service_audits, archive_audits
    from .closure_raw import queue_audits as raw_audits
    from .closure_collections import queue_audits as collection_audits
    from .closure_operations import queue_audits as operation_audits
    from .closure_calibration import queue_audits as calibration_audits
    from .closure_purpose import queue_audits as purpose_audits
    from .closure_genetic import queue_audits as genetic_audits
    from .closure_comparators import queue_audits as comparator_audits
    from .closure_diagnostics import queue_audits as diagnostic_audits
    plan = read(manifest_path); validate_manifest(plan); verify_sources(plan['sources'])
    state = read_status(queue_path / 'STATUS.json')
    if (read(queue_path / 'MANIFEST.json') != plan or state['manifest_sha256'] != digest(plan)
            or set(state['jobs']) != {j['id'] for j in plan['jobs']}):
        raise ValueError('final audit must cover the exact original queue')
    own, prior = prior_jobs(plan, own_cell); terminal = {}
    for key, job in prior.items():
        status = state['jobs'][key]
        if status['status'] not in ('COMPLETE', 'FAILED', 'NOT_RUN'):
            raise ValueError('every prior scientific, repair and confirmation job must be terminal')
        reason = conditions(job, state['jobs'], {j['id']: j for j in plan['jobs']})
        if status['status'] == 'COMPLETE':
            if reason is not None:
                raise ValueError('completed consumer has a failed current gate: ' + key)
            verify_committed(queue_path, job, plan, digest(plan))
            done = read(REPO / job['produces'])
            if 'outputs' in done and done['outputs'] != closure([REPO / p for p in done['outputs']['files']]):
                raise ValueError('completed producer output closure changed')
            verify_identity(job, done)
            terminal[key] = {'status': 'COMPLETE', 'produce_sha256': file_hash(REPO / job['produces']),
                             'commit_sha256': file_hash(queue_path / 'commits' / (key + '.json'))}
        else:
            verify_disposition(queue_path, job, status)
            disposition = read(queue_path / status['disposition_path'])
            if (disposition['cell_identity'] != digest({'manifest_sha256': digest(plan), 'job': job})
                    or not status.get('reason') or disposition['reason'] != status['reason']):
                raise ValueError('failed or unrun outcome lacks its original identity and reason')
            terminal[key] = {k: status[k] for k in ('status', 'reason', 'disposition_sha256')}
        terminal[key]['live_condition_failure'] = reason
    return {'manifest_sha256': digest(plan), 'source_sha256': plan['sources']['sha256'],
            'audit_job': own['id'], 'jobs': terminal, 'job_count': len(terminal),
            'resources': attempt_ledger(plan, queue_path, state, prior),
            'capsule_audits': queue_audits(plan, queue_path, prior),
            'baseline_semantic_audits': baseline_audits(plan, queue_path, prior),
            'neural_semantic_audits': neural_audits(plan, queue_path, prior),
            'neural_operation_audits': operation_audits(plan, queue_path, prior),
            'package_calibration_audits': calibration_audits(plan, queue_path, prior),
            'purpose_context_audits': purpose_audits(plan, queue_path, prior),
            'genetic_prediction_audits': genetic_audits(plan, queue_path, prior),
            'comparator_prediction_audits': comparator_audits(plan, queue_path, prior),
            'operation_diagnostic_audits': diagnostic_audits(plan, queue_path, prior),
            'human_semantic_audits': human_audits(plan, queue_path, prior),
            'prepared_source_audits': case_audits(plan, queue_path, prior),
            'resident_service_audits': service_audits(plan, queue_path, prior),
            'historical_service_audits': archive_audits(plan.get('service_archives', [])),
            'raw_source_audits': raw_audits(plan, queue_path, prior),
            'training_collection_audits': collection_audits(plan, queue_path, prior),
            'coverage_audit': coverage_audit(plan, queue_path, prior),
            'calculations': calculations(plan, queue_path, prior), 'scientific_admission': False,
            'remaining_validation': ['semantic adapter/data lineage', 'complete read-only capsule isolation',
                                     'all card/attack coverage', 'final public-claim decisions']}


def run(directory, manifest_path, queue_path, scope):
    start, cpu = time.monotonic(), time.process_time()
    directory, manifest_path, queue_path = map(inside, (directory, manifest_path, queue_path))
    if (scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / ('closure-ledger-' + scope))
            or read(manifest_path)['kind'] != ('prelaunch_rehearsal' if scope == 'pilot' else 'science')):
        raise ValueError('execution audit component output differs from its declared scope')
    cell = cell_identity(); result = snapshot(manifest_path, queue_path, cell)
    identity = {'cell_identity': cell, 'operation': 'closure-execution-ledger-v1', 'scope': scope,
                'source': sources(), 'manifest_sha256': result['manifest_sha256'], 'ledger_sha256': digest(result)}
    with writer(directory):
        Units(directory, identity); prior = reentry(directory, identity)
        if prior is not None:
            return prior
        attempt = directory / 'fresh-process'; attempt.mkdir(exist_ok=True)
        request = {'manifest': str(manifest_path), 'queue': str(queue_path), 'audit_cell': cell}
        freeze(attempt / 'REQUEST.json', request)
        config = {'repo': str(REPO), 'attempt': str(attempt), 'sources': identity['source'],
                  'cell_identity': digest({'fresh_final_ledger': identity}), 'module': MODULE,
                  'arguments': ['--recompute', str(attempt / 'REQUEST.json'), '--output', str(attempt / 'RESULT.json')]}
        freeze(attempt / 'CONFIG.json', config)
        with (attempt / 'stdout.log').open('wb') as out, (attempt / 'stderr.log').open('wb') as err:
            rc = subprocess.run([sys.executable, '-B', str(REPO / 'runners/stage9/source_bootstrap.py'),
                                 str(attempt / 'CONFIG.json')], cwd=REPO, stdout=out, stderr=err,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).returncode
        if rc:
            raise ValueError('fresh final calculation process failed; original failure retained')
        execution = verify_execution(attempt / 'EXECUTION.json', config['cell_identity'],
                                     read(manifest_path), {'module': MODULE})
        ready = read(attempt / 'READY.json')
        if ready['process']['pid'] == os.getpid() or ready['cell_identity'] != config['cell_identity']:
            raise ValueError('fresh calculation lacks an independent actual interpreter identity')
        if read(attempt / 'RESULT.json') != result or snapshot(manifest_path, queue_path, cell) != result:
            raise ValueError('fresh or repeated final ledger differs')
        freeze(directory / 'LEDGER.json', result)
        freeze(directory / 'REPRODUCTION.json', {'fresh_process': ready['process'],
            'execution_sha256': file_hash(attempt / 'EXECUTION.json'), 'ledger_sha256': digest(result),
            'loaded_source_files': len(execution['loaded_project_sources']),
            'scope': 'fresh-process calculation from saved outputs; not a new scientific replication'})
        return finish(directory, identity, start, cpu, ['LEDGER.json', 'REPRODUCTION.json', 'fresh-process'],
                      prior_jobs=result['job_count'], final_b03_complete=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recompute', type=Path)
    for key in ('manifest', 'queue'):
        parser.add_argument('--' + key, type=Path)
    parser.add_argument('--scope', choices=('pilot', 'scientific'))
    args = parser.parse_args()
    if args.recompute:
        request = read(inside(args.recompute))
        freeze(inside(args.output), snapshot(inside(Path(request['manifest'])), inside(Path(request['queue'])), request['audit_cell']))
    else:
        run(args.output, args.manifest, args.queue, args.scope)
