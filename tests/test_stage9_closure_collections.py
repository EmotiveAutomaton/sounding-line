"""Collection storage/queue mutations must fail without rerunning a reader."""
from copy import deepcopy
from pathlib import Path

import pytest

from runners.stage9 import closure_collections as subject, common
from runners.stage9.common import closure, digest, read, write


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr(common, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'inside', lambda path, root=None: Path(path).resolve())
    monkeypatch.setattr(subject, 'denial_probe', lambda *a: {})
    inspected = []
    def inspect(result, *args):
        inspected.append(result)
        return {'status': 'FAILED_RETAINED', 'accepted': False}
    monkeypatch.setattr(subject, 'inspect_call', inspect)
    root = tmp_path / 'collection'
    (root / 'services').mkdir(parents=True)
    identity = {'assigned_keys': ['a', 'b']}
    for key in identity['assigned_keys']:
        cap = root / 'capsules' / key
        write(cap / 'evidence.json', {'prefix': key, 'options': {}})
        (cap / 'bootstrap.py').write_text('literal test fixture', encoding='utf-8')
        copied = {'fixture': key}
        write(cap.parent / 'closures' / (key + '.json'), copied)
        result = {'capsule': str(cap), 'copied_sources': copied, 'accepted': False}
        record = {'key': key, 'identity': digest(identity), 'complete': True,
            'row': {'attempts': [{'turn': 0, 'evidence_sha256': digest(read(cap / 'evidence.json')), 'result': result}]}}
        write(root / 'units' / (digest(key) + '.json'), record)
    def done():
        return {'outputs': closure([root / name for name in ('units', 'capsules', 'services')])}
    return root, identity, done, inspected


def test_raw_failed_calls_are_retained_and_incomplete_orphans_not_promoted(storage):
    root, identity, done, inspected = storage
    write(root / 'capsules' / 'interrupted' / 'task.json', {'incomplete': True})
    units, result = subject.raw_storage(root, done(), identity, {'fixture': 'sources'}, {})
    assert set(units) == {'a', 'b'} and len(inspected) == result['call_count'] == 2
    assert all(c['inspection']['status'] == 'FAILED_RETAINED' for c in result['calls'])
    assert result['unbound_capsules'] == ['collection/capsules/interrupted']
    assert not result['scientific_admission']


@pytest.mark.parametrize('fault', ['identity', 'assignment', 'capsule_reuse', 'sidecar', 'evidence', 'extra_uncommitted', 'unknown_unit'])
def test_refreshed_hashes_do_not_hide_raw_storage_substitution(storage, fault):
    root, identity, done, _ = storage
    before = done(); path = root / 'units' / (digest('b') + '.json'); record = read(path)
    if fault == 'identity':
        record['identity'] = 'different'
    elif fault == 'assignment':
        identity = {'assigned_keys': ['a', 'b', 'missing']}
        # Preserve per-file identity validity so the whole assignment gate is tested.
        for p in (root / 'units').glob('*.json'):
            row = read(p); row['identity'] = digest(identity); write(p, row)
        record['identity'] = digest(identity)
    elif fault == 'capsule_reuse':
        record['row']['attempts'][0] = deepcopy(read(root / 'units' / (digest('a') + '.json'))['row']['attempts'][0])
    elif fault == 'sidecar':
        write(root / 'capsules/closures/b.json', {'fixture': 'substituted'})
    elif fault == 'evidence':
        record['row']['attempts'][0]['evidence_sha256'] = 'different'
    elif fault == 'extra_uncommitted':
        write(root / 'capsules' / 'extra.json', {'new': True})
    else:
        (root / 'units' / 'unrecognized.txt').write_text('not a unit', encoding='utf-8')
    write(path, record)
    with pytest.raises(ValueError):
        subject.raw_storage(root, before if fault == 'extra_uncommitted' else done(), identity, {'fixture': 'sources'}, {})


def plan():
    probe = {'id': 'probe', 'module': 'runners.stage9.closure_probe', 'arguments': ['--runtime', 'reader'], 'produces': 'probe/COMPLETE.json'}
    collect = {'id': 'collect', 'module': 'runners.stage9.training_jobs', 'arguments': ['collect', '--family', 'qwen', '--coverage', 'original'],
        'after': ['probe'], 'requires': [{'job': 'probe', 'field': ['isolation_probe_verified'], 'equals': True}], 'produces': 'dispatch/COMPLETE.json'}
    return {'jobs': [probe, collect], 'sources': {'files': {}, 'sha256': digest({})},
        'collection_reviews': {'collect': {'root': 'private/scientific-collection/qwen/original', 'probe_job': 'probe'}}}


