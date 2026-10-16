import copy
import json
import pytest
from runners.next_round import profiles as p


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
