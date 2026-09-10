"""Read-only final audit of raw training-collector calls outside dispatch storage.

DESIGN CHECK: B03/C05/C07/X01/X02/X08/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: a changed collection root, assignment, teacher continuation, copied reader,
probe or resident request must refuse even if superficial hashes are refreshed.
ALTERNATIVE: the original training sources reconstruct every saved learner attempt
and teacher target with no inference or writes. Failed calls stay failed; orphan
capsules and missing service evidence remain explicit, never scientific admission.
"""
from collections import Counter
from pathlib import Path

from .common import REPO, ROOT, closure, digest, file_hash, read
from .closure_capsules import denial_probe, inspect_call
from .closure_probe import bindings
from .closure_services import inspect as inspect_services
from .confirmation_summary import arguments
from .construction import register, rendered_prefix
from .learner import collect_one, MATCHED_TEACHER_DRAWS
from .live_status import read as read_status
from .matching import earlier_context
from .queue import inside, verify_committed
from .recipes import parameter_partition
from .scientific_collector import collection_inputs
from .training_jobs import training_root


def collection_root(job):
    """The actual command root, shared by generic identity and raw-call audits."""
    family, coverage = [arguments(job, '--' + key) for key in ('family', 'coverage')]
    if family not in ('qwen', 'smollm') or coverage not in ('original', 'both'):
        raise ValueError('raw collection command has an unknown family or coverage')
    if '--rehearsal-root' in job['arguments']:
        directory = inside(arguments(job, '--rehearsal-root'))
        base = ROOT / 'private/collection-handler-pilots'
        if directory == base or not directory.is_relative_to(base):
            raise ValueError('raw collection command differs from its discarded namespace')
        return directory
    return ROOT / 'private/scientific-collection' / family / coverage


def raw_storage(directory, done, identity, copied_sources, probe):
    """Inspect original raw unit calls; do not manufacture checkpoint-call caches."""
    directory = inside(directory)
    if done['outputs'] != closure([directory / name for name in ('units', 'capsules', 'services')]):
        raise ValueError('raw collection storage omitted, changed or added bytes')
    denial_probe(probe, copied_sources)
    units, capsules, inspections = {}, set(), []
    unit_paths = sorted((directory / 'units').glob('*.json'))
    if set(unit_paths) != {p for p in (directory / 'units').rglob('*') if p.is_file()}:
        raise ValueError('raw collection contains unrecognized unit storage')
    for path in unit_paths:
        record = read(path); key = record['key']
        if (type(key) is not str or key in units or path.name != digest(key) + '.json'
                or record.get('complete') is not True or record.get('identity') != digest(identity)):
            raise ValueError('raw collection unit identity or roster changed')
        units[key] = record['row']
        for attempt in record['row']['attempts']:
            result = attempt['result']; cap = inside(result['capsule'], directory / 'capsules')
            if cap in capsules:
                raise ValueError('raw collection reused a capsule across attempts')
            capsules.add(cap)
            sidecar = cap.parent / 'closures' / (cap.name + '.json')
            if read(sidecar) != result['copied_sources']:
                raise ValueError('raw collection call differs from its source sidecar')
            checked = inspect_call(result, copied_sources, probe)
            evidence = read(cap / 'evidence.json')
            if attempt['evidence_sha256'] != digest(evidence):
                raise ValueError('raw collection attempt lost its actual visible input')
            inspections.append({'unit': key, 'turn': attempt['turn'],
                'capsule': cap.relative_to(REPO).as_posix(), 'inspection': checked})
    if not units or set(units) != set(identity['assigned_keys']):
        raise ValueError('raw collection omitted or repeated assigned sources')
    capsule_root = directory / 'capsules'
    materialized = {p.parent.resolve() for p in capsule_root.rglob('bootstrap.py')}
    if not capsules <= materialized:
        raise ValueError('raw collection saved call has no materialized capsule')
    # Interrupted, uncached capsules are retained, with no inferred execution.
    unbound = sorted(p.relative_to(REPO).as_posix() for p in capsule_root.iterdir()
                     if p.name != 'closures' and p.resolve() not in capsules)
    return units, {'calls': inspections, 'call_count': len(inspections),
        'unbound_capsules': unbound, 'unbound_scope': 'Retained bytes without inferred execution or attempt attribution',
        'scientific_admission': False}


