import json
import pytest
from runners.drive import week4_val_main as p
from runners.drive import week4_val_main_monitor as monitor


def setup(tmp_path, monkeypatch, invalid=0, missing=False, unknown_usage=False):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    monkeypatch.setattr(p, 'check_sources', lambda: None)
    rows=p.read(p.calibration.ROOT/'REQUESTS.json')[100:103]
    monkeypatch.setattr(p, 'selected', lambda phase: rows)
    p.freeze(tmp_path/'REQUESTS.json', rows)
    p.freeze(tmp_path/'SOURCE.json', dict(fixture=True))
    events=[]
    def reserve(*args):
        assert args[1]=='VAL';events.append('reserve');return dict(fixture=True)
    monkeypatch.setattr(p.budget, 'reserve', reserve)
    monkeypatch.setattr(p.budget, 'reconcile', lambda *args: events.append('reconcile'))
    def request(path, payload=None):
        events.append(path)
        if path.startswith('/v1/models/'): return json.dumps({'id':p.MODEL}).encode()
        if path.endswith('count_tokens'): return b'{"input_tokens":100}'
        if path.endswith('/batches'):
            assert events[-2]=='reserve' and len(payload['requests'])==3
            return b'{"id":"msgbatch_fixture"}'
        if path.endswith('/results'):
            results=[]
            for i,row in enumerate(rows[:-1] if missing else rows):
                result=dict(type='succeeded',message=dict(model=p.MODEL,
                    stop_reason='max_tokens' if i<invalid else 'end_turn',
                    content=[dict(type='text',text='{"v":"0010000000","o":1}')],
                    usage=dict(input_tokens=100,output_tokens=20)))
                if unknown_usage and i==0: result=dict(type='errored',error=dict(type='fixture'))
                results.append(dict(custom_id=row['custom_id'],result=result))
            return '\n'.join(json.dumps(r) for r in results).encode()
        return b'{"id":"msgbatch_fixture","processing_status":"ended"}'
    monkeypatch.setattr(p, 'request', request)
    return events, rows


@pytest.mark.parametrize('invalid,complete', [(0,True),(1,False)])
def test_actual_count_submission_monitor_replay_and_reentry(tmp_path,monkeypatch,invalid,complete):
    events,_=setup(tmp_path,monkeypatch,invalid)
    plan=p.count(p.PHASE);folder=tmp_path/p.PHASE
    assert plan['attempted']==3 and p.read(folder/'COUNT_COMPLETE.json')['generation_submitted'] is False
    n=len(events);assert p.count(p.PHASE)==plan and len(events)==n
    p.submit(p.PHASE);p.freeze(folder/'MONITOR_PLAN.json',dict(pins={}))
    monitor.run();result=p.read(folder/'COMPLETE.json')
    assert result['complete_main_corpus']==complete and result['valid']==3-invalid
    assert not result['scientific_admission'] and not result['collection_assembled']
    assert events[-1]=='reconcile' and p.replay(p.PHASE)==result
    n=len(events);assert p.retrieve(p.PHASE)==result and len(events)==n
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)


def test_missing_results_never_complete_or_settle(tmp_path,monkeypatch):
    events,_=setup(tmp_path,monkeypatch,missing=True)
    p.count(p.PHASE);p.submit(p.PHASE)
    with pytest.raises(ValueError,match='coverage'):p.retrieve(p.PHASE)
    assert 'reconcile' not in events and not (tmp_path/p.PHASE/'COMPLETE.json').exists()


def test_unknown_submission_never_retries(tmp_path,monkeypatch):
    events,_=setup(tmp_path,monkeypatch);p.count(p.PHASE)
    def unknown(*args):raise TimeoutError('uncertain')
    monkeypatch.setattr(p,'request',unknown)
    with pytest.raises(TimeoutError):p.submit(p.PHASE)
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    assert (tmp_path/p.PHASE/'UNKNOWN.json').exists()


def test_unknown_usage_preserves_reservation(tmp_path,monkeypatch):
    events,_=setup(tmp_path,monkeypatch,unknown_usage=True)
    p.count(p.PHASE);p.submit(p.PHASE);result=p.retrieve(p.PHASE)
    assert not result['usage_complete'] and 'reconcile' not in events


def test_count_checkpoint_binding_and_failed_terminal(tmp_path,monkeypatch):
    events,rows=setup(tmp_path,monkeypatch);folder=tmp_path/p.PHASE
    p.freeze(folder/'counts'/(rows[0]['custom_id']+'.json'),dict(request_sha256='wrong',response=dict(input_tokens=100)))
    with pytest.raises(ValueError,match='checkpoint'):p.count(p.PHASE)
    assert (folder/'COUNT_FAILED.json').exists() and not (folder/'COUNT_COMPLETE.json').exists()
    with pytest.raises(ValueError,match='failed count'):p.count(p.PHASE)
    assert 'reserve' not in events


def test_count_cutoff_and_wire_mutation_refuse(tmp_path,monkeypatch):
    events,_=setup(tmp_path,monkeypatch);p.count(p.PHASE)
    folder=tmp_path/p.PHASE;wire=p.read(folder/'WIRE.json')
    wire['requests'][0]['params']['max_tokens']=33;p.atomic(folder/'WIRE.json',wire)
    with pytest.raises(ValueError):p.submit(p.PHASE)
    assert 'reserve' not in events


def test_count_expired_authority_stops_without_generation(tmp_path,monkeypatch):
    events,_=setup(tmp_path,monkeypatch);monkeypatch.setattr(p.budget,'CUTOFF',0)
    with pytest.raises(TimeoutError,match='finite count'):p.count(p.PHASE)
    assert (tmp_path/p.PHASE/'COUNT_FAILED.json').exists() and events==[]


def test_plan_allocation_metadata_change_refuses(tmp_path,monkeypatch):
    events,_=setup(tmp_path,monkeypatch);p.count(p.PHASE)
    path=tmp_path/p.PHASE/'PLAN.json';plan=p.read(path);plan['attempted']=2;p.atomic(path,plan)
    with pytest.raises(ValueError,match='allocation'):p.submit(p.PHASE)
    assert 'reserve' not in events


def test_actual_landed_dependency_and_wrong_parent_refusal(tmp_path,monkeypatch):
    assert p.admitted()==p.calibration.ROOT/p.calibration.PHASE
    v=p.read(p.LANDING);v['complete_sha256']='0'*64
    path=tmp_path/'wrong.json';p.freeze(path,v);monkeypatch.setattr(p,'LANDING',path)
    with pytest.raises(ValueError,match='landed'):p.admitted()


def test_actual_preparation_exact_remainder_and_source_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'ROOT',tmp_path/'prepared');result=p.prepare()
    assert result['main_items']==8231 and result['reused_calibration_items']==100
    rows=p.selected(p.PHASE);all_rows=p.read(p.calibration.ROOT/'REQUESTS.json')
    assert rows==all_rows[100:] and {r['custom_id'] for r in rows}.isdisjoint(r['custom_id'] for r in all_rows[:100])
    rows[0]['params']['max_tokens']=33;p.atomic(p.ROOT/'REQUESTS.json',rows)
    with pytest.raises(ValueError,match='changed'):p.check_sources()
