import json
import pytest
from runners.drive import week4_plant_main as p
from runners.drive import week4_plant_main_monitor as monitor


def setup(tmp_path,monkeypatch,invalid=0,missing=False):
    monkeypatch.setattr(p,'ROOT',tmp_path)
    monkeypatch.setattr(p,'check_sources',lambda:None)
    rows=p.calibration.allocation()['main']
    p.freeze(tmp_path/'REQUESTS.json',rows)
    p.freeze(tmp_path/'SOURCE.json',dict(fixture=True))
    events=[]
    def reserve(*args):
        assert args[1]=='PLANT';events.append('reserve');return dict(fixture=True)
    def reconcile(*args):events.append('reconcile')
    monkeypatch.setattr(p.budget,'reserve',reserve);monkeypatch.setattr(p.budget,'reconcile',reconcile)
    def request(path,payload=None):
        events.append(path)
        if path.startswith('/v1/models/'):return json.dumps({'id':p.MODEL}).encode()
        if path.endswith('count_tokens'):return b'{"input_tokens":100}'
        if path.endswith('/batches'):
            assert events[-2]=='reserve' and len(payload['requests'])==600
            return b'{"id":"msgbatch_fixture"}'
        if path.endswith('/results'):
            return '\n'.join(json.dumps(dict(custom_id=r['custom_id'],result=dict(type='succeeded',
                message=dict(model=p.MODEL,stop_reason='max_tokens' if i<invalid else 'end_turn',
                content=[dict(type='text',text=json.dumps({'piece':'Constructed transport fixture.'}))],
                usage=dict(input_tokens=100,output_tokens=100))))) for i,r in enumerate(rows[:599] if missing else rows)).encode()
        return b'{"id":"msgbatch_fixture","processing_status":"ended"}'
    monkeypatch.setattr(p,'request',request)
    return events


@pytest.mark.parametrize('invalid,passes',[(0,True),(1,False)])
def test_complete_main_handlers_and_no_salvage(tmp_path,monkeypatch,invalid,passes):
    events=setup(tmp_path,monkeypatch,invalid)
    plan=p.count(p.PHASE);assert plan['attempted']==600
    p.submit(p.PHASE)
    folder=tmp_path/p.PHASE;p.freeze(folder/'MONITOR_PLAN.json',dict(pins={}))
    monitor.run();receipt=p.read(folder/'COMPLETE.json')
    assert receipt['complete_main_corpus']==passes and receipt['valid']==600-invalid
    assert receipt['node_calibration_complete'] and not receipt['scientific_admission']
    assert receipt['usage_complete'] and events[-1]=='reconcile'
    assert len(p.read(folder/'PIECES.json'))==600-invalid
    n=len(events);assert p.retrieve(p.PHASE)==receipt and len(events)==n
    assert p.replay(p.PHASE)==receipt
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)


def test_missing_main_coverage_holds_accounting(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch,missing=True)
    p.count(p.PHASE);p.submit(p.PHASE)
    with pytest.raises(ValueError,match='coverage'):p.retrieve(p.PHASE)
    assert 'reconcile' not in events and not (tmp_path/p.PHASE/'COMPLETE.json').exists()


def test_unknown_never_resubmits(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch);p.count(p.PHASE)
    def unknown(*args):raise TimeoutError('unknown')
    monkeypatch.setattr(p,'request',unknown)
    with pytest.raises(TimeoutError):p.submit(p.PHASE)
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    assert (tmp_path/p.PHASE/'UNKNOWN.json').exists()


def test_counted_wire_change_refuses(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch);p.count(p.PHASE)
    folder=tmp_path/p.PHASE;wire=p.read(folder/'WIRE.json')
    wire['requests'][0]['params']['max_tokens']=701;p.atomic(folder/'WIRE.json',wire)
    with pytest.raises(ValueError):p.submit(p.PHASE)
    assert 'reserve' not in events


def test_actual_landed_dependency_and_mutation_refusal(tmp_path,monkeypatch):
    assert p.admitted()==p.calibration.ROOT/p.calibration.PHASE
    receipt=p.read(p.LANDING);receipt['verified_sha256']='0'*64
    path=tmp_path/'wrong-landing.json';p.freeze(path,receipt);monkeypatch.setattr(p,'LANDING',path)
    with pytest.raises(ValueError,match='landed'):p.admitted()


def test_real_preparation_rebuild_and_changed_output(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'ROOT',tmp_path/'prepared')
    result=p.prepare();p.check_sources()
    assert result['main_pieces']==600 and len(p.selected(p.PHASE))==600
    rows=p.read(p.ROOT/'REQUESTS.json');rows[0]['assignment']=[];p.atomic(p.ROOT/'REQUESTS.json',rows)
    with pytest.raises(ValueError,match='changed'):p.check_sources()
