"""Owner-ratified event delivery and resettable four-hour inactivity fallback."""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import codex_watch as watch
from codex_common import database, get, put
from runners.drive import calendar_20261107_week5_event_idle as calendar

OWNER = '01a0735d-fef3-7ce2-aaee-5f0029701cca'


def setup(tmp_path):
    repo = tmp_path / 'repo'
    state = repo / '.agent-state'
    with database(state) as db:
        put(db, 'owner', OWNER)
        put(db, 'owner_phase', 'idle')
        put(db, 'owner_seen', 100)
        put(db, 'last_fallback', 100)
    cfg = dict(codex='codex', paths=[], wake_mode='events_and_idle',
               fallback_seconds=14400, routine_interval_seconds=0, transition_only=False)
    return repo, state, cfg


def test_four_hours_not_one_and_rearms_from_attention(tmp_path):
    repo, state, cfg = setup(tmp_path)
    for at in (3700, 14500 - 1):
        assert watch.scan(cfg, repo=repo, state=state, now=at) == []
    events = watch.scan(cfg, repo=repo, state=state, now=14500)
    assert len(events) == 1
    assert watch.scan(cfg, repo=repo, state=state, now=14501) == []
    watch.acknowledge(events[0], state=state, now=15000)
    assert watch.scan(cfg, repo=repo, state=state, now=29399) == []
    assert len(watch.scan(cfg, repo=repo, state=state, now=29400)) == 1


def test_owner_activity_resets_idle_and_fixed_health_is_disabled(tmp_path):
    repo, state, cfg = setup(tmp_path)
    with database(state) as db:
        put(db, 'owner_seen', 14000)
        put(db, 'health_schedule', dict(owner=OWNER, due=1, interval_seconds=21600))
    assert watch.scan(cfg, repo=repo, state=state, now=14500) == []
    assert watch.scan(cfg, repo=repo, state=state, now=28399) == []
    assert len(watch.scan(cfg, repo=repo, state=state, now=28400)) == 1


def test_terminal_event_delivery_does_not_wait_for_idle(tmp_path):
    repo, state, cfg = setup(tmp_path)
    with database(state) as db:
        event = watch.add_event(db, 'run/COMPLETE.json', 'digest', 101)
    def queued(args, **kwargs):
        return subprocess.CompletedProcess(args, 0,
            f'Queued message 01234567-89ab-cdef-0123-456789abcdef for thread {OWNER}.\n', '')
    assert watch.deliver(cfg, repo=repo, state=state, now=102, runner=queued) == 'queued'
    assert watch.status(state)['events'][0]['id'] == event


def test_calendar_retains_milestones_without_installing_deadlines(tmp_path, monkeypatch):
    repo, state, cfg = setup(tmp_path)
    config = state / 'watch.json'
    config.write_text(json.dumps(cfg), encoding='utf8')
    monkeypatch.setattr(calendar, 'REPO', repo)
    at = calendar.MILESTONES[0][1]
    root = repo / 'calendar'
    assert calendar.tick(root, config, at) == [calendar.MILESTONES[0][0]]
    assert calendar.tick(root, config, at) == []
    assert calendar.ensure_build_wake(at) == 'events_and_four_hour_idle'
    with database(state) as db:
        assert get(db, 'wake_plan') is None
    cfg['transition_only'] = True
    config.write_text(json.dumps(cfg), encoding='utf8')
    calendar.tick(root, config, at)
    assert json.loads(config.read_text())['transition_only'] is False
