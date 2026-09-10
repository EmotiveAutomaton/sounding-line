"""Bound failures precede model loading; actual HTTP endpoint separates owner access."""
import threading
import time
import urllib.error

import pytest

from runners.stage9 import model_service as service
from runners.stage9.common import read
from runners.stage9.service_owner import post


def config(tmp_path):
    return {'family': 'qwen', 'precision': 'bfloat16', 'device': 'cpu', 'batch_size': 4,
            'max_context': 8192, 'max_support': 128, 'max_new_tokens': 256, 'port': 0,
            'token': 'a' * 64, 'shutdown_token': 'b' * 64, 'output': str(tmp_path)}


@pytest.mark.parametrize('changed', [{'batch_size': 0}, {'max_support': 129}, {'max_context': 8193},
                                    {'max_new_tokens': True}, {'device': 'remote'},
                                    {'shutdown_token': 'a' * 64}])
def test_invalid_envelope_is_rejected_before_model_import(tmp_path, changed):
    with pytest.raises(ValueError):
        service.Engine({**config(tmp_path), **changed})


def test_real_http_reader_cannot_shutdown_owner_service(tmp_path, monkeypatch):
    class FixtureEngine:
        def __init__(self, settings):
            self.identity = {'fixture': True}
        def infer(self, request):
            return {'valid': True, 'usage': {'fixture': 1}, 'inference_wall_seconds': 0}
    monkeypatch.setattr(service, 'Engine', FixtureEngine)
    settings = config(tmp_path)
    thread = threading.Thread(target=service.serve, args=(settings,), daemon=True)
    thread.start()
    for _ in range(200):
        if (tmp_path / 'READY.json').exists():
            break
        time.sleep(.01)
    ready = read(tmp_path / 'READY.json')
    endpoint = ready['endpoint']
    try:
        with pytest.raises(urllib.error.HTTPError) as caught:
            post(endpoint, settings['token'], '/shutdown', {})
        assert caught.value.code == 422
        assert thread.is_alive()
        assert post(endpoint, settings['token'], '/infer', {})['valid']
        with pytest.raises(urllib.error.HTTPError):
            post(endpoint, settings['shutdown_token'], '/infer', {})
    finally:
        post(endpoint, settings['shutdown_token'], '/shutdown', {})
        thread.join(5)
    assert not thread.is_alive()


def test_duplicate_continuation_likelihood_is_invariant_to_batch_remainder(tmp_path, monkeypatch):
    from runners.readout_repair import readout
    from runners.stage9.common import digest
    settings = config(tmp_path)
    engine = object.__new__(service.Engine)
    from types import SimpleNamespace
    engine.config, engine.model, engine.tok = settings, None, lambda *a, **k: SimpleNamespace(input_ids=[1])
    engine.identity = dict(model='fixture', revision='fixture', adapter_sha256='fixture', scorer_sha256='fixture')
    # Deliberate batch-shape arithmetic artifact: last duplicate gets a different value
    # unless there is exactly one measurement of each distinct continuation.
    def remainder_sensitive(model, tok, prefix, texts, batch, *bounds):
        return {'logprobs': [-1.0 if i // batch == (len(texts)-1) // batch else -1.2 for i in range(len(texts))]}
    monkeypatch.setattr(service, 'sequence_scores', remainder_sensitive)
    evidence = {'prefix': 'Next: ', 'options': {str(i): 'STOP' for i in range(13)}}
    identity = {**engine.identity, 'information_sha256': digest(evidence)}
    result = engine.infer({'operation': 'score', **evidence, 'identity': identity})
    outcome = readout(evidence['prefix'], evidence['options'], lambda *_: result['components'], identity)
    assert outcome['valid'] and len(outcome['ties']) == 13
    assert result['usage']['unique_continuations'] == 1
    assert result['usage']['offered_options'] == 13


def test_nested_service_execution_requires_actual_loaded_sources(tmp_path,monkeypatch):
    from runners.stage9 import service_owner as owner
    from runners.stage9.common import closure,write
    monkeypatch.setattr(owner,'REPO',tmp_path)
    names=('source_bootstrap.py','model_service.py','common.py','neural.py','train.py')
    for name in names:
        path=tmp_path/'runners/stage9'/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('fixture = 1\n',encoding='utf-8')
    source=closure([tmp_path/'runners']);source['files']={str(__import__('pathlib').Path(k).resolve().relative_to(tmp_path)).replace('\\','/'):v for k,v in source['files'].items()}
    # Use the owner's root for the independently checked closure shape.
    from runners.stage9.common import digest
    source['sha256']=digest(source['files'])
    config={'cell_identity':'a'*64,'sources':source}
    loaded=dict(source['files']);receipt={'cell_identity':'a'*64,'returncode':0,'error':None,'loaded_project_sources':loaded}
    path=tmp_path/'service/execution/EXECUTION.json';write(path,receipt)
    original_closure=owner.closure
    def local_closure(paths):
        result=original_closure(paths)
        files={str(__import__('pathlib').Path(k).resolve().relative_to(tmp_path)).replace('\\','/'):v for k,v in result['files'].items()}
        return {'files':files,'sha256':digest(files)}
    monkeypatch.setattr(owner,'closure',local_closure)
    assert owner.verify_execution(tmp_path/'service',config)
    del loaded['runners/stage9/neural.py'];write(path,receipt)
    with pytest.raises(ValueError,match='compiled source'):
        owner.verify_execution(tmp_path/'service',config)
    loaded['runners/stage9/neural.py']=source['files']['runners/stage9/neural.py'];write(path,receipt)
    (tmp_path/'runners/stage9/neural.py').write_text('fixture = 2\n',encoding='utf-8')
    with pytest.raises(ValueError,match='compiled source'):
        owner.verify_execution(tmp_path/'service',config)
