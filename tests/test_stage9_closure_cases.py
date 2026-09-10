"""Prepared-source composition guards; real corpus replay is a separate rehearsal."""
import copy
from pathlib import Path

import pytest

from runners.stage9 import closure_cases as subject, common, revision_predictions
# Load providers before the temporary repository override; their imported runtime
# globals must never capture another test's directory at first import.
from runners.stage9 import (revision_cases, iterater_cases, coauthor_cases,
                            schola_cases, record_jobs, commit_cases, broll_cases)
from runners.stage9.common import closure, digest, read, write

ROUTES = ('argrewrite', 'iterater', 'coauthor', 'scholawrite', 'commit', 'broll')


def fixture(tmp_path, monkeypatch, route='broll'):
    monkeypatch.setattr(common, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(revision_predictions, 'REPO', tmp_path)
    for module in (subject, revision_predictions):
        monkeypatch.setattr(module, 'inside', lambda p: Path(p).resolve())
    monkeypatch.setattr(subject, 'verify_committed', lambda *args: None)
    rows = {lane: [{'unit': lane, 'truth': lane}] for lane in ('train', 'development', 'evaluation')}
    metadata = {'allocation': {lane: lane for lane in rows}, 'scope': 'pilot', 'exclusions': ['retained']}
    modules = {'argrewrite': 'revision_cases', 'iterater': 'iterater_cases', 'coauthor': 'record_jobs',
               'scholawrite': 'record_jobs', 'commit': 'commit_jobs', 'broll': 'broll_jobs'}
    job = {'id': 'cases', 'module': 'runners.stage9.' + modules[route],
        'arguments': ([] if route in ('argrewrite', 'iterater') else ['prepare']) +
                     ['--output', str(tmp_path / 'case'), '--scope', 'pilot'],
        'produces': 'case/COMPLETE.json'}
    if route == 'argrewrite':
        from runners.stage9 import revision_cases
        monkeypatch.setattr(revision_cases, 'inputs', lambda scope: (copy.deepcopy(rows), ['excluded'], {'split': 'fixed'}, copy.deepcopy(metadata)))
    elif route == 'iterater':
        from runners.stage9 import iterater_cases
        monkeypatch.setattr(iterater_cases, 'pilot_inputs', lambda: (copy.deepcopy(rows), copy.deepcopy(metadata)))
        monkeypatch.setattr(subject, 'file_hash', lambda p: 'a' * 64 if p.name == 'COMPLETE.json' and 'cross-source' in str(p) else common.file_hash(p))
    elif route in ('coauthor', 'scholawrite'):
        from runners.stage9 import coauthor_cases, schola_cases, record_jobs
        job['arguments'] += ['--dataset', route]
        metadata.update(classes=record_jobs.contract(route))
        if route == 'coauthor':
            metadata['writer_component_allocation'] = metadata['allocation']
            monkeypatch.setattr(coauthor_cases, 'inputs', lambda scope: (copy.deepcopy(rows), copy.deepcopy(metadata)))
        else:
            job['arguments'] += ['--fold', '2']; metadata['fold'] = 2
            def inputs(scope, fold):
                return copy.deepcopy(rows), {**copy.deepcopy(metadata), 'fold': fold}
            monkeypatch.setattr(schola_cases, 'inputs', inputs)
    else:
        from runners.stage9 import commit_cases, broll_cases
        monkeypatch.setattr(commit_cases if route == 'commit' else broll_cases,
                            'inputs', lambda scope: (copy.deepcopy(rows), copy.deepcopy(metadata)))
    plan = {'jobs': [job], 'sources': {'files': {}, 'sha256': digest({})}}
    payloads, fields = subject.reconstruct(job, 'pilot')
    identity = {'cell_identity': digest({'manifest_sha256': digest(plan), 'job': job}),
        'operation': subject.ROUTES[job['module']], 'scope': 'pilot', 'source': plan['sources'], **fields}
    directory = tmp_path / 'case'
    for name, value in payloads.items(): write(directory / name, value)
    def seal():
        write(directory / 'IDENTITY.json', identity)
        write(directory / 'COMPLETE.json', {'identity_sha256': digest(identity),
            'cell_identity': identity['cell_identity'], 'execution_complete': True,
            'outputs': closure([directory / 'IDENTITY.json', *[directory / n for n in payloads]])})
    seal()
    return job, plan, tmp_path / 'queue', directory, identity, metadata, seal


@pytest.mark.parametrize('route', ROUTES)
def test_six_prepared_source_routes_reconstruct_without_writes(tmp_path, monkeypatch, route):
    job, plan, queue, directory, *_ = fixture(tmp_path, monkeypatch, route)
    before = closure([tmp_path]); result = subject.inspect_completed(job, plan, queue)
    assert closure([tmp_path]) == before
    assert result['status'] == 'RECONSTRUCTED' and result['lane_records'] == {'train': 1, 'development': 1, 'evaluation': 1}
    assert result['new_fits'] == result['new_reader_calls'] == result['new_reserve_openings'] == 0
    assert not result['scientific_admission']


@pytest.mark.parametrize('fault', ['rows', 'metadata_payload', 'source_metadata', 'identity_extra',
    'allocation', 'output', 'cell', 'source', 'scope', 'missing_output_commit', 'wrong_operation', 'duplicate_scope'])
def test_rehashed_forged_preparation_refuses(tmp_path, monkeypatch, fault):
    job, plan, queue, directory, identity, metadata, seal = fixture(tmp_path, monkeypatch)
    if fault == 'rows': write(directory / 'CASES.json', {'train': [], 'development': [], 'evaluation': []})
    elif fault == 'metadata_payload': write(directory / 'METADATA.json', {'exclusions': []})
    elif fault == 'source_metadata': metadata['exclusions'] = []
    elif fault == 'identity_extra': identity['unrecorded'] = True
    elif fault == 'allocation': metadata['allocation']['train'] = 'evaluation'
    elif fault == 'output': job['produces'] = 'other/COMPLETE.json'
    elif fault == 'cell': identity['cell_identity'] = 'b' * 64
    elif fault == 'source': identity['source'] = {'files': {}, 'sha256': 'b' * 64}
    elif fault == 'scope': job['arguments'][-1] = 'reserve'
    elif fault == 'wrong_operation': job['arguments'][0] = 'fit'
    elif fault == 'duplicate_scope': job['arguments'] += ['--scope', 'pilot']
    seal()
    if fault == 'missing_output_commit':
        done = read(directory / 'COMPLETE.json'); done['outputs']['files'].pop('case/CASES.json')
        done['outputs']['sha256'] = digest(done['outputs']['files']); write(directory / 'COMPLETE.json', done)
    with pytest.raises((ValueError, FileNotFoundError)):
        subject.inspect_completed(job, plan, queue)


def test_changed_actual_fold_refuses_even_with_rehashed_execution_identity(tmp_path, monkeypatch):
    job, plan, queue, directory, identity, metadata, seal = fixture(tmp_path, monkeypatch, 'scholawrite')
    job['arguments'][-1] = '3'
    identity['cell_identity'] = digest({'manifest_sha256': digest(plan), 'job': job}); seal()
    with pytest.raises(ValueError, match='allocation, source or metadata'):
        subject.inspect_completed(job, plan, queue)


def test_missing_original_commit_stops_before_source_reconstruction(tmp_path, monkeypatch):
    job, plan, queue, *_ = fixture(tmp_path, monkeypatch)
    def refused(*args): raise ValueError('original queue commit absent')
    def forbidden(*args): raise AssertionError('uncommitted input must not be reconstructed')
    monkeypatch.setattr(subject, 'verify_committed', refused); monkeypatch.setattr(subject, 'reconstruct', forbidden)
    with pytest.raises(ValueError, match='original queue commit'):
        subject.inspect_completed(job, plan, queue)


def test_failed_unrun_and_nonpreparation_jobs_do_not_read_source_payloads(tmp_path, monkeypatch):
    def forbidden(*args): raise AssertionError('failed/unrun preparation cannot read inputs')
    monkeypatch.setattr(subject, 'inspect_completed', forbidden)
    jobs = {key: {'id': key, 'module': 'runners.stage9.record_jobs', 'arguments': ['prepare']}
            for key in ('failed', 'unrun')}
    jobs['fit'] = {'id': 'fit', 'module': 'runners.stage9.record_jobs', 'arguments': ['fit']}
    state = {'jobs': {key: {'status': status, 'reason': 'original reason', 'disposition_sha256': 'a' * 64}
            for key, status in [('failed', 'FAILED'), ('unrun', 'NOT_RUN')]}}
    write(tmp_path / 'STATUS.json', state)
    assert subject.queue_audits({}, tmp_path, jobs)['jobs'] == state['jobs']
