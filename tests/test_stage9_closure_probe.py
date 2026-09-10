import copy
import importlib

import pytest

from runners.stage9 import closure_capsules as subject
from runners.stage9 import closure_probe
from runners.stage9.common import file_hash, write
from runners.stage9.revision_predictions import sources
from runners.stage9.launch import handler_operation


def fixture(tmp_path, monkeypatch):
    from tests.test_stage9_closure_storage import make_call, outputs
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr('runners.stage9.queue.verify_committed', lambda *args: None)
    call, cap, saved = make_call(tmp_path / 'work')
    copied = saved['copied_sources']['files']
    monkeypatch.setattr(closure_probe, 'bindings', lambda runtime, source: {'runtime': runtime, 'copied_sources': copied})
    monkeypatch.setattr(subject, 'inspect_call', lambda *args: {'status': 'VERIFIED', 'scientific_admission': False})
    probe = {'id': 'probe', 'module': 'runners.stage9.closure_probe', 'produces': 'probe/COMPLETE.json'}
    work = {'id': 'work', 'module': 'runners.stage9.confirmation_baselines', 'produces': 'work/COMPLETE.json',
            'after': ['probe'], 'requires': [{'job': 'probe', 'field': ['isolation_probe_verified'], 'equals': True}]}
    prior = {'probe': probe, 'work': work}
    plan = {'jobs': list(prior.values()), 'sources': {}, 'capsule_reviews': {'work': {'runtime': 'reader', 'probe_job': 'probe'}}}
    write(tmp_path / 'work/COMPLETE.json', {'outputs': outputs(tmp_path / 'work', tmp_path)})
    write(tmp_path / 'probe/COMPLETE.json', {'outputs': {'files': {}}})
    write(tmp_path / 'probe/BINDING.json', {'runtime': 'reader', 'copied_sources': copied})
    write(tmp_path / 'probe/PROBE.json', {})
    write(tmp_path / 'queue/STATUS.json', {'jobs': {key: {'status': 'COMPLETE'} for key in prior}})
    return plan, tmp_path / 'queue', prior


def test_review_covers_the_complete_committed_call_set(tmp_path, monkeypatch):
    plan, queue, prior = fixture(tmp_path, monkeypatch)
    result = subject.queue_audits(plan, queue, prior)
    assert set(result['jobs']) == {'work'} and result['jobs']['work']['call_count'] == 1
    assert not result['scientific_admission']


@pytest.mark.parametrize('fault', ['missing_review', 'extra_call', 'wrong_probe', 'missing_gate', 'changed_binding'])
def test_capsule_queue_review_refuses_uncovered_or_unprobed_readers(tmp_path, monkeypatch, fault):
    plan, queue, prior = fixture(tmp_path, monkeypatch)
    if fault == 'missing_review':
        plan['capsule_reviews'] = {}
    elif fault == 'extra_call':
        write(tmp_path / 'work/calls/uncommitted.json', {'input_sha256': 'b' * 64, 'result': {}})
    elif fault == 'wrong_probe':
        prior['probe']['module'] = 'runners.stage9.confirmation_summary'
    elif fault == 'missing_gate':
        prior['work']['requires'] = []
    else:
        write(tmp_path / 'probe/BINDING.json', {'runtime': 'other', 'copied_sources': {}})
    with pytest.raises(ValueError):
        subject.queue_audits(plan, queue, prior)


def test_failed_reader_disposition_is_retained_without_an_isolation_claim(tmp_path, monkeypatch):
    plan, queue, prior = fixture(tmp_path, monkeypatch)
    write(queue / 'STATUS.json', {'jobs': {'probe': {'status': 'COMPLETE'},
        'work': {'status': 'FAILED', 'reason': 'original failure', 'disposition_sha256': 'c' * 64}}})
    result = subject.queue_audits(plan, queue, prior)['jobs']['work']
    assert result['status'] == 'FAILED' and result['reason'] == 'original failure' and not result['scientific_admission']


@pytest.mark.parametrize('runtime', ['unreviewed', 'reader'])
def test_unknown_runtime_or_absent_original_source_binding_is_refused(runtime):
    with pytest.raises(ValueError):
        closure_probe.bindings(runtime, {'files': {}})


def test_launch_rehearsal_distinguishes_actual_probe_runtime():
    first = {'module': 'runners.stage9.closure_probe', 'arguments': ['--runtime', 'reader']}
    second = {'module': 'runners.stage9.closure_probe', 'arguments': ['--runtime', 'baseline_matrix']}
    assert handler_operation(first) != handler_operation(second)


@pytest.mark.parametrize('runtime', list(closure_probe.RUNTIMES))
def test_every_reviewed_materializer_runs_its_actual_exact_package_probe(tmp_path, monkeypatch, runtime):
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    binding = closure_probe.bindings(runtime, sources())
    sentinel = tmp_path / 'existing-hidden-data.json'
    sentinel.write_bytes(b'unchanged private fixture')
    task = {'probe': True, 'forbidden_paths': [str(sentinel)], 'other_port': 65534}
    result = importlib.import_module(binding['module']).execute(None, task=task, root=tmp_path / 'capsules')
    audit = subject.denial_probe(result, binding['copied_sources'])
    assert audit['attempts'] == 10 and sentinel.read_bytes() == b'unchanged private fixture'
    assert result['copied_sources']['files'] == binding['copied_sources']
    assert audit['source_sha256'] == binding['copied_sources_sha256']


@pytest.mark.parametrize('path', ['runners/stage9/capsule_host.py', 'runners/stage9/record_features.py',
                                  'runners/stage7/runtime.py', 'runners/stage9/record_runtime.py'])
def test_original_binding_rejects_changed_transport_materializer_and_copied_source(path):
    source = copy.deepcopy(sources()); source['files'][path] = '0' * 64
    with pytest.raises(ValueError, match='differs from the manifest'):
        closure_probe.bindings('record', source)
