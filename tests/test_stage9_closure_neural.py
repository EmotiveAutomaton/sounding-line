"""Constructed worlds and synthetic saved calls; no scientific fits or reserves."""
import copy
from pathlib import Path

import pytest

from runners.stage9 import closure_neural as subject
from runners.stage9 import common, artifact_comparisons
from runners.stage9.common import closure, digest, file_hash, read, write
from runners.stage9.prospective_choice import choice_input
from runners.stage9.series_cases import COHORTS, construct_attempt


@pytest.fixture(scope='module')
def cases():
    rows = []
    for i in range(20):
        case = construct_attempt(key='closure-neural-fixture-' + str(i), cohort=COHORTS[0], role='reserve', dose=0)
        if case['realized']:
            rows.append(case)
        if len(rows) == 2:
            break
    assert len(rows) == 2
    artifact_comparisons.validate_cases(rows, 'reserve')
    return rows


def fixture(tmp_path, monkeypatch, cases, failed=False):
    # Actual source reconstruction and capsule audit run; fitting provenance is a
    # separately tested contract, replaced here by explicit synthetic packages.
    for module in (subject, common, artifact_comparisons):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    monkeypatch.setattr(subject, 'inside', lambda p: Path(p).resolve())
    monkeypatch.setattr(subject, 'pointer_path', lambda p: tmp_path / p['path'])
    monkeypatch.setattr(subject, 'checked', lambda p: read(tmp_path / p['path']))
    monkeypatch.setattr(subject, 'validate_contract', lambda c, p: c['reserve'])
    directory = tmp_path / 'private/scientific-confirmations' / digest('fixture-claim')[:16]
    work = directory / 'work'; reserve = {}; readers = {}
    for case in cases:
        path = tmp_path / 'constructed' / (case['unit'] + '.json'); write(path, case)
        reserve[case['unit']] = {'input': {'path': path.relative_to(tmp_path).as_posix(), 'sha256': file_hash(path)},
                                 'content_sha256': digest(case['sources'])}
    for seed in subject.SEEDS:
        path = tmp_path / 'fixture-packages' / (str(seed) + '.json')
        write(path, {'synthetic_package': True, 'adapter_sha256': digest(seed)})
        readers[str(seed)] = {'package': {'path': path.relative_to(tmp_path).as_posix(), 'sha256': file_hash(path)}}
    contract = {'adapter': 'neural-choice-v1', 'reserve': reserve, 'readers': readers,
                'contrast': {'left': 'artifact_choice', 'right': 'process_choice'}}
    packet = {'id': 'fixture-claim', 'reserve_units': [c['unit'] for c in cases]}
    frozen = {'packet': packet, 'contract': contract, 'scope': 'scientific',
              'freeze_complete_sha256': digest('fixture-freeze'), 'claims_sha256': digest('fixture-claims')}
    source = {'files': {}, 'sha256': digest({})}; cell = digest('fixture-cell')
    access = {'operation': 'frozen-reserve-access-v1', 'frozen': frozen, 'selected': reserve}
    write(directory / 'IDENTITY.json', access)
    write(directory / 'OPENED.json', {'identity_sha256': digest(access), 'scope': 'scientific', 'scientific_confirmation': False})
    identity = {'cell_identity': cell, 'operation': 'frozen-neural-choice-confirmation-v1',
        'scope': 'scientific', 'role': 'reserve', 'source': source, 'claim_id': packet['id'],
        'freeze_complete_sha256': frozen['freeze_complete_sha256'], 'claims_sha256': frozen['claims_sha256'],
        'execution_contract_sha256': digest(contract), 'selected_units': packet['reserve_units'],
        'seeds': list(subject.SEEDS), 'access_identity_sha256': digest(access),
        'access_opened_sha256': file_hash(directory / 'OPENED.json')}
    write(work / 'IDENTITY.json', identity)
    rows = []
    for seed in subject.SEEDS:
        for case in cases:
            def save(evidence, side):
                package = read(tmp_path / readers[str(seed)]['package']['path'])
                task = subject.request_task(evidence, {'operation': 'choice'}, package)
                cap = work / 'capsules' / (digest([seed, case['unit'], side])[:16])
                write(cap / 'evidence.json', evidence); write(cap / 'task.json', task)
                accepted = not (failed and seed == 9003 and side == 'right')
                prediction = {'valid': accepted, 'probs': {k: 1 / len(evidence['options']) for k in evidence['options']}}
                receipt = {'loaded_sources': {}}
                write(cap / 'out/prediction.json', prediction); write(cap / 'out/receipt.json', receipt)
                result = {'accepted': accepted, 'rc': 0 if accepted else 1, 'capsule': str(cap),
                    'prediction': prediction, 'receipt': receipt, 'copied_sources': {'files': {}, 'sha256': digest({}),
                        'task_sha256': digest(task), 'evidence_sha256': digest(evidence)}}
                write(work / 'calls' / str(seed) / digest(case['unit'])[:16] / (side + '.json'),
                      {'input_sha256': digest({'evidence': evidence, 'task': task}), 'result': result})
                return result
            row = subject.forecast(case, seed, contract['contrast'], save); rows.append(row)
            key = [case['unit'], seed]
            write(work / 'units' / (digest(key) + '.json'), {'identity': digest(identity), 'key': key, 'complete': True, 'row': row})
    write(work / 'PREDICTIONS.json', rows)
    outcome = subject.calculation_input(rows, packet['reserve_units']); write(work / 'OUTCOME.json', outcome)
    done = {'execution_complete': True, 'identity_sha256': digest(identity), 'cell_identity': cell,
        'scientific_confirmation': False, 'assigned_units': len(cases), 'completed_units': len(cases),
        'training_seeds': list(subject.SEEDS), 'role': 'reserve', 'calculation_status': outcome['calculation_status']}
    def seal():
        done['outputs'] = closure([work / name for name in ('IDENTITY.json', 'units', 'calls', 'capsules', 'PREDICTIONS.json', 'OUTCOME.json')])
        write(work / 'COMPLETE.json', done)
    seal()
    return directory, frozen, cell, source, seal, done


