"""Deadline/coalescing contracts without live queue delivery or model calls."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import codex_watch as watch
from codex_common import database, get, put

OWNER = "01a0735d-fef3-7ce2-aaee-5f0029701cca"


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    state = repo / ".agent-state"
    with database(state) as db:
        put(db, "owner", OWNER)
        put(db, "owner_phase", "idle")
        put(db, "owner_seen", 100)
        put(db, "last_fallback", 100)
    return repo, state, {"codex": "codex", "paths": []}


def queued(args, **kwargs):
    return subprocess.CompletedProcess(args, 0,
        f"Queued message 01234567-89ab-cdef-0123-456789abcdef for thread {OWNER}.\n", "")


def event(state, name, now=110):
    with database(state) as db:
        return watch.add_event(db, name, "hash", now)


def test_successes_wait_and_arrive_in_one_batch_at_early_deadline(env):
    repo, state, cfg = env
    plan = watch.schedule(900, "Check before estimated finish", expected_seconds=1200, state=state, now=100)
    first = event(state, "first/COMPLETE.json")
    second = event(state, "second/COMPLETE.json", now=115)
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=999) == "scheduled"
    assert len(watch.scan(cfg, state=state, repo=repo, now=1000)) == 1
    sent = []
    def capture(args, **kwargs):
        sent.append(args)
        return queued(args, **kwargs)
    assert watch.deliver(cfg, state=state, repo=repo, runner=capture, now=1000) == "queued"
    assert len(sent) == 1 and first in sent[0][-1] and second in sent[0][-1]
    assert watch.status(state)["wake_plan"]["expected_finish"] == 1300
    assert watch.deliver(cfg, state=state, repo=repo, runner=capture, now=1001) == "awaiting-acknowledgement"
    assert all(e["acknowledged"] is None for e in watch.status(state)["events"])


def test_deadline_is_one_shot_survives_reopen_and_requires_inspection(env):
    repo, state, cfg = env
    watch.schedule(60, "Early liveness check", state=state, now=100)
    assert watch.scan(cfg, state=state, repo=repo, now=159) == []
    ids = watch.scan(cfg, state=state, repo=repo, now=160)
    assert len(ids) == 1
    assert watch.scan(cfg, state=state, repo=repo, now=50000) == []
    with pytest.raises(ValueError, match="acknowledge"):
        watch.schedule(60, "Cannot hide pending deadline", state=state, now=161)
    watch.acknowledge(ids[0], state=state, now=170)
    assert watch.status(state)["wake_plan"] is None
    assert watch.scan(cfg, state=state, repo=repo, now=180) == []


@pytest.mark.parametrize("name", ["FAILED.json", "CHAIN_FAILED.json", "PAUSED.json", "INTERRUPTS.json", "queue/COMPLETE.json"])
def test_urgent_events_bypass_schedule_and_routine_backlog(env, name):
    repo, state, cfg = env
    cfg["urgent_paths"] = ["queue/COMPLETE.json"]
    watch.schedule(7200, "Long job", state=state, now=100)
    for i in range(25):
        event(state, f"routine-{i}/COMPLETE.json", now=101+i)
    alarm = event(state, name, now=130)
    with database(state) as db:
        put(db, "owner_phase", "active")
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=140) == "queued"
    with database(state) as db:
        assert db.execute("SELECT state FROM events WHERE id=?", (alarm,)).fetchone()[0] == "queued"
    assert len([e for e in watch.status(state)["events"] if e["state"] == "pending"]) == 6


def test_active_owner_does_not_receive_redundant_routine_wake(env):
    repo, state, cfg = env
    watch.schedule(60, "Check long worker", state=state, now=100)
    event(state, "work/COMPLETE.json")
    with database(state) as db:
        put(db, "owner_phase", "active")
    assert watch.scan(cfg, state=state, repo=repo, now=160) == []
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=160) == "owner-active"
    with database(state) as db:
        put(db, "owner_phase", "idle")
    assert len(watch.scan(cfg, state=state, repo=repo, now=170)) == 1
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=170) == "queued"


def test_stale_active_owner_does_not_disable_recovery_forever(env):
    repo, state, cfg = env
    watch.schedule(60, "Recover missing owner", state=state, now=100)
    with database(state) as db:
        put(db, "owner_phase", "active")
    assert len(watch.scan(cfg, state=state, repo=repo, now=1001)) == 1
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=1001) == "queued"


def test_default_coalescing_and_ack_reset_prevent_success_bursts(env):
    repo, state, cfg = env
    first = event(state, "first/COMPLETE.json")
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=1899) == "coalescing"
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=1900) == "queued"
    watch.acknowledge(first, state=state, now=1910)
    event(state, "second/COMPLETE.json", now=1920)
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=3709) == "coalescing"
    assert watch.deliver(cfg, state=state, repo=repo, runner=queued, now=3710) == "queued"


def test_recent_attention_prevents_redundant_fixed_fallback(env):
    repo, state, cfg = env
    cfg["fallback_seconds"] = 100
    old = event(state, "done.json")
    watch.acknowledge(old, state=state, now=195)
    assert watch.scan(cfg, state=state, repo=repo, now=200) == []
    assert len(watch.scan(cfg, state=state, repo=repo, now=295)) == 1


def test_foreign_owner_plan_does_not_suppress_current_owner(env):
    repo, state, cfg = env
    watch.schedule(7200, "Other owner", state=state, now=100)
    with database(state) as db:
        put(db, "owner", "another-owner")
    cfg["fallback_seconds"] = 100
    assert len(watch.scan(cfg, state=state, repo=repo, now=200)) == 1


@pytest.mark.parametrize("seconds,expected,reason", [
    (59, None, "short"), (28801, None, "long"), (float('nan'), None, "nan"),
    (float('inf'), None, "inf"), (60, 59, "late"), (60, float('nan'), "nan"),
    (60, None, ""), (60, None, "x"*501),
])
def test_invalid_plan_is_rejected_without_replacing_prior(env, seconds, expected, reason):
    _, state, _ = env
    prior = watch.schedule(60, "Keep this plan", state=state, now=100)
    with pytest.raises(ValueError):
        watch.schedule(seconds, reason, expected_seconds=expected, state=state, now=110)
    assert watch.status(state)["wake_plan"] == prior
