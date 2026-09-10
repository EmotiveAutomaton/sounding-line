"""Semantic guards on explicit toy inputs; actual fitting/source replay is a queue pilot."""
import copy
from pathlib import Path

import pytest

from runners.stage9 import closure_baselines as subject
from runners.stage9 import confirmation_baselines
from runners.stage9.common import closure, digest, file_hash, read, write


def fixture(tmp_path, monkeypatch, accepted=True):
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    monkeypatch.setattr('runners.stage9.artifact_comparisons.REPO', tmp_path)
    monkeypatch.setattr(subject, 'inside', lambda p: Path(p).resolve())
    monkeypatch.setattr(subject, 'pointer_path', lambda p: Path(p['path']))
    directory = tmp_path / 'private/confirmation-execution-pilots/fixture'; work = directory / 'work'
    case = {'unit': 'u', 'sources': ['source'], 'role': 'pilot', 'target': 'a'}
    payload = directory / 'source.json'; write(payload, case)
    contrast = {'left': {'view': 'artifact', 'dose': 7, 'model': 'fit|cheap-8.0'},
                'right': {'view': 'artifact', 'dose': 0, 'model': 'fit|population'}}
    contract = {'reader': {'path': str(directory / 'fit/COMPLETE.json'), 'sha256': 'b' * 64},
        'contrast': contrast, 'reserve': {'u': {'input': {'path': str(payload), 'sha256': file_hash(payload)},
                                             'content_sha256': digest(case['sources'])}}}
    packet = {'id': 'claim', 'reserve_units': ['u']}
    frozen = {'packet': packet, 'contract': contract, 'scope': 'pilot',
              'freeze_complete_sha256': 'c' * 64, 'claims_sha256': 'd' * 64}
    source = {'files': {}, 'sha256': digest({})}; cell = 'e' * 64
    monkeypatch.setattr(subject, 'validate_contract', lambda c, p: c['reserve'])
    validations = []
    monkeypatch.setattr(subject, 'validate_cases', lambda cases, role: validations.append((copy.deepcopy(cases), role)))
    models = {'models': {'artifact': {'fit': {'coefficient': 2.}}}, 'types': {'artifact': {'a': 1.}},
              'completion_sha256': contract['reader']['sha256']}
    monkeypatch.setattr(subject, 'model_inputs', lambda *args: models)
    monkeypatch.setattr(confirmation_baselines, 'dose_view', lambda case, dose, view: {'support': ['a', 'b'], 'dose': dose, 'view': view})
    access = {'operation': 'frozen-reserve-access-v1', 'frozen': frozen, 'selected': contract['reserve']}
    write(directory / 'IDENTITY.json', access)
    write(directory / 'OPENED.json', {'identity_sha256': digest(access), 'scope': 'pilot', 'scientific_confirmation': False})
    identity = {'cell_identity': cell, 'operation': 'frozen-baseline-confirmation-v1',
        'scope': 'pilot', 'role': 'pilot', 'source': source, 'claim_id': 'claim',
        'freeze_complete_sha256': frozen['freeze_complete_sha256'], 'claims_sha256': frozen['claims_sha256'],
        'execution_contract_sha256': digest(contract), 'selected_units': ['u'],
        'access_identity_sha256': digest(access), 'access_opened_sha256': file_hash(directory / 'OPENED.json')}
    write(work / 'IDENTITY.json', identity)
    cap = work / 'capsules/one'
    def saved_call(bundle, view):
        task = {'operation': 'baseline_matrix', 'budget': 10000, 'information_sha256': digest(bundle), 'strengths': [8., 16., 32.]}
        write(cap / 'evidence.json', bundle); write(cap / 'task.json', task)
        prediction = {'valid': True, 'predictions': {
            side: {contrast[side]['model']: {'a': .6 if side == 'left' else .4, 'b': .4 if side == 'left' else .6}}
            for side in contrast}}
        receipt = {'loaded_sources': {}}
        write(cap / 'out/prediction.json', prediction); write(cap / 'out/receipt.json', receipt)
        result = {'accepted': accepted, 'rc': 0 if accepted else 1, 'wall_s': 0., 'capsule': str(cap),
            'prediction': prediction, 'receipt': receipt, 'copied_sources': {'files': {}, 'sha256': digest({}),
                'task_sha256': digest(task), 'evidence_sha256': digest(bundle)}}
        write(work / 'calls/u/artifact.json', {'input_sha256': digest(bundle), 'result': result})
        return result
    row = subject.forecast(case, models, contrast, saved_call)
    write(work / 'units' / (digest('u') + '.json'), {'identity': digest(identity), 'key': 'u', 'complete': True, 'row': row})
    write(work / 'PREDICTIONS.json', [row])
    outcome = subject.calculation_input([row], ['u']); write(work / 'OUTCOME.json', outcome)
    completed = {'execution_complete': True, 'cell_identity': cell, 'identity_sha256': digest(identity),
        'scientific_confirmation': False, 'assigned_units': 1, 'completed_units': 1, 'role': 'pilot',
        'calculation_status': outcome['calculation_status']}
    def seal():
        completed['outputs'] = closure([work / p for p in ('PREDICTIONS.json', 'OUTCOME.json', 'units', 'calls', 'capsules')])
        write(work / 'COMPLETE.json', completed)
    seal()
    return directory, frozen, cell, source, models, validations, seal