@pytest.mark.parametrize('failed', [False, True])
def test_complete_real_source_grid_reconstructs_read_only(tmp_path, monkeypatch, cases, failed):
    directory, frozen, cell, source, seal, done = fixture(tmp_path, monkeypatch, cases, failed)
    before = closure([tmp_path])
    result = subject.inspect_completed(directory, frozen, cell, source)
    assert closure([tmp_path]) == before
    assert (result['units'], result['seed_units'], result['calls']) == (2, 6, 12)
    assert result['new_reader_calls'] == result['new_reserve_openings'] == 0
    assert not result['scientific_admission']
    outcome = read(directory / 'work/OUTCOME.json')
    assert outcome['calculation_status'] == ('NOT_RUN' if failed else 'READY')
    assert outcome['excluded_seeds'] == 0
    if not failed:
        assert all(row['difference'] == 0 for row in outcome['paired_rows'])


@pytest.mark.parametrize('fault', ['unopened', 'uncommitted_access', 'payload', 'wrong_source', 'seed_package',
    'signature', 'capsule_evidence', 'capsule_task', 'nonboolean', 'unit_seed', 'missing_seed',
    'extra_unit', 'extra_call', 'prediction', 'calculation', 'counts', 'seeds'])
def test_rehashed_semantic_substitution_refuses(tmp_path, monkeypatch, cases, fault):
    directory, frozen, cell, source, seal, done = fixture(tmp_path, monkeypatch, cases)
    work = directory / 'work'; path = next((work / 'calls/9001').rglob('left.json'))
    cached = read(path); cap = Path(cached['result']['capsule'])
    if fault == 'unopened': (directory / 'OPENED.json').unlink()
    elif fault == 'uncommitted_access': write(directory / 'OPENED.json', {'scope': 'scientific'})
    elif fault == 'payload': write(tmp_path / frozen['contract']['reserve'][cases[0]['unit']]['input']['path'], {})
    elif fault == 'wrong_source': source['files']['substituted.py'] = digest('other')
    elif fault == 'seed_package': write(tmp_path / frozen['contract']['readers']['9001']['package']['path'], {'changed_seed': True})
    elif fault == 'signature': cached['input_sha256'] = digest('wrong'); write(path, cached)
    elif fault in ('capsule_evidence', 'capsule_task'):
        name = 'evidence' if fault == 'capsule_evidence' else 'task'; write(cap / (name + '.json'), {'private': True})
    elif fault == 'nonboolean': cached['result']['accepted'] = 1; write(path, cached)
    elif fault == 'unit_seed':
        unit = next((work / 'units').glob('*.json')); value = read(unit); value['row']['seed'] = 42; write(unit, value)
    elif fault == 'missing_seed':
        (work / 'units' / (digest([cases[0]['unit'], 9003]) + '.json')).unlink()
    elif fault == 'extra_unit': write(work / 'units/extra.json', {})
    elif fault == 'extra_call': write(work / 'calls/extra.json', cached)
    elif fault == 'prediction': write(work / 'PREDICTIONS.json', [])
    elif fault == 'calculation': write(work / 'OUTCOME.json', {'calculation_status': 'READY'})
    elif fault == 'counts': done['completed_units'] = 6
    elif fault == 'seeds': done['training_seeds'] = [9001]
    seal()  # Rehash every changed output; semantic guards must still fire.
    with pytest.raises((ValueError, FileNotFoundError)):
        subject.inspect_completed(directory, frozen, cell, source)


