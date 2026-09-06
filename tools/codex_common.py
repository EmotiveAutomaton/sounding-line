"""Local operational state, separate from scientific records. Standard library only."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

REPO = Path(__file__).resolve().parents[1]
STATE = REPO / ".agent-state"


@contextlib.contextmanager
def database(state: Path = STATE):
    state.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(state / "runtime.sqlite", timeout=20)
    db.row_factory = sqlite3.Row
    db.executescript("""
      CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS observed (path TEXT PRIMARY KEY, digest TEXT);
      CREATE TABLE IF NOT EXISTS file_stats (path TEXT PRIMARY KEY, size INTEGER, mtime_ns INTEGER);
      CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY, path TEXT NOT NULL, digest TEXT NOT NULL,
        created REAL NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
        attempts INTEGER NOT NULL DEFAULT 0, next_try REAL NOT NULL DEFAULT 0,
        queue_id TEXT, error TEXT, acknowledged REAL);
      CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY, state TEXT NOT NULL, updated REAL NOT NULL, error TEXT);
      CREATE TABLE IF NOT EXISTS audit (
        at REAL NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS deliveries (
        event_id TEXT PRIMARY KEY, at REAL NOT NULL, session TEXT NOT NULL);
    """)
    try:
        yield db
        db.commit()
    finally:
        db.close()


def get(db, key, default=None):
    row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def put(db, key, value):
    db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, json.dumps(value)))


def audit(db, event, detail):
    db.execute("INSERT INTO audit VALUES (?,?,?)", (time.time(), event, json.dumps(detail)))


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def digest(path: Path):
    try:
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None


@contextlib.contextmanager
def singleton(path: Path):
    """Kernel-held lock; exits release it even after crashes, unlike PID-only files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as f:
        if f.tell() == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            f.seek(0)
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
