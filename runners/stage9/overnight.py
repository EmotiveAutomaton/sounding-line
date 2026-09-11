"""Explicit continuation of the existing two-package competence diagnostics.

DESIGN CHECK: Stage 9 C01/C02/C04/C06, LESSONS 3--5; direct overnight
authorization on 2026-09-11. NULL: a changed experiment, unproved imported gate,
missing rehearsal, source drift or hidden previous cost refuses launch.
ALTERNATIVE: the complete existing diagnostic grid reuses verified prerequisites
without pretending they executed again. Bands: accepted discovery execution or
refusal. No confirmation, training, new threshold, full-generator admission or
final scientific acceptance follows from this operational certificate.
"""
from copy import deepcopy
import math
from pathlib import Path

from .common import REPO, ROOT, read, digest, file_hash
from .launch import checked, require, REQUIRED, CARDS

POLICY = 'stage9-overnight-20260911-v1'
OPERATIONS = ('offered', 'environment_outcome', 'self_outcome', 'reset_environment',
              'artifact_environment', 'prefix_match', 'finite_queries')
IDS = {f'diagnostic-{f}-archive-{op}' for f in ('qwen', 'smollm') for op in OPERATIONS}
IDS |= {f'diagnostic-{f}-archive-{op}-calibration' for f in ('qwen', 'smollm')
        for op in ('offered', 'prefix_match', 'finite_queries')}
IDS |= {f'diagnostic-{f}-archive-{op}-profile' for f in ('qwen', 'smollm')
        for op in ('rollouts', 'prefix', 'finite')}


def selected_graph(plan, original, reused):
    """Only remove prerequisites proved complete in the immutable prior queue."""
    selected = [j['id'] for j in plan['jobs']]
    require(set(selected) == IDS and len(selected) == len(IDS), 'complete original diagnostic grid required')
    require(selected == [j['id'] for j in original if j['id'] in IDS], 'original diagnostic order changed')
    by = {j['id']: j for j in original}
    needed = {k for j in plan['jobs'] for k in by[j['id']]['after'] if k not in IDS}
    require(set(reused) == needed, 'external prerequisites omitted or invented')
    for job in plan['jobs']:
        expected = deepcopy(by[job['id']])
        expected['estimated_gpu_seconds'] = job['estimated_gpu_seconds']
        expected['after'] = [k for k in expected['after'] if k not in reused]
        expected['requires'] = [c for c in expected['requires'] if c['job'] not in reused]
        require(job == expected, 'original diagnostic settings or internal gates changed')
        for condition in by[job['id']]['requires']:
            if condition['job'] in reused:
                value = reused[condition['job']]
                for field in condition['field']:
                    value = value[field]
                require(value == condition['equals'], 'imported scientific prerequisite did not pass')


