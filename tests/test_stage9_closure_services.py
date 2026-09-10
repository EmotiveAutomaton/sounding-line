"""Literal provenance fixtures; no model execution or scientific calibration."""
from collections import Counter
import copy
import hashlib
import json

import pytest

from runners.stage9 import closure_services as subject, common, artifact_comparisons, queue
from runners.stage7.runtime import BOOTSTRAP
from runners.stage9.common import digest, file_hash, read, write

PROTOCOL_PATHS = ['runners/stage9/reader.py', 'runners/readout_repair.py',
                  'runners/stage9/features.py', 'runners/stage7/runtime.py']
PROTOCOL_BYTES = {p: (subject.REPO / p).read_bytes() for p in PROTOCOL_PATHS}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    for module in (subject, common, artifact_comparisons):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    for p, body in PROTOCOL_BYTES.items():
        path = tmp_path / p; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
    files = {p: file_hash(tmp_path / p) for p in PROTOCOL_PATHS}
    files.update({p: 'a' * 64 for p in subject.REQUIRED_SOURCES})
    return tmp_path, {'files': files, 'sha256': digest(files)}


def service(setup, name='one'):
    repo, source = setup; root = repo / 'work/services' / name
    scorer = {'files': {p: source['files'][p] for p in subject.REQUIRED_SOURCES}}
    scorer['sha256'] = digest(scorer['files'])
    settings = {'output': str(root), 'precision': 'float32', 'device': 'cpu', 'batch_size': 4,
                'max_context': 4096, 'max_support': 128, 'max_new_tokens': 256}
    identity = {k: v for k, v in settings.items() if k != 'output'}
    identity.update(model='literal-fixture', revision='fixed', adapter_sha256='base-no-adapter',
                    base_files={'fixture': 'b' * 64}, scorer_sources=scorer, scorer_sha256=scorer['sha256'])
    identity['base_files_sha256'] = digest(identity['base_files'])
    write(root / 'config.json', settings)
    write(root / 'READY.json', {'identity': identity, 'pid': 11, 'at': 4.})
    write(root / 'EXECUTION_CONFIG.json', {'sources': source, 'module': 'runners.stage9.model_service',
        'repo': str(repo), 'attempt': str(root / 'execution'), 'arguments': [str(root / 'config.json')], 'cell_identity': 'cell'})
    write(root / 'execution/READY.json', {'cell_identity': 'cell', 'at': 3.,
        'command': 'runners.stage9.model_service', 'process': {'pid': 11, 'created_ticks': 100, 'executable': 'fixture'}})
    write(root / 'execution/EXECUTION.json', {'cell_identity': 'cell', 'returncode': 0,
        'error': None, 'started_at': 2., 'ended_at': 8., 'loaded_project_sources': scorer['files']})
    write(root / 'LIFECYCLE.json', {'worker_pid': 11, 'returncode': 0, 'graceful_shutdown': True,
        'compiled_execution_error': None, 'compiled_execution_sha256': file_hash(root / 'execution/EXECUTION.json'),
        'started_at': 1., 'ended_at': 9.})
    return root, identity


def mutate(root, name, field, value):
    path = root / name; obj = read(path); obj[field] = value; write(path, obj)
    if name == 'execution/EXECUTION.json':
        mutate(root, 'LIFECYCLE.json', 'compiled_execution_sha256', file_hash(path))


def usage(root, requests):
    (root / 'USAGE.jsonl').write_text(''.join(json.dumps({'request_sha256': sha, 'at': 5.}) + '\n'
        for sha, n in requests.items() for _ in range(n)), encoding='utf-8')


