"""Transition-only monitoring never wakes an agent for healthy elapsed time."""
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import codex_watch as watch
from codex_common import database, put


@pytest.fixture
def context(tmp_path):
    repo = tmp_path; state = repo/'.agent-state'
    native = {'pid': 123, 'created_ticks': 456, 'executable': 'python.exe'}
    cfg = {'transition_only': True, 'fallback_seconds': 1, 'paths': ['job/COMPLETE.json', 'job/FAILED.json'],
           'process_watches': [{'native': native, 'terminal_paths': ['job/COMPLETE.json', 'job/FAILED.json'],
                               'failure_output': '.agent-state/job-disappeared/FAILED.json'}]}
    with database(state) as db:
        put(db, 'owner', 'owner'); put(db, 'owner_phase', 'idle'); put(db, 'last_fallback', 0)
        put(db, 'wake_plan', {'owner': 'owner', 'id': 'obsolete', 'due': 1})
    return repo, state, cfg, native


def test_healthy_process_never_wakes_despite_deadlines(context, monkeypatch):
    repo, state, cfg, native = context
    monkeypatch.setattr(watch, 'native_identity', lambda pid: native)
    for now in (10, 10000, 10000000):
        assert watch.scan(cfg, repo=repo, state=state, now=now) == []
    with database(state) as db:
        put(db, 'wake_plan', None)
    assert watch.scan(cfg, repo=repo, state=state, now=20000000) == []


@pytest.mark.parametrize('actual', [None, {'pid': 123, 'created_ticks': 999, 'executable': 'python.exe'}])
def test_disappearance_or_reuse_creates_one_fault(context, monkeypatch, actual):
    repo, state, cfg, native = context
    monkeypatch.setattr(watch, 'native_identity', lambda pid: actual)
    assert len(watch.scan(cfg, repo=repo, state=state, now=10)) == 1
    assert watch.scan(cfg, repo=repo, state=state, now=1000) == []
    assert (repo/cfg['process_watches'][0]['failure_output']).is_file()


def test_unknown_identity_is_monitor_failure_not_claim_of_death(context, monkeypatch):
    repo, state, cfg, native = context
    def denied(pid):
        raise OSError('denied')
    monkeypatch.setattr(watch, 'native_identity', denied)
    assert len(watch.scan(cfg, repo=repo, state=state, now=10)) == 1
    record = json.loads((repo/cfg['process_watches'][0]['failure_output']).read_text())
    assert 'unavailable' in record['reason'] and not record['scientific_verdict']


@pytest.mark.parametrize('name,record', [
    ('COMPLETE.json', {'status': status})
    for status in ('COMPLETE', 'complete', 'Complete', 'PASS', 'pass', 'FITTED', 'fitted')
] + [('FAILED.json', {'status': 'failed'}), ('FAILED.json', {'error': 'failure'})])
def test_terminal_output_owns_notification(context, monkeypatch, name, record):
    repo, state, cfg, native = context
    (repo/'job').mkdir(); (repo/'job'/name).write_text(json.dumps(record))
    monkeypatch.setattr(watch, 'native_identity', lambda pid: None)
    assert len(watch.scan(cfg, repo=repo, state=state, now=10)) == 1
    assert not (repo/cfg['process_watches'][0]['failure_output']).exists()
    assert watch.urgent({'path': 'job/'+name}, cfg)


@pytest.mark.parametrize('record', [{}, {'status': 'running'}, {'status': 'incomplete'},
                                  {'status': None}, {'status': []}, [], True])
def test_invalid_terminal_does_not_hide_disappearance(context, monkeypatch, record):
    repo, state, cfg, native = context
    (repo/'job').mkdir(); (repo/'job/COMPLETE.json').write_text(json.dumps(record))
    monkeypatch.setattr(watch, 'native_identity', lambda pid: None)
    watch.scan(cfg, repo=repo, state=state, now=10)
    assert (repo/cfg['process_watches'][0]['failure_output']).exists()


@pytest.mark.parametrize('changes,expected', [({}, True), ({'saved_result_sha256':'bad'},False),
    ({'resume':''},False), ({'card':None},False), ({'scientific_admission':True},False),
    ({'status':'running'},False)])
