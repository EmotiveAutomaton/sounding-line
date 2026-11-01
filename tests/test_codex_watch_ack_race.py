"""Exercise ACK/delivery interleavings in disposable outboxes; never send a message."""
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import codex_watch as watch
from codex_common import database, get, put


@pytest.fixture
def env(tmp_path):
    state = tmp_path / '.agent-state'
    with database(state) as db:
        put(db, 'owner', 'owner')
        put(db, 'owner_phase', 'idle')
        event = watch.add_event(db, watch.HEALTH_PATH, 'digest', 10)
        put(db, 'health_schedule', dict(id='health', owner='owner', event_id=event,
            interval_seconds=21600, last_inspected=0, due=10))
    return tmp_path, state, {'codex': 'fake', 'transition_only': True}, event


def event_row(state, event):
    with database(state) as db:
        return dict(db.execute('SELECT * FROM events WHERE id=?', (event,)).fetchone())


@pytest.mark.parametrize('transport', ['queued', 'pending', 'unknown', 'exhausted', 'native-unknown'])
def test_ack_during_send_survives_transport_settlement(env, transport):
    repo, state, config, event = env
    if transport == 'exhausted':
        with database(state) as db:
            db.execute('UPDATE events SET attempts=4 WHERE id=?', (event,))

    def acknowledge_then_return(*args, **kwargs):
        watch.acknowledge(event, state=state, now=101)
        if transport == 'native-unknown':
            raise TimeoutError('acceptance uncertain')
        return SimpleNamespace(returncode=1 if transport in ('pending', 'exhausted') else 0,
            stdout='Queued message abc-def for thread owner' if transport == 'queued' else '')

    # Use a valid hexadecimal thread id for the CLI receipt parser.
    if transport == 'queued':
        with database(state) as db:
            put(db, 'owner', 'face')
            health = get(db, 'health_schedule'); health['owner'] = 'face'; put(db, 'health_schedule', health)
        def queued(*args, **kwargs):
            watch.acknowledge(event, state=state, now=101)
            return SimpleNamespace(returncode=0, stdout='Queued message abc-def for thread face')
        runner = queued
    else:
        runner = acknowledge_then_return
    if transport == 'native-unknown':
        config['queue_transport'] = 'native-api'
    outcome = watch.deliver(config, repo=repo, state=state, now=100,
        runner=runner, native_sender=acknowledge_then_return)
    assert outcome == ('unknown' if transport in ('unknown', 'native-unknown') else
                       'pending' if transport == 'exhausted' else transport)
    row = event_row(state, event)
    assert row['acknowledged'] == 101
    assert row['state'] == 'acknowledged'
    assert row['queue_id'] == ('abc-def' if transport == 'queued' else None)
    assert (row['error'] is None) == (transport == 'queued')
    health = watch.status(state)['health_schedule']
    assert health['due'] == 21701 and health['last_inspected'] == 101
    watch.acknowledge(event, state=state, now=200)
    assert watch.status(state)['health_schedule'] == health
    assert watch.status(state)['events'] == []
    assert watch.deliver(config, repo=repo, state=state, now=1000,
                         runner=lambda *a, **k: pytest.fail('duplicate send')) == 'nothing-pending'


def test_ack_during_cancel_check_is_not_reset_to_pending(env, monkeypatch):
    repo, state, config, event = env
    original = Path.exists
    checks = 0
    def exists(path):
        nonlocal checks
        if path == state / 'watch.cancel':
            checks += 1
            if checks == 2:
                watch.acknowledge(event, state=state, now=101)
                return True
        return original(path)
    monkeypatch.setattr(Path, 'exists', exists)
    assert watch.deliver(config, repo=repo, state=state, now=100,
        runner=lambda *a, **k: pytest.fail('cancelled send')) == 'cancelled'
    assert event_row(state, event)['state'] == 'acknowledged'
    assert event_row(state, event)['acknowledged'] == 101
    assert watch.status(state)['health_schedule']['due'] == 21701


def test_legacy_acknowledged_pending_row_is_never_sent_or_rewritten(env):
    repo, state, config, event = env
    watch.acknowledge(event, state=state, now=101)
    with database(state) as db:
        db.execute("UPDATE events SET state='pending' WHERE id=?", (event,))
    before = event_row(state, event)
    assert watch.deliver(config, repo=repo, state=state, now=1000,
        runner=lambda *a, **k: pytest.fail('legacy acknowledged row resent')) == 'nothing-pending'
    assert event_row(state, event) == before


def test_restart_reconciles_only_unacknowledged_inflight_rows(env):
    repo, state, config, event = env
    watch.acknowledge(event, state=state, now=101)
    with database(state) as db:
        db.execute("UPDATE events SET state='sending' WHERE id=?", (event,))
        other = watch.add_event(db, 'FAILED.json', 'other', 102)
        db.execute("UPDATE events SET state='sending' WHERE id=?", (other,))
    before = event_row(state, event)
    (state / 'watch.cancel').write_text('fixture stop')
    watch.run(config, state=state, repo=repo)
    assert event_row(state, event) == before
    assert event_row(state, other)['state'] == 'unknown'
    assert watch.status(state)['health_schedule']['due'] == 21701


def test_unacknowledged_failure_still_exhausts_retries(env):
    repo, state, config, event = env
    with database(state) as db:
        db.execute('UPDATE events SET attempts=4 WHERE id=?', (event,))
    assert watch.deliver(config, repo=repo, state=state, now=100,
        runner=lambda *a, **k: SimpleNamespace(returncode=1, stdout='')) == 'pending'
    row = event_row(state, event)
    assert row['state'] == 'failed' and row['attempts'] == 5 and row['acknowledged'] is None
    assert watch.status(state)['health_schedule']['event_id'] == event
