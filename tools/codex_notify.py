"""Codex -> existing ntfy wristwork bus. No network at import, no credentials in Git."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

from codex_common import STATE, database


def snippet(text, limit=90):
    text = " ".join((text or "").split())
    for stop in (". ", "! ", "? "):
        i = text.find(stop)
        if 0 < i < limit:
            return text[:i + 1]
    return text[:limit] + ("…" if len(text) > limit else "")


def settings(path=None):
    path = path or Path.home() / ".codex" / "sounding-line" / "bus.conf"
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    if not values.get("BASE", "").startswith(("https://", "http://")):
        raise ValueError("ntfy BASE missing or invalid")
    return values


def send(kind, payload, *, state=STATE, config=None, opener=urllib.request.urlopen):
    """A repeated Stop/approval event sends once. Ambiguous network failures stay visible.

    No automatic replay after an uncertain POST: ntfy has no idempotency key. This
    preserves deduplication without claiming exactly-once delivery over HTTP.
    """
    key = hashlib.sha256(json.dumps([kind, payload.get("session_id"),
        payload.get("turn_id"), payload.get("tool_use_id"),
        payload.get("last_assistant_message", "")], sort_keys=True).encode()).hexdigest()
    with database(state) as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM notifications WHERE id=?", (key,)).fetchone():
            return "duplicate"
        db.execute("INSERT INTO notifications VALUES (?,?,?,NULL)", (key, "sending", time.time()))
    outcome, error = "sent", None
    try:
        cfg = config or settings()
        base = cfg["BASE"].rstrip("/")
        headers = {"User-Agent": "wristwork-hook/1.0"}
        if cfg.get("TOKEN"):
            headers["Authorization"] = "Bearer " + cfg["TOKEN"]

        def last_time(topic, match):
            try:
                req = urllib.request.Request(f"{base}/{topic}/json?poll=1&since=96h", headers=headers)
                with opener(req, timeout=3) as response:
                    rows = response.read().decode(errors="replace").splitlines()
                best = 0
                for line in rows:
                    try:
                        row = json.loads(line)
                        if row.get("event") == "message" and match(row.get("message", "")):
                            best = max(best, int(row.get("time", 0)))
                    except (ValueError, TypeError):
                        continue
                return best
            except Exception:
                return 0

        project = "SoundingLine"
        if kind == "done":
            msg = f"done: {project}"
            text = snippet(payload.get("last_assistant_message"))
            if text:
                msg += ": " + text
            done = last_time("agents", lambda m: m.lower().startswith("done: soundingline"))
            ack = last_time("acks", lambda m: True)
            priority = "min" if done and done > ack else "default"
        else:
            msg, priority = f"needs input: {project}", "high"
        if payload.get("notification_test"):
            msg += " (migration test; no action needed)"
        req = urllib.request.Request(f"{base}/agents", data=msg.encode("utf-8"),
            headers={**headers, "Title": "Codex", "Priority": priority})
        with opener(req, timeout=3) as response:
            response.read()
    except Exception as exc:
        # Never put endpoint URLs, bearer tokens, or arbitrary server bodies into logs.
        outcome, error = "failed_or_unknown", type(exc).__name__
        if isinstance(exc, urllib.error.HTTPError):
            error += f" HTTP {exc.code}"
    with database(state) as db:
        db.execute("UPDATE notifications SET state=?,updated=?,error=? WHERE id=?",
                   (outcome, time.time(), error, key))
    return outcome