def test_saved_pause_owns_notification_without_claiming_completion(context,monkeypatch,changes,expected):
    repo,state,cfg,native=context
    record=dict(status='PAUSED',card='D32',saved_result_sha256='a'*64,
                resume='Owner must dispatch intervening work before resume',scientific_admission=False)
    record.update(changes)
    (repo/'job').mkdir();(repo/'job/PAUSED.json').write_text(json.dumps(record))
    cfg['paths']=['job/PAUSED.json'];cfg['process_watches'][0]['terminal_paths']=['job/PAUSED.json']
    monkeypatch.setattr(watch,'native_identity',lambda pid:None)
    events=watch.scan(cfg,repo=repo,state=state,now=10)
    assert (repo/cfg['process_watches'][0]['failure_output']).exists() is not expected
    assert len(events)==(1 if expected else 2)
    assert watch.urgent({'path':'job/PAUSED.json'},cfg)


@pytest.mark.parametrize('changes,expected', [({}, True),
    ({'checkpoint_validation_required': False}, False),
    ({'scientific_admission': True}, False), ({'cpu_seconds': True}, False),
    ({'cpu_seconds': float('nan')}, False), ({'cpu_seconds': -1}, False),
    ({'card': ''}, False), ({'at': None}, False),
    ({'reason': {'at': '2026-10-25T22:12:29Z', 'reason': 'running'}}, False),
    ({'reason': {'reason': 'resource_floor'}}, False),
    ({'reason': {'at': '2026-10-25T22:12:29Z', 'reason': 'week_drain'}}, True),
    ({'reason': {'at': '2026-11-16T06:00:00Z', 'reason': 'week5_drain'}}, True),
    ({'reason': {'at': '2026-11-07T20:00:00Z', 'reason': 'owner_cancel'}}, True),
    ({'reason': {'at': '2026-10-25T22:12:29Z', 'reason': 'cpu_projection_above_cumulative_S4_cap'}}, True)])
def test_week3_checkpoint_pause_not_a_disappeared_job(context, monkeypatch, changes, expected):
    repo, state, cfg, native = context
    record = dict(at='2026-10-25T22:12:53Z', status='PAUSED',
                  card='CA1-features-cost-pilot-recovery', cpu_seconds=3463.5625,
                  scientific_admission=False, checkpoint_validation_required=True,
                  reason={'at': '2026-10-25T22:12:29Z', 'reason': 'resource_floor'})
    record.update(changes)
    (repo/'job').mkdir(); (repo/'job/PAUSED.json').write_text(json.dumps(record))
    cfg['paths'] = ['job/PAUSED.json']
    cfg['process_watches'][0]['terminal_paths'] = ['job/PAUSED.json']
    monkeypatch.setattr(watch, 'native_identity', lambda pid: None)
    events = watch.scan(cfg, repo=repo, state=state, now=10)
    assert (repo/cfg['process_watches'][0]['failure_output']).exists() is not expected
    assert len(events) == (1 if expected else 2)
    assert watch.scan(cfg, repo=repo, state=state, now=100) == []


@pytest.mark.parametrize('name,changes,expected', [
    ('FAILED-123.json', {}, True),
    ('FAILED-worker.json', {}, False),
    ('FAILED-0.json', {}, False),
    ('FAILED-123.json.tmp', {}, False),
    ('FAILED-123.json', {'error': None}, False),
    ('FAILED-123.json', {'error': ''}, False),
    ('FAILED-123.json', {'traceback': []}, False),
    ('FAILED-123.json', {'at': None}, False),
    ('FAILED-123.json', {'status': 'running'}, False),
    ('FAILED-123.json', {'status': 'incomplete'}, False),
])
def test_pid_failure_receipt_owns_only_its_terminal_notification(context, monkeypatch, name, changes, expected):
    """The coordinator's real statusless failure shape must not become a missing-output alarm."""
    repo, state, cfg, native = context
    record = {'at': '2026-09-20T14:09:46.291625+00:00',
              'error': 'TimeoutExpired(worker, 21600)',
              'traceback': 'Traceback: child.wait(timeout=21600) raised TimeoutExpired',
              'dispositions': []}
    record.update(changes)
    (repo/'job').mkdir()
    terminal = 'job/'+name
    (repo/terminal).write_text(json.dumps(record))
    cfg['paths'] = [terminal]
    cfg['process_watches'][0]['terminal_paths'] = [terminal]
    monkeypatch.setattr(watch, 'native_identity', lambda pid: None)
    events = watch.scan(cfg, repo=repo, state=state, now=10)
    fault = repo/cfg['process_watches'][0]['failure_output']
    assert fault.exists() is not expected
    assert len(events) == (1 if expected else 2)
    assert watch.urgent({'path': terminal}, cfg)


