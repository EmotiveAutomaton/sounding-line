"""Actual finite queue rehearsal without model calls."""
import json
from pathlib import Path
import pytest
from runners.next_round import repair_queue as q
from runners.stage14.common import freeze, filehash, read


def fixture_plan(tmp_path):
    ids = ['producer', 'consumer']
    for i in ids:
        freeze(tmp_path / 'cards' / (i + '.json'), dict(id=i, requires=[] if i == 'producer' else ['producer'],
            gates=[], resource='cpu', source_pins={}, input_pins={}, wall_seconds=60))
    plan = dict(cards=ids, imported_dependencies=[], pins={}, reporting='2099-01-01T00:00:00+00:00',
                card_pins={i: filehash(tmp_path / 'cards' / (i + '.json')) for i in ids})
    freeze(tmp_path / 'PLAN.json', plan)
    return tmp_path / 'PLAN.json'


def fake_child(command, **kwargs):
    cp = Path(command[command.index('--card') + 1])
    raw = cp.parent.parent
    card = read(cp)
    out = raw / 'jobs' / card['id']
    freeze(out / 'answer.json', {'constructed': True})
    freeze(out / 'COMPLETE.json', dict(status='complete', card_sha256=filehash(cp),
          outputs={'answer.json': filehash(out / 'answer.json')}))
    class Child:
        pid = 999
        returncode = 0
        def poll(self): return 0
    return Child()


def test_actual_queue_and_no_duplicate_dispatch(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path)
    monkeypatch.setattr(q, 'native_identity', lambda *args: {'pid': 999, 'constructed': True})
    monkeypatch.setattr(q, 'limits', lambda: None)
    calls = []
    def spawn(*args, **kwargs):
        calls.append(args[0])
        return fake_child(*args, **kwargs)
    q.run(plan, sleep=lambda _: None, popen=spawn, ready=lambda c: (True, 'fixture', {}))
    assert read(tmp_path / 'EXIT.json')['states'] == {'producer': 'complete', 'consumer': 'complete'}
    assert len(calls) == 2
    with pytest.raises(FileExistsError):
        q.run(plan, popen=spawn)
    assert len(calls) == 2


def test_dependency_verdict_and_deadline_are_enforced(tmp_path):
    card = {'requires': ['a'], 'gates': ['a'], 'wall_seconds': 20}
    assert q.decision(card, {'a': 'failed'}, tmp_path, 100)[0] == 'blocked'
    assert q.decision(card, {}, tmp_path, 100)[0] == 'waiting'
    freeze(tmp_path / 'jobs/a/ADMISSION.json', {'admitted': False})
    assert q.decision(card, {'a': 'complete'}, tmp_path, 100)[0] == 'blocked'
    card['gates'] = []
    assert q.decision(card, {'a': 'complete'}, tmp_path, 19)[0] == 'held'
    assert q.decision(card, {'a': 'complete'}, tmp_path, 20)[0] == 'eligible'
    assert q.decision(card, {'a': 'complete'}, tmp_path, 100, True)[0] == 'held'


def test_actual_pause_never_spawns(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path)
    freeze(tmp_path / 'PAUSE.json', {'reason': 'fixture'})
    monkeypatch.setattr(q, 'native_identity', lambda *a: {'pid': 999})
    monkeypatch.setattr(q, 'limits', lambda: None)
    def refuse(*a, **kw): raise AssertionError('unexpected dispatch')
    q.run(plan, popen=refuse)
    assert read(tmp_path / 'EXIT.json')['disposition'] == 'held'


def test_card_drift_refuses_before_dispatch(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path)
    p = tmp_path / 'cards/producer.json'
    p.write_text(json.dumps(dict(read(p), wall_seconds=300)), encoding='utf8')
    monkeypatch.setattr(q, 'native_identity', lambda *a: {'pid': 999})
    monkeypatch.setattr(q, 'limits', lambda: None)
    with pytest.raises(ValueError, match='binding mismatch'):
        q.run(plan)


def test_actual_failed_producer_blocks_only_its_consumer(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path)
    monkeypatch.setattr(q, 'native_identity', lambda *a: {'pid': 999})
    monkeypatch.setattr(q, 'limits', lambda: None)
    calls = []
    def spawn(command, **kwargs):
        calls.append(command)
        class Child:
            pid = 999
            returncode = 1
            def poll(self): return 1
        return Child()
    q.run(plan, sleep=lambda _: None, popen=spawn, ready=lambda c: (True, 'fixture', {}))
    assert len(calls) == 1
    assert read(tmp_path / 'EXIT.json')['states'] == {'producer': 'failed', 'consumer': 'blocked'}
