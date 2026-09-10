import copy
import hashlib
from pathlib import Path

import pytest

from runners.stage7.runtime import BOOTSTRAP
from runners.stage9 import closure_capsules as subject
from runners.stage9 import runtime
from runners.stage9.common import REPO, file_hash, write


@pytest.fixture
def actual(tmp_path, monkeypatch):
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    outside = tmp_path / 'existing-truth.json'; outside.write_text('preserve fixture truth')
    probe = runtime.execute(None, {'probe': True, 'forbidden_paths': [str(outside)], 'other_port': 65534}, root=tmp_path/'probes')
    call = runtime.execute({'prefix': 'alpha beta', 'options': {'a': 'alpha beta', 'b': 'gamma'}},
                           {'operation': 'copy_baseline', 'copy_source': 'alpha beta'}, root=tmp_path/'calls')
    bindings = {name: file_hash(REPO / path) for name, path in {
        'reader/worker.py': 'runners/stage9/reader.py', 'reader/readout.py': 'runners/readout_repair.py',
        'reader/features.py': 'runners/stage9/features.py'}.items()}
    bindings['bootstrap.py'] = hashlib.sha256(BOOTSTRAP.encode('utf-8')).hexdigest()
    bindings['reader/__init__.py'] = hashlib.sha256(b'').hexdigest()
    assert outside.read_text() == 'preserve fixture truth'
    return call, probe, bindings


def test_actual_denials_and_loaded_source_output_verify_without_a_scientific_claim(actual):
    call, probe, bindings = actual
    result = subject.inspect_call(call, bindings, probe)
    assert result['status'] == 'VERIFIED' and result['denial_probe']['attempts'] == 10
    assert result['scientific_admission'] is False


@pytest.mark.parametrize('fault', ['missing_flag', 'substituted_binding', 'changed_source', 'changed_input',
    'altered_access', 'missing_access', 'omitted_attack', 'false_denial', 'wrong_denial_reason',
    'wrong_import_path', 'false_loaded_sources'])
def test_saved_capsule_audit_refuses_false_or_changed_boundary_evidence(actual, fault):
    call, probe, bindings = copy.deepcopy(actual)
    cap = Path(call['capsule']); probe_cap = Path(probe['capsule'])
    if fault == 'missing_flag':
        call.pop('accepted')
    elif fault == 'substituted_binding':
        bindings['reader/worker.py'] = 'a' * 64
    elif fault == 'changed_source':
        (cap / 'reader/worker.py').write_text('changed copied code')
    elif fault == 'changed_input':
        write(cap / 'task.json', {'operation': 'different'})
    elif fault == 'altered_access':
        call['access']['counts']['allowed'] += 1
    elif fault == 'missing_access':
        call['access'] = None; (cap / 'out/access.json').unlink()
    elif fault in ('omitted_attack', 'false_denial', 'wrong_denial_reason'):
        if fault == 'omitted_attack':
            probe['receipt']['attempts'].pop()
        elif fault == 'false_denial':
            probe['receipt']['attempts'][0]['denied'] = False
        else:
            probe['receipt']['attempts'][0]['error'] = 'FileNotFoundError is not boundary denial'
        write(probe_cap / 'out/receipt.json', probe['receipt'])
    elif fault == 'wrong_import_path':
        call['access']['sys_path'].append(str(cap.parent / 'unreviewed'))
        write(cap / 'out/access.json', call['access'])
    else:
        call['receipt']['loaded_sources']['reader.worker'] = 'f' * 64
        write(cap / 'out/receipt.json', call['receipt'])
    with pytest.raises(ValueError):
        subject.inspect_call(call, bindings, probe)


@pytest.mark.parametrize('missing_access', [False, True])
def test_failed_calls_remain_failed_including_incomplete_access_evidence(actual, missing_access):
    call, probe, bindings = copy.deepcopy(actual)
    call['accepted'] = False
    if missing_access:
        call['access'] = None; (Path(call['capsule']) / 'out/access.json').unlink()
    result = subject.inspect_call(call, bindings, probe)
    assert result['status'] == ('INCOMPLETE_FAILED_RETAINED' if missing_access else 'FAILED_RETAINED')
    assert not result['accepted'] and not result['scientific_admission']
