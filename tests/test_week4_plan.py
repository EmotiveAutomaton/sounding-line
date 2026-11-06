import copy
import json
import pytest
from runners.drive import week4_plan as p
from runners.drive import week4_plan_monitor as monitor


def sessions():
    return [dict(session='private-' + str(i), writer='secret', private_choices=[99],
        counts=dict(midpoint_nonempty=True, usable_later_openings=4, later_choices=0),
        provider_text_only=dict(midpoint_text='Visible text ' + str(i % 250),
                                later_options=[['future secret']] * 4)) for i in range(310)]


def message():
    return dict(model=p.MODEL, stop_reason='end_turn',
                content=[dict(type='text', text=json.dumps({k: 'Direction ' + k for k in p.KEYS}))],
                usage=dict(input_tokens=10, output_tokens=20))


def test_source_projection_dedup_order_and_future_invariance():
    source = sessions()
    rows, joins, n = p.rows_from_sessions(source)
    assert (len(rows), sum(map(len, joins.values())), n) == (250, 310, 310)
    assert p.rows_from_sessions(list(reversed(source)))[0] == rows
    for s in source:
        s['private_choices'] = ['CHANGED CHOICE']
        s['provider_text_only']['later_options'] = [['DIFFERENT FUTURE']] * 4
    assert p.rows_from_sessions(source)[0] == rows
    wire = json.dumps(rows)
    assert all(x not in wire for x in ['secret', 'private-', 'CHANGED', 'FUTURE'])
    assert len({r['custom_id'] for r in rows[:200]}) == 200
    assert set(json.loads(rows[0]['params']['messages'][0]['content'])) == {'midpoint_text'}
    assert rows[0]['params']['max_tokens'] == 300
    assert rows[0]['params']['thinking'] == {'type': 'disabled'}


@pytest.mark.parametrize('kind', ['duplicate', 'extra', 'count', 'midpoint', 'support', 'unique'])
def test_bad_source_refuses(kind):
    s = sessions()
    if kind == 'duplicate': s[-1]['session'] = s[0]['session']
    if kind == 'extra': s[0]['provider_text_only']['writer'] = 'secret'
    if kind == 'count': s[0]['counts']['usable_later_openings'] = 5
    if kind == 'midpoint': s[0]['counts']['midpoint_nonempty'] = False
    if kind == 'support': s = s[:299]
    if kind == 'unique':
        for x in s: x['provider_text_only']['midpoint_text'] = 'Identical'
    with pytest.raises(ValueError): p.rows_from_sessions(s)


@pytest.mark.parametrize('kind', ['model', 'stop', 'extra_block', 'extra_key', 'missing',
                                 'newline', 'duplicate_plan', 'empty', 'suffix', 'duplicate_key', 'wrong_type'])
def test_whole_message_refusal(kind):
    m = message()
    assert p.parse(m) is not None
    v = json.loads(m['content'][0]['text'])
    if kind == 'model': m['model'] = 'other'
    if kind == 'stop': m['stop_reason'] = 'max_tokens'
    if kind == 'extra_block': m['content'].append(dict(type='tool_use', text=''))
    if kind == 'extra_key': v['explanation'] = 'extra'
    if kind == 'missing': del v['p4']
    if kind == 'newline': v['p0'] = 'one\ntwo'
    if kind == 'duplicate_plan': v['p4'] = ' DIRECTION   p0 '
    if kind == 'empty': v['p0'] = ' '
    if kind == 'wrong_type': v['p0'] = True
    m['content'][0]['text'] = json.dumps(v)
    if kind == 'suffix': m['content'][0]['text'] += ' explanation'
    if kind == 'duplicate_key': m['content'][0]['text'] = m['content'][0]['text'][:-1] + ',"p0":"another"}'
    assert p.parse(m) is None


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    monkeypatch.setattr(p, 'check_sources', lambda: None)
    rows = p.rows_from_sessions(sessions())[0]
    p.freeze(tmp_path / 'REQUESTS.json', rows)
    p.freeze(tmp_path / 'SOURCE.json', {'fixture': True})
    events = []
    def reserve(*args):
        events.append('reserve')
        return {'fixture': True}
    def reconcile(*args):
        events.append('reconcile')
    monkeypatch.setattr(p.budget, 'reserve', reserve)
    monkeypatch.setattr(p.budget, 'reconcile', reconcile)
    def request(path, payload=None):
        events.append(path)
        if path.startswith('/v1/models/'): return json.dumps(dict(id=p.MODEL)).encode()
        if path.endswith('count_tokens'): return b'{"input_tokens":100}'
        if path.endswith('/batches'):
            assert events[-2] == 'reserve'
            assert len(payload['requests']) == 100
            return b'{"id":"msgbatch_fixture"}'
        if path.endswith('/results'):
            return ('\n'.join(json.dumps(dict(custom_id=r['custom_id'], result=dict(type='succeeded', message=message()))) for r in rows[:100])).encode()
        return b'{"id":"msgbatch_fixture","processing_status":"ended"}'
    monkeypatch.setattr(p, 'request', request)
    return events