def test_failed_and_unrun_jobs_keep_dispositions_without_opening(tmp_path, monkeypatch):
    def forbidden(*args): raise AssertionError('no reserve access for an uncompleted job')
    monkeypatch.setattr(subject, 'frozen_claim', forbidden)
    prior = {k: {'module': 'runners.stage9.confirmation_neural'} for k in ('failed', 'unrun')}
    statuses = {k: {'status': s, 'reason': 'original reason', 'disposition_sha256': digest(s)}
                for k, s in [('failed', 'FAILED'), ('unrun', 'NOT_RUN')]}
    write(tmp_path / 'STATUS.json', {'jobs': statuses})
    assert subject.queue_audits({}, tmp_path, prior)['jobs'] == statuses


def test_queue_routes_original_frozen_producer_to_semantic_inspection(tmp_path, monkeypatch, cases):
    directory, frozen, cell, source, seal, done = fixture(tmp_path, monkeypatch, cases)
    job = {'id': 'confirm', 'module': 'runners.stage9.confirmation_neural',
        'produces': str(directory / 'work/COMPLETE.json'), 'arguments': ['--output', str(directory),
        '--freeze', str(tmp_path / 'freeze'), '--manifest', str(tmp_path / 'manifest'),
        '--claim', 'fixture-claim', '--scope', 'scientific']}
    plan = {'sources': source}; write(tmp_path / 'STATUS.json', {'jobs': {'confirm': {'status': 'COMPLETE'}}})
    monkeypatch.setattr(subject, 'frozen_claim', lambda *args: frozen)
    observed = []
    monkeypatch.setattr(subject, 'inspect_completed', lambda *args: observed.append(args) or {'status': 'RECONSTRUCTED'})
    assert subject.queue_audits(plan, tmp_path, {'confirm': job})['jobs']['confirm']['status'] == 'RECONSTRUCTED'
    assert observed == [(directory, frozen, digest({'manifest_sha256': digest(plan), 'job': job}), source)]
    job['produces'] = str(directory / 'other/COMPLETE.json')
    with pytest.raises(ValueError, match='producer'):
        subject.queue_audits(plan, tmp_path, {'confirm': job})
