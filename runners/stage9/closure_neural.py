"""Read-only B03 reconstruction of complete three-seed neural confirmations.

DESIGN CHECK: B03/X01/X02/X06/X11/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: unopened reserves, changed sources, seed/package/view substitutions, missing
calls, extra units and a rewritten calculation refuse even with refreshed hashes.
ALTERNATIVE: all assigned seed/unit pairs reconstruct from the original opened
inputs and actual saved capsule evidence, with no model or reserve-access action.
Failed calls remain in the whole calculation. Failed/unrun jobs never open inputs.
Capsule isolation, resident/request reconciliation and public claims remain the
separate final-ledger components; this semantic check cannot grant admission.
"""
import hashlib
import json
from pathlib import Path

from .artifact_comparisons import audit_execution, validate_cases
from .common import REPO, ROOT, closure, digest, file_hash, read
from .confirmation_access import frozen_claim, pointer_path, validate_contract
from .confirmation_neural import SEEDS, calculation_input, forecast, seed_grid
from .launch import checked
from .live_status import read as read_status
from .neural_operations import request_task
from .queue import inside


def inspect_completed(directory, frozen, cell, source):
    """Require original access before parsing payloads; never invoke a writer."""
    directory = inside(directory); work = directory / 'work'
    packet, contract = frozen['packet'], frozen['contract']
    scope = frozen['scope']; seeds = seed_grid(scope); role = 'pilot' if scope == 'pilot' else 'reserve'
    expected = ROOT / 'private/scientific-confirmations' / digest(packet['id'])[:16]
    adapter_kind = 'neural-choice-rehearsal-v1' if scope == 'pilot' else 'neural-choice-v1'
    if (scope == 'scientific' and directory != expected
            or scope == 'pilot' and not directory.is_relative_to(ROOT / 'private/confirmation-execution-pilots')
            or contract['adapter'] != adapter_kind):
        raise ValueError('neural inspection requires the original scoped confirmation directory')
    done = read(work / 'COMPLETE.json'); opened = read(directory / 'OPENED.json')
    selected = validate_contract(contract, packet)
    access = {'operation': 'frozen-reserve-access-v1', 'frozen': frozen, 'selected': selected}
    if (read(directory / 'IDENTITY.json') != access or opened.get('identity_sha256') != digest(access)
            or opened.get('scope') != scope or opened.get('scientific_confirmation') is not False):
        raise ValueError('neural execution lacks its original opened reserve identity')
    identity = {'cell_identity': cell, 'operation': 'frozen-neural-choice-confirmation-v1',
        'scope': scope, 'role': role, 'source': source, 'claim_id': packet['id'],
        'freeze_complete_sha256': frozen['freeze_complete_sha256'], 'claims_sha256': frozen['claims_sha256'],
        'execution_contract_sha256': digest(contract), 'selected_units': packet['reserve_units'],
        'seeds': list(seeds), 'access_identity_sha256': digest(access),
        'access_opened_sha256': file_hash(directory / 'OPENED.json')}
    if (read(work / 'IDENTITY.json') != identity or done.get('execution_complete') is not True
            or done.get('cell_identity') != cell or done.get('identity_sha256') != digest(identity)
            or done.get('scientific_confirmation') is not False):
        raise ValueError('neural completion differs from its frozen execution identity')
    if done['outputs'] != closure([REPO / p for p in done['outputs']['files']]):
        raise ValueError('completed neural output closure changed')
    cases = []
    for unit in packet['reserve_units']:
        item = selected[unit]; data = pointer_path(item['input']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['input']['sha256']:
            raise ValueError('original reserved payload bytes changed')
        case = json.loads(data)
        if case['unit'] != unit or digest(case['sources']) != item['content_sha256']:
            raise ValueError('reserved content differs from the frozen source unit')
        cases.append(case)
    validate_cases(cases, role)
    rows = []; calls = set(); units = set(); capsules = set()
    packages = {seed: checked(contract['readers'][str(seed)]['package']) for seed in seeds}
    for seed in seeds:
        for case in cases:
            def call(evidence, side):
                task = request_task(evidence, {'operation': 'choice'}, packages[seed])
                path = work / 'calls' / str(seed) / digest(case['unit'])[:16] / (side + '.json')
                calls.add(path.resolve()); saved = read(path)
                if set(saved) != {'input_sha256', 'result'} or saved['input_sha256'] != digest({'evidence': evidence, 'task': task}):
                    raise ValueError('saved neural call differs from the original seed, package or evidence')
                result = saved['result']; cap = Path(result['capsule']).resolve()
                if not cap.is_relative_to(work / 'capsules') or cap in capsules:
                    raise ValueError('neural call substitutes or reuses another execution capsule')
                capsules.add(cap)
                if type(result.get('accepted')) is not bool:
                    raise ValueError('actual neural call validity must be boolean')
                if read(cap / 'evidence.json') != evidence or read(cap / 'task.json') != task:
                    raise ValueError('actual neural capsule used different evidence or package')
                audit_execution(result)
                return result
            row = forecast(case, seed, contract['contrast'], call, scope=scope)
            key = [case['unit'], seed]; path = work / 'units' / (digest(key) + '.json')
            units.add(path.resolve())
            if read(path) != {'identity': digest(identity), 'key': key, 'complete': True, 'row': row}:
                raise ValueError('saved seed unit differs from original source and forecasts')
            rows.append(row)
    if ({p.resolve() for p in (work / 'calls').rglob('*.json')} != calls
            or {p.resolve() for p in (work / 'units').rglob('*.json')} != units):
        raise ValueError('completed neural execution has extra or missing calls or seed units')
    outcome = calculation_input(rows, packet['reserve_units'], scope=scope)
    if read(work / 'PREDICTIONS.json') != rows or read(work / 'OUTCOME.json') != outcome:
        raise ValueError('saved neural predictions or paired calculation differ from actual inputs')
    if (done.get('assigned_units') != len(cases) or done.get('completed_units') != len(cases)
            or done.get('training_seeds') != list(seeds) or done.get('role') != role
            or done.get('calculation_status') != outcome['calculation_status']):
        raise ValueError('completion counts or seed grid differ from the whole execution')
    return {'status': 'RECONSTRUCTED', 'units': len(cases), 'seed_units': len(rows), 'calls': len(calls),
        'training_seeds': list(seeds), 'complete_sha256': file_hash(work / 'COMPLETE.json'),
        'reader_packages_sha256': digest({str(s): p for s, p in packages.items()}),
        'predictions_sha256': digest(rows), 'outcome_sha256': digest(outcome),
        'new_reserve_openings': 0, 'new_reader_calls': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    from .confirmation_summary import arguments
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        if job['module'] != 'runners.stage9.confirmation_neural':
            continue
        current = state['jobs'][key]
        if current['status'] != 'COMPLETE':
            result[key] = {k: current[k] for k in ('status', 'reason', 'disposition_sha256')}
            continue
        directory = inside(Path(arguments(job, '--output')))
        if (REPO / job['produces']).resolve() != directory / 'work/COMPLETE.json':
            raise ValueError('semantic review differs from the original neural producer')
        frozen = frozen_claim(Path(arguments(job, '--freeze')), Path(arguments(job, '--manifest')),
                              queue_path, arguments(job, '--claim'), arguments(job, '--scope'))
        cell = digest({'manifest_sha256': digest(plan), 'job': job})
        result[key] = inspect_completed(directory, frozen, cell, plan['sources'])
    return {'jobs': result, 'scope': 'completed three-seed structured-choice confirmations only',
            'scientific_admission': False}
