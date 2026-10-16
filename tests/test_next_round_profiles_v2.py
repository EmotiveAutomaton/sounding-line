import copy
import json
import pytest
from runners.next_round import profiles_v2 as p


def message(obj=None):
    return {'stop_reason': 'end_turn', 'model': p.api.MODELS['RS'],
            'usage': {'input_tokens': 1200, 'output_tokens': 80},
            'content': [{'type': 'text', 'text': json.dumps(obj or {'preferences': [
                {'statement': 'Often edits offered continuations.', 'evidence_indices': [0]}]})}]}


@pytest.mark.parametrize('bad', [
    {'preferences': []}, {'preferences': [{'statement': ' '.join(['word']*25), 'evidence_indices': [0]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [True]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [2]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [0, 0]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': []}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [0]}], 'future': 'x'},
])
def test_bad_profiles(bad):
    with pytest.raises(ValueError): p.parse(message(bad), 2)


def test_duplicate_json_and_truncation():
    m = message(); m['content'][0]['text'] = '{"preferences":[],"preferences":[]}'
    with pytest.raises(ValueError): p.parse(m, 2)
    m = message(); m['stop_reason'] = 'max_tokens'
    with pytest.raises(ValueError): p.parse(m, 2)
    assert len(p.parse(message(), 2)['preferences']) == 1


def test_whole_lifecycle_and_reentry(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    row = {'custom_id': 'known', 'params': {'model': p.api.MODELS['RS'], 'max_tokens': 1500},
           'reader': 'RS', 'history_records': 2}
    monkeypatch.setattr(p, 'rows_for', lambda phase: [copy.deepcopy(row)])
    calls = []
    def transport(path, body=None):
        calls.append((path, body))
        if path.startswith('/v1/models/'): return json.dumps({'id': p.api.MODELS['RS']}).encode()
        if path.endswith('count_tokens'): return b'{"input_tokens":1200}'
        if path == '/v1/messages/batches': return b'{"id":"fixture_batch"}'
        if path.endswith('/results'):
            return json.dumps({'custom_id': 'known', 'result': {'type': 'succeeded', 'message': message()}}).encode()
        return b'{"id":"fixture_batch","processing_status":"ended"}'
    monkeypatch.setattr(p.api, 'request', transport)
    # A scratch root still needs repo-relative pins; substitute only this test's root.
    monkeypatch.setattr(p, 'REPO', p.REPO)
    monkeypatch.setattr(p, 'prepare', p.prepare)
    folder = tmp_path/'pilot'
    p.freeze(folder/'REQUESTS.json', [row])
    p.freeze(folder/'PLAN.json', {'at': p.time.time(), 'source_pins': {}, 'request_digest': p.digest([row]),
                               'reserved_cents': 4, 'max_seconds': 86400})
    reservations = []
    def reserve(*args): reservations.append(args); return {'reserved_cents': args[2]}
    monkeypatch.setattr(p.budget, 'reserve', reserve)
    monkeypatch.setattr(p.budget, 'reconcile_tokens', lambda *args: None)
    p.submit('pilot')
    with pytest.raises(ValueError): p.submit('pilot')
    assert len(reservations) == 1
    assert len([c for c in calls if c[0] == '/v1/messages/batches']) == 1
    first = p.retrieve('pilot'); count = len(calls)
    assert first['valid'] == first['attempted'] == 1
    assert p.replay('pilot') == first
    assert p.reconcile('pilot')['status'] == 'RECONCILED'
    assert len(calls) == count
    result = folder/'RESULTS.jsonl'
    result.write_text(result.read_text()+'\n'+result.read_text(), encoding='utf8')
    with pytest.raises(ValueError): p.replay('pilot')


def test_uncertain_submit_retains_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    folder = tmp_path/'pilot'; rows = [{'custom_id': 'fixture', 'params': {}}]
    p.freeze(folder/'REQUESTS.json', rows)
    p.freeze(folder/'PLAN.json', {'at': p.time.time(), 'source_pins': {}, 'request_digest': p.digest(rows),
                               'reserved_cents': 2, 'max_seconds': 86400})
    monkeypatch.setattr(p.budget, 'reserve', lambda *a: {'reserved_cents': 2})
    def fail(*args): raise TimeoutError()
    monkeypatch.setattr(p.api, 'request', fail)
    with pytest.raises(TimeoutError): p.submit('pilot')
    assert p.read(folder/'UNKNOWN.json')['reservation_retained']
    with pytest.raises(ValueError): p.submit('pilot')


def test_real_request_separation():
    pilot, main = p.rows_for('pilot'), p.rows_for('main')
    assert len(pilot) == 6 and len(main) == 62
    assert not {r['writer'] for r in pilot} & {r['writer'] for r in main}
    for r in pilot+main:
        assert set(json.loads(r['params']['messages'][0]['content'])) == {'history'}
        assert r['params']['max_tokens'] == 1500
        assert r['params']['output_config']['format']['schema'] == p.SCHEMA


@pytest.mark.parametrize('words,valid', [(0, False), (1, True), (24, True), (25, False)])
def test_exact_word_bound(words, valid):
    text = ' '.join(['word']*words)
    m = message({'preferences': [{'statement': text, 'evidence_indices': [0]}]})
    assert bool(p.re.fullmatch(p.STATEMENT_PATTERN, text)) == valid
    if valid:
        assert p.parse(m, 1)['preferences'][0]['statement'] == text
    else:
        with pytest.raises(ValueError): p.parse(m, 1)


@pytest.mark.parametrize('text', [' two', 'two ', 'two  words', 'two\twords',
                                  'two\nwords', 'two\u00a0words', 'two\u2003words', 'word\n'])
def test_noncanonical_whitespace_rejected(text):
    with pytest.raises(ValueError):
        p.parse(message({'preferences': [{'statement': text, 'evidence_indices': [0]}]}), 1)


def test_same_evidence_and_original_gate():
    from runners.next_round import profiles as old
    for phase in ['pilot', 'main']:
        before, after = old.rows_for(phase), p.rows_for(phase)
        for a, b in zip(before, after):
            for key in ['writer', 'arm', 'history_records', 'evidence_sha256']:
                assert a[key] == b[key]
            assert a['params']['messages'] == b['params']['messages']
            assert a['custom_id'] != b['custom_id']
    # New accepted representation remains acceptable under the unchanged old gate.
    for n in range(1, 25):
        m = message({'preferences': [{'statement': ' '.join(['w']*n), 'evidence_indices': [0]}]})
        assert p.parse(m, 1) == old.parse(m, 1)


@pytest.mark.parametrize('defect', ['invalid', 'usage', 'landing', 'pins'])
def test_main_refuses_before_reservation(tmp_path, monkeypatch, defect):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    monkeypatch.setattr(p, 'validate_plan', lambda root: {'at': p.time.time()})
    pilot = {'attempted': 6, 'valid': 5 if defect == 'invalid' else 6,
             'usage_complete': defect != 'usage'}
    monkeypatch.setattr(p, 'replay', lambda phase: pilot)
    p.freeze(tmp_path/'pilot/COMPLETE.json', pilot)
    p.freeze(tmp_path/'pilot/LANDED.json', {
        'complete_sha256': p.filehash(tmp_path/'pilot/COMPLETE.json'),
        'full_write_through': defect != 'landing'})
    monkeypatch.setattr(p.budget, 'reserve', lambda *a: pytest.fail('must refuse before reserve'))
    with pytest.raises(ValueError): p.submit('main')


def test_supervisor_registers_before_post(tmp_path, monkeypatch):
    from runners.next_round import profile_supervisor_v2 as s
    monkeypatch.setattr(s, 'REPO', tmp_path)
    monkeypatch.setattr(p, 'ROOT', tmp_path/'raw')
    native = {'pid': 123, 'creation_time': 456}
    monkeypatch.setattr(s, 'native_identity', lambda: native)
    monkeypatch.setattr(p, 'validate_plan', lambda root: {'max_seconds': 86400})
    p.freeze(tmp_path/'.agent-state/watch.json', {'process_watches': [], 'paths': []})
    def submit(phase):
        cfg = p.read(tmp_path/'.agent-state/watch.json')
        assert cfg['process_watches'][0]['native'] == native
        assert 'raw/pilot/UNKNOWN.json' in cfg['paths']
        p.freeze(p.ROOT/phase/'SUBMITTED.json', {'at': p.time.time()})
    monkeypatch.setattr(p, 'submit', submit)
    monkeypatch.setattr(p, 'retrieve', lambda phase: {'status': 'COMPLETE'})
    monkeypatch.setattr(p, 'reconcile', lambda phase: None)
    s.worker('pilot')
    assert p.read(p.ROOT/'pilot/EXIT.json')['status'] == 'COMPLETE'
