"""Composition guards; source-specific reconstruction has its own tests and pilots."""
import importlib
from pathlib import Path

import pytest

from runners.stage9 import closure_human as subject
from runners.stage9.common import closure, digest, file_hash, read, write


def fixture(tmp_path, monkeypatch, module_name='runners.stage9.record_jobs', valid=True):
    monkeypatch.setattr(subject, 'inside', lambda p: Path(p).resolve())
    monkeypatch.setattr(subject, 'verify_committed', lambda *args: None)
    route = subject.ROUTES[module_name]
    cases, fit, prediction = [tmp_path / name for name in ('cases', 'fit', 'prediction')]
    source_job = {'id': 'cases', 'module': 'runners.stage9.fixture_cases', 'arguments': [],
                  'produces': str(cases / 'COMPLETE.json'), 'after': []}
    fit_job = {'id': 'fit', 'module': module_name, 'arguments': ['fit', '--cases', str(cases)],
               'produces': str(fit / 'COMPLETE.json'), 'after': ['cases']}
    job = {'id': 'prediction', 'module': module_name, 'arguments': ['predict', '--output', str(prediction),
        '--cases', str(cases), '--fit', str(fit), '--scope', 'pilot', '--lane', 'development'],
        'produces': str(prediction / 'COMPLETE.json'), 'after': ['fit']}
    prior = {j['id']: j for j in (source_job, fit_job, job)}
    plan = {'jobs': list(prior.values()), 'sources': {'files': {}, 'sha256': digest({})}}
    state = {'jobs': {key: {'status': 'COMPLETE'} for key in prior}}
    original = {'train': [{'unit': 'train-person'}], 'development': [{'key': 'original'}], 'evaluation': [{'key': 'other'}]}
    write(cases / 'CASES.json', original); write(cases / 'COMPLETE.json', {'complete': True})
    fit_identity = {'operation': route['fit'], 'scope': 'pilot', 'cell_identity': 'fit-cell',
        'cases_complete_sha256': file_hash(cases / 'COMPLETE.json'), 'training_rows_sha256': digest(original['train'])}
    write(fit / 'IDENTITY.json', fit_identity)
    write(fit / 'COMPLETE.json', {'execution_complete': True, 'cell_identity': 'fit-cell',
        'identity_sha256': digest(fit_identity), 'outputs': closure([fit / 'IDENTITY.json']), 'training_only': True})
    identity = {'operation': route['prediction'], 'scope': 'pilot', 'cell_identity': digest({'manifest_sha256': digest(plan), 'job': job}),
        'source': plan['sources'], 'lane': 'development', 'cases': str(cases), 'fit': str(fit),
        'cases_complete_sha256': file_hash(cases / 'COMPLETE.json'), 'fit_complete_sha256': file_hash(fit / 'COMPLETE.json'),
        'assigned_rows_sha256': digest(original['development'])}
    write(prediction / 'IDENTITY.json', identity)
    cap = prediction / 'capsules/one'
    actual = {'evidence': {'public': 'input'}, 'task': {'parameters': {'fitted': 1}}}
    write(cap / 'evidence.json', actual['evidence']); write(cap / 'task.json', actual['task'])
    result = {'capsule': str(cap), 'accepted': valid}
    row = {'key': 'original', 'unit': 'person', 'view': 'artifact', 'valid': valid, 'call': result}
    rows = [row]
    key = row['key'] if route['runtime'] == 'commit' else {'case': row['key'], 'view': row['view']}
    call_name = row['key'] if route['runtime'] == 'commit' else digest(key)
    call_path = prediction / 'calls' / (call_name + '.json')
    unit_path = prediction / 'units' / (digest(key) + '.json')
    write(call_path, {'input_sha256': digest(actual), 'result': result})
    write(unit_path, {'identity': digest(identity), 'key': key, 'complete': True, 'row': row})
    write(prediction / 'PREDICTIONS.json', rows)
    done = {'execution_complete': True, 'cell_identity': identity['cell_identity'], 'identity_sha256': digest(identity),
            'assigned_calls': 1, 'invalid_calls': int(not valid)}
    def seal():
        done['outputs'] = closure([prediction / p for p in ('IDENTITY.json', 'PREDICTIONS.json', 'calls', 'units', 'capsules')])
        write(prediction / 'COMPLETE.json', done)
    seal()
    validator = importlib.import_module(route['validator'])
    monkeypatch.setattr(validator, 'verified_predictions', lambda *args: (rows, identity))
    return job, plan, tmp_path / 'queue', prior, state, identity, done, seal, call_path, unit_path