@pytest.mark.parametrize('changes,expected', [({},True),
    ({'checkpoint_validation_required':False},False),({'scientific_admission':True},False),
    ({'cpu_seconds':float('nan')},False),({'cpu_seconds':True},False),({'card':''},False),
    ({'reason':{'reason':'Producer checkpoint quantum','producer':{'status':'running','reason':'wait'}}},False),
    ({'reason':{'reason':'Producer checkpoint quantum','producer':{'status':'yielded','reason':''}}},False)])
def test_week5_producer_pause_is_terminal_but_not_science(context,monkeypatch,changes,expected):
    repo,state,cfg,native=context
    record=dict(at='2026-11-07T18:45:19Z',status='PAUSED',card='native-quantum',cpu_seconds=.2,
        scientific_admission=False,checkpoint_validation_required=True,
        reason=dict(reason='Producer checkpoint quantum',producer=dict(status='yielded',reason='quantum')))
    record.update(changes)
    (repo/'job').mkdir();(repo/'job/PAUSED.json').write_text(json.dumps(record))
    cfg['paths']=['job/PAUSED.json'];cfg['process_watches'][0]['terminal_paths']=['job/PAUSED.json']
    monkeypatch.setattr(watch,'native_identity',lambda pid:None)
    events=watch.scan(cfg,repo=repo,state=state,now=10)
    assert (repo/cfg['process_watches'][0]['failure_output']).exists() is not expected
    assert len(events)==(1 if expected else 2)


@pytest.mark.parametrize('change,expected', [({}, True),
    ({'checkpoint_outputs': {}}, False),
    ({'checkpoint_outputs': {'a': 'bad'}}, False),
    ({'paused_operation': 'running'}, False),
    ({'completed': True}, False), ({'completed': -1}, False),
    ({'completed': 2000}, False), ({'total': None}, False),
    ({'phase': ''}, False), ({'status': 'running'}, False)])
def test_week5_counter_pause_owns_notification(context, monkeypatch, change, expected):
    repo,state,cfg,native=context
    producer=dict(status='yielded',phase='primary_bootstrap',completed=100,total=2000)
    record=dict(at='2026-11-07T20:00:06Z',status='PAUSED',card='MD3-full-pilot-v2',
                cpu_seconds=139.734375,scientific_admission=False,
                checkpoint_validation_required=True,paused_operation='execute',
                checkpoint_outputs={'first-play/standing_bootstrap.npz':'a'*64},
                reason=dict(reason='Producer checkpoint quantum',producer=producer))
    for k,v in change.items():
        (producer if k in producer else record)[k]=v
    (repo/'job').mkdir();(repo/'job/PAUSED.json').write_text(json.dumps(record))
    cfg['paths']=['job/PAUSED.json'];cfg['process_watches'][0]['terminal_paths']=['job/PAUSED.json']
    monkeypatch.setattr(watch,'native_identity',lambda pid:None)
    events=watch.scan(cfg,repo=repo,state=state,now=10)
    assert (repo/cfg['process_watches'][0]['failure_output']).exists() is not expected
    assert len(events)==(1 if expected else 2)


def test_week5_sealed_document_quantum_without_phase_reason(context, monkeypatch):
    repo,state,cfg,native=context
    record=dict(at='2026-11-07T20:00:06Z',status='PAUSED',card='GO2-source-pilot',
                cpu_seconds=10,scientific_admission=False,checkpoint_validation_required=True,
                paused_operation='execute',checkpoint_outputs={'document-parts/000000/SEAL.json':'b'*64},
                reason=dict(reason='Producer checkpoint quantum',producer=dict(status='yielded',
                    source_only=True,documents_complete=10,documents_total=200)))
    (repo/'job').mkdir();(repo/'job/PAUSED.json').write_text(json.dumps(record))
    cfg['paths']=['job/PAUSED.json'];cfg['process_watches'][0]['terminal_paths']=['job/PAUSED.json']
    monkeypatch.setattr(watch,'native_identity',lambda pid:None)
    assert len(watch.scan(cfg,repo=repo,state=state,now=10))==1
    assert not (repo/cfg['process_watches'][0]['failure_output']).exists()


