import copy
from collections import Counter
import json
import subprocess
import sys
import pytest
from runners.drive import week4_plant as p
from runners.drive import week4_plant_monitor as monitor


def message(text='A complete constructed piece for a transport rehearsal.'):
    return dict(model=p.MODEL, stop_reason='end_turn',
        content=[dict(type='text', text=json.dumps({'piece': text}))],
        usage=dict(input_tokens=100, output_tokens=100))


def test_complete_allocation_independent_census_and_fresh_process():
    banks = p.allocation()
    assert {k: len(v) for k, v in banks.items()} == {'main': 600, 'calibration': 100, 'fresh-correction': 100}
    combined = sum(banks.values(), [])
    assert len({r['prompt'] for r in combined}) == len({r['custom_id'] for r in combined}) == 800
    assert Counter((r['genre'], len(r['assignment'])) for r in banks['main']) == {
        (g, n): count for g in ('argument','story') for n, count in [(0,50),(1,125),(2,125)]}
    assert set(g for r in banks['main'] for g in r['assignment']) == set(p.GOALS)
    for r in combined:
        body = json.loads(r['params']['messages'][0]['content'])
        assert set(body) == {'goal_library','assigned_goals','genre_prompt'}
        assert body['assigned_goals'] == r['assignment']
        assert body['genre_prompt'] == r['prompt']
        assert r['custom_id'] == p.digest(r['params'])
        assert r['params']['max_tokens'] == 700
        assert r['params']['thinking'] == {'type':'disabled'}
    key = p.blind_sample(banks['calibration'])
    assert len(key) == len(set(key.values())) == 50
    by = {r['custom_id']: r for r in banks['calibration']}
    assert all(by[k]['assignment'] for k in key.values())
    assert Counter(by[k]['genre'] for k in key.values()) == {'argument':25,'story':25}
    raw = subprocess.check_output([sys.executable,'-X','utf8','-B','-c',
        'from runners.drive.week4_plant import allocation,digest; print(digest(allocation()))'])
    assert raw.decode().strip() == p.digest(banks)


@pytest.mark.parametrize('kind', ['model','stop','extra_block','extra_key','empty','suffix','duplicate_key','type'])
def test_whole_message_refusal(kind):
    m = message()
    assert p.parse(m) is not None
    if kind == 'model': m['model'] = 'other'
    if kind == 'stop': m['stop_reason'] = 'max_tokens'
    if kind == 'extra_block': m['content'].append(dict(type='thinking',text='extra'))
    if kind == 'extra_key': m['content'][0]['text'] = '{"piece":"text","goal":"G01"}'
    if kind == 'empty': m['content'][0]['text'] = '{"piece":" "}'
    if kind == 'suffix': m['content'][0]['text'] += ' explanation'
    if kind == 'duplicate_key': m['content'][0]['text'] = '{"piece":"one","piece":"two"}'
    if kind == 'type': m['content'][0]['text'] = '{"piece":true}'
    assert p.parse(m) is None


def setup(tmp_path, monkeypatch, invalid=0):
    monkeypatch.setattr(p,'ROOT',tmp_path)
    monkeypatch.setattr(p,'check_sources',lambda:None)
    rows = p.allocation()['calibration']
    p.freeze(tmp_path/'REQUESTS.json',rows)
    p.freeze(tmp_path/'SOURCE.json',{'fixture':True})
    p.freeze(tmp_path/'PRIVATE_BLIND_KEY.json',p.blind_sample(rows))
    events=[]
    def reserve(*args):
        assert args[1] == 'PLANT'
        events.append('reserve')
        return {'fixture':True}
    def reconcile(*args): events.append('reconcile')
    monkeypatch.setattr(p.budget,'reserve',reserve)
    monkeypatch.setattr(p.budget,'reconcile',reconcile)
    def request(path,payload=None):
        events.append(path)
        if path.startswith('/v1/models/'): return json.dumps({'id':p.MODEL}).encode()
        if path.endswith('count_tokens'): return b'{"input_tokens":100}'
        if path.endswith('/batches'):
            assert events[-2] == 'reserve'
            assert len(payload['requests']) == 100
            return b'{"id":"msgbatch_fixture"}'
        if path.endswith('/results'):
            output=[]
            for i,r in enumerate(rows):
                m=message()
                if i < invalid: m['stop_reason']='max_tokens'
                output.append(dict(custom_id=r['custom_id'],result=dict(type='succeeded',message=m)))
            return '\n'.join(json.dumps(r) for r in output).encode()
        return b'{"id":"msgbatch_fixture","processing_status":"ended"}'
    monkeypatch.setattr(p,'request',request)
    return events


