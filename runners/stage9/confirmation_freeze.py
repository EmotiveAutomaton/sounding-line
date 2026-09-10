"""B01: freeze a manual claim review against actual completed producer outputs.

DESIGN CHECK: B01/B02/X01/X05/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: incomplete upstream work, changed evidence, failed required gates, omitted
seeds, unmatched targets or reused reserve groups refuse the freeze. ALTERNATIVE:
zero to three manually selected exact comparisons retain the original selection
policy, all exclusions, full paired source grid and one fixed reserve allocation.
Bands are a completed immutable planning receipt or explicit refusal; this module
never executes a reserve reader or assigns scientific confirmation.

The policy is part of the original queue manifest, so it precedes discovery. The
operator supplies the completed review only after examining discovery. Scheduler
admission of B01 must wait for that review; this module does not invent a review.
Current numerical support is one-way paired proper log-score comparisons. Crossed
designs and other estimands require separately validated adapters, not relabeling.
"""
from .live_status import read as read_status
import argparse
import math
import time
from pathlib import Path

from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .confirmation_planning import allocate, SCIENTIFIC_SEEDS
from .confirmation_statistics import CONTRACT as ANALYSIS_CONTRACT
from .confirmation_access import bind_contracts
from .launch import checked
from .queue import inside, verify_committed, verify_disposition, verify_sources, writer
from .revision_predictions import finish, reentry, sources
from .scoring import log_score
from .training_jobs import cell_identity

PRIORITIES = ('broken_comparison', 'serious_rival', 'useful_capability')


def at_path(value, path):
    if not isinstance(path, list) or not path or any(not isinstance(k, str) or not k for k in path):
        raise ValueError('a nonempty explicit object-field path is required')
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ValueError('declared evidence field is absent')
        value = value[key]
    return value


def paired_rows(left, right, layout_left, layout_right, seed):
    """Recompute the declared proper score from complete committed forecasts."""
    fields = {'unit', 'target', 'truth', 'probabilities', 'valid'}
    def project(rows, layout):
        if not isinstance(rows, list) or not rows or set(layout) != fields:
            raise ValueError('complete forecast rows and exact declared layout required')
        result = {}
        for row in rows:
            item = {k: at_path(row, v) for k, v in layout.items()}
            if item['valid'] is not True:
                raise ValueError('failed assigned forecast cannot disappear from confirmation planning')
            if any(not isinstance(item[k], str) or not item[k] for k in ('unit', 'target', 'truth')):
                raise ValueError('explicit unit, target and truth identities required')
            key = (item['unit'], item['target'])
            if key in result:
                raise ValueError('duplicate source target in a paired forecast')
            result[key] = item
        return result
    a, b = project(left, layout_left), project(right, layout_right)
    if set(a) != set(b):
        raise ValueError('paired sides omit or add assigned source targets')
    output = []
    for key in sorted(a):
        x, y = a[key], b[key]
        if x['truth'] != y['truth'] or set(x['probabilities']) != set(y['probabilities']):
            raise ValueError('paired truth or forecast support differs')
        difference = log_score(x['probabilities'], x['truth']) - log_score(y['probabilities'], y['truth'])
        if not math.isfinite(difference):
            raise ValueError('nonfinite complete contrast cannot supply normal planning variance')
        output.append({'unit': key[0], 'target': key[1], 'seed': seed, 'difference': difference})
    return output