@pytest.mark.parametrize('producer,valid',[
    ({'status':'yielded','phase':'encoding','texts_completed':512,'texts_total':600,'new_chunks':1},True),
    ({'status':'yielded','phase':'V1_directions','bank':0,'annotator_index':1,'new_fits':1,'full_fits':36},True),
    ({'status':'yielded','phase':'clustering_pending','texts_completed':600,'texts_total':600},True),
    ({'status':'yielded','phase':''},False),
    ({'status':'yielded','phase':False},False),
    ({'status':'running','phase':'encoding','texts_completed':512,'texts_total':600},False),
    ({'status':'yielded','phase':'encoding','completed':5},False),
    ({'status':'yielded','phase':'encoding','completed':True,'total':10},False),
    ({'status':'yielded','phase':'encoding','completed':10,'total':10},False),
])
def test_phase_is_not_a_generic_counter_pair(tmp_path,producer,valid):
    record=dict(status='PAUSED',at='2026-11-07T21:23:14Z',card='constructed',cpu_seconds=.5,
        checkpoint_validation_required=True,scientific_admission=False,paused_operation='execute',
        checkpoint_outputs={'chunk.bin':'a'*64},reason={'reason':'Producer checkpoint quantum','producer':producer})
    path=tmp_path/'PAUSED.json';path.write_text(json.dumps(record),encoding='utf8')
    assert watch.valid_json(path) is valid
    path=tmp_path/'PROGRESS.json';path.write_text(json.dumps(record),encoding='utf8')
    assert not watch.valid_json(path)
    record['checkpoint_outputs']={};path=tmp_path/'PAUSED.json';path.write_text(json.dumps(record),encoding='utf8')
    assert not watch.valid_json(path)


@pytest.mark.parametrize('change,valid',[
    ({},True),({'guard_reason':'native precision memory guard requested a sealed-block yield'},True),
    ({'guard_reason':'generic wait'},False),({'identity':{}},False),({'identity_pid':True},False),
    ({'identity_creation_time':float('nan')},False),({'identity_creation_time':0},False),
    ({'identity_executable':''},False),({'identity_command_line':'python'},False),({'identity_command_line':[]},False),
    ({'snapshot':{}},False),({'snapshot':{'commit_headroom_bytes':True,'ram_available_bytes':10}},False),
    ({'snapshot':{'commit_headroom_bytes':-1,'ram_available_bytes':10}},False),
    ({'snapshot':{'memory_query_error':'failed'},'guard_reason':'native precision memory guard requested a sealed-block yield'},True),
    ({'snapshot':{'memory_query_error':''},'guard_reason':'native precision memory guard requested a sealed-block yield'},False),
    ({'snapshot':{'memory_query_error':'failed'}},False),
    ({'checkpoint_outputs':{}},False),({'checkpoint_outputs':{'x':'bad'}},False),
    ({'paused_operation':'running'},False),({'scientific_admission':True},False),
    ({'checkpoint_validation_required':False},False),({'status':'running'},False),({'cpu_seconds':True},False),
])
def test_exact_self_owned_guard_pause(tmp_path,change,valid):
    identity=dict(pid=123,creation_time=100.,executable='python.exe',command_line=['python.exe','fixture'])
    reason=dict(reason='precision verification resource admission refused',identity=identity,
        snapshot={'commit_headroom_bytes':10,'ram_available_bytes':20})
    record=dict(status='PAUSED',at='2026-11-07T21:37:15Z',card='constructed-guard',cpu_seconds=1.,
        scientific_admission=False,checkpoint_validation_required=True,paused_operation='verify',
        checkpoint_outputs={'guard.json':'a'*64},reason=reason)
    for k,v in change.items():
        if k.startswith('identity_'):identity[k.removeprefix('identity_')]=v
        elif k in ['identity','snapshot']:reason[k]=v
        elif k=='guard_reason':reason['reason']=v
        else:record[k]=v
    path=tmp_path/'PAUSED.json';path.write_text(json.dumps(record),encoding='utf8')
    assert watch.valid_json(path) is valid
    path=tmp_path/'PROGRESS.json';path.write_text(json.dumps(record),encoding='utf8')
    assert not watch.valid_json(path)
