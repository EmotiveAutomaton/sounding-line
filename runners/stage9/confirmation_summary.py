"""B02 complete-family collection after every selected execution is terminal.

DESIGN CHECK: B02/B03/X05/X11/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: a missing, running, substituted or changed selected execution cannot produce
a final family. Failed selected claims occupy their original slots. ALTERNATIVE:
the exact frozen family, including an empty selection, reconciles actual queue
commits and complete saved predictions before one fixed numerical calculation.
This collector reports numerical outcomes; final live admission and public scientific
confirmation are deferred to B03 and the final packet, never inferred from file presence.
"""
from .live_status import read as read_status
import argparse
from functools import partial
from pathlib import Path
import time

from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .confirmation_access import frozen_review
from .confirmation_baselines import calculation_input
from .confirmation_statistics import family
from .queue import inside, verify_committed, verify_disposition, writer
from .revision_predictions import finish, reentry, sources
from .training_jobs import cell_identity


def arguments(job, flag):
    args = job['arguments']
    if args.count(flag) != 1:
        raise ValueError('one exact execution argument required: ' + flag)
    at = args.index(flag)
    if at + 1 == len(args) or args[at + 1].startswith('--'):
        raise ValueError('execution argument has no value: ' + flag)
    return args[at + 1]


def collect(context, queue_path, own_cell):
    plan, frozen = context['plan'], context['review']
    jobs = {j['id']: j for j in plan['jobs']}
    mappings = plan.get('confirmation_result_jobs', {})
    if (not isinstance(mappings, dict) or not set(mappings) <= set(frozen['policy']['candidates'])
            or len(set(mappings.values())) != len(mappings)):
        raise ValueError('original manifest requires a unique explicit result job per candidate')
    own = [j for j in plan['jobs'] if digest({'manifest_sha256': digest(plan), 'job': j}) == own_cell]
    if (len(own) != 1 or own[0]['module'] != 'runners.stage9.confirmation_summary'
            or own[0]['role'] != 'closure' or own[0].get('allow_failed_dependencies') is not True
            or context['freeze_job'] not in own[0]['after']):
        raise ValueError('final family requires its actual failure-retaining closure job')
    state = read_status(queue_path / 'STATUS.json')
    if state['manifest_sha256'] != digest(plan):
        raise ValueError('family queue differs from its original manifest')
    outcomes, receipts = {}, {}
    for packet in frozen['selected']:
        key = packet['id'];job_id = mappings.get(key)
        if job_id not in jobs or job_id not in own[0]['after']:
            raise ValueError('selected claim lacks its declared prior execution job')
        job, status = jobs[job_id], state['jobs'][job_id]
        contract = plan.get('confirmation_execution', {}).get(key)
        expected_module = ('runners.stage9.confirmation_neural'
                           if contract and contract.get('adapter') in ('neural-choice-v1', 'neural-choice-rehearsal-v1')
                           else 'runners.stage9.confirmation_baselines')
        if (job['module'] not in ('runners.stage9.confirmation_baselines', 'runners.stage9.confirmation_neural')
                or job['module'] != expected_module
                or arguments(job, '--claim') != key
                or arguments(job, '--scope') != context['scope']
                or (REPO / arguments(job, '--freeze')).resolve() != (REPO / jobs[context['freeze_job']]['produces']).parent):
            raise ValueError('selected result job executes another claim, freeze or scope')
        if status['status'] in ('FAILED', 'NOT_RUN'):
            verify_disposition(queue_path, job, status)
            receipts[key] = {'job': job_id, 'status': status['status'], 'sha256': status['disposition_sha256']}
            outcomes[key] = {'status': status['status'], 'reason': status['reason'],
                             'receipt_sha256': status['disposition_sha256']}
            continue
        if status['status'] != 'COMPLETE':
            raise ValueError('all selected confirmation jobs must be terminal before final calculation')
        verify_committed(queue_path, job, plan, digest(plan))
        directory = (REPO / job['produces']).parent
        done, identity = read(directory / 'COMPLETE.json'), read(directory / 'IDENTITY.json')
        if (done.get('execution_complete') is not True or done['identity_sha256'] != digest(identity)
                or identity['claim_id'] != key or identity['claims_sha256'] != context['claims_sha256']
                or identity['freeze_complete_sha256'] != context['freeze_complete_sha256']
                or identity['selected_units'] != packet['reserve_units']
                or identity['execution_contract_sha256'] != packet['execution_contract_sha256']
                or done['outputs'] != closure([REPO / p for p in done['outputs']['files']])):
            raise ValueError('actual confirmation output differs from its frozen claim')
        outcome = read(directory / 'OUTCOME.json')
        calculate = calculation_input
        if job['module'] == 'runners.stage9.confirmation_neural':
            from .confirmation_neural import calculation_input as neural_calculation, seed_grid
            calculate = partial(neural_calculation, scope=context['scope'])
            if (identity.get('operation') != 'frozen-neural-choice-confirmation-v1'
                    or identity.get('seeds') != list(seed_grid(context['scope']))):
                raise ValueError('neural confirmation lacks its full frozen seed identity')
        if outcome != calculate(read(directory / 'PREDICTIONS.json'), packet['reserve_units']):
            raise ValueError('saved confirmation contrast does not reproduce from complete predictions')
        receipts[key] = {'job': job_id, 'status': 'COMPLETE', 'sha256': file_hash(directory / 'COMPLETE.json')}
        if outcome['calculation_status'] == 'READY':
            outcomes[key] = {'status': 'COMPLETE', 'rows': outcome['paired_rows'],
                             'assigned_targets': outcome['assigned_targets']}
        else:
            outcomes[key] = {'status': 'NOT_RUN', 'reason': 'finite inference unavailable; all failed/nonfinite forecasts retained in OUTCOME.json',
                             'receipt_sha256': file_hash(directory / 'OUTCOME.json')}
    return {'family': family(frozen['selected'], outcomes), 'execution_receipts': receipts,
            'freeze_complete_sha256': context['freeze_complete_sha256'], 'claims_sha256': context['claims_sha256'],
            'scope': context['scope'], 'scientific_confirmation': False, 'public_claim': 'unchanged'}