@pytest.mark.parametrize('invalid,passes',[(0,True),(2,True),(3,False)])
def test_real_handlers_gate_boundaries_reentry_monitor(tmp_path,monkeypatch,invalid,passes):
    events=setup(tmp_path,monkeypatch,invalid)
    plan=p.count(p.PHASE)
    assert plan['attempted']==100 and plan['node']=='PLANT'
    before=len(events)
    assert p.count(p.PHASE)==plan and len(events)==before
    p.submit(p.PHASE)
    folder=tmp_path/p.PHASE
    p.freeze(folder/'MONITOR_PLAN.json',dict(pins={}))
    monitor.run()
    result=p.read(folder/'COMPLETE.json')
    assert result['format_passes']==passes and result['valid']==100-invalid
    assert result['blind_non_disclosure']=='untested'
    assert not result['node_calibration_complete'] and not result['main_admission']
    assert events[-1]=='reconcile' and (folder/'RECONCILED.json').exists()
    view=p.read(folder/'BLIND_PIECES.json')
    assert len(view)==50 and all(set(r)=={'blind_id','piece','valid'} for r in view)
    before=len(events)
    assert p.retrieve(p.PHASE)==result and len(events)==before
    assert p.replay(p.PHASE)==result
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    with pytest.raises(ValueError,match='blocked'):p.selected('main')


def test_unknown_delivery_no_retry(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch)
    p.count(p.PHASE)
    def unknown(*args): events.append('uncertain');raise TimeoutError('uncertain')
    monkeypatch.setattr(p,'request',unknown)
    with pytest.raises(TimeoutError):p.submit(p.PHASE)
    assert events[-2:]==['reserve','uncertain']
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    folder=tmp_path/p.PHASE
    p.freeze(folder/'MONITOR_PLAN.json',dict(pins={}))
    with pytest.raises(RuntimeError,match='unknown'):monitor.run()
    assert p.read(folder/'MONITOR_FAILED.json')['submission_retry_authorized'] is False


def test_changed_wire_rejected_before_charge(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch)
    p.count(p.PHASE)
    folder=tmp_path/p.PHASE
    wire=p.read(folder/'WIRE.json');wire['requests'][0]['params']['max_tokens']=701
    p.atomic(folder/'WIRE.json',wire)
    with pytest.raises(ValueError):p.submit(p.PHASE)
    assert 'reserve' not in events


def test_missing_coverage_stops_and_keeps_reservation(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch)
    p.count(p.PHASE);p.submit(p.PHASE)
    folder=tmp_path/p.PHASE
    p.freeze(folder/'STATUS.json',dict(id='msgbatch_fixture',processing_status='ended'))
    (folder/'RESULTS.jsonl').write_text('',encoding='utf8')
    with pytest.raises(ValueError,match='coverage'):p.replay(p.PHASE)
    assert 'reconcile' not in events and not (folder/'COMPLETE.json').exists()


def test_actual_preparation_and_changed_pins(tmp_path,monkeypatch):
    root=tmp_path/'preparation'
    monkeypatch.setattr(p,'ROOT',root)
    source=p.prepare();p.check_sources()
    assert source['main_pieces']==600
    original=p.read(root/'PRIVATE_BLIND_KEY.json')
    changed=copy.deepcopy(original);changed.pop(next(iter(changed)))
    p.atomic(root/'PRIVATE_BLIND_KEY.json',changed)
    with pytest.raises(ValueError,match='changed'):p.check_sources()