def reserve_units(inventory, used_units, count, order_seed, claim_id):
    """Read only the frozen source-allocation metadata, never reserve outcomes."""
    fields = {'unit', 'role', 'content_sha256'}
    roles = {'training', 'pilot', 'development', 'discovery', 'reserve'}
    if not isinstance(inventory, list) or not inventory or type(order_seed) is not int:
        raise ValueError('complete source allocation and fixed ordering seed required')
    units, content_roles = {}, {}
    for row in inventory:
        if (set(row) != fields or row['role'] not in roles
                or not isinstance(row['unit'], str) or not row['unit']
                or not isinstance(row['content_sha256'], str) or len(row['content_sha256']) != 64
                or any(c not in '0123456789abcdef' for c in row['content_sha256'])):
            raise ValueError('exact source metadata only; reserve payload cannot enter B01')
        if row['unit'] in units:
            raise ValueError('one canonical source unit cannot have multiple allocations')
        if row['content_sha256'] in content_roles:
            raise ValueError('duplicate source content must be resolved before reserve allocation')
        units[row['unit']] = row['role']
        content_roles[row['content_sha256']] = row['role']
    if any(units.get(unit) != 'discovery' for unit in used_units):
        raise ValueError('discovery predictions are not in their frozen source role')
    eligible = [unit for unit, role in units.items() if role == 'reserve']
    if type(count) is not int or count < 1 or count > len(eligible):
        raise ValueError('requested reserve exceeds independently allocated groups')
    return sorted(eligible, key=lambda unit: digest([order_seed, claim_id, unit]))[:count]


def inspect_queue(manifest_path, queue_path, scope):
    plan = read(manifest_path)
    verify_sources(plan['sources'])
    expected_kind = 'prelaunch_rehearsal' if scope == 'pilot' else 'science'
    if plan['kind'] != expected_kind or read(queue_path / 'MANIFEST.json') != plan:
        raise ValueError('claim review differs from the actual queue or scientific scope')
    state = read_status(queue_path / 'STATUS.json')
    if state['manifest_sha256'] != digest(plan):
        raise ValueError('upstream queue identity differs')
    jobs = {j['id']: j for j in plan['jobs']}
    upstream = {k: j for k, j in jobs.items() if j['role'] != 'closure'}
    if not upstream:
        raise ValueError('empty upstream workload cannot freeze scientific claims')
    snapshot = {}
    for key, job in upstream.items():
        status = state['jobs'][key]
        if status['status'] == 'COMPLETE':
            verify_committed(queue_path, job, plan, digest(plan))
            snapshot[key] = {'status': 'COMPLETE', 'produce_sha256': file_hash(REPO / job['produces'])}
        elif status['status'] in ('FAILED', 'NOT_RUN'):
            verify_disposition(queue_path, job, status)
            snapshot[key] = {k: status[k] for k in ('status', 'disposition_sha256')}
        else:
            raise ValueError('all scientific and repair jobs must be terminal before B01')
    return plan, upstream, snapshot


def producer_object(reference, jobs, snapshot):
    """Only a completed queue producer's committed output can supply evidence."""
    if not isinstance(reference, dict) or set(reference) != {'job', 'path'}:
        raise ValueError('evidence must name its actual upstream producer and output')
    key = reference['job']
    if key not in jobs or snapshot[key]['status'] != 'COMPLETE':
        raise ValueError('required claim evidence producer did not complete')
    completion_path = REPO / jobs[key]['produces']
    done = read(completion_path)
    path = inside(REPO / reference['path'])
    if path == completion_path:
        return done
    if done.get('execution_complete') is not True or not isinstance(done.get('outputs'), dict):
        raise ValueError('producer lacks complete immutable output evidence')
    named = path.relative_to(REPO).as_posix()
    if done['outputs']['files'].get(named) != file_hash(path):
        raise ValueError('claim data are not the completed producer output')
    return read(path)


def prediction_rows(reference, jobs, snapshot, scope):
    rows = producer_object(reference, jobs, snapshot)
    completion = REPO / jobs[reference['job']]['produces']
    done = read(completion)
    identity = read(completion.parent / 'IDENTITY.json')
    if digest(identity) != done.get('identity_sha256'):
        raise ValueError('forecast producer identity is not its completed identity')
    if identity.get('role') != ('pilot' if scope == 'pilot' else 'discovery'):
        raise ValueError('confirmation planning requires the explicit discovery forecast role')
    return rows


