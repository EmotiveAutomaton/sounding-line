"""The owner's actual Stop path must recognize build work on both hosts."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import codex_hooks
from codex_common import database, get, put
from grind_coverage import actionable


@pytest.fixture
def roster(tmp_path):
    state = tmp_path / "state"
    with database(state) as db:
        put(db, "owner", "owner")
    deadline = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = dict(owner="owner", active=True, until=deadline, work=[
        dict(host="Spark", card="SM1", state="build"),
        dict(host="local", card="KP1", state="running", evidence="native lease", review_by=deadline)])
    (state / "work-coverage.json").write_text(json.dumps(payload), encoding="utf8")
    return tmp_path, state, payload


def call(roster, session="owner", event="Stop", **extra):
    repo, state, _ = roster
    sent = []
    answer, rc = codex_hooks.handle(dict(cwd=str(repo), session_id=session,
                                         hook_event_name=event, **extra),
                                    repo=repo, state=state, notifier=lambda *args, **kw: sent.append(args))
    assert rc == 0
    return answer, sent


def test_one_healthy_machine_does_not_conceal_the_other_build(roster):
    answer, sent = call(roster)
    assert answer["decision"] == "block" and "SM1: build" in answer["reason"]
    assert not sent
    with database(roster[1]) as db:
        assert get(db, "owner_phase") == "active"
    assert call(roster, stop_hook_active=True) == ({}, [])


def test_empty_queue_with_known_build_work_remains_actionable(roster):
    repo, state, data = roster
    data["work"] = [dict(card="next", host="local", state="build")]
    (state / "work-coverage.json").write_text(json.dumps(data))
    assert "next: build" in call(roster)[0]["reason"]


def test_interrupt_and_builder_exit_are_normal(roster):
    assert call(roster, event="Interrupt") == ({}, [])
    assert call(roster, session="builder") == ({}, [])


def test_evidence_expires_and_held_lanes_do_not_block_independent_work(roster):
    _, state, data = roster
    now = datetime.now(timezone.utc)
    data["work"] = [dict(host="Spark", card="SM2", state="waiting", evidence="archive receipt",
                         review_by=(now + timedelta(hours=3)).isoformat())]
    (state / "work-coverage.json").write_text(json.dumps(data))
    assert actionable(state, "owner", now=now) == []
    assert actionable(state, "owner", now=now + timedelta(hours=4)) == [
        "Spark SM2: verify the expired waiting disposition"]
    assert actionable(state, "owner", now=now + timedelta(days=2)) == []


def test_explicit_pause_and_ordinary_completed_handoffs(roster):
    _, state, data = roster
    data["active"] = False
    (state / "work-coverage.json").write_text(json.dumps(data))
    assert call(roster)[0] == {}
    assert call(roster)[1][0][0] == "done"
