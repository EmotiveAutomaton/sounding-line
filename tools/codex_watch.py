"""Durable final-produce watcher. It queues work to ONE existing Codex thread.

No research execution, model calls, stage creation, or scientific interpretation.
Queue acceptance and completed write-through are separate states. A failed or
ambiguous send remains visible; a cancel file is checked just before every send.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

from codex_common import REPO, STATE, atomic_json, database, digest, get, put, singleton


def candidates(config, repo=REPO):
    paths = {repo / p for p in config.get("paths", [])}
    inventory_path = repo / ".agent-state/queue-produces.json"
    if config.get("queue_inventory"):
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        if digest(repo / "runners/run_queue.py") != inventory["source_sha256"]:
            raise ValueError("Queue source changed; run codex_watch.py register-queue after review")
        paths.update(repo / name for name in inventory["paths"])
    for name in config.get("manifests", []):
        manifest = repo / name
        if not manifest.exists():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for row in data.values():
            if isinstance(row, dict) and row.get("produces"):
                p = Path(row["produces"])
                paths.add(p if p.is_absolute() else repo / p)
    for path in paths:
        path = path.resolve()
        if not path.is_relative_to(repo.resolve()):
            raise ValueError(f"Watch path outside this repository: {path}")
        yield path


def add_event(db, path, content_hash, now):
    event_id = hashlib.sha256((path + "\0" + content_hash).encode()).hexdigest()[:24]
    db.execute("INSERT OR IGNORE INTO events (id,path,digest,created) VALUES (?,?,?,?)",
               (event_id, path, content_hash, now))
    return event_id


def scan(config, *, repo=REPO, state=STATE, baseline=False, now=None, baseline_since=None):
    now = time.time() if now is None else now
    files = list(candidates(config, repo))
    changes = []
    with database(state) as db:
        db.execute("BEGIN IMMEDIATE")
        for path in files:
            name = path.relative_to(repo.resolve()).as_posix()
            stat = path.stat() if path.exists() else None
            stamp = (stat.st_size, stat.st_mtime_ns) if stat else (None, None)
            prior_stat = db.execute("SELECT size,mtime_ns FROM file_stats WHERE path=?", (name,)).fetchone()
            if not baseline and prior_stat and tuple(prior_stat) == stamp:
                continue
            current = digest(path)
            # A migration may span a running experiment. New landings during the
            # cutover must not be marked as already processed by initial baselining.
            if baseline and baseline_since is not None and current and path.stat().st_mtime > baseline_since:
                db.execute("INSERT OR REPLACE INTO observed VALUES (?,NULL)", (name,))
                continue
            old = db.execute("SELECT digest FROM observed WHERE path=?", (name,)).fetchone()
            if current and not baseline and (old is None or current != old[0]):
                # Refuse partially written JSON; try it next poll without moving the baseline.
                if path.suffix == ".json":
                    try:
                        json.loads(path.read_text(encoding="utf-8"))
                    except (ValueError, OSError):
                        continue
                changes.append(add_event(db, name, current, now))
            # Absence is retained: removing and recreating the same bytes needs inspection.
            db.execute("INSERT OR REPLACE INTO observed VALUES (?,?)", (name, current))
            db.execute("INSERT OR REPLACE INTO file_stats VALUES (?,?,?)", (name, *stamp))
        if baseline:
            put(db, "baseline_at", now)
            put(db, "last_fallback", now)
        elif now - get(db, "last_fallback", now) >= config.get("fallback_seconds", 28800):
            changes.append(add_event(db, "[watch deadline: inspect queue liveness]", str(int(now)), now))
            put(db, "last_fallback", now)
        put(db, "last_scan", now)
    return changes


def prompt(events):
    rows = "\n".join(f"- {e['id']}: {e['path']}" for e in events)
    return ("Sounding Line operational wake. Continue the existing authorized task and load "
        ".agents/skills/grind/SKILL.md. Inspect these final produces or liveness events; "
        "this message contains no scientific verdict and grants no new research, gear, "
        "spend, or delegation authority. Follow the active stage's internal write-through "
        "and final-packet policy. Do not report unfinished per-artifact scores.\n" + rows +
        "\nAfter each full write-through (or documented liveness inspection), acknowledge "
        "with python tools/codex_watch.py ack EVENT_ID. Do not acknowledge merely receiving this message.")


def deliver(config, *, state=STATE, repo=REPO, runner=subprocess.run, now=None):
    now = time.time() if now is None else now
    if (state / "watch.cancel").exists():
        return "cancelled"
    with database(state) as db:
        owner = get(db, "owner")
        if not owner:
            return "no-owner"
        # A queued landing is already assigned; never bombard a disconnected session.
        if db.execute("SELECT 1 FROM events WHERE state IN ('queued','sending','unknown') "
                      "AND acknowledged IS NULL LIMIT 1").fetchone():
            return "awaiting-acknowledgement"
        events = [dict(r) for r in db.execute(
            "SELECT * FROM events WHERE state='pending' AND next_try<=? ORDER BY created LIMIT 20", (now,))]
        if not events:
            return "nothing-pending"
        for event in events:
            db.execute("UPDATE events SET state='sending',attempts=attempts+1 WHERE id=?", (event["id"],))
    if (state / "watch.cancel").exists():
        with database(state) as db:
            for event in events:
                db.execute("UPDATE events SET state='pending' WHERE id=?", (event["id"],))
        return "cancelled"
    cmd = [config["codex"], "queue", "--thread", owner, "--message", prompt(events)]
    if config.get("remote"):
        cmd += ["--remote", config["remote"]]
    try:
        result = runner(cmd, cwd=repo, capture_output=True, text=True, timeout=45)
        match = re.search(r"Queued message ([0-9a-f-]+) for thread ([0-9a-f-]+)", result.stdout)
        if result.returncode == 0 and match and match[2] == owner:
            status, queue_id, error = "queued", match[1], None
        else:
            # A zero exit without the documented receipt is ambiguous, not successful.
            status, queue_id = ("unknown" if result.returncode == 0 else "pending"), None
            error = f"queue exit={result.returncode}; valid receipt absent"
    except subprocess.TimeoutExpired:
        status, queue_id, error = "unknown", None, "queue timed out; inspect queue before retry"
    except OSError as exc:
        status, queue_id, error = "pending", None, type(exc).__name__
    with database(state) as db:
        for event in events:
            attempts = event["attempts"] + 1
            settled = "failed" if status == "pending" and attempts >= 5 else status
            db.execute("UPDATE events SET state=?,queue_id=?,error=?,next_try=? WHERE id=?",
                (settled, queue_id, error, now + min(3600, 60 * 2**attempts), event["id"]))
    return status


def acknowledge(event_id, *, state=STATE):
    with database(state) as db:
        row = db.execute("SELECT state FROM events WHERE id=?", (event_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown event ID")
        db.execute("UPDATE events SET state='acknowledged',acknowledged=? WHERE id=?",
                   (time.time(), event_id))


def register_queue(*, repo=REPO, state=STATE):
    """Explicit, agent-reviewed inventory step; the waiting service never imports code.

    run_name avoids the queue's __main__ entry point. This reads the same constructed
    STAGES the engine sees, including loops and composed paths missed by text scans.
    """
    import runpy
    source = repo / "runners/run_queue.py"
    module = runpy.run_path(str(source), run_name="codex_queue_inventory")
    paths = []
    for stage in module["STAGES"]:
        produce = stage.get("produces")
        if produce:
            paths.append(produce)
        elif stage["name"] == "multiplicity":
            # Existing always-run audit intentionally bypasses a skip guard.
            paths.append("results/multiplicity.json")
        else:
            raise ValueError(f"Stage without a final produce: {stage['name']}")
    atomic_json(state / "queue-produces.json", {"source_sha256": digest(source), "paths": sorted(set(paths))})
    return len(paths)


def status(state=STATE):
    with database(state) as db:
        return {"owner": get(db, "owner"), "owner_phase": get(db, "owner_phase"),
            "watcher": get(db, "watcher"), "last_scan": get(db, "last_scan"),
            "watch_error": get(db, "watch_error"),
            "cancelled": (state / "watch.cancel").exists(),
            "wake_probe_received": get(db, "wake_probe_received"),
            "events": [dict(r) for r in db.execute("SELECT events.*,deliveries.at AS delivered_at "
                "FROM events LEFT JOIN deliveries ON events.id=deliveries.event_id "
                "WHERE acknowledged IS NULL")],
            "notification_failures": [dict(r) for r in db.execute(
                "SELECT * FROM notifications WHERE state NOT IN ('sent')")],
            "recent_hooks": [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY at DESC LIMIT 8")]}


def run(config, state=STATE, repo=REPO):
    with singleton(state / "watcher.lock"):
        with database(state) as db:
            # A crash between queue acceptance and persisting its ID cannot safely replay.
            db.execute("UPDATE events SET state='unknown',error='watcher restarted during send; reconcile queue' "
                       "WHERE state='sending'")
            put(db, "watcher", {"pid": os.getpid(), "started": time.time(),
                "source_sha256": digest(Path(__file__)),
                "common_sha256": digest(Path(__file__).with_name("codex_common.py"))})
        while not (state / "watch.cancel").exists():
            try:
                if (state / "watch.json").exists():
                    config = json.loads((state / "watch.json").read_text(encoding="utf-8"))
                scan(config, repo=repo, state=state)
                deliver(config, repo=repo, state=state)
                with database(state) as db:
                    put(db, "watch_error", None)
            except Exception as exc:
                with database(state) as db:
                    put(db, "watch_error", type(exc).__name__ + ": " + str(exc)[:200])
            # The helper waits, not an occupied agent turn. Cancellation latency <= 1 second.
            for _ in range(max(1, int(config.get("interval_seconds", 60)))):
                if (state / "watch.cancel").exists():
                    break
                time.sleep(1)


def wait_stopped(state=STATE, timeout=50):
    """Wait for the cancelled helper to release its kernel lock before resuming."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            with singleton(state / "watcher.lock"):
                return
        except OSError:
            if time.monotonic() >= deadline:
                raise TimeoutError("Watcher still holds its lock; cancellation remains in place")
            time.sleep(0.2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["baseline", "scan", "run", "deliver", "status", "bind", "handoff", "register", "register-queue", "ack", "retry", "cancel", "wait-stopped"])
    parser.add_argument("value", nargs="?")
    parser.add_argument("--previous", help="Current owner UUID for an explicit cancelled-watcher handoff")
    parser.add_argument("--since", type=float, help="Baseline cutoff epoch; newer produces remain pending")
    args = parser.parse_args()
    if args.command == "wait-stopped":
        wait_stopped(); return
    if args.command == "status":
        print(json.dumps(status(), indent=2)); return
    if args.command == "bind":
        uuid.UUID(args.value)
        with database() as db:
            previous = get(db, "owner")
            if previous and previous != args.value:
                raise ValueError("Another session owns the watcher; use the documented handoff procedure")
            put(db, "owner", args.value)
            put(db, "owner_phase", "active")
        return
    if args.command == "ack":
        acknowledge(args.value); return
    if args.command == "handoff":
        uuid.UUID(args.value)
        if not (STATE / "watch.cancel").exists():
            raise ValueError("Cancel the watcher before handing off ownership")
        with database() as db:
            if get(db, "owner") != args.previous:
                raise ValueError("Previous owner does not match")
            if db.execute("SELECT 1 FROM events WHERE state IN ('queued','sending','unknown') "
                          "AND acknowledged IS NULL").fetchone():
                raise ValueError("Reconcile and acknowledge the old session's outstanding messages first")
            put(db, "owner", args.value)
            put(db, "owner_phase", "active")
        return
    if args.command == "retry":
        with database() as db:
            row = db.execute("SELECT state FROM events WHERE id=?", (args.value,)).fetchone()
            if not row or row[0] not in {"failed", "unknown"}:
                raise ValueError("Retry only a failed/unknown event after reconciling the Codex queue")
            db.execute("UPDATE events SET state='pending',attempts=0,next_try=0,error=NULL WHERE id=?", (args.value,))
        return
    if args.command == "cancel":
        STATE.mkdir(exist_ok=True)
        (STATE / "watch.cancel").write_text("cancel\n"); return
    if args.command == "register-queue":
        print(f"Registered {register_queue()} queue produces")
        return
    config = json.loads((STATE / "watch.json").read_text(encoding="utf-8"))
    if args.command == "register":
        path = (REPO / args.value).resolve()
        name = path.relative_to(REPO).as_posix()
        config["paths"] = sorted(set(config.get("paths", []) + [name]))
        atomic_json(STATE / "watch.json", config)
        print(f"Registered {name}; an already present produce will be inspected, not silently baselined")
        return
    if args.command == "baseline":
        with database() as db:
            if get(db, "baseline_at"):
                raise ValueError("Baseline already exists; do not hide pending landings")
        print(scan(config, baseline=True, baseline_since=args.since))
    elif args.command == "scan":
        print(scan(config))
    elif args.command == "deliver":
        print(deliver(config))
    else:
        run(config)


if __name__ == "__main__":
    main()