def test_actual_handlers_complete_reentry_and_monitor(tmp_path, monkeypatch):
    events = setup(tmp_path, monkeypatch)
    plan = p.count(p.PHASE)
    assert plan['attempted'] == 100 and plan['reserved_cents'] >= 3
    count_calls = len(events)
    assert p.count(p.PHASE) == plan and len(events) == count_calls
    p.submit(p.PHASE)
    folder = tmp_path / p.PHASE
    p.freeze(folder / 'MONITOR_PLAN.json', dict(pins={}))
    monitor.run()
    result = p.read(folder / 'COMPLETE.json')
    assert result['format_passes'] and result['valid'] == 100
    assert not result['node_calibration_complete'] and not result['main_admission']
    assert result['semantic_agreement'] == 'untested' and result['usage_complete']
    assert events[-1] == 'reconcile' and (folder / 'RECONCILED.json').exists()
    before = len(events)
    assert p.retrieve(p.PHASE) == result and len(events) == before
    assert p.replay(p.PHASE) == result
    with pytest.raises(ValueError, match='consumed'): p.submit(p.PHASE)
    with pytest.raises(ValueError, match='blocked'): p.selected('main')


def test_unknown_never_resubmits(tmp_path, monkeypatch):
    events = setup(tmp_path, monkeypatch)
    p.count(p.PHASE)
    def unknown(*args): events.append('uncertain'); raise TimeoutError('uncertain')
    monkeypatch.setattr(p, 'request', unknown)
    with pytest.raises(TimeoutError): p.submit(p.PHASE)
    assert events[-2:] == ['reserve', 'uncertain']
    with pytest.raises(ValueError, match='consumed'): p.submit(p.PHASE)
    folder = tmp_path / p.PHASE
    p.freeze(folder / 'MONITOR_PLAN.json', dict(pins={}))
    with pytest.raises(RuntimeError, match='unknown'): monitor.run()
    assert p.read(folder / 'MONITOR_FAILED.json')['submission_retry_authorized'] is False


def test_wire_mutation_refuses_before_reservation(tmp_path, monkeypatch):
    events = setup(tmp_path, monkeypatch)
    p.count(p.PHASE)
    folder = tmp_path / p.PHASE
    wire = p.read(folder / 'WIRE.json')
    wire['requests'][0]['params']['messages'][0]['content'] = '{"midpoint_text":"changed"}'
    p.atomic(folder / 'WIRE.json', wire)
    with pytest.raises(ValueError): p.submit(p.PHASE)
    assert 'reserve' not in events


@pytest.mark.parametrize('invalid', [2, 3])
def test_format_floor_and_missing_coverage(tmp_path, monkeypatch, invalid):
    setup(tmp_path, monkeypatch)
    p.count(p.PHASE); p.submit(p.PHASE); p.retrieve(p.PHASE)
    folder = tmp_path / p.PHASE
    # Independent scratch attempt, preserve initial attempt rather than rewrite terminals.
    other = tmp_path / 'second'
    other.mkdir()
    for n in ['REQUESTS.json', 'SOURCE.json']: (other / n).write_bytes((tmp_path / n).read_bytes())
    f = other / p.PHASE
    f.mkdir()
    for n in ['STATUS.json', 'SUBMITTED.json']: (f / n).write_bytes((folder / n).read_bytes())
    results = [json.loads(x) for x in (folder / 'RESULTS.jsonl').read_text().splitlines()]
    for r in results[:invalid]: r['result']['message']['stop_reason'] = 'max_tokens'
    (f / 'RESULTS.jsonl').write_text('\n'.join(map(json.dumps, results)))
    monkeypatch.setattr(p, 'ROOT', other)
    result = p.replay(p.PHASE)
    assert result['format_passes'] == (invalid == 2)
    assert result['valid'] == 100 - invalid and not result['main_admission']
    (f / 'RESULTS.jsonl').write_text('\n'.join(map(json.dumps, results[:-1])))
    with pytest.raises(ValueError, match='coverage'): p.replay(p.PHASE)