def run(directory, freeze_directory, manifest_path, queue_path, scope):
    start, cpu = time.monotonic(), time.process_time()
    directory, queue_path = map(inside, (directory, queue_path))
    if (scope not in ('pilot', 'scientific') or scope == 'scientific' and directory != ROOT / 'B02'
            or scope == 'pilot' and not directory.is_relative_to(ROOT / 'private/confirmation-execution-pilots')):
        raise ValueError('final confirmation family output differs from its declared scope')
    context = frozen_review(freeze_directory, manifest_path, queue_path, scope)
    cell = cell_identity()
    result = collect(context, queue_path, cell)
    identity = {'cell_identity': cell, 'operation': 'confirmation-family-v1', 'scope': scope,
        'source': sources(), 'manifest_sha256': context['manifest_sha256'],
        'freeze_complete_sha256': context['freeze_complete_sha256'], 'claims_sha256': context['claims_sha256'],
        'execution_receipts': result['execution_receipts']}
    with writer(directory):
        Units(directory, identity)
        prior = reentry(directory, identity)
        freeze(directory / 'FAMILY.json', result)
        if prior is not None:
            return prior
        if collect(context, queue_path, cell) != result:
            raise ValueError('confirmation evidence changed during final collection')
        return finish(directory, identity, start, cpu, ['FAMILY.json'],
                      selected_claims=result['family']['selected_count'], scientific_confirmation=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('output', 'freeze', 'manifest', 'queue'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args()
    run(args.output, args.freeze, args.manifest, args.queue, args.scope)