def review_packets(policy, review, jobs, snapshot, scope='scientific'):
    if (set(policy) != {'version', 'candidate_order', 'candidates', 'reserve_order_seed'}
            or type(policy['version']) is not int or policy['version'] != 1
            or type(policy['reserve_order_seed']) is not int):
        raise ValueError('exact pre-discovery confirmation policy required')
    order, candidates = policy['candidate_order'], policy['candidates']
    if (not isinstance(order, list) or not order or len(order) != len(set(order))
            or set(order) != set(candidates)):
        raise ValueError('the policy must enumerate every candidate exactly once')
    if set(review) != {'selected', 'reasons'} or set(review['reasons']) != set(order):
        raise ValueError('manual review must retain every selected and excluded candidate')
    selected = review['selected']
    if (not isinstance(selected, list) or len(selected) > 3 or len(set(selected)) != len(selected)
            or not set(selected) <= set(order)
            or selected != [key for key in order if key in selected]):
        raise ValueError('freeze at most three claims in the declared priority order')
    if any(not isinstance(reason, str) or not reason.strip() for reason in review['reasons'].values()):
        raise ValueError('every candidate requires the operator reasoning, including an empty selection')
    required = {'question', 'target', 'contrast', 'view', 'unit', 'priority', 'claim_kind',
                'practical_threshold', 'threshold_evidence', 'gate_scope', 'gates',
                'reader_packages', 'strongest_adversary', 'seed_forecasts', 'seed_evidence', 'layouts', 'allocation'}
    priorities = []
    for key in order:
        c = candidates[key]
        if set(c) != required or c['priority'] not in PRIORITIES:
            raise ValueError('complete exact candidate description and priority required')
        priorities.append(PRIORITIES.index(c['priority']))
        if any(not isinstance(c[k], str) or not c[k].strip() for k in
               ('question', 'target', 'contrast', 'view', 'unit', 'gate_scope', 'strongest_adversary')):
            raise ValueError('claim meaning and strongest adversary cannot be empty')
    if priorities != sorted(priorities):
        raise ValueError('selection priority must retain broken comparisons, serious rivals, then capabilities')
    packets = []
    for key in selected:
        c = candidates[key]
        if c['target'] != 'proper_log_score' or c['practical_threshold'] != .05:
            raise ValueError('this B01 adapter supports the declared .05-nat paired log-score estimand only')
        checked(c['threshold_evidence'])
        if not c['gates'] or not c['reader_packages']:
            raise ValueError('selected claim requires actual scoped gates and reader packages')
        for gate in c['gates']:
            if set(gate) != {'evidence', 'field'} or at_path(producer_object(gate['evidence'], jobs, snapshot), gate['field']) is not True:
                raise ValueError('selected claim has a failed or non-boolean required gate')
        packages = [producer_object(p, jobs, snapshot) for p in c['reader_packages']]
        forecasts = c['seed_forecasts']
        seeds = list(SCIENTIFIC_SEEDS) if set(forecasts) == {'9001', '9002', '9003'} else [None]
        if set(forecasts) != {str(seed) for seed in seeds} or set(c['layouts']) != {'left', 'right'}:
            raise ValueError('the complete scientific seed grid or untrained arm is required')
        bindings = c['seed_evidence']
        if set(bindings) != (set(forecasts) if seeds != [None] else set()):
            raise ValueError('every scientific seed requires its actual training and forecast identity')
        rows = []
        for seed in seeds:
            pair = forecasts[str(seed)]
            if set(pair) != {'left', 'right'}:
                raise ValueError('each seed requires both exact comparison sides')
            if seed is not None:
                binding = bindings[str(seed)]
                if set(binding) != {'training', 'forecast_identity'}:
                    raise ValueError('explicit actual fit-to-forecast binding required')
                training = producer_object(binding['training'], jobs, snapshot)
                observed = producer_object(binding['forecast_identity'], jobs, snapshot)
                forecast_job = jobs[binding['forecast_identity']['job']]
                expected_identity = (REPO / forecast_job['produces']).parent / 'IDENTITY.json'
                training_job = jobs[binding['training']['job']]
                expected_training_module = ('runners.stage9.confirmation_fixture' if scope == 'pilot'
                                            else 'runners.stage9.training_jobs')
                if (training_job['module'] != expected_training_module
                        or scope != 'pilot' and training.get('full_validation_retained') is not True
                        or scope == 'pilot' and training.get('synthetic_seed_metadata') is not True
                        or REPO / binding['forecast_identity']['path'] != expected_identity
                        or binding['forecast_identity']['job'] not in {pair[side]['job'] for side in pair}
                        or type(training.get('seed')) is not int or training['seed'] != seed
                        or not training.get('training_complete_sha256')
                        or observed.get('training_complete_sha256') != training['training_complete_sha256']):
                    raise ValueError('forecast labels cannot impersonate distinct fitted seeds')
            left, right = [prediction_rows(pair[side], jobs, snapshot, scope) for side in ('left', 'right')]
            rows.extend(paired_rows(left, right, c['layouts']['left'], c['layouts']['right'], seed))
        allocation = checked(c['allocation'])
        if not isinstance(allocation, list):
            raise ValueError('source allocation metadata must be an explicit row inventory')
        available = sum(row.get('role') == 'reserve' for row in allocation)
        planning = allocate(rows, seeds=seeds, threshold=.05, available_units=available, kind=c['claim_kind'])
        units = reserve_units(allocation, planning['discovery']['units'], planning['planned_units'],
                              policy['reserve_order_seed'], key)
        packets.append({'id': key, 'candidate': c, 'review_reason': review['reasons'][key],
            'planning': planning, 'reserve_units': units, 'paired_discovery_sha256': digest(rows),
            'analysis_contract': ANALYSIS_CONTRACT,
            'reader_package_content_hashes': [digest(p) for p in packages],
            'scientific_confirmation': False})
    return {'selected': packets, 'review': review, 'policy': policy, 'selected_count': len(packets),
            'selection_is_manual': True, 'reserve_outcomes_read': False,
            'scientific_confirmation': False, 'public_claim': 'unchanged'}