@pytest.mark.parametrize('accepted', [True, False])
def test_complete_semantic_reconstruction_is_read_only_and_retains_failed_calls(tmp_path, monkeypatch, accepted):
    directory, frozen, cell, source, models, validations, seal = fixture(tmp_path, monkeypatch, accepted)
    before = closure([directory])
    result = subject.inspect_completed(directory, frozen, cell, source)
    assert closure([directory]) == before and validations[0][1] == 'pilot'
    assert result['units'] == result['calls'] == 1 and result['status'] == 'RECONSTRUCTED'
    assert result['new_reserve_openings'] == result['new_reader_calls'] == 0 and not result['scientific_admission']
    assert read(directory / 'work/OUTCOME.json')['calculation_status'] == ('READY' if accepted else 'NOT_RUN')


@pytest.mark.parametrize('fault', ['unopened', 'payload', 'fit', 'signature', 'capsule_evidence',
    'capsule_task', 'unit', 'extra_unit', 'missing_call', 'prediction', 'counts'])
def test_hash_consistent_but_semantically_wrong_execution_refuses(tmp_path, monkeypatch, fault):
    directory, frozen, cell, source, models, validations, seal = fixture(tmp_path, monkeypatch)
    work = directory / 'work'; cap = work / 'capsules/one'
    if fault == 'unopened': (directory / 'OPENED.json').unlink()
    elif fault == 'payload': write(directory / 'source.json', {'unit': 'different'})
    elif fault == 'fit': models['completion_sha256'] = 'z' * 64
    elif fault == 'signature':
        path = work / 'calls/u/artifact.json'; value = read(path); value['input_sha256'] = 'z' * 64; write(path, value)
    elif fault in ('capsule_evidence', 'capsule_task'):
        name = 'evidence' if fault == 'capsule_evidence' else 'task'
        path = cap / (name + '.json'); value = read(path); value['extra_hidden_input'] = True; write(path, value)
    elif fault == 'unit':
        path = work / 'units' / (digest('u') + '.json'); value = read(path); value['row']['truth'] = 'b'; write(path, value)
    elif fault == 'extra_unit': write(work / 'units/extra.json', {'complete': True})
    elif fault == 'missing_call': (work / 'calls/u/artifact.json').unlink()
    elif fault == 'prediction': write(work / 'PREDICTIONS.json', [])
    else:
        seal(); path = work / 'COMPLETE.json'; value = read(path); value['assigned_units'] = 2; write(path, value)
    if fault != 'counts': seal()  # Rehash outputs: semantics, not a stale output hash, must reject.
    with pytest.raises((ValueError, FileNotFoundError)):
        subject.inspect_completed(directory, frozen, cell, source)
    if fault == 'unopened': assert validations == [] and not (directory / 'OPENED.json').exists()


def test_failed_and_unrun_jobs_do_not_open_reserved_inputs(tmp_path, monkeypatch):
    def forbidden(*args): raise AssertionError('reserve must not be opened')
    monkeypatch.setattr(subject, 'frozen_claim', forbidden)
    prior = {key: {'id': key, 'module': 'runners.stage9.confirmation_baselines'} for key in ('failed', 'unrun')}
    statuses = {key: {'status': state, 'reason': 'original reason', 'disposition_sha256': 'f' * 64}
                for key, state in [('failed', 'FAILED'), ('unrun', 'NOT_RUN')]}
    write(tmp_path / 'STATUS.json', {'jobs': statuses})
    result = subject.queue_audits({}, tmp_path, prior)
    assert result['jobs'] == statuses and not result['scientific_admission']
