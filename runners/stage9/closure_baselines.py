"""B03 read-only semantic reconstruction of completed baseline confirmations.

DESIGN CHECK: B03/X01/X02/X05/X06/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: unopened reserves, substituted worlds/fits/views/doses/tasks, missing calls,
extra units or saved forecasts disconnected from actual capsule inputs refuse.
ALTERNATIVE: original B01 inputs reconstruct the complete saved predictions and
paired calculation without opening a new reserve, invoking a reader or writing.
Failed/unrun executions retain their dispositions and never open their inputs.
This validates this adapter only; full workload lineage/claims remain separate.
"""
from .live_status import read as read_status
import hashlib
import json
from pathlib import Path

from .artifact_comparisons import audit_execution, model_inputs, validate_cases
from .common import REPO, ROOT, closure, digest, file_hash, read
from .confirmation_access import frozen_claim, pointer_path, validate_contract
from .confirmation_baselines import calculation_input, forecast
from .queue import inside


def inspect_completed(directory, frozen, cell, source):
    """Require saved access and complete execution before reading reserved payloads."""
    directory = inside(directory); work = directory / 'work'
    packet, contract, scope = frozen['packet'], frozen['contract'], frozen['scope']
    expected = ROOT / 'private/scientific-confirmations' / digest(packet['id'])[:16]
    if (scope not in ('pilot', 'scientific') or scope == 'scientific' and directory != expected
            or scope == 'pilot' and not directory.is_relative_to(ROOT / 'private/confirmation-execution-pilots')):
        raise ValueError('final inspection cannot substitute the original reserve directory')
    # No Units(), writer(), freeze(), reservation() or runtime.execute() here.
    done = read(work / 'COMPLETE.json'); opened = read(directory / 'OPENED.json')
    selected = validate_contract(contract, packet)
    access_identity = {'operation': 'frozen-reserve-access-v1', 'frozen': frozen, 'selected': selected}
    if (read(directory / 'IDENTITY.json') != access_identity
            or opened.get('identity_sha256') != digest(access_identity)
            or opened.get('scope') != scope or opened.get('scientific_confirmation') is not False):
        raise ValueError('complete execution lacks its original opened reserve identity')
    role = 'pilot' if scope == 'pilot' else 'reserve'
    identity = {'cell_identity': cell, 'operation': 'frozen-baseline-confirmation-v1',
        'scope': scope, 'role': role, 'source': source, 'claim_id': packet['id'],
        'freeze_complete_sha256': frozen['freeze_complete_sha256'], 'claims_sha256': frozen['claims_sha256'],
        'execution_contract_sha256': digest(contract), 'selected_units': packet['reserve_units'],
        'access_identity_sha256': digest(access_identity), 'access_opened_sha256': file_hash(directory / 'OPENED.json')}
    if (read(work / 'IDENTITY.json') != identity or done.get('execution_complete') is not True
            or done.get('cell_identity') != cell or done.get('identity_sha256') != digest(identity)
            or done.get('scientific_confirmation') is not False):
        raise ValueError('completed baseline identity differs from its original frozen execution')
    if done['outputs'] != closure([REPO / p for p in done['outputs']['files']]):
        raise ValueError('completed baseline output closure changed')
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
    models = model_inputs((REPO / contract['reader']['path']).parent, role)
    if models['completion_sha256'] != contract['reader']['sha256']:
        raise ValueError('reconstructed fitting package differs from the frozen reader')
    rows = []; calls = set(); units = set()
    for case in cases:
        def call(bundle, view):
            path = work / 'calls' / case['unit'][:16] / (view + '.json'); calls.add(path.resolve())
            saved = read(path)
            if set(saved) != {'input_sha256', 'result'} or saved['input_sha256'] != digest(bundle):
                raise ValueError('saved baseline call differs from reconstructed permitted inputs')
            result = saved['result']; cap = Path(result['capsule']).resolve()
            if not cap.is_relative_to(work / 'capsules'):
                raise ValueError('baseline result refers to another execution capsule')
            task = {'operation': 'baseline_matrix', 'budget': 10000,
                    'information_sha256': digest(bundle), 'strengths': [8., 16., 32.]}
            if read(cap / 'evidence.json') != bundle or read(cap / 'task.json') != task:
                raise ValueError('actual baseline capsule used different evidence, fits or task settings')
            audit_execution(result)
            return result
        row = forecast(case, models, contract['contrast'], call)
        path = work / 'units' / (digest(case['unit']) + '.json'); units.add(path.resolve())
        if read(path) != {'identity': digest(identity), 'key': case['unit'], 'complete': True, 'row': row}:
            raise ValueError('saved complete unit differs from reconstructed source and forecasts')
        rows.append(row)
    if ({p.resolve() for p in (work / 'calls').rglob('*.json')} != calls
            or {p.resolve() for p in (work / 'units').rglob('*.json')} != units):
        raise ValueError('completed execution has extra or missing calls or units')
    outcome = calculation_input(rows, packet['reserve_units'])
    if read(work / 'PREDICTIONS.json') != rows or read(work / 'OUTCOME.json') != outcome:
        raise ValueError('saved final predictions or paired calculation differ from actual inputs')
    if (done.get('assigned_units') != len(cases) or done.get('completed_units') != len(rows)
            or done.get('role') != role or done.get('calculation_status') != outcome['calculation_status']):
        raise ValueError('completion counts or calculation status differ from the whole execution')
    return {'status': 'RECONSTRUCTED', 'units': len(rows), 'calls': len(calls),
            'complete_sha256': file_hash(work / 'COMPLETE.json'),
            'reader_complete_sha256': models['completion_sha256'],
            'predictions_sha256': digest(rows), 'outcome_sha256': digest(outcome),
            'new_reserve_openings': 0, 'new_reader_calls': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    from .confirmation_summary import arguments
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        if job['module'] != 'runners.stage9.confirmation_baselines':
            continue
        current = state['jobs'][key]
        if current['status'] != 'COMPLETE':
            result[key] = {k: current[k] for k in ('status', 'reason', 'disposition_sha256')}
            continue
        directory = inside(Path(arguments(job, '--output')))
        if (REPO / job['produces']).resolve() != directory / 'work/COMPLETE.json':
            raise ValueError('semantic review differs from the original baseline producer')
        frozen = frozen_claim(Path(arguments(job, '--freeze')), Path(arguments(job, '--manifest')),
                              queue_path, arguments(job, '--claim'), arguments(job, '--scope'))
        cell = digest({'manifest_sha256': digest(plan), 'job': job})
        result[key] = inspect_completed(directory, frozen, cell, plan['sources'])
    return {'jobs': result, 'scope': 'completed numerical-baseline confirmations only', 'scientific_admission': False}