def capsule(setup, identity, operation='choice'):
    repo, source = setup; cap = repo / 'work/capsules/call'; cap.mkdir(parents=True)
    evidence = {'prefix': 'visible text', 'options': {'z': 'last', 'a': 'first'} if operation == 'choice' else {}}
    own = {**identity, 'information_sha256': digest(evidence)}
    task = {'operation': operation, 'identity': own, 'max_new_tokens': 9, 'seed': 123}
    copies = {'reader/worker.py': PROTOCOL_BYTES[PROTOCOL_PATHS[0]],
        'reader/readout.py': PROTOCOL_BYTES[PROTOCOL_PATHS[1]], 'reader/features.py': PROTOCOL_BYTES[PROTOCOL_PATHS[2]],
        'reader/__init__.py': b'', 'bootstrap.py': BOOTSTRAP.encode('utf-8')}
    for name, body in copies.items():
        path = cap / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
    files = {p: file_hash(cap / p) for p in copies}
    write(cap / 'task.json', task); write(cap / 'evidence.json', evidence)
    write(cap.parent / 'closures/call.json', {'files': files, 'sha256': digest(files),
        'task_sha256': digest(task), 'evidence_sha256': digest(evidence)})
    write(cap / 'out/prediction.json', {'valid': True, 'identity': own})
    write(cap / 'out/receipt.json', {'loaded_sources': {('reader' if p == 'reader/__init__.py' else p[:-3].replace('/', '.')):
        sha for p, sha in files.items() if p.startswith('reader/')}})
    write(cap / 'out/access.json', {'cwd': str(cap), 'counts': {'allowed': 1, 'denied': 0}})
    own = read(cap / 'task.json')['identity']  # The real reader receives canonically saved JSON.
    payload = ({'operation': 'score', 'prefix': 'visible text', 'options': {'a': 'first', 'z': 'last'}, 'identity': own}
        if operation == 'choice' else {'operation': 'generate', 'prefix': 'visible text', 'identity': own, 'max_new_tokens': 9, 'seed': 123})
    return cap, hashlib.sha256(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def test_original_compiled_service_preserves_source_subset_and_errors(setup):
    root, identity = service(setup); source = copy.deepcopy(setup[1]); source['files']['outer.py'] = 'c' * 64
    source['sha256'] = digest(source['files'])
    (root / 'ERRORS.jsonl').write_text(json.dumps({'valid': False, 'error': 'deliberate invalid input', 'at': 5.}) + '\n')
    record, actual = subject.inspect_service(root, source, 'cell')
    assert actual == identity and record['status'] == 'RECORDED_EXECUTION_VERIFIED'
    assert record['retained_errors'] == 1 and not record['scientific_admission']


@pytest.mark.parametrize('name,field,value', [
    ('EXECUTION_CONFIG.json', 'cell_identity', 'another'),
    ('EXECUTION_CONFIG.json', 'arguments', ['another']),
    ('execution/READY.json', 'cell_identity', 'another'),
    ('execution/EXECUTION.json', 'loaded_project_sources', {}),
    ('execution/EXECUTION.json', 'returncode', 1),
    ('execution/EXECUTION.json', 'cell_identity', 'another'),
    ('execution/EXECUTION.json', 'ended_at', 0.),
    ('LIFECYCLE.json', 'compiled_execution_sha256', 'wrong'),
    ('LIFECYCLE.json', 'graceful_shutdown', False),
    ('LIFECYCLE.json', 'worker_pid', 12),
    ('LIFECYCLE.json', 'started_at', 99.),
    ('config.json', 'batch_size', 1),
])
def test_original_service_refuses_substitution(setup, name, field, value):
    root, _ = service(setup); mutate(root, name, field, value)
    with pytest.raises(ValueError):
        subject.inspect_service(root, setup[1], 'cell')


def test_original_source_swap_is_refused(setup):
    root, _ = service(setup); source = copy.deepcopy(setup[1]); source['files']['runners/stage9/neural.py'] = 'changed'
    with pytest.raises(ValueError):
        subject.inspect_service(root, source, 'cell')


def test_reviewed_legacy_timeout_variant_keeps_its_original_reader_hash(setup):
    source = copy.deepcopy(setup[1])
    legacy = '5ffa1ed5115281b5b3652b1b64450810ddb99f9ba44b6ae677d9d493cbff286f'
    source['files']['runners/stage9/reader.py'] = legacy
    assert subject.protocol_sources(source)['reader/worker.py'] == legacy
    source['files']['runners/stage9/reader.py'] = '0' * 64
    with pytest.raises(ValueError):
        subject.protocol_sources(source)


def test_legacy_missing_compilation_is_retained_and_cannot_gain_verification(setup):
    root, _ = service(setup); (root / 'execution/EXECUTION.json').unlink()
    record, _ = subject.inspect_service(root, setup[1], 'cell')
    assert record['status'] == 'INCOMPLETE_SERVICE_RETAINED'
    assert 'execution/EXECUTION.json' in record['missing_execution_files']
    assert not subject.inspect(setup[0] / 'work', common.closure([setup[0] / 'work']), setup[1], 'cell')['all_recorded_services_reconciled']


@pytest.mark.parametrize('fault', ['omitted', 'changed', 'uncommitted'])
def test_service_inventory_refuses_missing_or_extra_bytes(setup, fault):
    root, _ = service(setup); outputs = common.closure([root])
    if fault == 'omitted':
        outputs['files'].pop((root / 'READY.json').relative_to(setup[0]).as_posix())
    elif fault == 'changed':
        mutate(root, 'READY.json', 'pid', 90)
    else:
        write(root / 'extra.json', {})
    with pytest.raises(ValueError):
        subject.inventory(setup[0] / 'work', outputs)


@pytest.mark.parametrize('operation', ['choice', 'generate'])
def test_saved_request_matches_exact_wire_and_is_not_canonical_digest(setup, operation):
    root, identity = service(setup); cap, sha = capsule(setup, identity, operation); usage(root, {sha: 1})
    before = common.closure([setup[0] / 'work'])
    result = subject.inspect(setup[0] / 'work', before, setup[1], 'cell')
    assert result['matched_saved_requests'] == 1 and result['all_recorded_services_reconciled']
    assert result['new_model_calls'] == 0 and common.closure([setup[0] / 'work']) == before


def test_restarts_share_identity_without_inventing_per_process_attribution(setup):
    root, identity = service(setup); second, _ = service(setup, 'two'); cap, sha = capsule(setup, identity)
    usage(second, {sha: 1})
    result = subject.inspect(setup[0] / 'work', common.closure([setup[0] / 'work']), setup[1], 'cell')
    assert result['service_count'] == 2 and result['matched_saved_requests'] == 1
    assert result['all_recorded_services_reconciled']


def test_missing_accepted_request_refuses_a_successful_saved_capsule(setup):
    root, identity = service(setup); capsule(setup, identity)
    with pytest.raises(ValueError, match='accepted service request'):
        subject.inspect(setup[0] / 'work', common.closure([setup[0] / 'work']), setup[1], 'cell')


def test_incomplete_capsule_and_excess_usage_remain_unresolved(setup):
    root, identity = service(setup); cap, sha = capsule(setup, identity); usage(root, {sha: 2})
    (cap / 'out/prediction.json').unlink()
    result = subject.inspect(setup[0] / 'work', common.closure([setup[0] / 'work']), setup[1], 'cell')
    assert len(result['incomplete_model_capsules']) == 1 and not result['all_recorded_services_reconciled']
    assert result['unmatched_accepted_requests'][digest(identity)] == {sha: 2}


@pytest.mark.parametrize('fault', ['malformed_usage', 'promoted_error', 'request_time', 'source_protocol', 'identity'])
def test_request_and_protocol_substitutions_refuse(setup, fault):
    root, identity = service(setup); cap, sha = capsule(setup, identity); usage(root, {sha: 1})
    source = copy.deepcopy(setup[1])
    if fault == 'malformed_usage': usage(root, {'invalid': 1})
    elif fault == 'promoted_error': (root / 'ERRORS.jsonl').write_text(json.dumps({'valid': True, 'error': 'ignored', 'at': 5.}))
    elif fault == 'request_time': (root / 'USAGE.jsonl').write_text(json.dumps({'request_sha256': sha, 'at': 100.}))
    elif fault == 'source_protocol': source['files']['runners/stage9/reader.py'] = 'changed'
    else: mutate(cap, 'out/prediction.json', 'identity', {})
    with pytest.raises(ValueError):
        subject.inspect(setup[0] / 'work', common.closure([setup[0] / 'work']), source, 'cell')


def test_failed_jobs_are_not_promoted_by_completion_files(setup, monkeypatch):
    root, _ = service(setup); work = setup[0] / 'work'; write(work / 'COMPLETE.json', {'outputs': common.closure([root])})
    write(setup[0] / 'queue/STATUS.json', {'jobs': {'job': {'status': 'FAILED'}}})
    monkeypatch.setattr(queue, 'verify_committed', lambda *args: pytest.fail('failed job has no completion commit'))
    assert subject.queue_audits({'sources': setup[1]}, setup[0] / 'queue', {'job': {'produces': 'work/COMPLETE.json'}})['jobs'] == {}


@pytest.mark.parametrize('references', [None, {}, [{'manifest': 'missing'}]])
def test_historical_references_require_explicit_schema(references):
    with pytest.raises(ValueError): subject.archive_audits(references)