def validate(plan, evidence):
    from .queue import validate_manifest, verify_sources, verify_committed
    from .tranche import rehearsal, compatibility
    validate_manifest(plan); verify_sources(plan['sources'])
    value = plan['overnight_continuation']
    require(value['policy'] == POLICY and plan['kind'] == 'science', 'unknown continuation')
    require('execution_scope' not in plan, 'continuation cannot masquerade as original recovery')
    authorization = checked(value['authorization'])
    require(authorization['authority'] == 'curator' and authorization['gear'] == 2
            and authorization['minimum_estimated_gpu_seconds'] == 36000
            and authorization['additional_repairs_authorized'] is True
            and authorization['paid_compute'] is False and authorization['delegation'] is False,
            'explicit overnight continuation authority required')
    require(plan['horizon_epoch'] == authorization['admission_horizon_epoch'], 'undeclared admission horizon')
    prior = checked(value['prior_plan']); original = checked(value['original_jobs'])
    campaign = read(ROOT / 'CAMPAIGN.json')
    require(plan['campaign_start'] == prior['campaign_start'] == campaign['started_epoch'],
            'original campaign clock must remain intact')
    require(authorization['original_horizon_epoch'] == campaign['horizon_epoch'], 'old horizon hidden')
    require(value['original_jobs'] == prior['execution_scope']['original_jobs'], 'commissioned job catalog substituted')
    prior_certificate = checked(value['prior_certificate'])
    require(prior_certificate.get('accepted') is True and prior_certificate['manifest_sha256'] == digest(prior),
            'prerequisite lineage was not launch accepted')
    queue = (REPO / value['prior_queue']).resolve()
    require(queue.is_relative_to(ROOT), 'prior queue escaped stage')
    terminal = read(queue / 'COMPLETE.json')
    require(terminal == checked(value['prior_terminal']) and terminal['manifest_sha256'] == digest(prior),
            'prior terminal history changed')
    prior_jobs = {j['id']: j for j in prior['jobs']}
    reused = {}
    for key, pointer in value['reused'].items():
        require(key in prior_jobs and terminal['jobs'][key]['status'] == 'COMPLETE', 'cannot reuse failed or absent job')
        verify_committed(queue, prior_jobs[key], prior, digest(prior))
        require(pointer['path'] == prior_jobs[key]['produces'], 'import substituted another produce')
        reused[key] = checked(pointer)
        if 'outputs' in reused[key]:
            for path, sha in reused[key]['outputs']['files'].items():
                require(file_hash(REPO / path) == sha, 'imported data changed')
    selected_graph(plan, original, reused)
    require(set(evidence) == REQUIRED, 'all nine applicable launch evidence categories required')
    objects = {k: checked(v) for k, v in evidence.items()}
    review = objects['manual_review']
    require(review['manifest_sha256'] == digest(plan) and set(review['jobs']) == IDS,
            'manual review must cover every exact continuation job')
    require(set(review['cards']) == CARDS and review['final_integrity_required'] is True
            and review['full_stage_complete'] is False and review['confirmation_authorized'] is False,
            'card dispositions or final claim limits missing')
    for job in plan['jobs']:
        row = review['jobs'][job['id']]
        require(row['source_sha256'] == plan['sources']['files'][job['module'].replace('.', '/') + '.py'],
                'manual review entrypoint changed')
        require(all(isinstance(row.get(k), str) and row[k].strip() for k in
                    ('hypothesis', 'method', 'independent_unit', 'evidence_view', 'strongest_rival',
                     'null_expectation', 'alternative_expectation', 'failure_direction', 'exhaustive_bands')),
                'incomplete diagnostic design review')
    sources = objects['sources']
    compatibility(prior['sources'], plan['sources'], sources['compatibility'])
    for path, sha in prior['sources']['files'].items():
        archive = REPO / sources['prior_source_archive'] / path
        require(archive.is_relative_to(ROOT) and file_hash(archive) == sha, 'original executed source archive incomplete')
    require(set(sources['compatibility']['changes']) <= {'runners/stage9/process_identity.py', 'runners/stage9/launch.py', 'runners/stage9/README.md'},
            'scientific source modification requires a separate continuation review')
    # Reuse the exact source, package, split and actual idle-wake evidence from
    # the accepted prior campaign. No new data, model, reserve or tokenizer.
    prior_evidence = prior_certificate['checked_evidence']
    for key in ('packages', 'splits', 'wake'):
        require(evidence[key] == prior_evidence[key], 'continuation substituted inherited ' + key)
        checked(prior_evidence[key])
    require(objects['splits']['reserve_truth_opened'] is False, 'reserve must stay unopened')
    require(objects['wake']['delivered'] is True, 'actual idle delivery required')
    for ptr in objects['fixtures']['checks']:
        checked(ptr)
    require(objects['fixtures']['checks'] and objects['fixtures']['operations'] == list(OPERATIONS),
            'applicable executed diagnostic controls missing')
    interruption = objects['interruption']
    prior_interruption = checked(prior_evidence['interruption'])
    require(interruption['original'] == prior_evidence['interruption']
            and all(prior_interruption['checks'].values()), 'actual restart evidence lost')
    compatibility(prior['sources'], plan['sources'], interruption['compatibility'])
    rehearsal(plan, objects['dress_rehearsal'])
    forecast = objects['forecast']; calls = checked(forecast['calls']); startup = checked(forecast['startup'])
    require(set(forecast['jobs']) == IDS, 'forecast omits an actual job')
    typical = upper = 0.0
    for job in plan['jobs']:
        row = forecast['jobs'][job['id']]
        require(all(math.isfinite(row[k]) and row[k] >= 0 for k in ('gpu_typical_seconds', 'gpu_upper_seconds', 'cpu_seconds')),
                'nonfinite or negative forecast')
        if job['resource'] == 'gpu':
            call, start = calls[job['id']], startup[job['id']]
            require(call['planned_source_units'] == 192 and call['planning_multiplier'] == 1.5,
                    'original full diagnostic population and timing basis required')
            require(row['gpu_typical_seconds'] == call['observed_work_seconds'] + start['estimated_gpu_seconds']
                    and row['gpu_upper_seconds'] == call['full_declared_seconds'] + start['estimated_gpu_seconds'],
                    'GPU forecast differs from existing measured call/startup rates')
        else:
            checked(row['cpu_forecast'])
            require(row['gpu_typical_seconds'] == row['gpu_upper_seconds'] == 0, 'CPU work cannot fill GPU runway')
        require(job['estimated_gpu_seconds'] == row['gpu_upper_seconds'], 'queue reservation differs from forecast')
        typical += row['gpu_typical_seconds']; upper += row['gpu_upper_seconds']
    prior_gpu = sum(a.get('gpu_reserved_wall_seconds', 0) for a in terminal['attempts'])
    prior_forecast = checked(prior_evidence['forecast'])
    require(forecast['previous_science_gpu_seconds'] == prior_gpu
            and forecast['preparation_gpu_reserved_seconds'] == prior_forecast['preparation_gpu_reserved_seconds'],
            'prior occupied work or preparation reservation omitted')
    require(typical >= 36000 and upper + prior_gpu + forecast['preparation_gpu_reserved_seconds'] <= 92 * 3600,
            'overnight runway below request or total GPU cap exceeded')
    return {'manifest_sha256': digest(plan), 'checked_evidence': evidence, 'jobs': len(IDS), 'cards': 42,
            'acceptance_scope': 'overnight_continuation', 'execution_scope_sha256': digest(value),
            'permitted_claims': ['package_specific_competence_profiles_after_final_integrity'],
            'full_stage_accepted': False, 'scientific_claim': 'none from launch mechanics'}