@pytest.mark.parametrize('reviews', [None, {}, {'unexpected': {'root': 'x', 'probe_job': 'probe'}}])
def test_every_collector_needs_its_own_explicit_review(reviews):
    p = plan(); p['collection_reviews'] = reviews
    with pytest.raises(ValueError, match='explicit final review'):
        subject.queue_audits(p, Path('unused'), {j['id']: j for j in p['jobs']})


def test_no_collectors_need_no_payload_or_status_read(monkeypatch):
    monkeypatch.setattr(subject, 'read_status', lambda *a: pytest.fail('unexpected status read'))
    assert subject.queue_audits({}, Path('unused'), {}) == {'jobs': {}, 'scientific_admission': False}


@pytest.mark.parametrize('status', ['FAILED', 'NOT_RUN'])
def test_failed_and_unrun_collectors_retain_disposition_without_payload_read(monkeypatch, status):
    p = plan(); row = {'status': status, 'reason': 'original failure', 'disposition_sha256': 'saved'}
    monkeypatch.setattr(subject, 'read_status', lambda *a: {'jobs': {'collect': row}})
    monkeypatch.setattr(subject, 'read', lambda *a: pytest.fail('unrun payload opened'))
    result = subject.queue_audits(p, Path('unused'), {j['id']: j for j in p['jobs']})
    assert result['jobs']['collect'] == row


@pytest.fixture
def queued(tmp_path, monkeypatch):
    p = plan(); root = tmp_path / 'private/scientific-collection/qwen/original'
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'inside', lambda path, root=None: (tmp_path / path).resolve())
    monkeypatch.setattr(subject, 'training_root', lambda *a: tmp_path / 'training')
    states = {j['id']: {'status': 'COMPLETE'} for j in p['jobs']}
    monkeypatch.setattr(subject, 'read_status', lambda *a: {'jobs': states})
    committed = []
    monkeypatch.setattr(subject, 'verify_committed', lambda q, j, *a: committed.append(j['id']))
    monkeypatch.setattr(subject, 'bindings', lambda *a: {'runtime': 'reader'})
    write(tmp_path / 'probe/COMPLETE.json', {'isolation_probe_verified': True})
    write(tmp_path / 'probe/BINDING.json', {'runtime': 'reader'})
    write(tmp_path / 'probe/PROBE.json', {'saved': 'probe'})
    calls = []
    def inspect(*args, **kwargs):
        calls.append((args, kwargs))
        return {'status': 'INSPECTED', 'scientific_admission': False}
    monkeypatch.setattr(subject, 'inspect_completed', inspect)
    return p, tmp_path, states, committed, calls


def test_queue_binds_original_dispatch_and_probe_to_external_collection(queued):
    p, root, states, committed, calls = queued
    result = subject.queue_audits(p, root / 'queue', {j['id']: j for j in p['jobs']})
    assert committed == ['collect', 'probe'] and len(calls) == 1
    args, kwargs = calls[0]
    assert args[0] == root / 'private/scientific-collection/qwen/original'
    assert args[1] == root / 'dispatch/COMPLETE.json'
    assert args[3] == digest({'manifest_sha256': digest(p), 'job': p['jobs'][1]})
    assert kwargs['family'] == 'qwen' and kwargs['coverage'] == 'original' and not kwargs['rehearsal']
    assert result['jobs']['collect']['status'] == 'INSPECTED'


@pytest.mark.parametrize('fault', ['root', 'dependency', 'gate', 'runtime', 'failed_probe', 'false_probe', 'binding'])
def test_queue_refuses_wrong_root_and_unprobed_collector_before_inspection(queued, fault):
    p, root, states, committed, calls = queued
    if fault == 'root': p['collection_reviews']['collect']['root'] = 'wrong'
    elif fault == 'dependency': p['jobs'][1]['after'] = []
    elif fault == 'gate': p['jobs'][1]['requires'] = []
    elif fault == 'runtime': p['jobs'][0]['arguments'] = ['--runtime', 'comparison']
    elif fault == 'failed_probe': states['probe']['status'] = 'FAILED'
    elif fault == 'false_probe': write(root / 'probe/COMPLETE.json', {'isolation_probe_verified': False})
    elif fault == 'binding': write(root / 'probe/BINDING.json', {'runtime': 'substituted'})
    with pytest.raises(ValueError):
        subject.queue_audits(p, root / 'queue', {j['id']: j for j in p['jobs']})
    assert not calls
