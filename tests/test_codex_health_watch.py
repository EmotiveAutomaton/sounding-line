"""Recurring health inspections: fake clock and transport, no model calls."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import codex_watch as watch
from codex_common import database, put


@pytest.fixture
def env(tmp_path):
    state = tmp_path / '.agent-state'
    with database(state) as db:
        put(db, 'owner', 'owner')
        put(db, 'owner_phase', 'idle')
    config = {'transition_only': True, 'health_interval_seconds': 14400,
              'paths': [], 'codex': 'fake', 'queue_transport': 'native-api'}
    return tmp_path, state, config


def scan(env, now):
    repo, state, config = env
    return watch.scan(config, repo=repo, state=state, now=now)


def test_four_hour_boundary_persists_and_recurs_only_after_health_ack(env):
    _, state, _ = env
    assert scan(env, 100) == []
    assert scan(env, 14499) == []
    ids = scan(env, 14500)
    assert len(ids) == 1
    assert scan(env, 99999) == []
    with database(state) as db:
        unrelated = watch.add_event(db, 'done.json', 'hash', 14501)
    watch.acknowledge(unrelated, state=state, now=14502)
    assert watch.status(state)['health_schedule']['event_id'] == ids[0]
    watch.acknowledge(ids[0], state=state, now=14510)
    assert watch.status(state)['health_schedule']['due'] == 28910
    watch.acknowledge(ids[0], state=state, now=15000)
    assert watch.status(state)['health_schedule']['due'] == 28910
    assert scan(env, 28909) == []
    assert len(scan(env, 28910)) == 1


def test_activity_does_not_reset_due_but_delivery_waits_for_idle(env):
    repo, state, cfg = env
    scan(env, 100)
    with database(state) as db:
        put(db, 'owner_phase', 'active')
        put(db, 'owner_seen', 14500)
        put(db, 'last_acknowledged', 14500)
    assert len(scan(env, 14500)) == 1
    sent = []
    def sender(*args):
        sent.append(args)
        return 'queued-id'
    assert watch.deliver(cfg, repo=repo, state=state, now=14500, native_sender=sender) == 'owner-active'
    watch.schedule(7200, 'Unrelated later ETA', state=state, now=14500)
    with database(state) as db:
        put(db, 'owner_phase', 'idle')
    assert watch.deliver(cfg, repo=repo, state=state, now=14501, native_sender=sender) == 'queued'
    assert len(sent) == 1
    assert 'intentional gear pause' in sent[0][4]
    assert watch.deliver(cfg, repo=repo, state=state, now=14502, native_sender=sender) == 'awaiting-acknowledgement'


def test_cancel_and_unknown_delivery_preserve_single_pending_inspection(env):
    repo, state, cfg = env
    scan(env, 100)
    ids = scan(env, 14500)
    (state / 'watch.cancel').write_text('cancel')
    assert watch.deliver(cfg, repo=repo, state=state, now=14501) == 'cancelled'
    (state / 'watch.cancel').unlink()
    def uncertain(*args):
        raise TimeoutError('unknown acceptance')
    assert watch.deliver(cfg, repo=repo, state=state, now=14502, native_sender=uncertain) == 'unknown'
    assert scan(env, 50000) == []
    assert watch.deliver(cfg, repo=repo, state=state, now=50000, native_sender=uncertain) == 'awaiting-acknowledgement'
    assert watch.status(state)['health_schedule']['event_id'] == ids[0]


def test_failure_still_delivers_immediately_while_owner_active(env):
    repo, state, cfg = env
    scan(env, 100)
    with database(state) as db:
        put(db, 'owner_phase', 'active')
        put(db, 'owner_seen', 101)
        watch.add_event(db, 'FAILED.json', 'hash', 101)
    assert watch.deliver(cfg, repo=repo, state=state, now=101,
                         native_sender=lambda *args: 'queue-id') == 'queued'
    assert watch.status(state)['health_schedule']['due'] == 14500


def test_opt_in_only_and_foreign_owner_does_not_inherit_clock(env):
    _, state, cfg = env
    cfg.pop('health_interval_seconds')
    assert scan(env, 100000) == []
    assert watch.status(state)['health_schedule'] is None
    cfg['health_interval_seconds'] = 14400
    scan(env, 100001)
    with database(state) as db:
        put(db, 'owner', 'new-owner')
    assert scan(env, 120000) == []
    assert watch.status(state)['health_schedule']['owner'] == 'new-owner'
    assert watch.status(state)['health_schedule']['due'] == 134400


@pytest.mark.parametrize('interval', [True, '14400', 0, 59, 28801, float('inf'), float('nan')])
def test_invalid_interval_refused(env, interval):
    _, state, cfg = env
    cfg['health_interval_seconds'] = interval
    with pytest.raises(ValueError, match='Health interval'):
        scan(env, 100)
    assert watch.status(state)['health_schedule'] is None


def test_interval_change_cannot_hide_existing_due_event(env):
    _, state, cfg = env
    scan(env, 100)
    ids = scan(env, 14500)
    cfg['health_interval_seconds'] = 28800
    with pytest.raises(ValueError, match='Reconcile'):
        scan(env, 14501)
    assert watch.status(state)['health_schedule']['event_id'] == ids[0]
