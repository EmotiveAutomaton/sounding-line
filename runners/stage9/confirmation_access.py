"""Bind reserve access to a committed B01 and an original execution contract.

DESIGN CHECK: B01/B02/X01/X02/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: an unselected claim, altered reader, substituted source, alternate output or
second concurrent writer refuses access. ALTERNATIVE: exactly the frozen source
groups open under one immutable claim identity, with the first access retained
even if subsequent prediction fails. No reserve payload is parsed during B01.
This is an access boundary, not a reader, source-semantic validator or confirmation
verdict. The actual adapter still owes source-role/projection validation, cached
prediction execution, retained failures and final complete-family calculations.
"""
from .live_status import read as read_status
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .launch import checked
from .queue import inside, verify_committed, writer
from .confirmation_statistics import CONTRACT


def pointer_path(pointer):
    if (not isinstance(pointer, dict) or set(pointer) != {'path', 'sha256'}
            or not isinstance(pointer['path'], str) or not pointer['path']
            or not isinstance(pointer['sha256'], str) or len(pointer['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in pointer['sha256'])):
        raise ValueError('exact input path and content hash required')
    original = REPO / pointer['path']
    if original.is_symlink():
        raise ValueError('reserve pointers cannot redirect through a symbolic link')
    return inside(original)


def validate_contract(contract, packet):
    """Inspect only source-allocation metadata and already-open reader evidence."""
    if isinstance(contract, dict) and contract.get('adapter') == 'neural-choice-rehearsal-v1':
        from .confirmation_neural import validate_rehearsal_contract
        validate_rehearsal_contract(contract, packet)
        return validate_reserve(contract, packet)
    if isinstance(contract, dict) and contract.get('adapter') == 'neural-choice-v1':
        from .confirmation_neural import validate_reader_contract
        validate_reader_contract(contract, packet)
        return validate_reserve(contract, packet)
    if (not isinstance(contract, dict)
            or set(contract) != {'adapter', 'resource', 'reader', 'reserve', 'contrast'}
            or contract['adapter'] != 'artifact-baselines-v1' or contract['resource'] != 'cpu'):
        raise ValueError('explicit supported CPU confirmation adapter contract required')
    if (packet['analysis_contract'] != CONTRACT
            or packet['planning']['discovery']['seeds'] != [None]
            or packet['candidate']['target'] != 'proper_log_score'):
        raise ValueError('this numerical-baseline adapter does not execute a neural training-seed claim')
    pointer_path(contract['reader'])
    package = checked(contract['reader'])
    if (packet['reader_package_content_hashes'] != [digest(package)]
            or len(packet['candidate']['reader_packages']) != 1
            or contract['reader']['path'] != packet['candidate']['reader_packages'][0]['path']):
        raise ValueError('execution reader differs from the exact selected package')
    contrast = contract['contrast']
    if not isinstance(contrast, dict) or set(contrast) != {'left', 'right'}:
        raise ValueError('exact paired baseline routes required')
    for side in contrast.values():
        if (not isinstance(side, dict) or set(side) != {'view', 'dose', 'model'}
                or side['view'] not in ('artifact', 'process_record')
                or type(side['dose']) is not int or side['dose'] not in (0, 1, 3, 7)
                or not isinstance(side['model'], str) or not side['model']):
            raise ValueError('each route requires its exact view, dose and fitted baseline key')
    if contrast['left'] == contrast['right']:
        raise ValueError('confirmation requires two explicitly distinct routes')
    return validate_reserve(contract, packet)


def validate_reserve(contract, packet):
    """Shared metadata-only allocation check; never parse reserved payloads here."""
    allocation = checked(packet['candidate']['allocation'])
    eligible = {r['unit']: r['content_sha256'] for r in allocation if r['role'] == 'reserve'}
    reserve = contract['reserve']
    if not isinstance(reserve, dict) or set(reserve) != set(eligible):
        raise ValueError('original execution inventory must cover the whole eligible reserve')
    paths = set()
    for unit, item in reserve.items():
        if (not isinstance(item, dict) or set(item) != {'input', 'content_sha256'}
                or item['content_sha256'] != eligible[unit]):
            raise ValueError('reserve descriptor differs from the frozen allocation metadata')
        path = pointer_path(item['input'])
        if path in paths:
            raise ValueError('one reserve payload cannot impersonate multiple source units')
        paths.add(path)
    if (len(packet['reserve_units']) != packet['planning']['planned_units']
            or len(set(packet['reserve_units'])) != len(packet['reserve_units'])
            or not set(packet['reserve_units']) <= set(reserve)):
        raise ValueError('exact frozen reserve count and source identities required')
    return {unit: reserve[unit] for unit in packet['reserve_units']}


def resolve_contract(contract, plan, snapshot=None):
    """Resolve predeclared producer outputs only after verified queue completion.

    Future fitting/forecast identities contain the manifest hash, so the manifest
    cannot precompute their hashes. It names their producer and output instead.
    B01 freezes the resulting bytes separately from that original declaration.
    Reserve pointers remain predeclared hashes and are never resolved or opened.
    """
    from .confirmation_freeze import producer_object
    result = deepcopy(contract)
    def resolve(reference):
        if not isinstance(reference, dict) or set(reference) != {'job', 'path'}:
            pointer_path(reference)
            return reference
        if snapshot is None:
            raise ValueError('producer references require the verified upstream snapshot')
        jobs = {j['id']: j for j in plan['jobs'] if j['role'] != 'closure'}
        if reference['job'] not in jobs or reference['job'] not in snapshot:
            raise ValueError('execution reference lacks its original upstream producer')
        completion = REPO / jobs[reference['job']]['produces']
        if (snapshot[reference['job']]['status'] != 'COMPLETE'
                or file_hash(completion) != snapshot[reference['job']]['produce_sha256']):
            raise ValueError('execution producer differs from its verified terminal snapshot')
        obj = producer_object(reference, jobs, snapshot)
        path = inside(REPO / reference['path'])
        sha = (snapshot[reference['job']]['produce_sha256'] if path == completion
               else read(completion)['outputs']['files'][path.relative_to(REPO).as_posix()])
        pointer = {'path': reference['path'], 'sha256': sha}
        pointer_path(pointer)
        if checked(pointer) != obj:
            raise ValueError('producer output changed while binding its execution pointer')
        return pointer
    def resolve_fit(reference):
        pointer = resolve(reference)
        if set(reference) != {'job', 'path'}:
            return pointer
        from .training_jobs import training_root
        from .confirmation_summary import arguments
        job = next(j for j in plan['jobs'] if j['id'] == reference['job'])
        if (result['adapter'] != 'neural-choice-v1' or job['module'] != 'runners.stage9.training_jobs'
                or not job['arguments'] or job['arguments'][0] != 'fit'
                or pointer_path(pointer) != (REPO / job['produces']).resolve()):
            raise ValueError('future training must name its actual scientific fitting-job completion')
        family, recipe = arguments(job, '--family'), arguments(job, '--recipe')
        seed = int(arguments(job, '--seed'))
        directory = training_root(family, recipe, seed)
        wrapper = checked(pointer)
        cell = digest({'manifest_sha256': digest(plan), 'job': job})
        if (wrapper.get('cell_identity') != cell or wrapper.get('full_validation_retained') is not True
                or (wrapper.get('family'), wrapper.get('recipe'), wrapper.get('seed')) != (family, recipe, seed)
                or (REPO / wrapper.get('training_root', '')).resolve() != directory):
            raise ValueError('fitting-job summary differs from its original factorial invocation')
        fitted = {'path': (directory / 'COMPLETE.json').relative_to(REPO).as_posix(),
                  'sha256': wrapper.get('training_complete_sha256')}
        pointer_path(fitted); done = checked(fitted)
        identity = read(directory / 'IDENTITY.json'); inputs = read(directory / 'SCIENTIFIC_INPUT.json')
        if (done.get('identity_sha256') != digest(identity) or digest(inputs) != wrapper.get('input_sha256')
                or inputs.get('cell_identity') != cell
                or (inputs.get('family'), inputs.get('recipe'), inputs.get('seed')) != (family, recipe, seed)
                or (identity.get('family'), identity.get('seed'), identity.get('split')) != (family, seed, 'training')
                or done.get('selected_checkpoint_sha256') != wrapper.get('selected_checkpoint_sha256')):
            raise ValueError('fitted checkpoint is not the original job-bound training evidence')
        return fitted
    if result.get('adapter') in ('neural-choice-v1', 'neural-choice-rehearsal-v1'):
        for item in result['readers'].values():
            item['training'] = resolve_fit(item['training'])
            item['package'] = resolve(item['package'])
            item['forecasts'] = {side: resolve(p) for side, p in item['forecasts'].items()}
    elif 'reader' in result:
        result['reader'] = resolve(result['reader'])
    return result


def bind_contracts(result, plan, scope, *, snapshot=None):
    """The original manifest, not post-discovery code, supplies execution recipes."""
    contracts = plan.get('confirmation_execution', {})
    if not isinstance(contracts, dict) or not set(contracts) <= set(result['policy']['candidates']):
        raise ValueError('confirmation execution inventory names an unknown candidate')
    for packet in result['selected']:
        contract = contracts.get(packet['id'])
        if contract is None:
            if scope == 'scientific':
                raise ValueError('selected scientific claim lacks its predeclared execution contract')
            packet['execution_contract_sha256'] = None
        else:
            validate_scope(contract, scope)
            resolved = resolve_contract(contract, plan, snapshot)
            validate_contract(resolved, packet)
            packet['execution_contract_sha256'] = digest(resolved)
            if resolved != contract:
                packet['execution_declaration_sha256'] = digest(contract)
    return result


def validate_scope(contract, scope):
    if contract.get('adapter') == 'neural-choice-rehearsal-v1' and scope != 'pilot':
        raise ValueError('discarded neural rehearsal cannot enter scientific reserve access')


def frozen_review(directory, manifest_path, queue_path, scope):
    """Require actual B01 completion, source-bound commit and original review."""
    from .confirmation_freeze import inspect_queue
    directory, manifest_path, queue_path = map(inside, (directory, manifest_path, queue_path))
    if (scope not in ('pilot', 'scientific')
            or scope == 'scientific' and directory != ROOT / 'B01'
            or scope == 'pilot' and not directory.is_relative_to(ROOT / 'private/confirmation-freeze-pilots')):
        raise ValueError('claim freeze namespace differs from its declared scope')
    plan, _, snapshot = inspect_queue(manifest_path, queue_path, scope)
    matches = [j for j in plan['jobs'] if REPO / j['produces'] == directory / 'COMPLETE.json'
               and j['module'] == 'runners.stage9.confirmation_freeze']
    if len(matches) != 1 or read_status(queue_path / 'STATUS.json')['jobs'][matches[0]['id']]['status'] != 'COMPLETE':
        raise ValueError('reserve requires the actual completed B01 queue job')
    job = matches[0]
    verify_committed(queue_path, job, plan, digest(plan))
    identity, done = read(directory / 'IDENTITY.json'), read(directory / 'COMPLETE.json')
    if (done.get('execution_complete') is not True or done['identity_sha256'] != digest(identity)
            or identity['upstream'] != snapshot or identity['manifest_sha256'] != digest(plan)
            or identity['scope'] != scope
            or done['outputs'] != closure([REPO / p for p in done['outputs']['files']])):
        raise ValueError('frozen claim evidence is incomplete or changed')
    args = job['arguments'];review_path = inside(REPO / args[args.index('--review') + 1])
    if file_hash(review_path) != identity['review_sha256']:
        raise ValueError('the original manual claim review changed')
    frozen = read(directory / 'CLAIMS.json')
    if frozen['review'] != read(review_path) or frozen['selected_count'] != len(frozen['selected']):
        raise ValueError('frozen selection differs from the complete original manual review')
    return {'plan': plan, 'review': frozen, 'scope': scope, 'freeze_job': job['id'], 'upstream': snapshot,
            'freeze_complete_sha256': file_hash(directory / 'COMPLETE.json'),
            'claims_sha256': file_hash(directory / 'CLAIMS.json'), 'manifest_sha256': digest(plan)}


def frozen_claim(directory, manifest_path, queue_path, claim_id, scope):
    context = frozen_review(directory, manifest_path, queue_path, scope)
    plan, frozen = context['plan'], context['review']
    selected = [p for p in frozen['selected'] if p['id'] == claim_id]
    if len(selected) != 1:
        raise ValueError('unselected claim cannot open a reserve')
    packet = selected[0];contract = plan.get('confirmation_execution', {}).get(claim_id)
    if contract is None:
        raise ValueError('execution differs from the original frozen claim contract')
    declared = digest(contract)
    contract = resolve_contract(contract, plan, context.get('upstream'))
    if (packet.get('execution_contract_sha256') != digest(contract)
            or declared != digest(contract) and packet.get('execution_declaration_sha256') != declared):
        raise ValueError('execution differs from the original frozen claim contract')
    validate_scope(contract, scope)
    validate_contract(contract, packet)
    return {'packet': packet, 'contract': contract, 'scope': scope,
            **{k: context[k] for k in ('freeze_complete_sha256', 'claims_sha256', 'manifest_sha256')}}


@contextmanager
def reservation(directory, frozen):
    """Hold one writer across opening and execution; retain a failed first access."""
    directory = inside(directory)
    packet, contract, scope = frozen['packet'], frozen['contract'], frozen['scope']
    validate_scope(contract, scope)
    expected = ROOT / 'private/scientific-confirmations' / digest(packet['id'])[:16]
    if (scope not in ('pilot', 'scientific') or scope == 'scientific' and directory != expected
            or scope == 'pilot' and not directory.is_relative_to(ROOT / 'private/confirmation-execution-pilots')):
        raise ValueError('one canonical scientific execution directory per frozen claim is required')
    selected = validate_contract(contract, packet)
    identity = {'operation': 'frozen-reserve-access-v1', 'frozen': frozen, 'selected': selected}
    with writer(directory):
        Units(directory, identity)
        opened = directory / 'OPENED.json'
        if opened.exists():
            if read(opened)['identity_sha256'] != digest(identity):
                raise ValueError('an opened reserve cannot change its claim or inputs')
        else:
            freeze(opened, {'at': datetime.now(timezone.utc).isoformat(), 'identity_sha256': digest(identity),
                            'scope': scope, 'scientific_confirmation': False})
        payloads = {}
        for unit, item in selected.items():
            # Hash and parse the same bytes, after durable access registration.
            data = pointer_path(item['input']).read_bytes()
            if hashlib.sha256(data).hexdigest() != item['input']['sha256']:
                raise ValueError('reserved payload changed from the frozen execution inventory')
            payloads[unit] = json.loads(data)
        yield {'payloads': payloads, 'packet': packet, 'contract': contract, 'identity': identity}