def reconstruct_unit(key, row, source_row, world, *, adapter_sha, base):
    previous = earlier_context(source_row); with_goal = source_row['raw_record']['with_goal']
    attempts = row['attempts']; used = []
    def render(current, events):
        return previous + rendered_prefix(current, events, with_goal=with_goal)
    def saved(evidence, turn):
        if turn >= len(attempts) or attempts[turn]['turn'] != turn:
            raise ValueError('raw collection learner attempt missing or out of order')
        result = attempts[turn]['result']; cap = Path(result['capsule'])
        task = read(cap / 'task.json'); package = task['identity']
        expected = {'operation': 'generate', 'identity': package, 'max_new_tokens': 32,
                    'seed': int(digest({'collection': key, 'turn': turn})[:8], 16)}
        if (task != expected or read(cap / 'evidence.json') != evidence
                or package['information_sha256'] != digest(evidence)
                or package['adapter_sha256'] != adapter_sha
                or any(package[name] != base[name] for name in ('model', 'revision'))
                or package['precision'] != 'float16' or package['max_new_tokens'] != 32):
            raise ValueError('raw collection call changed its original input, seed or fitted package')
        used.append(turn)
        return result
    rebuilt = collect_one(world, saved, maximum_actions=4, teacher_draws=MATCHED_TEACHER_DRAWS, render=render)
    rebuilt.update(training_source_lineages=source_row['lineages'], with_goal=with_goal,
        earlier_context_sha256=digest(previous), parameter_partition=parameter_partition(world),
        source_parameter_roles=row['source_parameter_roles'])
    if used != list(range(len(attempts))) or rebuilt != row:
        raise ValueError('raw collection states, teacher targets or retained failures do not reconstruct')
    return len(used)


