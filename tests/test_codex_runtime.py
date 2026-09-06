"""Known-answer checks for the operating transition, with no real bus or model calls."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import codex_hooks as hooks
import codex_notify as notify
import codex_policy as policy
import codex_setup as setup
import codex_watch as watch
from codex_common import database, get, put, singleton
from codex_common import atomic_json, digest
import design_lint
from lintio import paths_from_payload

OWNER = "01a0735d-fef3-7ce2-aaee-5f0029701cca"


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    state = repo / ".agent-state"
    with database(state) as db:
        put(db, "owner", OWNER)
    return repo, state


def payload(repo, event="PostToolUse", name="apply_patch", command=""):
    return {"cwd": str(repo), "session_id": OWNER, "turn_id": "turn-test",
            "hook_event_name": event, "tool_name": name, "tool_input": {"command": command}}


def test_patch_paths_cover_add_edit_move_delete_and_spaces(tmp_path):
    patch = "*** Begin Patch\n*** Add File: a b.md\n+x\n*** Update File: old.py\n*** Move to: new.py\n@@\n-a\n+b\n*** Delete File: gone.md\n*** End Patch"
    got = paths_from_payload(payload(tmp_path, command=patch))
    assert got == [tmp_path / x for x in ["a b.md", "old.py", "new.py", "gone.md"]]


@pytest.mark.parametrize("bad", [[], {}, {"tool_input": {}}, {"tool_input": {"command": "echo ok"}},
    {"tool_input": {"command": "*** Begin Patch\n*** Add File: x"}}])
def test_unknown_edit_shapes_cannot_pass(bad):
    with pytest.raises(ValueError):
        paths_from_payload(bad)


def test_claude_payload_resolves_cwd(tmp_path):
    assert paths_from_payload({"cwd": str(tmp_path), "tool_input": {"file_path": "a.py"}}) == [tmp_path / "a.py"]


def test_real_theory_linter_bad_then_repaired(env):
    repo, state = env
    path = repo / "docs/theory/fixture.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Fixture\n\n| # | hypothesis | status |\n|---|---|---|\n| 1 | A | OPEN |\n", encoding="utf-8")
    data = payload(repo, command="*** Begin Patch\n*** Update File: docs/theory/fixture.md\n@@\n-a\n+b\n*** End Patch")
    result, rc = hooks.handle(data, repo=repo, state=state)
    assert rc == 0 and result["decision"] == "block"
    path.write_text(path.read_text() + "\n**What the table says.** The claim remains open. Confidence: untested, logic only.\n", encoding="utf-8")
    assert hooks.handle(data, repo=repo, state=state) == ({}, 0)


def test_actual_design_linter_rejects_undeclared_gate(env):
    repo, state = env
    path = repo / "runners/fixture.py"
    path.parent.mkdir()
    path.write_text('"""An undeclared VOID gate."""\n')
    data = payload(repo, command="*** Begin Patch\n*** Add File: runners/fixture.py\n+x\n*** End Patch")
    result, _ = hooks.handle(data, repo=repo, state=state)
    assert result["decision"] == "block" and "DESIGN CHECK" in result["reason"]


def test_shell_edit_is_checked_even_without_patch_event(env, monkeypatch):
    repo, state = env
    path = repo / "docs/theory/shell.md"
    path.parent.mkdir(parents=True)
    path.write_text("# An em dash\n\nThis has an em dash — in prose.\n", encoding="utf-8")
    monkeypatch.setattr(design_lint, "_changed_paths", lambda: [path])
    result, _ = hooks.handle(payload(repo, name="Bash", command="python edit.py"), repo=repo, state=state)
    assert result["decision"] == "block"


def test_git_failure_is_not_clean(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 128, "", "dubious ownership"))
    with pytest.raises(RuntimeError, match="nothing certified"):
        design_lint._changed_paths()


def test_git_nul_paths_preserve_spaces(monkeypatch, tmp_path):
    monkeypatch.setattr(design_lint, "repo_root", lambda: tmp_path)
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "docs/theory/a b.md\0", "")
    monkeypatch.setattr(subprocess, "run", run)
    assert design_lint._changed_paths() == [tmp_path / "docs/theory/a b.md"]
    assert all("-z" in c and f"safe.directory={tmp_path.as_posix()}" in c for c in calls)


@pytest.mark.parametrize("command", ["shutdown /s", "restart-computer", "rm -rf /", "rm -rf E:/", "format C:", "diskpart"])
def test_catastrophic_denies(command):
    assert policy.classify(command)[0] == "deny"


@pytest.mark.parametrize("command", ["python -c 'do_anything()'", "python script.py", "git push", "git reset --hard HEAD", "rg --pre evil needle .", "curl https://example.com", "Get-Content .env", "Get-Content ~/.codex/auth.json", "cat bus.conf", "rm -rf results", "pwsh -c script", "ls $(rm -rf x)", "Get-Content x; Stop-Process -Id 1", "node -e anything", "git -c core.sshCommand=evil fetch"])
def test_dynamic_and_mutating_commands_use_native_permission_flow(command):
    assert policy.classify(command)[0] != "allow"


@pytest.mark.parametrize("command", ["git status --short", "rg -n hypothesis docs", "Get-Content README.md", "Get-Process python"])
def test_static_reads_are_allowed_inside_sandbox(command):
    assert policy.classify(command)[0] == "allow"


def test_native_escalation_cannot_be_approved_by_hook(tmp_path):
    data = payload(tmp_path, "PermissionRequest", "Bash", "git status --short")
    assert policy.decision(data)[0] == "default"
    data["hook_event_name"] = "PreToolUse"
    data["tool_input"]["sandbox_permissions"] = "require_escalated"
    assert policy.decision(data)[0] == "default"


def test_notifications_use_codex_events_and_no_transcript_read(env):
    repo, state = env
    calls = []
    def send(kind, data, **kwargs):
        calls.append((kind, data.get("last_assistant_message"))); return "sent"
    data = payload(repo, "Stop")
    data["last_assistant_message"] = "The transition passed."
    data["transcript_path"] = str(repo / "must-not-read.jsonl")
    hooks.handle(data, repo=repo, state=state, notifier=send)
    hooks.handle(payload(repo, "PermissionRequest", "Bash", "python script.py"), repo=repo, state=state, notifier=send)
    hooks.handle(payload(repo, "PreToolUse", "request_user_input_async"), repo=repo, state=state, notifier=send)
    assert [x[0] for x in calls] == ["done", "input"]
    assert calls[0][1] == "The transition passed."


def test_session_reload_and_owner_are_preserved(env):
    repo, state = env
    data = payload(repo, "PostCompact")
    result, _ = hooks.handle(data, repo=repo, state=state)
    assert "docs/theory" in result["hookSpecificOutput"]["additionalContext"]
    data["hook_event_name"] = "SessionStart"
    data["session_id"] = "another-session"
    hooks.handle(data, repo=repo, state=state)
    with database(state) as db:
        assert get(db, "owner") == OWNER


def test_other_projects_are_not_notified(env):
    repo, state = env
    data = payload(repo, "Stop")
    data["cwd"] = str(repo.parent / "unrelated")
    def fail(*a, **kw):
        pytest.fail("Must not notify another project")
    assert hooks.handle(data, repo=repo, state=state, notifier=fail) == ({}, 0)


def test_ntfy_ack_priority_snippet_and_duplicate(env):
    repo, state = env
    requests = []
    def opener(req, **kwargs):
        requests.append(req)
        if "/agents/json" in req.full_url:
            return io.BytesIO(b'{"event":"message","message":"done: SoundingLine","time":200}\n')
        if "/acks/json" in req.full_url:
            return io.BytesIO(b'{"event":"message","message":"ack","time":100}\n')
        return io.BytesIO(b'{}')
    data = payload(repo, "Stop")
    data["last_assistant_message"] = "Passed the guards. More detail."
    cfg = {"BASE": "https://bus.invalid", "TOKEN": "fixture-token"}
    assert notify.send("done", data, state=state, config=cfg, opener=opener) == "sent"
    assert requests[-1].get_header("Priority") == "min"
    assert requests[-1].get_header("Title") == "Codex"
    assert requests[-1].data.decode() == "done: SoundingLine: Passed the guards."
    assert notify.send("done", data, state=state, config=cfg, opener=opener) == "duplicate"
    assert len(requests) == 3


def test_ntfy_failure_is_visible_without_leaking_secrets(env):
    repo, state = env
    def broken(*a, **kw):
        raise OSError("TOKEN=do-not-log-me")
    assert notify.send("input", payload(repo), state=state,
        config={"BASE": "https://bus.invalid"}, opener=broken) == "failed_or_unknown"
    with database(state) as db:
        row = dict(db.execute("SELECT * FROM notifications").fetchone())
        assert row["error"] == "OSError" and "do-not-log-me" not in str(row)


def make_landing(env):
    repo, state = env
    config = {"paths": ["verdict.json"], "codex": "codex"}
    watch.scan(config, repo=repo, state=state, baseline=True, now=0)
    (repo / "verdict.json").write_text('{"complete":true}')
    events = watch.scan(config, repo=repo, state=state, now=1)
    return config, events


def test_new_final_produce_survives_reconnect_and_is_delivered_once(env):
    repo, state = env
    config, events = make_landing(env)
    calls = []
    def queue(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, f"Queued message 01234567-89ab-cdef-0123-456789abcdef for thread {OWNER}.\n", "")
    assert watch.deliver(config, repo=repo, state=state, runner=queue, now=2) == "queued"
    assert watch.deliver(config, repo=repo, state=state, runner=queue, now=3) == "awaiting-acknowledgement"
    assert watch.scan(config, repo=repo, state=state, now=4) == []
    assert len(calls) == 1 and calls[0][3] == OWNER
    watch.acknowledge(events[0], state=state)
    assert watch.status(state)["events"] == []


def test_partial_json_waits_for_valid_completion(env):
    repo, state = env
    config = {"paths": ["verdict.json"]}
    watch.scan(config, repo=repo, state=state, baseline=True, now=0)
    (repo / "verdict.json").write_text('{"partial":')
    assert watch.scan(config, repo=repo, state=state, now=1) == []
    (repo / "verdict.json").write_text('{"complete":true}')
    assert len(watch.scan(config, repo=repo, state=state, now=2)) == 1


def test_queue_timeout_is_not_retried_blindly(env):
    repo, state = env
    config, _ = make_landing(env)
    def timeout(*a, **kw):
        raise subprocess.TimeoutExpired("codex", 45)
    assert watch.deliver(config, repo=repo, state=state, runner=timeout, now=2) == "unknown"
    assert watch.deliver(config, repo=repo, state=state, runner=timeout, now=10000) == "awaiting-acknowledgement"


def test_queue_zero_exit_without_receipt_is_not_success(env):
    repo, state = env
    config, _ = make_landing(env)
    assert watch.deliver(config, repo=repo, state=state,
        runner=lambda *a, **kw: subprocess.CompletedProcess(a, 0, "", ""), now=2) == "unknown"


def test_failed_queue_delivery_retries_then_stops(env):
    repo, state = env
    config, events = make_landing(env)
    def failure(*a, **kw):
        return subprocess.CompletedProcess(a, 1, "", "disconnected")
    for n in range(5):
        watch.deliver(config, repo=repo, state=state, runner=failure, now=10000 * (n+1))
    with database(state) as db:
        row = db.execute("SELECT * FROM events WHERE id=?", (events[0],)).fetchone()
        assert row["state"] == "failed" and row["attempts"] == 5


def test_cancel_prevents_queued_action(env):
    repo, state = env
    config, _ = make_landing(env)
    (state / "watch.cancel").touch()
    def fail(*a, **kw):
        pytest.fail("Cancelled watcher must not deliver")
    assert watch.deliver(config, repo=repo, state=state, runner=fail) == "cancelled"


def test_deadline_wakes_when_no_file_changes(env):
    repo, state = env
    cfg = {"fallback_seconds": 20}
    watch.scan(cfg, repo=repo, state=state, baseline=True, now=0)
    assert watch.scan(cfg, repo=repo, state=state, now=19) == []
    assert len(watch.scan(cfg, repo=repo, state=state, now=20)) == 1


def test_watcher_cannot_escape_repository(env):
    repo, state = env
    with pytest.raises(ValueError, match="outside"):
        list(watch.candidates({"paths": ["../foreign/verdict.json"]}, repo))


def test_second_watcher_cannot_acquire_live_lock(env):
    _, state = env
    with singleton(state / "watcher.lock"):
        with pytest.raises(OSError):
            with singleton(state / "watcher.lock"):
                pytest.fail("Two watchers acquired the same lock")


def test_resume_waits_for_the_old_watcher_to_release_ownership(env):
    _, state = env
    with singleton(state / "watcher.lock"):
        with pytest.raises(TimeoutError, match="still holds"):
            watch.wait_stopped(state, timeout=0)
    watch.wait_stopped(state, timeout=0)


def test_landings_during_migration_are_not_baselined_away(env):
    repo, state = env
    path = repo / "verdict.json"
    path.write_text('{"complete":true}')
    config = {"paths": ["verdict.json"]}
    watch.scan(config, repo=repo, state=state, baseline=True, baseline_since=0)
    assert len(watch.scan(config, repo=repo, state=state)) == 1


def test_queue_inventory_includes_composed_paths_and_never_runs_main(env):
    repo, state = env
    source = repo / "runners/run_queue.py"
    source.parent.mkdir()
    source.write_text('prefix="results/"\nSTAGES=[{"name":"a","produces":prefix+"done.json"}]\n'
                      'if __name__ == "__main__":\n    raise RuntimeError("queue ran")\n')
    assert watch.register_queue(repo=repo, state=state) == 1
    config = {"queue_inventory": True}
    assert list(watch.candidates(config, repo)) == [repo / "results/done.json"]
    source.write_text(source.read_text() + "# new stage definition\n")
    with pytest.raises(ValueError, match="Queue source changed"):
        list(watch.candidates(config, repo))


def installation(env, monkeypatch):
    repo, state = env
    monkeypatch.setattr(setup, "REPO", repo)
    monkeypatch.setattr(setup, "STATE", state)
    primary = repo.parent / ".codex/hooks.json"
    unrelated = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "unrelated-notifier"}]}]}}
    atomic_json(primary, unrelated)
    backup = state / "backup"
    backup.mkdir()
    (backup / "0").write_bytes(primary.read_bytes())
    atomic_json(state / "install-receipt.json", {"backup": str(backup), "files": [
        {"path": str(primary), "before": str(backup / "0"), "after_sha256": digest(primary)}]})
    atomic_json(state / "install-plan.json", {"sources": {}, "workspace": str(repo.parent),
        "hooks_path": str(primary), "hooks": setup.hook_config(repo)})
    return repo, state, primary, unrelated


def test_refresh_covers_both_roots_and_preserves_unrelated_hooks(env, monkeypatch):
    repo, state, primary, _ = installation(env, monkeypatch)
    setup.refresh()
    first = primary.read_bytes()
    setup.refresh()
    assert primary.read_bytes() == first
    groups = json.loads(first)["hooks"]["Stop"]
    assert len(groups) == 2 and groups[0]["hooks"][0]["command"] == "unrelated-notifier"
    assert (repo / ".codex/hooks.json").exists()
    stub = (repo.parent / ".agents/skills/grind/SKILL.md").read_text()
    assert f"{repo.name}/.agents/skills/grind/SKILL.md" in stub


def test_rollback_restores_exact_prior_bytes_and_cancels_watcher(env, monkeypatch):
    repo, state, primary, _ = installation(env, monkeypatch)
    before = primary.read_bytes()
    setup.refresh()
    setup.rollback()
    assert primary.read_bytes() == before
    assert not (repo / ".codex/hooks.json").exists()
    assert not (repo.parent / ".agents/skills/grind/SKILL.md").exists()
    assert (state / "watch.cancel").exists()


def test_rollback_refuses_to_overwrite_later_user_edits(env, monkeypatch):
    repo, state, primary, _ = installation(env, monkeypatch)
    setup.refresh()
    primary.write_text('{"user":"changed this"}')
    with pytest.raises(ValueError, match="changed"):
        setup.rollback()
    assert json.loads(primary.read_text())["user"] == "changed this"


def test_native_wake_receipt_is_separate_from_completed_write_through(env):
    repo, state = env
    _, ids = make_landing(env)
    with database(state) as db:
        db.execute("UPDATE events SET state='queued'")
    data = payload(repo, "UserPromptSubmit")
    data["prompt"] = "Sounding Line operational wake.\n- " + ids[0] + ": verdict.json"
    hooks.handle(data, repo=repo, state=state)
    event = watch.status(state)["events"][0]
    assert event["delivered_at"] is not None
    assert event["acknowledged"] is None and event["state"] == "queued"