@pytest.mark.parametrize('module', list(subject.ROUTES))
@pytest.mark.parametrize('valid', [True, False])
def test_all_four_adapters_compose_read_only_and_retain_invalid_calls(tmp_path, monkeypatch, module, valid):
    args = fixture(tmp_path, monkeypatch, module, valid); before = closure([tmp_path])
    result = subject.inspect_completed(*args[:5])
    assert closure([tmp_path]) == before and result['calls'] == 1
    assert result['invalid_calls_retained'] == int(not valid)
    assert result['new_capsule_executions'] == result['refits'] == 0 and not result['scientific_admission']


@pytest.mark.parametrize('fault', ['missing_producer', 'wrong_fit_module', 'missing_dependency', 'training',
    'allocation', 'capsule_input', 'extra_call', 'unit', 'missing_call', 'count', 'failure_count'])
def test_source_fit_and_actual_call_faults_refuse_even_after_rehashing(tmp_path, monkeypatch, fault):
    job, plan, queue, prior, state, identity, done, seal, call_path, unit_path = fixture(tmp_path, monkeypatch)
    if fault == 'missing_producer': prior.pop('cases')
    elif fault == 'wrong_fit_module': prior['fit']['module'] = 'runners.stage9.other'
    elif fault == 'missing_dependency': job['after'] = []
    elif fault == 'training':
        path = tmp_path / 'cases/CASES.json'; data = read(path); data['train'].append({'unit': 'evaluation-person'}); write(path, data)
    elif fault == 'allocation':
        path = tmp_path / 'cases/CASES.json'; data = read(path); data['development'] = []; write(path, data)
    elif fault == 'capsule_input': write(tmp_path / 'prediction/capsules/one/task.json', {'parameters': {'fitted': 2}})
    elif fault == 'extra_call': write(call_path.parent / 'extra.json', {'unexpected': True})
    elif fault == 'unit':
        data = read(unit_path); data['row']['unit'] = 'another person'; write(unit_path, data)
    elif fault == 'missing_call': call_path.unlink()
    elif fault == 'count': done['assigned_calls'] = 2
    else: done['invalid_calls'] = 1
    seal()
    with pytest.raises((ValueError, FileNotFoundError)):
        subject.inspect_completed(job, plan, queue, prior, state)


def test_failed_unrun_and_nonprediction_jobs_never_invoke_a_reconstructor(tmp_path, monkeypatch):
    def forbidden(*args): raise AssertionError('failed/unrun job must not reconstruct')
    monkeypatch.setattr(subject, 'inspect_completed', forbidden)
    jobs = {key: {'id': key, 'module': 'runners.stage9.record_jobs', 'arguments': ['predict']} for key in ('failed', 'unrun')}
    jobs['fit'] = {'id': 'fit', 'module': 'runners.stage9.record_jobs', 'arguments': ['fit']}
    state = {'jobs': {key: {'status': status, 'reason': 'original reason', 'disposition_sha256': 'a' * 64}
                     for key, status in [('failed', 'FAILED'), ('unrun', 'NOT_RUN')]}}
    write(tmp_path / 'STATUS.json', state)
    result = subject.queue_audits({}, tmp_path, jobs)
    assert result['jobs'] == state['jobs'] and not result['scientific_admission']
