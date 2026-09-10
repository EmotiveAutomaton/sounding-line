import copy

import pytest

from runners.stage9 import closure_ledger as subject
from runners.stage9.common import digest, write


def plan_fixture():
    work = {'id': 'work', 'module': 'runners.stage9.confirmation_rehearsal',
            'resource': 'cpu', 'role': 'work', 'after': [], 'arguments': []}
    audit = {'id': 'audit', 'module': subject.MODULE, 'resource': 'cpu', 'role': 'closure',
             'after': ['work'], 'allow_failed_dependencies': True}
    return {'jobs': [work, audit], 'sources': {'files': {}, 'sha256': digest({})}}


def cell(plan):
    return digest({'manifest_sha256': digest(plan), 'job': plan['jobs'][1]})


@pytest.mark.parametrize('fault', ['missing_dependency', 'failed_dependency_excluded', 'later_science', 'wrong_module'])
def test_audit_cannot_close_before_its_complete_workload(fault):
    plan = plan_fixture()
    if fault == 'missing_dependency':
        plan['jobs'][1]['after'] = []
    elif fault == 'failed_dependency_excluded':
        plan['jobs'][1]['allow_failed_dependencies'] = False
    elif fault == 'later_science':
        plan['jobs'].append({'id': 'late', 'module': 'runners.stage9.confirmation_baselines',
                             'role': 'work', 'after': ['audit']})
    else:
        plan['jobs'][1]['module'] = 'runners.stage9.confirmation_summary'
    with pytest.raises(ValueError):
        subject.prior_jobs(plan, cell(plan))


def attempts_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'native_identity', lambda pid: None)
    plan = plan_fixture(); job = plan['jobs'][0]; queue = tmp_path / 'queue'
    attempts = []
    for number, start, end, rc in [(1, 10., 12., 1), (2, 14., 17., 0)]:
        directory = queue / 'attempts' / ('work-' + str(number))
        identity = digest({'manifest_sha256': digest(plan), 'job': job})
        write(directory / 'CONFIG.json', {'repo': str(tmp_path), 'attempt': str(directory),
            'cell_identity': identity, 'module': job['module'], 'arguments': job['arguments'], 'sources': plan['sources']})
        attempts.append({'job': 'work', 'directory': 'attempts/work-' + str(number),
            'cell_identity': identity, 'resource': 'cpu', 'started_at': start, 'ended_at': end,
            'occupied_wall_seconds': end - start, 'gpu_reserved_wall_seconds': 0., 'returncode': rc})
    write(queue / 'commits/work.json', {'execution_path': 'attempts/work-2/EXECUTION.json'})
    state = {'jobs': {'work': {'status': 'COMPLETE', 'attempt': 2}}, 'attempts': attempts}
    return plan, queue, state, {'work': job}


def test_failed_attempt_cost_is_retained_without_counting_the_idle_gap(tmp_path, monkeypatch):
    plan, queue, state, prior = attempts_fixture(tmp_path, monkeypatch)
    result = subject.attempt_ledger(plan, queue, state, prior)
    assert result['attempt_count'] == 2
    assert result['occupied_wall_seconds'] == result['cpu_job_wall_seconds'] == 5.
    assert result['gpu_reserved_wall_seconds'] == 0.
    assert [a['returncode'] for a in result['attempts']] == [1, 0]


@pytest.mark.parametrize('fault', ['lost_attempt', 'lost_cost', 'changed_command', 'overlap', 'live_worker', 'wrong_commit', 'unrun_executed'])
def test_attempt_audit_refuses_lost_or_substituted_execution(tmp_path, monkeypatch, fault):
    plan, queue, state, prior = attempts_fixture(tmp_path, monkeypatch)
    if fault == 'lost_attempt':
        state['attempts'].pop(0)
    elif fault == 'lost_cost':
        state['attempts'][0]['occupied_wall_seconds'] = 0.
    elif fault == 'changed_command':
        path = queue / 'attempts/work-1/CONFIG.json'
        config = subject.read(path); config['arguments'] = ['--substituted']; write(path, config)
    elif fault == 'overlap':
        state['attempts'][1].update(started_at=11., occupied_wall_seconds=6.)
    elif fault == 'live_worker':
        process = {'pid': 100, 'created_ticks': 200, 'executable': 'python.exe'}
        state['attempts'][0]['wrapper_process'] = process
        monkeypatch.setattr(subject, 'native_identity', lambda pid: process)
    elif fault == 'wrong_commit':
        write(queue / 'commits/work.json', {'execution_path': 'attempts/work-1/EXECUTION.json'})
    else:
        state['jobs']['work']['status'] = 'NOT_RUN'
    with pytest.raises(ValueError):
        subject.attempt_ledger(plan, queue, state, prior)


def test_absent_or_unsupported_final_calculations_cannot_be_called_reproduction(tmp_path):
    for selection in (None, [], [{'kind': 'new_scientific_fit', 'job': 'work'}]):
        plan = plan_fixture(); plan['final_calculations'] = selection
        write(tmp_path / 'STATUS.json', {'jobs': {}})
        with pytest.raises(ValueError):
            subject.calculations(plan, tmp_path, {'work': plan['jobs'][0]})


@pytest.mark.parametrize('rehearsal', [False, True])
@pytest.mark.parametrize('fault', [None, 'changed_actual', 'missing_actual', 'wrong_namespace'])
def test_collector_identity_comes_from_actual_storage_not_dispatch(tmp_path, monkeypatch, rehearsal, fault):
    from runners.stage9 import closure_collections
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(closure_collections, 'ROOT', tmp_path)
    monkeypatch.setattr(closure_collections, 'inside', lambda path: tmp_path / path)
    actual = tmp_path / ('private/collection-handler-pilots/test' if rehearsal else 'private/scientific-collection/qwen/original')
    job = {'module': 'runners.stage9.training_jobs', 'produces': 'dispatch/DISPATCH.json',
           'arguments': ['collect', '--family', 'qwen', '--coverage', 'original']}
    if rehearsal:
        job['arguments'] += ['--rehearsal-root', str(actual)]
    identity = {'cell_identity': 'original', 'family': 'qwen', 'coverage': 'original'}
    done = {'identity_sha256': digest(identity)}
    if fault:
        # A matching file at the wrong location must not rescue missing/changed data.
        write(tmp_path / 'dispatch/IDENTITY.json', identity)
    if fault != 'missing_actual':
        write(actual / 'IDENTITY.json', identity if fault != 'changed_actual' else {'cell_identity': 'substituted'})
    if fault == 'wrong_namespace':
        if rehearsal:
            job['arguments'][-1] = str(tmp_path / 'dispatch')
        else:
            job['arguments'][-1] = 'unknown'
    if fault is None:
        subject.verify_identity(job, done)
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            subject.verify_identity(job, done)


@pytest.mark.parametrize('operation', ['fit', 'pack'])
def test_other_training_dispatches_keep_their_original_identity_check(tmp_path, monkeypatch, operation):
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    job = {'module': 'runners.stage9.training_jobs', 'arguments': [operation], 'produces': 'dispatch/COMPLETE.json'}
    identity = {'cell_identity': 'original'}
    write(tmp_path / 'dispatch/IDENTITY.json', identity)
    done = {'identity_sha256': digest(identity)}
    subject.verify_identity(job, done)
    write(tmp_path / 'dispatch/IDENTITY.json', {'cell_identity': 'changed'})
    with pytest.raises(ValueError, match='identity changed'):
        subject.verify_identity(job, done)