def inspect_completed(directory, dispatch, source, cell, *, family, coverage, training, rehearsal, probe):
    directory, dispatch, training = map(inside, (directory, dispatch, training))
    if (family not in ('qwen', 'smollm') or coverage not in ('original', 'both')
            or (rehearsal and not directory.is_relative_to(ROOT / 'private/collection-handler-pilots'))
            or (not rehearsal and directory != ROOT / 'private/scientific-collection' / family / coverage)):
        raise ValueError('raw collection root differs from its declared scope')
    done = read(directory / 'COMPLETE.json'); wrapper = read(dispatch); identity = read(directory / 'IDENTITY.json')
    if (done.get('identity_sha256') != digest(identity) or done.get('cell_identity') != cell
            or identity.get('cell_identity') != cell or wrapper.get('cell_identity') != cell
            or wrapper.get('operation') != 'collect' or wrapper.get('family') != family
            or wrapper.get('coverage') != coverage or identity.get('family') != family
            or identity.get('coverage') != coverage or identity.get('discarded_rehearsal') is not rehearsal
            or done.get('discarded_rehearsal') is not rehearsal
            or wrapper.get('collection_complete_sha256') != file_hash(directory / 'COMPLETE.json')
            or any(wrapper.get(k) != v for k, v in done.items())):
        raise ValueError('raw collection completion differs from its original dispatch identity')
    original = identity['sources']
    if (original['sha256'] != digest(original['files']) or not original['files']
            or any(source['files'].get(p) != sha or file_hash(REPO / p) != sha for p, sha in original['files'].items())):
        raise ValueError('raw collection reconstruction sources differ from the original caller')
    register()
    fitted, completed_fit, pool, chosen = collection_inputs(family, coverage, training, rehearsal=rehearsal)
    adapter = inside(training / completed_fit['selected_checkpoint'], training)
    adapter_sha = closure([adapter])['sha256']
    if (identity['collector_fit'] != fitted or identity['selected_checkpoint'] != adapter_sha
            or completed_fit['selected_checkpoint_sha256'] != adapter_sha or identity['pool_sha256'] != digest(pool)
            or identity['assigned_keys'] != sorted(chosen) or identity['actions_per_source'] != 4
            or identity['teacher_draws_per_state'] != MATCHED_TEACHER_DRAWS
            or identity['precision'] != 'float16'
            or identity['parameter_roles'] != dict(Counter(parameter_partition(w) for w in pool['private_worlds'].values()))):
        raise ValueError('raw collection source allocation or fitted checkpoint changed')
    binding = bindings('reader', source)
    units, storage = raw_storage(directory, done, identity, binding['copied_sources'], probe)
    source_rows = {row['key']: row for row in pool['candidate_examples']}
    for key, row in units.items():
        source_row = source_rows[key]
        if row['source_parameter_roles'] != {lid: parameter_partition(pool['private_worlds'][lid]) for lid in source_row['lineages']}:
            raise ValueError('raw collection earlier-source roles changed')
        reconstruct_unit(key, row, source_row, pool['private_worlds'][key],
            adapter_sha=adapter_sha, base=fitted['base'])
    if (done['sources_attempted'] != len(units)
            or done['actual_learner_actions'] != sum(row['learner_actions_applied'] for row in units.values())
            or done['sources_with_actual_visits'] != sum(row['learner_actions_applied'] > 0 for row in units.values())
            or done['domains'] != dict(Counter(row['domain'] for row in units.values()))):
        raise ValueError('raw collection completion counts changed')
    services = inspect_services(directory, done['outputs'], source, cell)
    return {'status': 'INSPECTED', 'collection_complete_sha256': file_hash(directory / 'COMPLETE.json'),
        'dispatch_sha256': file_hash(dispatch), 'training_complete_sha256': file_hash(training / 'COMPLETE.json'),
        'assigned_sources': len(units), 'raw_storage': storage, 'resident_services': services,
        'reconstruction': 'Every saved learner attempt, original visible input and teacher continuation; no inference',
        'new_model_calls': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    collectors = {key: job for key, job in prior.items() if job['module'] == 'runners.stage9.training_jobs'
                  and job['arguments'] and job['arguments'][0] == 'collect'}
    reviews = plan.get('collection_reviews', {})
    if not isinstance(reviews, dict) or set(reviews) != set(collectors):
        raise ValueError('every raw collector requires its explicit final review')
    if not collectors:
        return {'jobs': {}, 'scientific_admission': False}
    state = read_status(queue_path / 'STATUS.json'); results = {}
    for key, job in collectors.items():
        review = reviews[key]
        if not isinstance(review, dict) or set(review) != {'root', 'probe_job'}:
            raise ValueError('raw collection review fields differ')
        current = state['jobs'][key]
        if current['status'] in ('FAILED', 'NOT_RUN'):
            results[key] = {k: current[k] for k in ('status', 'reason', 'disposition_sha256')}
            continue
        if current['status'] != 'COMPLETE':
            raise ValueError('raw collection cannot be audited before terminal execution')
        family, coverage = [arguments(job, '--' + k) for k in ('family', 'coverage')]
        rehearsal = '--rehearsal-root' in job['arguments']
        directory = collection_root(job)
        training = inside(arguments(job, '--pilot-training')) if rehearsal else training_root(family, 'original_expert', 9001)
        if inside(REPO / review['root']) != directory:
            raise ValueError('raw collection review points outside its actual command root')
        probe_id = review['probe_job']; probe_job = prior.get(probe_id)
        required = {'job': probe_id, 'field': ['isolation_probe_verified'], 'equals': True}
        if (probe_job is None or probe_job['module'] != 'runners.stage9.closure_probe'
                or arguments(probe_job, '--runtime') != 'reader' or state['jobs'][probe_id]['status'] != 'COMPLETE'
                or probe_id not in job['after'] or required not in job.get('requires', [])):
            raise ValueError('raw collector did not require its successful reader probe')
        verify_committed(queue_path, job, plan, digest(plan))
        verify_committed(queue_path, probe_job, plan, digest(plan))
        probe_directory = (REPO / probe_job['produces']).parent
        if (read(REPO / probe_job['produces']).get('isolation_probe_verified') is not True
                or read(probe_directory / 'BINDING.json') != bindings('reader', plan['sources'])):
            raise ValueError('raw collector probe package or verdict changed')
        results[key] = inspect_completed(directory, REPO / job['produces'], plan['sources'],
            digest({'manifest_sha256': digest(plan), 'job': job}), family=family, coverage=coverage,
            training=training, rehearsal=rehearsal, probe=read(probe_directory / 'PROBE.json'))
    return {'jobs': results, 'scientific_admission': False,
            'scope': 'Original dispatch-bound raw collector storage, fitted sources, saved reconstruction and service accounting'}
