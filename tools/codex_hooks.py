"""Lifecycle dispatcher for Codex's actual hook payloads; never imports research runners."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import sys
import time

from codex_common import REPO, STATE, audit, database, get, put
from codex_policy import decision
from lintio import paths_from_payload


def in_workspace(cwd, repo=REPO):
    path = Path(cwd).resolve()
    return path == repo.parent or path.is_relative_to(repo)


def context(repo=REPO, state=STATE):
    with database(state) as db:
        pending = [dict(r) for r in db.execute(
            "SELECT id,path,state FROM events WHERE acknowledged IS NULL ORDER BY created")]
        owner = get(db, "owner")
    theory = sorted((repo / "docs/theory").rglob("*.md"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    return (f"Repository: {repo}. Read AGENTS.md, FINDINGS.md, docs/STATE.md and TODO.md. "
        "Complete the initial docs/theory read newest first before research or scientific interpretation; "
        "it may span context windows. After compaction, resume recorded unread portions instead of "
        "restarting; hashes, summaries and truncated output do not prove reading. Reload shared/project "
        "instructions, current state/findings and the theory index; before research, literature or theory "
        "edits reread relevant sections, afterwords and corrections under AGENTS.md. "
        "Read each folder README again before edits. Current ratified stage limits and its "
        "final-packet reporting policy override old general queue defaults. Never infer a "
        "new gear or paid-compute authorization from a wake. Load .agents/skills/grind/SKILL.md "
        "for queue duties; a result is not landed until its full write-through is done. "
        "Do not report per-artifact scores from an unfinished cell. For operational health "
        "and recovery read docs/CODEX_OPERATIONS.md. This reminder does not replace reading.\n"
        f"Owner: {owner}. Pending delivery/landing events: {json.dumps(pending)}.\n"
        "Theory read order: " + ", ".join(str(p.relative_to(repo)) for p in theory))


def lint(payload, repo=REPO):
    import design_lint
    import lint_hook
    name = payload.get("tool_name", "")
    if name in {"Bash", "PowerShell", "exec_command", "shell", "shell_command"}:
        paths = design_lint._changed_paths()
    else:
        paths = paths_from_payload(payload)
    # Do not silently certify a deleted locked artifact.
    import verify_locks
    locked = {verify_locks.current_path(k).resolve() for k in verify_locks.LOCKS}
    missing = [p for p in paths if p in locked and not p.exists()]
    if missing:
        raise ValueError("Locked artifacts deleted: " + ", ".join(map(str, missing)))
    output = io.StringIO()
    with contextlib.redirect_stderr(output):
        rc = lint_hook._dispatch(paths)
    return rc, output.getvalue()


def handle(payload, *, repo=REPO, state=STATE, notifier=None):
    if not isinstance(payload, dict) or not isinstance(payload.get("hook_event_name"), str):
        raise ValueError("hook_event_name is required")
    if not payload.get("cwd") or not in_workspace(payload["cwd"], repo):
        return {}, 0
    event = payload["hook_event_name"]
    session = payload.get("session_id")
    with database(state) as db:
        audit(db, "hook", {"event": event, "session": session,
                           "tool": payload.get("tool_name"), "turn": payload.get("turn_id")})
        owner = get(db, "owner")
        if owner == session:
            if event in {"SessionStart", "UserPromptSubmit", "PreToolUse"}:
                put(db, "owner_phase", "active")
            elif event == "Stop":
                put(db, "owner_phase", "idle")
            elif event in {"SessionEnd", "Interrupt"}:
                put(db, "owner_phase", "disconnected" if event == "SessionEnd" else "interrupted")
            put(db, "owner_seen", time.time())
            if event == "UserPromptSubmit":
                submitted = payload.get("prompt", "")
                if isinstance(submitted, str) and submitted.startswith("Sounding Line operational wake."):
                    for row in db.execute("SELECT id FROM events WHERE state='queued'").fetchall():
                        if row["id"] in submitted:
                            db.execute("INSERT OR IGNORE INTO deliveries VALUES (?,?,?)",
                                       (row["id"], time.time(), session))
                if isinstance(submitted, str) and "SOUNDINGLINE_WAKE_PROBE_20260905" in submitted:
                    put(db, "wake_probe_received", {"at": time.time(), "session": session})

    if event in {"SessionStart", "PostCompact", "UserPromptSubmit"}:
        return {"hookSpecificOutput": {"hookEventName": event,
                                      "additionalContext": context(repo, state)}}, 0

    name = payload.get("tool_name", "")
    if event == "PreToolUse" and name in {"apply_patch", "Edit", "Write", "MultiEdit"}:
        import verify_locks
        paths = paths_from_payload(payload)
        locked = {verify_locks.current_path(k).resolve() for k in verify_locks.LOCKS}
        locked.add((repo / "soundingline/locks.py").resolve())
        if any(p in locked or p.is_relative_to(repo / "prereg") for p in paths):
            return {"hookSpecificOutput": {"hookEventName": event,
                "permissionDecision": "deny", "permissionDecisionReason":
                "AGENTS.md freezes these research files. Preserve the original; record deviations separately."}}, 0

    if event in {"PreToolUse", "PermissionRequest"} and name in {
            "Bash", "PowerShell", "exec_command", "shell", "shell_command"}:
        result, reason = decision(payload)
        if result != "default":
            body = {"hookEventName": event}
            if event == "PermissionRequest":
                body["decision"] = {"behavior": result, "message": reason}
            else:
                body.update(permissionDecision=result, permissionDecisionReason=reason)
            return {"hookSpecificOutput": body}, 0

    if event == "PostToolUse" and name in {"Bash", "PowerShell", "exec_command", "shell",
                                           "shell_command", "apply_patch", "Edit", "Write", "MultiEdit"}:
        try:
            rc, message = lint(payload, repo)
        except (ValueError, TypeError, RuntimeError, OSError) as exc:
            rc, message = 3, f"Codex lint hook checked nothing: {exc}. Repair this invocation in this turn."
        if rc:
            return {"decision": "block", "reason": message}, 0

    kind = None
    if event == "Stop" and not payload.get("stop_hook_active"):
        kind = "done"
    # Automatic review candidates are not human-input events.
    elif (event == "PreToolUse" and
          name.rsplit("__", 1)[-1].rsplit(".", 1)[-1] in
          {"request_user_input", "request_user_input_async"}):
        kind = "input"
    if kind and (not owner or owner == session):
        if notifier is None:
            from codex_notify import send
            notifier = send
        outcome = notifier(kind, payload, state=state)
        with database(state) as db:
            audit(db, "notification", {"kind": kind, "outcome": outcome})
    return {}, 0


def main():
    try:
        payload = json.load(sys.stdin)
        result, rc = handle(payload)
        if result:
            print(json.dumps(result, ensure_ascii=True))
        return rc
    except Exception as exc:
        # Hook failures are never represented as an empty successful validation.
        print(f"Sounding Line hook failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