def run(directory, manifest_path, queue_path, review_path, scope):
    started, cpu = time.monotonic(), time.process_time()
    directory, manifest_path, queue_path, review_path = map(inside, (directory, manifest_path, queue_path, review_path))
    if (scope not in ('pilot', 'scientific') or scope == 'scientific' and directory != ROOT / 'B01'
            or scope == 'pilot' and not directory.is_relative_to(ROOT / 'private/confirmation-freeze-pilots')):
        raise ValueError('B01 output differs from its explicit scope')
    plan, jobs, snapshot = inspect_queue(manifest_path, queue_path, scope)
    policy = checked(plan['confirmation_policy'])
    review = read(review_path)
    result = bind_contracts(review_packets(policy, review, jobs, snapshot, scope), plan, scope, snapshot=snapshot)
    identity = {'cell_identity': cell_identity(), 'operation': 'confirmation-freeze-v1',
        'scope': scope, 'source': sources(), 'manifest_sha256': digest(plan),
        'policy': plan['confirmation_policy'], 'review_sha256': file_hash(review_path),
        'upstream': snapshot}
    with writer(directory):
        Units(directory, identity)
        prior = reentry(directory, identity)
        if prior is not None:
            if read(directory / 'CLAIMS.json') != result:
                raise ValueError('frozen confirmation packets changed after selection')
            return prior
        freeze(directory / 'CLAIMS.json', result)
        if file_hash(review_path) != identity['review_sha256']:
            raise ValueError('operator review changed while freezing claims')
        checked(plan['confirmation_policy'])
        _, _, after = inspect_queue(manifest_path, queue_path, scope)
        if after != snapshot or bind_contracts(review_packets(policy, review, jobs, snapshot, scope), plan, scope, snapshot=snapshot) != result:
            raise ValueError('claim evidence changed while freezing the completed review')
        return finish(directory, identity, started, cpu, ['CLAIMS.json'], selected_claims=len(result['selected']),
                      claim_selected={key: key in result['review']['selected'] for key in policy['candidate_order']},
                      reserve_outcomes_read=False, scientific_confirmation=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args()
    run(args.output, args.manifest, args.queue, args.review, args.scope)
